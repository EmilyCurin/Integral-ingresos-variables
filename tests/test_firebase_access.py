from fastapi.testclient import TestClient
from app.main import app
from app import storage

def test_missing_firebase_token_is_rejected(monkeypatch):
    monkeypatch.delenv('INTEGRAL_DEV_AUTH',raising=False)
    client=TestClient(app)
    response=client.get('/api/data')
    assert response.status_code==401
    assert 'Google' in response.json()['detail']

def test_login_page_is_public_and_private_api_is_not(monkeypatch):
    monkeypatch.delenv('INTEGRAL_DEV_AUTH',raising=False)
    client=TestClient(app)
    assert client.get('/').status_code==200
    assert b'Continuar con Google' in client.get('/').content
    assert client.get('/api/export').status_code==401

def test_user_isolation_via_api(tmp_path,monkeypatch):
    monkeypatch.setenv('INTEGRAL_DEV_AUTH','1')
    monkeypatch.setattr(storage,'BASE',tmp_path)
    client=TestClient(app)
    assert client.post('/api/movement',json={'date':'2026-10-01','amount':'250.00','description':'clase','category':'variable'}).status_code==200
    assert len(client.get('/api/data').json()['movements'])==1
    storage.CURRENT_UID.set('different-user')
    assert storage.movements(storage.local_fernet())==[]
