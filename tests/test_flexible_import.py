from pathlib import Path
from app.importer import parse, structured_rows, classify


def test_excel_like_with_preamble_and_separate_columns():
    rows=[['Mis ingresos'],['Periodo enero'],['Fecha','Concepto','Crédito','Débito','Saldo'],
          ['12/09/2026','Clase de matemáticas','250.00',None,'350.00'],
          ['13/09/2026','Compra',None,'100.00','250.00']]
    result=structured_rows(rows)
    assert len(result)==2
    assert result[0]['category']=='variable'
    assert result[1]['category']=='gasto'


def test_unknown_incoming_remains_pending():
    assert classify('ACH persona desconocida')[0]=='pendiente'
    assert classify('BI-APP TRANSF DE CTA GT 4443488')[0]=='pendiente'
    assert classify('Clases de matemáticas')[0]=='variable'


def test_bank_statement_fixture_if_present():
    path=Path(__file__).parent/'fixtures'/'estado_cuenta_sintetico.pdf'
    if path.exists():
        rows,_=parse(path.name,path.read_bytes())
        assert len(rows)>0
        assert any(r['category']=='gasto' for r in rows)
