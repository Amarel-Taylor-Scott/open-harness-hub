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
</style></head><body>
<header><h1>Open Harness Hub <span style="color:var(--acc)">·</span> paste a task, get a flow</h1>
<div style="margin:6px 0 2px;font-size:13.5px"><a href="/" style="color:var(--acc);font-weight:600;margin-right:14px;text-decoration:none">Build a flow</a><a href="/browse" style="color:var(--acc);font-weight:600;text-decoration:none">Browse components →</a></div>
<div class=sub>Describe a task in plain language. The builder hybrid-searches the component registry and assembles a costed, deployable pipeline of existing components.</div></header>
<main>
<textarea id=task placeholder="e.g. Screen supplier disclosures for forced-labor risk, cite the relevant regulations, and route high-risk cases to human review."></textarea>
<div class=chips id=examples></div>
<div class=row><button id=go>Build pipeline</button><span class=muted id=status></span></div>
<div id=banner></div>
<div id=out></div>
</main>
<script>
const EX=["Detect human-trafficking indicators in a recruitment ad and route to the right hotline with citations",
"Screen a labor-recruitment contract for modern-slavery and debt-bondage red flags against ILO indicators",
"Flag predatory overcharging and illegal recruitment fees in a migrant worker's pay statement",
"Aggregate beneficial ownership under the OFAC 50% Rule to decide if an unlisted entity is blocked",
"Classify a CVE: derive its CVSS v3.1 vector and map it to the correct CWE",
"Triage acute malnutrition from MUAC and bilateral oedema under the CMAM protocol",
"Validate an HGVS variant string and map it to current ClinVar clinical significance"];
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
function render(r){let h='';
 h+='<div class=card><h3>Pipeline flow '+(r.selection_by_model?'<span class=muted>(orchestrated by local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><div class=fc>';
 r.flow.stages.forEach((st,i)=>{
   h+='<div class=stage><div class=lbl>'+esc(st.stage)+'</div>';
   st.components.forEach(c=>{h+='<div class=comp><span class=cn>'+esc(c.name)+'</span> <span class=ci>'+esc(c.id)+'</span><div class=role>'+esc(c.role||'')+'</div></div>'});
   h+='</div>';
   if(i<r.flow.stages.length-1)h+='<div class=arrow>↓</div>';
 });
 h+='</div>';
 if(r.flow.dropped&&r.flow.dropped.length){h+='<div class=dropped>Pruned as off-topic: '+r.flow.dropped.map(d=>esc(d.id||d)).join(', ')+'</div>';}
 h+='</div>';
 var et=encodeURIComponent(r.task);
 h+='<div class=card><h3>Export &amp; standardize</h3><a href="/api/export?format=yaml&task='+et+TQ+'">⬇ Open Harness Hub pipeline (YAML)</a> · <a href="/api/export?format=json&task='+et+TQ+'">JSON</a><div class=muted style=margin-top:6px>Standard catalog format — round-trips into the registry as a reusable component. Per-component exports (MCP · Croissant · HF card · SPDX · lm-eval · …) via scripts/emit/.</div></div>';
 h+='<div class=card><h3>Cost profile (per task)</h3><div class=costs>';
 ['cheap','balanced','quality'].forEach(k=>{h+='<div class=cost><b>'+k+'</b><br>$'+esc(r.cost[k].per_task_usd)+'<br><span class=muted>'+esc(r.cost[k].how)+'</span></div>'});
 h+='</div><div class=muted style=margin-top:8px>'+esc(r.cost.note)+'</div></div>';
 h+='<div class=card><h3>Why this flow '+(r.llm_used?'<span class=muted>(local model)</span>':'<span class=muted>(deterministic)</span>')+'</h3><pre class=narr>'+esc(r.narrative)+'</pre></div>';
 out.innerHTML=h;}
go.onclick=build;health();
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
