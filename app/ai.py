"""Asistente local opcional. No se envían originales a servicios externos."""
import os, requests, json

def ollama_status():
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    model=os.getenv('OLLAMA_MODEL','gemma3:4b')
    try:
        r=requests.get(url+'/api/tags',timeout=2); r.raise_for_status()
        available=[m['name'] for m in r.json().get('models',[])]
        return {'available':True,'model':model,'installed':model in available,'models':available}
    except requests.RequestException: return {'available':False,'model':model,'installed':False,'models':[]}

def interpret_notes(note, rows):
    """Solo muestra sugerencias; no cambia datos automáticamente."""
    url=os.getenv('OLLAMA_URL','http://127.0.0.1:11434').rstrip('/')
    model=os.getenv('OLLAMA_MODEL','gemma3:4b')
    # Solo información que la persona decidió enviar a su servicio Ollama local.
    summary=[{'indice':i,'descripcion':r.get('description','')[:90], 'monto':r.get('amount_cents',0)/100,
              'categoria':r.get('category')} for i,r in enumerate(rows[:40])]
    prompt='''Eres un asistente para entender ingresos variables. Responde en ESPAÑOL, brevemente. Explica qué depósitos podrían ser extraordinarios, préstamos, reembolsos o transferencias propias según la nota. No inventes hechos. No recalcules montos. No asegures que tus clasificaciones sean correctas. Las sugerencias deben ser confirmadas por el usuario.\nNota: '''+note[:2000]+'\nMovimientos de muestra: '+json.dumps(summary,ensure_ascii=False)
    try:
        r=requests.post(url+'/api/generate',json={'model':model,'prompt':prompt,'stream':False,
                        'options':{'num_predict':350,'temperature':0.2}},timeout=45)
        r.raise_for_status()
        return r.json().get('response','Sin interpretación disponible')
    except requests.RequestException as e:
        raise ValueError('Ollama no disponible o modelo no instalado. Puede seguir sin IA; consulte el README.') from e
