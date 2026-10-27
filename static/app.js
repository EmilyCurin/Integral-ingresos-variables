const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const categories=['pendiente','recurrente','variable','extraordinario','transferencia_propia','reembolso','prestamo','gasto','excluir'];
let data={movements:[],notes:[],documents:[]},pending=[],selectedFile=null;
let plannedAnswers={};
const money=c=>new Intl.NumberFormat('es-GT',{style:'currency',currency:'GTQ'}).format((Number(c)||0)/100);
const today=()=>new Date(Date.now()-new Date().getTimezoneOffset()*60000).toISOString().slice(0,10);
function notify(msg){$('#toast').textContent=msg;$('#toast').style.display='block';setTimeout(()=>$('#toast').style.display='none',5200)}
async function api(url,opts={}){let token=await window.integralAuth.token();let r=await fetch(url,{...opts,headers:{'Authorization':'Bearer '+token,...(opts.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(opts.headers||{})}});let j;try{j=await r.json()}catch{j={detail:'Error de respuesta'}};if(!r.ok)throw new Error(j.detail||'No fue posible completar la operación');return j}
const enc=x=>String(x??'');
function elem(tag,txt,cls){let el=document.createElement(tag);if(txt!==undefined)el.textContent=enc(txt);if(cls)el.className=cls;return el}
function paintCategory(s){s.dataset.category=s.value}
const option=(value,selected)=>{let s=document.createElement('select');categories.forEach(c=>{let o=document.createElement('option');o.value=c;o.textContent=c.replaceAll('_',' ');o.selected=c===selected;s.append(o)});paintCategory(s);s.addEventListener('change',()=>paintCategory(s));return s};
function showTab(name){$$('.tab').forEach(t=>t.classList.toggle('hidden',t.id!=='tab-'+name));$$('.tabs button').forEach(b=>b.classList.toggle('active',b.dataset.tab===name))}
async function init(){let user=await window.integralAuth.ready;if(user){await api('/api/state');await refresh()}}
window.addEventListener('integral-login',async()=>{try{await api('/api/state');await refresh()}catch(e){notify(e.message)}});
async function refresh(){data=await api('/api/data');renderLedger();renderNotes();renderDocs();renderFinancialTabs();let ai=data.ai;$('#ai-status').textContent=ai.available?'Gemini configurado: '+ai.model:'Gemini no está configurado; siguen disponibles las reglas locales.';await analyze()}
$$('.tabs button').forEach(b=>b.onclick=()=>showTab(b.dataset.tab));
$$('select.category').forEach(s=>categories.forEach(c=>{let o=elem('option',c.replaceAll('_',' '));o.value=c;o.selected=c==='recurrente';s.append(o)}));
$$('select.category').forEach(s=>{paintCategory(s);s.addEventListener('change',()=>paintCategory(s))});
$$('input[type=date]').forEach(x=>x.value=today());
$('#manual').onsubmit=async e=>{e.preventDefault();let p=Object.fromEntries(new FormData(e.target));try{await api('/api/movement',{method:'POST',body:JSON.stringify(p)});e.target.reset();e.target.querySelector('input[type=date]').value=today();notify('Movimiento guardado');await refresh();showTab('ledger')}catch(e){notify(e.message)}};
$('#parse').onclick=async()=>{let f=$('#file').files[0];if(!f)return notify('Seleccione un archivo');selectedFile=f;let fd=new FormData();fd.append('file',f);$('#parse').disabled=true;try{let r=await api('/api/upload',{method:'POST',body:fd});pending=r.rows;renderPreview();if(!pending.length)return notify('No se detectaron movimientos. Comprueba la legibilidad del archivo.');await classifyPending($('#send-ai').checked);notify(`Se detectaron ${pending.length} movimientos, ya preclasificados. Revise antes de guardar.`)}catch(e){notify(e.message)}finally{$('#parse').disabled=false}};
async function classifyPending(useAI){
  if(!pending.length)return notify('Primero carga un archivo con movimientos');
  const btn=$('#auto-classify'), offline=$('#rules-classify');
  btn.disabled=offline.disabled=true;
  $('#classification-status').textContent=useAI?'Clasificando con IA y tus notas: esto puede tardar un momento...':'Aplicando reglas locales...';
  try{
    const edits=chosenAllRows();
    pending=edits.map((row,i)=>({...pending[i],...row}));
    const result=await api('/api/classify-proposals',{method:'POST',body:JSON.stringify({rows:edits,note:$('#import-context').value,use_ai:useAI})});
    let changed=0,uncertain=0;
    for(const item of result.proposals){
      const i=item.index;
      if(!Number.isInteger(i)||i<0||i>=pending.length)continue;
      if(pending[i].category!==item.category)changed++;
      pending[i].category=item.category;
      pending[i].confidence=item.confidence;
      pending[i].reason=item.reason;
      pending[i].note=$('#import-context').value;
      if(item.category==='pendiente')uncertain++;
    }
    renderPreview();
    $('#classification-status').textContent=`${pending.length} revisados · ${changed} categorías ajustadas · ${uncertain} pendientes. ${result.warning}`;
    notify('Clasificación aplicada a la tabla. Revisa y confirma para guardar.');
  }catch(e){notify(e.message);$('#classification-status').textContent=e.message}
  finally{btn.disabled=offline.disabled=false}
}
$('#auto-classify').onclick=()=>classifyPending(true);
$('#rules-classify').onclick=()=>classifyPending(false);
function chosenAllRows(){return $$('#preview-table tbody tr').map(tr=>{let get=f=>tr.querySelector(`[data-field=${f}]`).value;let n=Number(get('amount_cents'));if(!Number.isFinite(n)||n<=0)throw new Error('Monto inválido');return {date:get('date'),amount_cents:Math.round(n*100),description:get('description'),source:get('source'),category:get('category'),note:$('#import-context').value}})}
function renderPreview(){let tbody=$('#preview-table tbody');tbody.replaceChildren();$('#preview-area').classList.toggle('hidden',!pending.length);$('#preview-count').textContent='('+pending.length+')';pending.forEach((r,i)=>{let tr=elem('tr');let ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.dataset.field='include';let td=document.createElement('td');td.append(ch);tr.append(td);for(const field of ['date','amount_cents','description','source']){let cell=document.createElement('td'),inp=document.createElement('input');inp.dataset.field=field;inp.value=field==='amount_cents'?(r[field]/100).toFixed(2):enc(r[field]);if(field==='date')inp.type='date';cell.append(inp);tr.append(cell)}let cell=document.createElement('td');let s=option(null,r.category);s.dataset.field='category';s.title=(r.confidence?'Confianza: '+r.confidence+' · ':'')+(r.reason||'');cell.append(s);tr.append(cell);if(r.amount_cents>=200000 && (r.category==='pendiente'||r.category==='variable') && r.confidence!=='alta'){let warn=elem('small',' · Revisar abono alto','high-amount');cell.append(warn)}tbody.append(tr)})}
function chosenRows(){return $$('#preview-table tbody tr').filter(tr=>tr.querySelector('[data-field=include]').checked).map(tr=>{let get=f=>tr.querySelector(`[data-field=${f}]`).value;let n=Number(get('amount_cents'));if(!Number.isFinite(n)||n<=0)throw new Error('Monto inválido en revisión');return {date:get('date'),amount_cents:Math.round(n*100),description:get('description'),source:get('source'),category:get('category'),note:$('#import-context').value}})}
function fileBase64(file){return new Promise((resolve,reject)=>{let r=new FileReader();r.onload=()=>resolve(String(r.result).split(',')[1]);r.onerror=reject;r.readAsDataURL(file)})}
$('#commit').onclick=async()=>{try{let rows=chosenRows();if(!rows.length)return notify('No hay filas seleccionadas');let original_base64=$('#keep-document').checked?await fileBase64(selectedFile):null;let r=await api('/api/import',{method:'POST',body:JSON.stringify({filename:selectedFile?.name||'registro',rows,original_base64})});notify(`Guardados: ${r.added}. Duplicados omitidos: ${r.duplicates_skipped}`);pending=[];$('#preview-area').classList.add('hidden');await refresh();showTab('gastos')}catch(e){notify(e.message)}};
$('#discard').onclick=()=>{pending=[];$('#preview-area').classList.add('hidden')};
function renderLedger(){let q=$('#search').value.toLowerCase(),tbody=$('#ledger-table tbody');tbody.replaceChildren();data.movements.filter(r=>(r.date+' '+r.description+' '+r.source).toLowerCase().includes(q)).forEach(r=>{let tr=elem('tr');tr.append(elem('td',r.date),elem('td',money(r.amount_cents)));let desc=elem('td',r.description||'Sin descripción');desc.append(elem('div',r.source||'Sin fuente','small'));tr.append(desc);let td=document.createElement('td'),sel=option(null,r.category);sel.onchange=async()=>{try{await api('/api/movement/'+r.id,{method:'PATCH',body:JSON.stringify({category:sel.value})});await refresh()}catch(e){notify(e.message)}};td.append(sel);tr.append(td);let actions=elem('td'),edit=elem('button','Editar','mini secondary'),del=elem('button','Eliminar','mini secondary');edit.onclick=async()=>{let description=prompt('Descripción:',r.description);if(description===null)return;let amount=prompt('Monto Q:',(r.amount_cents/100).toFixed(2));if(amount===null)return;let number=Number(amount);if(!Number.isFinite(number)||number<=0)return notify('Monto inválido');try{await api('/api/movement/'+r.id,{method:'PATCH',body:JSON.stringify({description,amount_cents:Math.round(number*100)})});await refresh()}catch(e){notify(e.message)}};del.onclick=async()=>{if(!confirm('¿Eliminar este movimiento definitivamente?'))return;try{await api('/api/movement/'+r.id,{method:'DELETE'});await refresh()}catch(e){notify(e.message)}};actions.append(edit,del);tr.append(actions);tbody.append(tr)});if(!tbody.children.length){let tr=elem('tr'),td=elem('td','No se encontraron movimientos.');td.colSpan=5;tr.append(td);tbody.append(tr)}}
$('#search').oninput=renderLedger;
function securedDownload(url,filename){return async()=>{try{let token=await window.integralAuth.token();let r=await fetch(url,{headers:{Authorization:'Bearer '+token}});if(!r.ok)throw Error('No se pudo descargar');let blob=await r.blob(),a=document.createElement('a'),u=URL.createObjectURL(blob);a.href=u;a.download=filename;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}catch(e){notify(e.message)}}}
$('#export').onclick=e=>{e.preventDefault();securedDownload('/api/export','ingresos_exportados.csv')()};
function renderDocs(){let node=$('#docs');node.replaceChildren();if(!data.documents.length)return node.append(elem('p','No se guardaron documentos originales.'));data.documents.forEach(d=>{let a=elem('button',`${d.filename} · ${d.uploaded_at}`,'secondary');a.onclick=securedDownload('/api/document/'+d.id,d.filename);node.append(a)})}

$('#note-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/note',{method:'POST',body:JSON.stringify(Object.fromEntries(new FormData(e.target)))});e.target.reset();e.target.querySelector('input[type=date]').value=today();await refresh();notify('Nota guardada')}catch(e){notify(e.message)}};
function renderNotes(){let el=$('#note-list');el.replaceChildren();data.notes.forEach(n=>{let wrap=elem('div',null,'note');wrap.append(elem('small',n.date),elem('p',n.text));let b=elem('button','Eliminar','mini secondary');b.onclick=async()=>{if(confirm('¿Eliminar nota?')){await api('/api/note/'+n.id,{method:'DELETE'});await refresh()}};wrap.append(b);el.append(wrap)})}
function selectedDates(){let d=new Date(),end=today(),start=null;let period=$('#period').value;if(period==='month'){start=end.slice(0,7)+'-01'}if(period==='quarter'||period==='year'){let count=period==='quarter'?3:12;start=new Date(d.getFullYear(),d.getMonth()-(count-1),1).toLocaleDateString('en-CA');let x=new Date(d.getFullYear(),d.getMonth()-(count-1),1);start=`${x.getFullYear()}-${String(x.getMonth()+1).padStart(2,'0')}-01`}return {start,end}}
async function analyze(){try{let dates=selectedDates(),r=await api('/api/analyze',{method:'POST',body:JSON.stringify({...dates,budget:$('#budget').value.trim()||null})});$('#stat-total').textContent=money(r.income_cents);$('#stat-avg').textContent=money(r.avg_cents);$('#stat-extra').textContent=money(r.extra_cents);$('#stat-months').textContent=r.active_months;let bars=$('#bars');bars.replaceChildren();let max=Math.max(1,...r.monthly.map(m=>m.total));r.monthly.forEach(m=>{let row=elem('div',null,'barrow');row.append(elem('span',m.month));let bg=elem('div',null,'barbg'),fill=elem('div',null,'barfill');fill.style.width=`${m.total/max*100}%`;bg.append(fill);row.append(bg,elem('b',money(m.total)));bars.append(row)});if(!r.monthly.length)bars.append(elem('p','Todavía no hay ingresos clasificados.','muted'));let pre=$('#prediction');pre.replaceChildren();if(r.prediction){for(let type of ['conservador','esperado','optimista']){let row=elem('div',null,'scenario');row.append(elem('span',type[0].toUpperCase()+type.slice(1)),elem('b',money(r.prediction[type])));pre.append(row)}pre.append(elem('p',r.prediction.method,'explain'))}else pre.append(elem('p','Agrega y clasifica ingresos para estimar.','empty'));let saving=$('#saving');saving.replaceChildren();if(r.savings){saving.append(elem('h3','Ahorro orientativo: '+money(r.savings.ahorro_sugerido_centavos)),elem('p',r.savings.method,'explain'))}else if(r.prediction)saving.append(elem('p','Ingresa tu presupuesto mensual para calcular una meta orientativa de ahorro.','explain'));let src=$('#sources');src.replaceChildren();r.sources.forEach(x=>{let row=elem('div',null,'scenario');row.append(elem('span',x.name),elem('b',money(x.amount_cents)));src.append(row)});if(!r.sources.length)src.append(elem('p','Sin fuentes en este periodo.','muted'));$('#warnings').textContent=r.warnings.join(' ') }catch(e){notify(e.message)}}
$('#analyze').onclick=analyze;$('#period').onchange=analyze;
$('#ask-ai').onclick=async()=>{let note=$('#ai-note').value.trim();if(!note)return notify('Escribe una nota');$('#ask-ai').disabled=true;$('#ai-answer').textContent='Consultando IA en la nube...';try{let r=await api('/api/interpret',{method:'POST',body:JSON.stringify({note})});$('#ai-answer').textContent=r.answer}catch(e){$('#ai-answer').textContent=e.message}finally{$('#ask-ai').disabled=false}};

// Dictado por Web Speech API, disponible en navegadores compatibles y con permiso de micrófono.
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
const dictate=$('#dictate-notes');
if(!SpeechRecognition){dictate.disabled=true;dictate.title='Dictado no disponible en este navegador';$('#dictation-status').textContent='Dictado no disponible; escribe tus notas.'}
else{let recognition=new SpeechRecognition();recognition.lang='es-GT';recognition.continuous=true;recognition.interimResults=false;let listening=false;
recognition.onresult=e=>{const parts=[];for(let i=e.resultIndex;i<e.results.length;i++)if(e.results[i].isFinal)parts.push(e.results[i][0].transcript);if(parts.length){let field=$('#import-context');field.value+=(field.value.trim()?' ':'')+parts.join(' ');}};
recognition.onend=()=>{listening=false;dictate.textContent='🎙 Dictar observaciones';$('#dictation-status').textContent='Dictado detenido';};
recognition.onerror=e=>{notify('No se pudo usar el micrófono: '+e.error)};
dictate.onclick=()=>{if(listening){recognition.stop();return}try{recognition.start();listening=true;dictate.textContent='■ Detener dictado';$('#dictation-status').textContent='Escuchando…'}catch(e){notify(e.message)}}}
const expenseGroups=[
 ['Comida fuera','restaurante|campero|burger|pizza|uber\\*eats|r[aá]men|caf[eé]|sushi|mcdonald|papa john|pollo brujo|hotdog|pops'],
 ['Supermercado','walmart|super 24|torre|pricesmart|abarroteria|mercado'],
 ['Transporte y combustible','gasolina|shell|uber\\*rides|parqueo|estacionamiento'],
 ['Videojuegos y ocio','steam|playstation|xbox|nintendo|videojuego|games|cine|disney|netflix'],
 ['Compras','temu|amazon|stradivarius|cemaco|ishop|tienda|shopping'],
 ['Servicios y suscripciones','apple|chatgpt|openai|tigo|facebook|mesh[y]|servicio|internet|luz'],
 ['Vivienda y pagos','casa|alquiler|renta|hipoteca|impuesto|municipalidad'],
 ['Otros gastos','.*']
].map(([label,pattern])=>({label,regex:new RegExp(pattern,'i')}));
function expenseCategory(row){const desc=(row.description||'')+' '+(row.source||'');return expenseGroups.find(g=>g.regex.test(desc))?.label||'Otros gastos'}
function expenseTotals(){const totals={};for(const r of data.movements){if(r.category!=='gasto')continue;const key=expenseCategory(r);totals[key]=(totals[key]||0)+Number(r.amount_cents||0)}return Object.entries(totals).sort((a,b)=>b[1]-a[1]);}
function renderFinancialTabs(){
 const expenses=$('#expense-breakdown');expenses.replaceChildren();for(const [cat,amount] of expenseTotals()){let row=elem('div',null,'scenario');row.append(elem('span',cat),elem('b',money(amount)));expenses.append(row)}if(!expenses.children.length)expenses.append(elem('p','No hay gastos clasificados.','muted'));
 const incomes=$('#income-breakdown');incomes.replaceChildren();let byType={};for(const r of data.movements){if(!['recurrente','variable','extraordinario'].includes(r.category))continue;byType[r.category]=(byType[r.category]||0)+Number(r.amount_cents||0)}for(const [cat,amount] of Object.entries(byType)){let row=elem('div',null,'scenario');row.append(elem('span',cat),elem('b',money(amount)));incomes.append(row)}if(!incomes.children.length)incomes.append(elem('p','No hay ingresos confirmados.','muted'));
 const questions=$('#plan-questions');questions.replaceChildren();let top=expenseTotals().slice(0,3);for(const [cat,amount] of top){const label=elem('label',`${cat} — ${money(amount)}. ¿Este gasto era necesario?`);const select=document.createElement('select');select.dataset.expenseCategory=cat;for(const [v,t] of [['','Selecciona una respuesta'],['necesario','Sí, era necesario'],['reducible','Podría reducirlo'],['ocasional','Fue excepcional y no se repetirá']]){const o=elem('option',t);o.value=v;select.append(o)}select.value=plannedAnswers[cat]||'';select.onchange=()=>{plannedAnswers[cat]=select.value};label.append(select);questions.append(label)}if(!top.length)questions.append(elem('p','Importa y confirma gastos para obtener preguntas personalizadas.','muted'));
}
$('#make-plan').onclick=()=>{
 const dest=$('#plan-result');dest.replaceChildren();const regular=data.movements.filter(r=>['recurrente','variable'].includes(r.category)).reduce((a,r)=>a+Number(r.amount_cents||0),0);const monthCount=new Set(data.movements.filter(r=>['recurrente','variable'].includes(r.category)).map(r=>r.date.slice(0,7))).size||1;
 const monthly=Math.round(regular/monthCount);const fixed=Math.max(0,Math.round((Number($('#fixed-costs').value)||0)*100));const groups=expenseTotals();const expenseMonths=new Set(data.movements.filter(r=>r.category==='gasto').map(r=>r.date.slice(0,7))).size||1;
 const expenseMonthly=Math.round(groups.reduce((a,g)=>a+g[1],0)/expenseMonths);const reducible=Math.round(groups.filter(([g])=>plannedAnswers[g]==='reducible').reduce((a,[_,v])=>a+v,0)/expenseMonths);
 const available=Math.max(0,monthly-Math.max(fixed,expenseMonthly));const saving=Math.min(available,Math.max(0,Math.round(monthly*.10)+Math.round(reducible*.2)));const spending=Math.max(0,monthly-saving);
 dest.append(elem('h3','Plan orientativo mensual'));for(const [label,value] of [['Ingreso habitual aproximado',monthly],['Meta de ahorro',saving],['Presupuesto máximo de gasto',spending],['Gasto promedio observado',expenseMonthly]]){let row=elem('div',null,'scenario');row.append(elem('span',label),elem('b',money(value)));dest.append(row)}dest.append(elem('p',saving===0?'No hay margen confirmado para recomendar ahorro; revisa tu presupuesto y deudas.':'Se reservó una meta prudente según tus ingresos, gastos y respuestas. Ajusta el monto si hay deudas u obligaciones que no aparecen en el estado de cuenta.','explain'));};

if(SpeechRecognition){const aiRecognition=new SpeechRecognition();aiRecognition.lang='es-GT';aiRecognition.onresult=e=>{let t=[...e.results].map(r=>r[0].transcript).join(' ');let field=$('#ai-note');field.value+=(field.value.trim()?' ':'')+t};$('#dictate-ai').onclick=()=>{try{aiRecognition.start()}catch(e){notify(e.message)}}}else{$('#dictate-ai').disabled=true;$('#dictate-ai').title='No disponible en este navegador'}
init().catch(e=>notify(e.message));
