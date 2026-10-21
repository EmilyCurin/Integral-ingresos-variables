"""Bóveda local monousuario: contraseña con scrypt y campos/archivos cifrados con Fernet."""
import sqlite3, os, json, secrets, hashlib, base64, hmac
from pathlib import Path
from cryptography.fernet import Fernet, InvalidToken

BASE = Path(os.environ.get('INCOME_DATA_DIR', Path(__file__).resolve().parent.parent / 'data'))
BASE.mkdir(parents=True, exist_ok=True)
DB = BASE / 'vault.db'

SCHEMA = '''
CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY, filename TEXT, encrypted BLOB, uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS movements (id INTEGER PRIMARY KEY, date TEXT NOT NULL, payload BLOB NOT NULL, category TEXT NOT NULL, document_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, date TEXT NOT NULL, payload BLOB NOT NULL);
'''

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con

def local_fernet():
    """Key file local; use only with loopback binding. Not compatible with old password vaults."""
    key_file=BASE/'local.key'
    if not key_file.exists():
        fd=os.open(key_file,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'wb') as f: f.write(Fernet.generate_key())
    return Fernet(key_file.read_bytes())

def configured():
    with db() as con: return bool(con.execute("SELECT 1 FROM settings WHERE key='pw_hash'").fetchone())

def derive(password, salt):
    return hashlib.scrypt(password.encode(), salt=salt, n=2**14, r=8, p=1, dklen=32)

def setup(password):
    if len(password) < 10: raise ValueError('La contraseña debe tener al menos 10 caracteres')
    with db() as con:
        if configured(): raise ValueError('Ya existe una bóveda')
        salt = secrets.token_bytes(16)
        key = derive(password,salt)
        con.execute("INSERT INTO settings VALUES('salt',?)", (salt.hex(),))
        con.execute("INSERT INTO settings VALUES('pw_hash',?)", (hashlib.sha256(key).hexdigest(),))
        con.execute("INSERT INTO settings VALUES('check',?)", (Fernet(base64.urlsafe_b64encode(key)).encrypt(b'vault-ok').decode(),))

def unlock(password):
    with db() as con:
        rows = dict(con.execute("SELECT key,value FROM settings").fetchall())
    if not rows: raise ValueError('Primero configure su contraseña')
    key = derive(password,bytes.fromhex(rows['salt']))
    if not hmac.compare_digest(hashlib.sha256(key).hexdigest(),rows['pw_hash']):
        raise ValueError('Contraseña incorrecta')
    return Fernet(base64.urlsafe_b64encode(key))

def encrypt_json(fernet, obj): return fernet.encrypt(json.dumps(obj,ensure_ascii=False).encode())
def decrypt_json(fernet, b): return json.loads(fernet.decrypt(b))

def put_document(fernet, name, data):
    with db() as con:
        cur = con.execute('INSERT INTO documents(filename,encrypted) VALUES(?,?)', (Path(name).name,fernet.encrypt(data)))
        return cur.lastrowid

def add_movement(fernet, movement, document_id=None):
    payload = {k:movement.get(k,'') for k in ('amount_cents','description','source','note')}
    with db() as con:
        cur = con.execute('INSERT INTO movements(date,payload,category,document_id) VALUES(?,?,?,?)',
                          (movement['date'],encrypt_json(fernet,payload),movement['category'],document_id))
        return cur.lastrowid

def movements(fernet):
    with db() as con: rows = con.execute('SELECT * FROM movements ORDER BY date DESC,id DESC').fetchall()
    return [dict(id=r['id'],date=r['date'],category=r['category'],document_id=r['document_id'],
                 **decrypt_json(fernet,r['payload'])) for r in rows]

def update_movement(fernet, id, patch):
    with db() as con:
        row = con.execute('SELECT * FROM movements WHERE id=?',(id,)).fetchone()
        if row is None: return False
        data = decrypt_json(fernet,row['payload'])
        data.update({k:v for k,v in patch.items() if k in ('amount_cents','description','source','note')})
        con.execute('UPDATE movements SET date=?,category=?,payload=? WHERE id=?',
                    (patch.get('date',row['date']),patch.get('category',row['category']),encrypt_json(fernet,data),id))
        return True

def delete_movement(id):
    with db() as con: return con.execute('DELETE FROM movements WHERE id=?',(id,)).rowcount > 0

def add_note(fernet, date, text):
    with db() as con: con.execute('INSERT INTO notes(date,payload) VALUES(?,?)',(date,fernet.encrypt(text.encode())))
def notes(fernet):
    with db() as con: rows = con.execute('SELECT * FROM notes ORDER BY date DESC').fetchall()
    return [{'id':r['id'],'date':r['date'],'text':fernet.decrypt(r['payload']).decode()} for r in rows]
def delete_note(id):
    with db() as con: return con.execute('DELETE FROM notes WHERE id=?',(id,)).rowcount > 0

def documents():
    with db() as con: return [dict(id=r['id'],filename=r['filename'],uploaded_at=r['uploaded_at']) for r in con.execute('SELECT id,filename,uploaded_at FROM documents ORDER BY id DESC')]
def get_document(fernet,id):
    with db() as con: row = con.execute('SELECT filename,encrypted FROM documents WHERE id=?',(id,)).fetchone()
    return (row['filename'],fernet.decrypt(row['encrypted'])) if row else None
