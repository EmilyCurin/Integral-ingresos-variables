"""IA en la nube (Gemini). La clave solo vive en el backend."""
import os, requests, json

API_URL='https://generativelanguage.googleapis.com/v1beta/models/'

def ai_status():
    return {'available':bool(os.getenv('GEMINI_API_KEY')),'provider':'Gemini','model':os.getenv('GEMINI_MODEL','gemini-2.5-flash')}

def gemini_json(prompt, max_tokens=3000):
    key=os.getenv('GEMINI_API_KEY','').strip()
    if not key: raise ValueError('Falta GEMINI_API_KEY. Se pueden usar las reglas sin IA.')
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    url=f'{API_URL}{model}:generateContent'
    response=requests.post(url,params={'key':key},json={'contents':[{'parts':[{'text':prompt}]}],
       'generationConfig':{'responseMimeType':'application/json','temperature':0,'maxOutputTokens':max_tokens}},timeout=75)
    response.raise_for_status()
    text=response.json()['candidates'][0]['content']['parts'][0]['text']
    return json.loads(text)

def interpret_notes(note, rows):
    sample=[{'descripcion':r.get('description','')[:90],'monto':r.get('amount_cents',0)/100,
             'categoria':r.get('category')} for r in rows[:30]]
    prompt=('Devuelve JSON {"respuesta":"..."} en español. Ayuda a entender ingresos variables, '
      'no inventes hechos ni modifiques montos. No asumas transferencias propias sin confirmación. '
      'NOTA: '+note[:2000]+' MOVIMIENTOS: '+json.dumps(sample,ensure_ascii=False))
    try: return str(gemini_json(prompt,1200).get('respuesta','Sin respuesta'))
    except (requests.RequestException,ValueError,KeyError,TypeError) as e:
        raise ValueError('IA en nube no disponible. Intenta otra vez o continúa con reglas locales.') from e
