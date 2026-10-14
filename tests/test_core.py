from app.core import summary,parse_amount,date_normalize

def test_money():
    assert parse_amount('Q1,234.50')==123450
    assert parse_amount('1.234,50')==123450
    assert parse_amount('250')==25000

def test_dates(): assert date_normalize('05/09/2026')=='2026-09-05'

def test_prediction_excludes_extra():
    rows=[{'date':'2026-07-01','amount_cents':25000,'category':'recurrente','source':'A'},
          {'date':'2026-08-01','amount_cents':25000,'category':'recurrente','source':'A'},
          {'date':'2026-08-02','amount_cents':500000,'category':'extraordinario','source':'B'}]
    r=summary(rows)
    assert r['income_cents']==550000
    assert r['prediction']['esperado']==25000

def test_exclusions():
    rows=[{'date':'2026-08-01','amount_cents':99900,'category':'transferencia_propia'}]
    assert summary(rows)['income_cents']==0
