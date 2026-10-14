import os
os.environ['INCOME_DATA_DIR']='/tmp/integral_test_vault'
from app import storage

def test_encrypt_roundtrip(tmp_path,monkeypatch):
    monkeypatch.setattr(storage,'DB',tmp_path/'test.db')
    storage.setup('contraseña-de-prueba-segura')
    import pytest
    with pytest.raises(ValueError): storage.unlock('incorrecta')
    f=storage.unlock('contraseña-de-prueba-segura')
    storage.add_movement(f,{'date':'2026-08-01','amount_cents':35000,'description':'Secreto','category':'variable'})
    assert storage.movements(f)[0]['amount_cents']==35000
    assert b'Secreto' not in (tmp_path/'test.db').read_bytes()
