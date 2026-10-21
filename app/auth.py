"""Validate Firebase ID tokens on every protected API call.
Development bypass only when explicitly configured. NEVER on public deploy.
"""
import os
from fastapi import HTTPException, Request
from . import storage

try:
    import firebase_admin
    from firebase_admin import auth as fb_auth, credentials
except ImportError:
    firebase_admin=None

def verify_request(request:Request):
    if os.getenv('INTEGRAL_DEV_AUTH')=='1':
        if request.client and request.client.host not in ('127.0.0.1','::1','localhost','testclient'):
            raise HTTPException(403,'Modo desarrollo disponible solo localmente')
        uid='dev-local-user'
    else:
        token=request.headers.get('authorization','')
        if not token.startswith('Bearer '): raise HTTPException(401,'Inicia sesión con Google')
        if firebase_admin is None: raise HTTPException(503,'Falta firebase-admin en el servidor')
        try:
            if not firebase_admin._apps:
                project=os.environ.get('FIREBASE_PROJECT_ID','integral-18a66')
                service_json=os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
                if service_json:
                    import json
                    cred=credentials.Certificate(json.loads(service_json))
                    firebase_admin.initialize_app(cred,{'projectId':project})
                else:
                    firebase_admin.initialize_app(options={'projectId':project})
            decoded=fb_auth.verify_id_token(token[7:],check_revoked=False)
            uid=decoded['uid']
        except Exception:
            raise HTTPException(401,'Token Firebase inválido o vencido')
    storage.CURRENT_UID.set(uid)
    request.state.uid=uid
    return storage.local_fernet()
