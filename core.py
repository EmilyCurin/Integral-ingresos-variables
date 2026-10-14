"""Cálculos reproducibles sin depender de IA."""
from collections import defaultdict
from statistics import median, pstdev
from datetime import date

INCOME = {'recurrente', 'variable', 'extraordinario'}
EXCLUDED = {'excluir', 'reembolso', 'transferencia_propia', 'prestamo', 'gasto', 'pendiente'}
CATEGORIES = sorted(INCOME | EXCLUDED)

def month_key(value):
    return str(value)[:7]

def summary(rows, start=None, end=None, monthly_budget=None):
    selected = [r for r in rows if (not start or r['date'] >= start) and (not end or r['date'] <= end)]
    selected.sort(key=lambda r: r['date'])
    monthly = defaultdict(lambda: {'total': 0, 'regular': 0, 'extra': 0, 'count': 0})
    sources = defaultdict(int)
    for r in selected:
        if r['category'] not in INCOME: continue
        amount = int(r['amount_cents'])
        m = monthly[month_key(r['date'])]
        m['total'] += amount
        m['count'] += 1
        if r['category'] == 'extraordinario': m['extra'] += amount
        else: m['regular'] += amount
        sources[r.get('source') or 'Sin fuente'] += amount
    # No imputar meses vacíos al calcular un promedio observacional: explicar muestra.
    keys = sorted(monthly)
    values = [monthly[k]['total'] for k in keys]
    regular = [monthly[k]['regular'] for k in keys]
    avg = round(sum(values) / len(values)) if values else 0
    baseline = round(median(regular)) if regular else 0
    variability = round(pstdev(regular)) if len(regular) > 1 else 0
    prediction = None
    if regular:
        expected = baseline
        prediction = {'conservador': max(0, expected - variability), 'esperado': expected,
                      'optimista': expected + variability,
                      'method': 'Mediana de ingresos no extraordinarios por mes con ingresos; rango ± desviación estándar. No garantiza resultados.',
                      'months_used': len(regular)}
    budget = None
    if monthly_budget is not None and prediction:
        margin = max(0, prediction['conservador'] - monthly_budget)
        budget = {'presupuesto_centavos': monthly_budget, 'margen_conservador_centavos': margin,
                  'ahorro_sugerido_centavos': round(margin * 0.5),
                  'method': 'Referencia: 50% del margen entre escenario conservador y presupuesto; no considera deudas o emergencias no declaradas.'}
    return {'movements': len(selected), 'income_cents': sum(values), 'avg_cents': avg,
            'active_months': len(keys), 'extra_cents': sum(monthly[k]['extra'] for k in keys),
            'monthly': [{'month': k, **monthly[k]} for k in keys],
            'sources': [{'name': k, 'amount_cents': v} for k,v in sorted(sources.items(), key=lambda x:-x[1])],
            'prediction': prediction, 'savings': budget,
            'warnings': ['Los meses sin movimientos no se incluyen en el promedio ni la predicción.',
                         'Las notas deben reflejarse en las categorías revisadas para afectar la estimación.']}

def parse_amount(text):
    """Admite Q1,234.56 o 1.234,56; rechaza valores ambiguos como 1,234."""
    import re
    from decimal import Decimal, InvalidOperation
    raw = str(text or '').strip().replace('Q','').replace('$','').replace(' ','')
    neg = raw.startswith('-')
    raw = raw.lstrip('+-')
    if not re.fullmatch(r'\d[\d.,]*', raw): raise ValueError('Monto inválido')
    if ',' in raw and '.' in raw:
        decimal_sep = ',' if raw.rfind(',') > raw.rfind('.') else '.'
        thousand_sep = '.' if decimal_sep == ',' else ','
        raw = raw.replace(thousand_sep, '').replace(decimal_sep, '.')
    elif ',' in raw:
        if raw.count(',') == 1 and len(raw.split(',')[-1]) in (1,2): raw = raw.replace(',','.')
        elif raw.count(',') >= 1 and all(len(s)==3 for s in raw.split(',')[1:]): raw = raw.replace(',','')
        else: raise ValueError('Separadores ambiguos')
    elif '.' in raw and raw.count('.') > 1:
        if all(len(s)==3 for s in raw.split('.')[1:]): raw = raw.replace('.','')
        else: raise ValueError('Separadores ambiguos')
    elif '.' in raw and len(raw.split('.')[-1]) == 3: raise ValueError('Separadores ambiguos')
    try:
        value = Decimal(raw)
        if value <= 0 or value > 1000000000: raise ValueError('Monto fuera de rango')
        cents = int((value*100).quantize(Decimal('1')))
        return -cents if neg else cents
    except InvalidOperation: raise ValueError('Monto inválido')

def date_normalize(text):
    from datetime import datetime
    s = str(text or '').strip()
    for fmt in ('%Y-%m-%d','%d/%m/%Y','%d-%m-%Y','%d/%m/%y','%m/%d/%Y'):
        try: return datetime.strptime(s,fmt).date().isoformat()
        except ValueError: pass
    raise ValueError('Fecha inválida: ' + s)
