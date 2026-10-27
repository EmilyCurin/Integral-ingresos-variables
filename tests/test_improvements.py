from app.classifier import rules


def test_unknown_small_credit_proposed_variable():
    category, confidence, _ = rules({'description':'ACH SIN REFERENCIA', 'category':'pendiente', 'amount_cents':15000})
    assert category == 'variable' and confidence == 'baja'


def test_unknown_large_credit_requires_review():
    category, _, _ = rules({'description':'ABONO', 'category':'pendiente', 'amount_cents':250000})
    assert category == 'pendiente'


def test_debit_remains_expense():
    category, _, _ = rules({'description':'PAGO IMPUESTOS', 'category':'gasto', 'amount_cents':350000})
    assert category == 'gasto'
