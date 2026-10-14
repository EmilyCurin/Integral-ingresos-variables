import pytest
from fastapi.testclient import TestClient
from app import storage
from app.main import app

def test_auth_and_import(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    c=TestClient(app)
    assert c.get('/api/data').status_code==401
    assert c.post('/api/setup',json={'password':'contraseña-muy-segura'}).status_code==200
    r=c.post('/api/import',json={'rows':[{'date':'2026-08-01','amount_cents':20000,'description':'clase','category':'recurrente'}]})
    assert r.json()['added']==1
    assert c.get('/api/data').json()['movements'][0]['description']=='clase'
    assert c.post('/api/import',json={'rows':[{'date':'2026-08-01','amount_cents':20000,'description':'clase','category':'recurrente'}]}).json()['duplicates_skipped']==1
