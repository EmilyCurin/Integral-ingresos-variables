from app import storage

def test_encrypt_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(storage,'BASE',tmp_path)
    storage.CURRENT_UID.set('test-user')
    f=storage.local_fernet()
    storage.add_movement(f,{'date':'2026-08-01','amount_cents':35000,'description':'Secreto','category':'variable'})
    assert storage.movements(f)[0]['amount_cents']==35000
    assert b'Secreto' not in storage.user_db().read_bytes()

def test_separation_by_user(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'BASE',tmp_path)
    storage.CURRENT_UID.set('user-A')
    fa=storage.local_fernet()
    storage.add_movement(fa,{'date':'2026-09-01','amount_cents':10000,'description':'Privado A','category':'variable'})
    storage.CURRENT_UID.set('user-B')
    fb=storage.local_fernet()
    assert storage.movements(fb)==[]
    storage.CURRENT_UID.set('user-A')
    assert storage.movements(fa)[0]['description']=='Privado A'
