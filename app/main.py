import os, json, base64, secrets, hashlib, hmac, mimetypes
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent/'.env')
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from cryptography.fernet import Fernet
from . import storage as st
from .core import summary, date_normalize, parse_amount, CATEGORIES
from .importer import parse,MAX_BYTES
from .ai import ai_status, interpret_notes
from .classifier import classify_batch

ROOT=Path(__file__).resolve().parent.parent
app=FastAPI(title='Integral | Ingresos variables',docs_url=None,redoc_url=None)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')
# Uso LOCAL sin contraseña. Nunca se expone una bóveda compartida en una URL pública.
# Si se quiere publicar, implementar primero autenticación Google/Firebase y aislamiento por usuario.
def session_key(request):
    host=request.client.host if request.client else ''
    requested_host=request.headers.get('host','').split(':')[0].strip('[]').lower()
    if host not in ('127.0.0.1','::1','localhost','testclient') or requested_host not in ('127.0.0.1','::1','localhost','testserver'):
        raise HTTPException(403,'Datos privados: Integral requiere acceso local. Para acceso público implemente Firebase Auth y aislamiento por usuario.')
    return st.local_fernet()

def ensure_csrf(request):
    origin=request.headers.get('origin')
    host=request.headers.get('host')
    if origin and host and origin not in ('http://'+host,'https://'+host):
        raise HTTPException(403,'Origen inválido')

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
    session_key(request)
    return {'configured':True,'authenticated':True,'mode':'local'}

@app.get('/api/data')
def data(request:Request):
    f=session_key(request)
    return {'movements':st.movements(f),'notes':st.notes(f),'documents':st.documents(),
            'categories':CATEGORIES,'ai':ai_status()}

@app.post('/api/upload')
async def upload(request:Request,file:UploadFile=File(...)):
    session_key(request)
    raw=await file.read(MAX_BYTES+1)
    try: rows,preview=parse(file.filename or 'archivo',raw)
    except Exception as e: raise HTTPException(422,f'No se pudo leer el archivo: {e}')
    if len(rows)>1500: rows=rows[:1500]
    return {'rows':rows,'text_preview':preview,'filename':file.filename,'total_proposals':len(rows),
            'warning':'Revise montos y fechas, especialmente en PDF o imágenes. Nada se agrega hasta que confirme.'}

class ClassificationRequest(BaseModel):
    rows:list[dict]
    note:str=''
    use_ai:bool=True
@app.post('/api/classify-proposals')
def classify_proposals(request:Request,p:ClassificationRequest):
    session_key(request)
    if len(p.note)>5000: raise HTTPException(422,'Nota demasiado larga')
    if len(p.rows)>1500: raise HTTPException(422,'Demasiados movimientos')
    for r in p.rows:
        if r.get('category') not in CATEGORIES: raise HTTPException(422,'Categoría inválida')
        try:
            if int(r.get('amount_cents',0))<=0: raise ValueError()
        except (TypeError,ValueError): raise HTTPException(422,'Monto inválido')
    return classify_batch(p.rows,p.note,p.use_ai)

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
