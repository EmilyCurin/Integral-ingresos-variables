from fastapi.testclient import TestClient
from app import storage
from app.main import app

def test_local_import_without_password(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    monkeypatch.setattr(storage,'BASE',tmp_path)
    c=TestClient(app)
    assert c.get('/api/state').json()['authenticated']
    row={'date':'2026-08-01','amount_cents':20000,'description':'clase','category':'recurrente'}
    assert c.post('/api/import',json={'rows':[row]}).json()['added']==1
    assert c.get('/api/data').json()['movements'][0]['description']=='clase'
    assert c.post('/api/import',json={'rows':[row]}).json()['duplicates_skipped']==1
