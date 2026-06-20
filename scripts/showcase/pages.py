"""HTML templates for the showcase (Build page + Browse page). No logic."""
from __future__ import annotations

HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Open Harness Hub — paste a task, get a flow</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#fb7714;--good:#3fb950}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:28px 22px 10px;max-width:980px;margin:0 auto}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mut);font-size:14px}
main{max-width:980px;margin:0 auto;padding:12px 22px 60px}
textarea{width:100%;min-height:96px;background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:12px;font:inherit;resize:vertical}
.row{display:flex;gap:10px;align-items:center;margin:10px 0}
button{background:var(--acc);color:#1a1300;border:0;border-radius:9px;padding:11px 18px;font-weight:650;cursor:pointer}
button:disabled{opacity:.5;cursor:wait}
.chips{display:flex;flex-wrap:wrap;gap:7px;margin:6px 0 2px}
.chip{font-size:12.5px;color:var(--mut);border:1px solid var(--line);border-radius:20px;padding:4px 11px;cursor:pointer;background:var(--panel)}
.banner{font-size:13px;border:1px solid var(--line);border-left:3px solid var(--acc);border-radius:8px;padding:9px 12px;color:var(--mut);margin:12px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:11px;padding:14px 16px;margin:14px 0}
.step{display:flex;gap:11px;padding:9px 0;border-bottom:1px solid var(--line)}.step:last-child{border:0}
.badge{font-size:11px;font-weight:700;letter-spacing:.3px;text-transform:uppercase;color:var(--acc);min-width:118px}
.sid{font-weight:600}.role{color:var(--mut);font-size:13.5px}
.matched{color:var(--good);font-size:12px}
.fc{display:flex;flex-direction:column}
.stage{border:1px solid var(--line);border-radius:9px;padding:8px 12px;background:#11161d}
.stage>.lbl{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--acc);margin-bottom:5px}
.stage .comp{font-size:13.5px;padding:3px 0}.stage .comp .cn{font-weight:600}.stage .comp .ci{color:var(--mut);font-size:12px}
.arrow{align-self:center;color:var(--mut);font-size:15px;margin:3px 0}
.dropped{color:var(--mut);font-size:12.5px;margin-top:10px;border-top:1px dashed var(--line);padding-top:8px}
.costs{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}
.cost{border:1px solid var(--line);border-radius:9px;padding:10px}.cost b{color:var(--acc)}
pre.narr{white-space:pre-wrap;background:transparent;color:var(--fg);margin:0;font:inherit}
.muted{color:var(--mut);font-size:12.5px}h3{margin:0 0 8px;font-size:15px}
a{color:var(--acc)}
.legend{display:flex;flex-wrap:wrap;gap:7px;margin:12px 0 2px}
.legend .lgh{width:100%;font-size:12px;color:var(--mut);margin-bottom:2px}
.legend .lg{font-size:11px;display:inline-flex;align-items:center;gap:5px;border:1px solid var(--line);border-radius:16px;padding:2px 9px;background:var(--panel);cursor:help}
.legend .sw{width:10px;height:10px;border-radius:3px;display:inline-block}
.dag{display:flex;flex-direction:column;align-items:center;margin:8px 0 2px}
.node{width:min(560px,100%);background:#11161d;border:1px solid var(--line);border-left:5px solid var(--nc,#8b949e);border-radius:10px;padding:9px 13px}
.node .pl{font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--nc,#8b949e)}
.node .nn{font-weight:600;font-size:14px;margin-top:1px}
.node .ni{color:var(--mut);font-size:11.5px;font-family:ui-monospace,SFMono-Regular,monospace}
.node .nr{color:var(--mut);font-size:12.5px;margin-top:2px}
.node .sub{display:inline-block;font-size:10px;font-weight:700;color:#0d1117;border-radius:5px;padding:0 6px;margin-left:7px;vertical-align:1px}
.wire{width:2px;height:18px;background:var(--line);position:relative}
.wire:after{content:"▼";position:absolute;bottom:-6px;left:-5px;color:var(--line);font-size:10px}
.cond{display:flex;gap:10px;flex-wrap:wrap;justify-content:center;width:min(560px,100%)}
.cond .node{flex:1 1 210px;width:auto}
.combine{font-size:11.5px;font-weight:700;color:var(--acc);border:1px dashed var(--acc);border-radius:16px;padding:3px 13px;margin-top:7px}
.combine small{color:var(--mut);font-weight:400}
.leafrow{display:flex;gap:7px;align-items:center;width:min(560px,100%);margin:7px 0 0 32px}
.leafrow .node{flex:1;width:auto}
.leafarm{color:var(--mut);font-size:17px;line-height:1}
.node.leaf{border-style:dashed;opacity:.92}
.node.leaf .pl:after{content:" · leaf · off critical path";color:var(--mut);font-weight:400;text-transform:none;letter-spacing:0}
.node.op{width:auto;min-width:170px;max-width:340px;text-align:center;border:2px solid var(--nc);border-radius:24px;background:#1a1408;padding:7px 16px}
.node.op .nn{font-size:16px;margin-top:0}
.node.op .pl{color:var(--nc)}
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> paste a task, get a flow</h1>
<div style="margin:6px 0 2px;font-size:13.5px"><a href="/" style="color:var(--acc);font-weight:600;margin-right:14px;text-decoration:none">Build a flow</a><a href="/browse" style="color:var(--acc);font-weight:600;text-decoration:none">Browse components →</a></div>
<div class=sub>Describe a task in plain language. The builder hybrid-searches the component registry and assembles a costed, deployable pipeline of existing components.</div></header>
<main>
<textarea id=task placeholder="e.g. Screen supplier disclosures for forced-labor risk, cite the relevant regulations, and route high-risk cases to human review."></textarea>
<div class=chips id=examples></div>
<div class=row><button id=go>Build pipeline</button><span class=muted id=status></span></div>
<div id=banner></div>
<div class=legend id=legend></div>
<div id=out></div>
</main>
<script>
const EX=["Detect human-trafficking indicators in a recruitment ad and route to the right hotline with citations",
"Screen a labor-recruitment contract for modern-slavery and debt-bondage red flags against ILO indicators",
"Flag predatory overcharging and illegal recruitment fees in a migrant worker's pay statement",
"Inspect a building permit: flag approved-vs-actual floor count and missing engineer sign-off, route to the building official",
"Aggregate beneficial ownership under the OFAC 50% Rule to decide if an unlisted entity is blocked",
"Classify a CVE: derive its CVSS v3.1 vector and map it to the correct CWE",
"Triage acute malnutrition from MUAC and bilateral oedema under the CMAM protocol",
"Validate an HGVS variant string and map it to current ClinVar clinical significance",
"Guide a blind user with on-device vision: describe the scene, read text with offline OCR, warn of hazards",
"Build an offline village tutor in Marathi on a low-end phone with no internet",
"Give offline disaster-survival first aid (flood, fire, earthquake, CPR) when the network is down",
"Route an on-device model request: try local CPU, then a local-GPU server, else a cloud model"];
const exDiv=document.getElementById('examples');
EX.forEach(t=>{const c=document.createElement('span');c.className='chip';c.textContent=t;c.onclick=()=>{task.value=t;build()};exDiv.appendChild(c)});
const task=document.getElementById('task'),go=document.getElementById('go'),out=document.getElementById('out'),status=document.getElementById('status'),banner=document.getElementById('banner');
const TOKEN=new URLSearchParams(location.search).get('token')||'';const TQ=TOKEN?('&token='+encodeURIComponent(TOKEN)):'';
async function health(){try{const h=await (await fetch('/api/health')).json();
 banner.innerHTML='<div class=banner>'+(h.embedding.promotable?'✓ semantic embeddings active ('+h.embedding.embedding_model+')':'⚠ offline <b>placeholder</b> embeddings ('+h.embedding.embedding_model+') — hybrid keyword+label search is doing the work; set OH_EMBED_* for semantic ranking.')+' · '+h.components+' components · model polish: '+(h.llm_reachable?('on ('+h.llm.model+')'):'off (deterministic)')+'</div>';}catch(e){}}
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
async function build(){const t=task.value.trim();if(!t)return;go.disabled=true;status.textContent='retrieving + assembling…';out.innerHTML='';
 try{const resp=await fetch('/api/build?task='+encodeURIComponent(t)+TQ);
   if(resp.status===401)throw new Error('this demo link needs its access token — open the full URL you were sent (…?token=…)');
   if(!resp.ok)throw new Error('server returned HTTP '+resp.status);
   const ct=resp.headers.get('content-type')||'';
   if(ct.indexOf('application/json')<0)throw new Error('stale tab — this tunnel URL is no longer served; reload the current URL');
   render(await resp.json());
 }catch(e){out.innerHTML='<div class=card>Error: '+esc(''+e)+'<div class=muted style=margin-top:6px>If this says "stale", your browser tab is pointing at an old (ephemeral) tunnel URL — reload the current one.</div></div>'}
 go.disabled=false;status.textContent='';}
const STAGE_COLOR={"Input":"#8b949e","Knowledge Corpus":"#3fb950","Conditional":"#d29922","Actions":"#fb7714","Flow / Loops":"#a371f7","Stop/End":"#f85149","Output":"#58a6ff"};
async function loadMeta(){try{const p=await(await fetch('/api/primitives')).json();
  let h='<span class=lgh>The 7 primitives — every component is one of these (hover for subtypes):</span>';
  p.forEach(x=>{const col=STAGE_COLOR[x.stage]||'#8b949e';const subs=(x.subtypes&&x.subtypes.length)?(' — subtypes: '+x.subtypes.join(', ')):'';
    h+='<span class=lg title="'+esc((x.description||'')+subs)+'"><span class=sw style="background:'+col+'"></span>'+esc(x.label)+'</span>';});
  document.getElementById('legend').innerHTML=h;}catch(e){}}
function node(c,stage){const col=STAGE_COLOR[stage]||'#8b949e';
  const showId=c.id&&c.id!=='result'&&String(c.id).indexOf('input-')!==0;
  return '<div class="node'+(c.branch==='leaf'?' leaf':'')+'" style="--nc:'+col+'"><div class=pl>'+esc(stage)+(c.subtype?'<span class=sub style="background:'+col+'">'+esc(c.subtype)+'</span>':'')+'</div><div class=nn>'+esc(c.name)+'</div>'+(showId?'<div class=ni>'+esc(c.id)+'</div>':'')+(c.role?'<div class=nr>'+esc(c.role)+'</div>':'')+'</div>';}
function opNode(op){return '<div class="node op" style="--nc:#e3b341"><div class=pl>Logical Operator</div><div class=nn>◇ '+esc(op.op||op.name||'OR')+'</div>'+(op.role?'<div class=nr>'+esc(op.role)+'</div>':'')+'</div>';}
function dag(stages){let h='';stages.forEach((st,i)=>{
  const mains=st.components.filter(c=>c.branch!=='leaf'),leaves=st.components.filter(c=>c.branch==='leaf');
  if(st.operator&&mains.length>=2){
    h+='<div class=cond>'+mains.map(c=>node(c,st.stage)).join('')+'</div>';
    h+='<div class=wire></div>'+opNode(st.operator);
  }else{mains.forEach((c,j)=>{h+=node(c,st.stage);if(j<mains.length-1)h+='<div class=wire></div>';});}
  leaves.forEach(c=>{h+='<div class=leafrow><span class=leafarm>↳</span>'+node(c,st.stage)+'</div>';});
  if(i<stages.length-1)h+='<div class=wire></div>';
 });return h;}
function render(r){let h='';
 h+='<div class=card><h3>Pipeline flow '+(r.selection_by_model?'<span class=muted>(orchestrated by local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3>';
 h+='<div class=muted style="margin:-2px 0 8px">Built for your task: '+esc(r.task)+'</div>';
 h+='<div class=dag>'+dag(r.flow.stages)+'</div>';
 if(r.flow.dropped&&r.flow.dropped.length){h+='<div class=dropped>Pruned as off-topic: '+r.flow.dropped.map(d=>esc(d.id||d)).join(', ')+'</div>';}
 const an=r.flow.analysis||{};const un=an.undermatched||[],ov=an.overmatched||[];
 if(un.length||ov.length){h+='<div class=dropped>'+un.map(u=>'⚠ under-matched: '+esc(u)).concat(ov.map(o=>'⚠ over-matched: '+esc(o))).join('<br>')+'</div>';}
 h+='</div>';
 var et=encodeURIComponent(r.task);
 h+='<div class=card><h3>Export &amp; standardize</h3><a href="/api/export?format=yaml&task='+et+TQ+'">⬇ Open Harness Hub pipeline (YAML)</a> · <a href="/api/export?format=json&task='+et+TQ+'">JSON</a><div class=muted style=margin-top:6px>Standard catalog format — round-trips into the registry as a reusable component. Per-component exports (MCP · Croissant · HF card · SPDX · lm-eval · …) via scripts/emit/.</div></div>';
 h+='<div class=card><h3>Cost profile (per task)</h3><div class=costs>';
 ['cheap','balanced','quality'].forEach(k=>{h+='<div class=cost><b>'+k+'</b><br>$'+esc(r.cost[k].per_task_usd)+'<br><span class=muted>'+esc(r.cost[k].how)+'</span></div>'});
 h+='</div><div class=muted style=margin-top:8px>'+esc(r.cost.note)+'</div></div>';
 h+='<div class=card><h3>Why this flow '+(r.llm_used?'<span class=muted>(local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><pre class=narr>'+esc(r.narrative)+'</pre></div>';
 out.innerHTML=h;}
go.onclick=build;health();loadMeta();
</script></body></html>"""


BROWSE_HTML = """<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Open Harness Hub — browse components</title>
<style>
:root{--bg:#0d1117;--panel:#161b22;--line:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#fb7714;--good:#3fb950}
*{box-sizing:border-box}body{margin:0;font:15px/1.55 -apple-system,Segoe UI,Roboto,sans-serif;background:var(--bg);color:var(--fg)}
header{padding:24px 22px 8px;max-width:1000px;margin:0 auto}h1{font-size:21px;margin:0 0 4px}
.nav{margin:6px 0 2px;font-size:13.5px}.nav a{color:var(--acc);text-decoration:none;font-weight:600;margin-right:14px}
.sub{color:var(--mut);font-size:13.5px}
main{max-width:1000px;margin:0 auto;padding:10px 22px 60px}
input{width:100%;background:var(--panel);color:var(--fg);border:1px solid var(--line);border-radius:9px;padding:10px 12px;font:inherit}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.chip{font-size:12px;color:var(--mut);border:1px solid var(--line);border-radius:18px;padding:3px 10px;cursor:pointer;background:var(--panel)}
.chip.on{color:#1a1300;background:var(--acc);border-color:var(--acc);font-weight:650}
.muted{color:var(--mut);font-size:12.5px;margin:8px 0}
.item{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:9px 12px;margin:7px 0}
.badge{display:inline-block;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.3px;color:var(--acc);border:1px solid var(--line);border-radius:5px;padding:1px 6px;margin-right:8px}
.nm{font-weight:600}.cid{color:var(--mut);font-size:12px}.ds{color:var(--mut);font-size:13px;margin-top:3px}
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> browse components</h1>
<div class=nav><a href="/">← Build a flow</a><a href="/browse">Browse</a></div>
<div class=sub id=count>loading…</div></header>
<main>
<input id=q placeholder="Search components by name, id, or description…">
<div class=chips id=types></div>
<div class=muted id=status></div>
<div id=list></div>
</main>
<script>
let TYPE='';
const q=document.getElementById('q'),types=document.getElementById('types'),list=document.getElementById('list'),status=document.getElementById('status'),count=document.getElementById('count');
function esc(s){return (s||'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}
let T=null,L={};
async function load(){
 const url='/api/components?limit=300'+(TYPE?('&type='+encodeURIComponent(TYPE)):'')+(q.value.trim()?('&q='+encodeURIComponent(q.value.trim())):'');
 const r=await (await fetch(url)).json();
 if(!T){T=r.by_type;L=r.labels||{};count.textContent=r.total+' components';renderChips()}
 status.textContent=r.matched+' match'+(r.matched===1?'':'es')+(r.matched>r.results.length?(' (showing '+r.results.length+')'):'');
 list.innerHTML=r.results.map(c=>'<div class=item><div><span class=badge>'+esc(c.label||c.type)+'</span><span class=nm>'+esc(c.name)+'</span> <span class=cid>'+esc(c.id)+'</span></div>'+(c.desc?'<div class=ds>'+esc(c.desc)+'</div>':'')+'</div>').join('');
}
function renderChips(){
 let h='<span class="chip'+(TYPE===''?' on':'')+'" data-t="">all</span>';
 Object.keys(T).sort().forEach(t=>{h+='<span class="chip'+(TYPE===t?' on':'')+'" data-t="'+t+'">'+esc(L[t]||t)+' '+T[t]+'</span>'});
 types.innerHTML=h;
 [...types.querySelectorAll('.chip')].forEach(c=>c.onclick=()=>{TYPE=c.dataset.t;renderChips();load()});
}
let deb;q.oninput=()=>{clearTimeout(deb);deb=setTimeout(load,180)};
load();
</script></body></html>"""
