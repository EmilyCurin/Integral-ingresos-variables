"""Clasificador: reglas locales + Gemini opcional; revisión antes de guardar."""
import json, re, unicodedata, os, requests
from .ai import gemini_json
from .core import CATEGORIES

CREDIT_CATS={'recurrente','variable','extraordinario','transferencia_propia','reembolso','prestamo','pendiente','excluir'}

def clean(s):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(s or '').casefold()) if not unicodedata.combining(c))

def rules(row, note=''):
    desc=clean(row.get('description',''))
    ctx=clean(note)
    old=row.get('category','pendiente')
    if old=='gasto':return 'gasto','alta','Débito bancario: no es un depósito.'
    # Inferencias limitadas: las coincidencias de texto NO demuestran titularidad.
    if re.search(r'\b(reembolso|devolucion|reintegro)\b',desc):return 'reembolso','media','Descripción compatible con reembolso.'
    if re.search(r'\b(prestamo|prestamo recibido)\b',desc):return 'prestamo','media','Descripción compatible con préstamo.'
    if 'transf de cta' in desc or 'transferencia entre cuentas' in desc:
        return 'pendiente','baja','Posible transferencia entre cuentas; falta verificar titularidad.'
    if re.search(r'\b(clases?|tutorias?|tutoras?|ajedrez|inscripc\w*|mensualidad|cuota mensual|maqueta|honorarios|servicio profesional)\b',desc):
        return 'variable','media','Concepto compatible con pago por servicios; confirmar si es habitual.'
    if int(row.get('amount_cents',0))>=200000:
        return 'pendiente','baja','Abono grande de origen incierto: confirmar una sola vez antes de contarlo como ingreso.'
    return 'variable','baja','Abono propuesto como ingreso variable; verificar si es transferencia o pago propio.'

def classify_batch(rows,note='',use_ai=True,model=None):
    if len(rows)>1500:raise ValueError('Máximo 1500 movimientos por lote')
    proposals=[]
    for i,row in enumerate(rows):
        cat,confidence,reason=rules(row,note)
        proposals.append({'index':i,'category':cat,'confidence':confidence,'reason':reason,'engine':'reglas'})
    if not use_ai or not os.getenv('GEMINI_API_KEY'):return {'proposals':proposals,'engine':'reglas','warning':'IA desactivada: reglas conservadoras; revisa los pendientes.'}
    # Limitar tamaño de solicitudes y no enviar información personal innecesaria.
    try:
        for offset in range(0,len(rows),30):
            subset=rows[offset:offset+30]
            payload=[{'id':offset+j,'descripcion':str(r.get('description',''))[:180],
                      'monto':round(int(r.get('amount_cents',0))/100,2),
                      'tipo':'DEBITO' if r.get('category')=='gasto' else 'CREDITO'} for j,r in enumerate(subset)]
            prompt=(
                'Eres un clasificador financiero cauteloso. Evalúa CADA movimiento del JSON, con las notas de la persona. '
                'Devuelve exclusivamente JSON {"items":[{"id":numero,"category":cadena,"confidence":"alta|media|baja","reason":cadena}]}. '
                'Categorías permitidas: recurrente, variable, extraordinario, transferencia_propia, reembolso, prestamo, pendiente, gasto, excluir. '
                'REGLAS: DEBITO siempre es gasto; NUNCA un préstamo o transferencia propia sin evidencia. '
                'Los nombres de comercios y gastos NO son transferencias propias. '
                'Un crédito o nota crédito NO demuestra ingreso por servicios. '
                'No adivines propiedad de cuentas ni periodicidad a partir de una sola transacción. '
                'Ante débitos, siempre gasto. Para créditos pequeños desconocidos sugiere variable con confianza baja; para abonos de 2000 GTQ o más sin origen claro, pendiente. No supongas que un monto alto es recurrente. Las notas son contexto, no prueban hechos faltantes. '
                'No inventes movimientos ni cambies montos. Todas tus etiquetas son propuestas que revisará la persona.\n'
                'NOTAS: '+note[:3000]+'\nMOVIMIENTOS: '+json.dumps(payload,ensure_ascii=False))
            answer=gemini_json(prompt,3500)
            items=answer.get('items',[]) if isinstance(answer,dict) else []
            if not isinstance(items,list):continue
            for item in items:
                if not isinstance(item,dict):continue
                idx=item.get('id')
                if type(idx)!=int or not offset<=idx<offset+len(subset):continue
                category=item.get('category')
                if category not in CATEGORIES:continue
                if rows[idx].get('category')=='gasto' and category!='gasto':continue
                if category=='gasto' and rows[idx].get('category')!='gasto':continue
                # Posible transferencia propia solo con confirmación explícita de titularidad en notas.
                if category=='transferencia_propia' and not any(x in clean(note) for x in ('cuenta propia','mis cuentas','cuentas mias','cuenta mia','mi otra cuenta')):
                    category='pendiente'
                confidence=item.get('confidence','baja')
                if confidence not in ('alta','media','baja'):confidence='baja'
                proposals[idx]={'index':idx,'category':category,'confidence':confidence,
                                'reason':str(item.get('reason','Clasificación contextual'))[:200], 'engine':'gemini'}
        return {'proposals':proposals,'engine':'gemini','warning':'Propuestas generadas con IA en la nube. Revisa las categorías antes de confirmar.'}
    except (requests.RequestException,ValueError,KeyError,TypeError,json.JSONDecodeError) as err:
        return {'proposals':proposals,'engine':'reglas','warning':'La IA no respondió; se aplicaron reglas locales conservadoras. Revisa los pendientes.'}
