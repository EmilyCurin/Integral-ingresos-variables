import os, json, base64, secrets, hashlib, hmac, mimetypes
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from cryptography.fernet import Fernet
from . import storage as st
from .core import summary, date_normalize, parse_amount, CATEGORIES
from .importer import parse,MAX_BYTES
from .ai import ollama_status, interpret_notes

ROOT=Path(__file__).resolve().parent.parent
SECRET_PATH=st.BASE/'session.secret'
if not SECRET_PATH.exists():
    SECRET_PATH.write_text(secrets.token_hex(32))
    try: os.chmod(SECRET_PATH,0o600)
    except OSError: pass
serializer=URLSafeTimedSerializer(SECRET_PATH.read_text())
app=FastAPI(title='Integral | Ingresos variables',docs_url=None,redoc_url=None)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
# Contraseña derivada nunca se guarda en cookie; sesión cifrada autenticada que contiene la clave.
SESSION_HOURS=8
ACTIVE_SESSIONS={}  # Claves solo en memoria del servidor, nunca en cookies.

def session_key(request):
    token=request.cookies.get('iv_session')
    if not token: raise HTTPException(401,'Inicie sesión')
    try:
        payload=serializer.loads(token,max_age=SESSION_HOURS*3600)
        key=ACTIVE_SESSIONS.get(payload['sid'])
        if not key: raise ValueError('Sesión no activa')
        return Fernet(base64.urlsafe_b64encode(key))
    except (BadSignature,SignatureExpired,ValueError,KeyError): raise HTTPException(401,'Sesión vencida')

def login_response(key):
    sid=secrets.token_urlsafe(32)
    ACTIVE_SESSIONS[sid]=key
    res=JSONResponse({'ok':True})
    res.set_cookie('iv_session',serializer.dumps({'sid':sid}),max_age=SESSION_HOURS*3600,
                   httponly=True,samesite='strict',secure=False,path='/')
    return res

def ensure_csrf(request):
    origin=request.headers.get('origin')
    host=request.headers.get('host')
    if origin and host and origin not in ('http://'+host,'https://'+host): raise HTTPException(403,'Origen inválido')

@app.middleware('http')
async def guard(request,call_next):
    if request.method in ('POST','PUT','PATCH','DELETE'): ensure_csrf(request)
    response=await call_next(request)
    response.headers['Cache-Control']='no-store'
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'"
    return response

@app.get('/')
def index(): return FileResponse(ROOT/'static'/'index.html')
@app.get('/api/state')
def state(request:Request):
    auth=False
    try: session_key(request); auth=True
    except HTTPException: pass
    return {'configured':st.configured(),'authenticated':auth}
class Password(BaseModel): password:str
@app.post('/api/setup')
def setup(p:Password):
    try:
        st.setup(p.password)
        return make_login(p.password)
    except ValueError as e: raise HTTPException(400,str(e))
def make_login(password):
    # Obtiene material derivado para sesión solo luego de verificar credenciales.
    with st.db() as con: salt=bytes.fromhex(con.execute("SELECT value FROM settings WHERE key='salt'").fetchone()[0])
    st.unlock(password)
    return login_response(st.derive(password,salt))
@app.post('/api/login')
def login(p:Password):
    try: return make_login(p.password)
    except ValueError as e: raise HTTPException(401,str(e))
@app.post('/api/logout')
def logout(request:Request):
    token=request.cookies.get('iv_session')
    try:
        if token: ACTIVE_SESSIONS.pop(serializer.loads(token,max_age=SESSION_HOURS*3600)['sid'],None)
    except (BadSignature,SignatureExpired,KeyError): pass
    r=JSONResponse({'ok':True});r.delete_cookie('iv_session');return r

@app.get('/api/data')
def data(request:Request):
    f=session_key(request)
    return {'movements':st.movements(f),'notes':st.notes(f),'documents':st.documents(),
            'categories':CATEGORIES,'ollama':ollama_status()}

@app.post('/api/upload')
async def upload(request:Request,file:UploadFile=File(...)):
    session_key(request)
    raw=await file.read(MAX_BYTES+1)
    try: rows,preview=parse(file.filename or 'archivo',raw)
    except Exception as e: raise HTTPException(422,f'No se pudo leer el archivo: {e}')
    if len(rows)>1500: rows=rows[:1500]
    return {'rows':rows,'text_preview':preview,'filename':file.filename,'total_proposals':len(rows),
            'warning':'Revise montos y fechas, especialmente en PDF o imágenes. Nada se agrega hasta que confirme.'}

class ImportBatch(BaseModel):
    filename:str='registro_manual'
    rows:list[dict]
    original_base64:str|None=None
@app.post('/api/import')
def batch(request:Request,p:ImportBatch):
    f=session_key(request)
    if len(p.rows)>1500: raise HTTPException(400,'Máximo 1500 movimientos por lote')
    validated=[]
    for row in p.rows:
        try:
            dt=date_normalize(row.get('date'))
            cents=int(row.get('amount_cents'))
            if cents<=0 or cents>100000000000: raise ValueError('Monto inválido')
            category=row.get('category','pendiente')
            if category not in CATEGORIES: raise ValueError('Categoría inválida')
            validated.append({'date':dt,'amount_cents':cents,'category':category,
                              'description':str(row.get('description',''))[:300],
                              'source':str(row.get('source',''))[:100], 'note':str(row.get('note',''))[:1000]})
        except (ValueError,TypeError,OverflowError) as e: raise HTTPException(422,str(e))
    existing={(r['date'],r['amount_cents'],r['description'].strip().casefold()) for r in st.movements(f)}
    doc_id=None
    if p.original_base64:
        try:
            content=base64.b64decode(p.original_base64,validate=True)
            if len(content)>MAX_BYTES: raise ValueError('Archivo demasiado grande')
            doc_id=st.put_document(f,p.filename,content)
        except Exception: raise HTTPException(422,'Documento adjunto inválido')
    added=skipped=0
    for row in validated:
        fingerprint=(row['date'],row['amount_cents'],row['description'].strip().casefold())
        if fingerprint in existing: skipped+=1; continue
        st.add_movement(f,row,doc_id);existing.add(fingerprint);added+=1
    return {'added':added,'duplicates_skipped':skipped,'document_id':doc_id}

class Movement(BaseModel):
    date:str
    amount:str
    description:str=''
    source:str=''
    category:str='pendiente'
    note:str=''
@app.post('/api/movement')
def create_movement(request:Request,p:Movement):
    f=session_key(request)
    try:
        if p.category not in CATEGORIES: raise ValueError('Categoría inválida')
        cents=parse_amount(p.amount)
        if cents<=0: raise ValueError('Use un monto positivo y categoría gasto si corresponde')
        return {'id':st.add_movement(f,{'date':date_normalize(p.date),'amount_cents':cents,
                 'description':p.description[:300],'source':p.source[:100], 'note':p.note[:1000], 'category':p.category})}
    except ValueError as e: raise HTTPException(422,str(e))
@app.patch('/api/movement/{id}')
def patch_movement(request:Request,id:int,p:dict):
    f=session_key(request)
    if 'category' in p and p['category'] not in CATEGORIES: raise HTTPException(422,'Categoría inválida')
    if 'date' in p:
        try: p['date']=date_normalize(p['date'])
        except ValueError as e: raise HTTPException(422,str(e))
    if 'amount_cents' in p:
        try:
            p['amount_cents']=int(p['amount_cents'])
            if p['amount_cents']<=0: raise ValueError('Monto inválido')
        except (TypeError,ValueError): raise HTTPException(422,'Monto inválido')
    if not st.update_movement(f,id,p): raise HTTPException(404,'No existe')
    return {'ok':True}
@app.delete('/api/movement/{id}')
def remove_movement(request:Request,id:int):
    session_key(request)
    if not st.delete_movement(id): raise HTTPException(404,'No existe')
    return {'ok':True}
class Note(BaseModel): date:str; text:str
@app.post('/api/note')
def note(request:Request,p:Note):
    f=session_key(request)
    if not p.text.strip(): raise HTTPException(422,'La nota está vacía')
    st.add_note(f,date_normalize(p.date),p.text[:3000])
    return {'ok':True}
@app.delete('/api/note/{id}')
def remove_note(request:Request,id:int):
    session_key(request)
    if not st.delete_note(id): raise HTTPException(404,'No existe')
    return {'ok':True}
class Analyze(BaseModel): start:str|None=None; end:str|None=None; budget:str|None=None
@app.post('/api/analyze')
def analyze(request:Request,p:Analyze):
    f=session_key(request)
    budget=None
    if p.budget:
        try: budget=parse_amount(p.budget)
        except ValueError as e: raise HTTPException(422,str(e))
    result=summary(st.movements(f),p.start,p.end,budget)
    result['notes']= [n for n in st.notes(f) if (not p.start or n['date']>=p.start) and (not p.end or n['date']<=p.end)]
    return result
class Ask(BaseModel): note:str
@app.post('/api/interpret')
def interpret(request:Request,p:Ask):
    f=session_key(request)
    try: return {'answer':interpret_notes(p.note,st.movements(f))}
    except ValueError as e: raise HTTPException(503,str(e))
@app.get('/api/document/{id}')
def document(request:Request,id:int):
    f=session_key(request)
    item=st.get_document(f,id)
    if not item: raise HTTPException(404,'No existe')
    filename,data=item
    return Response(data,media_type='application/octet-stream',headers={'Content-Disposition':f'attachment; filename="documento_{id}{Path(filename).suffix}"'})
@app.get('/api/export')
def export(request:Request):
    import csv,io
    f=session_key(request); s=io.StringIO(); w=csv.writer(s)
    w.writerow(['fecha','monto','descripcion','fuente','categoria','nota'])
    for r in st.movements(f): w.writerow([r['date'],f"{r['amount_cents']/100:.2f}",r['description'],r['source'],r['category'],r['note']])
    return Response('\ufeff'+s.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="ingresos_exportados.csv"'})
