"""Three end-to-end API flows with a simulated cloud model; no real users involved."""
import io
from fastapi.testclient import TestClient
from app import storage
from app.main import app


def test_document_to_predictions(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    monkeypatch.setattr(storage,'BASE',tmp_path)
    client=TestClient(app)
    csv=b'Fecha,Monto,Descripcion,Fuente\n2026-09-05,250.00,Mensualidad alumno A,Clases\n'
    upload=client.post('/api/upload',files={'file':('demo.csv',io.BytesIO(csv),'text/csv')})
    assert upload.status_code==200
    rows=upload.json()['rows']
    assert len(rows)==1
    assert rows[0]['amount_cents']==25000
    classify=client.post('/api/classify-proposals',json={'rows':rows,'note':'Son pagos de clases','use_ai':False})
    assert classify.status_code==200
    rows[0]['category']=classify.json()['proposals'][0]['category']
    assert client.post('/api/import',json={'rows':rows}).json()['added']==1
    report=client.post('/api/analyze',json={}).json()
    assert report['income_cents']==25000
    assert report['prediction']['esperado']>0


def test_contextual_classification_to_saved_category(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    monkeypatch.setattr(storage,'BASE',tmp_path)
    monkeypatch.setenv('GEMINI_API_KEY','fixture')
    import app.classifier as classifier
    monkeypatch.setattr(classifier,'gemini_json',lambda prompt, max_tokens:{'items':[{'id':0,'category':'extraordinario','confidence':'alta','reason':'Trabajo único según nota'}]})
    client=TestClient(app)
    rows=[{'date':'2026-09-07','amount_cents':120000,'description':'Maqueta','category':'variable','source':'Cliente'}]
    response=client.post('/api/classify-proposals',json={'rows':rows,'note':'La maqueta fue un trabajo único','use_ai':True})
    assert response.status_code==200
    assert response.json()['proposals'][0]['category']=='extraordinario'
    rows[0]['category']='extraordinario'
    assert client.post('/api/import',json={'rows':rows}).json()['added']==1
    assert client.get('/api/data').json()['movements'][0]['category']=='extraordinario'


def test_duplicate_import_not_counted_twice(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    monkeypatch.setattr(storage,'BASE',tmp_path)
    client=TestClient(app)
    row={'date':'2026-09-08','amount_cents':50000,'description':'Clase','category':'variable'}
    assert client.post('/api/import',json={'rows':[row]}).json()['added']==1
    assert client.post('/api/import',json={'rows':[row]}).json()['duplicates_skipped']==1
    assert client.post('/api/analyze',json={}).json()['income_cents']==50000
