from app.classifier import classify_batch

def test_rules_preserve_debits_and_uncertainty():
    rows=[{'category':'gasto','description':'PAGO IMPUESTOS','amount_cents':39500},
          {'category':'pendiente','description':'BI-APP TRANSF DE CTA GT 4443488','amount_cents':30000},
          {'category':'variable','description':'TUTORIA MATE','amount_cents':10000}]
    result=classify_batch(rows,'esa cuenta es mía',use_ai=False)
    assert [x['category'] for x in result['proposals']]==['gasto','pendiente','variable']

def test_gemini_applies_notes_but_never_relabels_debits(monkeypatch):
    import app.classifier as c
    monkeypatch.setenv('GEMINI_API_KEY','test')
    def fake_gemini(prompt,max_tokens):
        assert 'maqueta fue extraordinaria' in prompt
        return {'items':[{'id':0,'category':'prestamo','confidence':'alta'},
                         {'id':1,'category':'extraordinario','confidence':'alta'},
                         {'id':2,'category':'transferencia_propia','confidence':'alta'}]}
    monkeypatch.setattr(c,'gemini_json',fake_gemini)
    rows=[{'category':'gasto','description':'IMPUESTOS','amount_cents':300},
          {'category':'variable','description':'MAQUETA','amount_cents':20000},
          {'category':'pendiente','description':'BANCO TRANSFER','amount_cents':30000}]
    result=classify_batch(rows,'la maqueta fue extraordinaria')
    assert [x['category'] for x in result['proposals']]==['gasto','extraordinario','pendiente']
    assert result['engine']=='gemini'
