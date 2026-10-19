#!/usr/bin/env python3
"""Build a standalone offline drag-to-position web editor with embedded original sample frames."""
from pathlib import Path
import json,base64,io
from PIL import Image
import composer_v02
ROOT=Path(__file__).resolve().parent
cfg=json.loads((ROOT/'layouts.json').read_text())
imgs={}
for name,spec in cfg['layouts'].items():
 plan=next(x for x in cfg['shots'] if x['layout']==name)
 bg,_,_=composer_v02.background(plan['start']+3)
 bg=bg.convert('RGB').resize((405,720),Image.Resampling.LANCZOS)
 data=io.BytesIO();bg.save(data,format='JPEG',quality=79,optimize=True)
 imgs[name]='data:image/jpeg;base64,'+base64.b64encode(data.getvalue()).decode()
print('Embedded',len(imgs),'original artwork frames')
css='''
:root {font-family:Inter,ui-sans-serif,system-ui,Arial,sans-serif;color:#eaf2f5;background:#0a121d;--accent:#75e8e2;--muted:#8dabb6}
*{box-sizing:border-box}body{margin:0}header{padding:15px 24px;border-bottom:1px solid #294050;display:flex;gap:15px;align-items:center;justify-content:space-between}
h1{font-size:19px;margin:0;font-weight:750;letter-spacing:.01em}small{color:var(--muted)}button,select,input,textarea{font:inherit;background:#142434;color:#eaf3f5;border:1px solid #345064;border-radius:7px;padding:8px;}
button{cursor:pointer}button:hover{border-color:var(--accent)}label{display:flex;align-items:center;gap:8px}.main{display:grid;grid-template-columns:minmax(320px,1.1fr) minmax(360px,.9fr);gap:18px;padding:18px;max-width:1500px;margin:auto}
.stage-wrap{background:#101d2a;border:1px solid #2d4354;border-radius:13px;padding:12px;display:flex;flex-direction:column;align-items:center;gap:10px}
canvas{width:auto;height:min(76vh,830px);max-width:100%;aspect-ratio:9/16;border:1px solid #425969;box-shadow:0 10px 45px #0009;touch-action:none}
.sidebar{display:flex;flex-direction:column;min-height:0;gap:12px}.card{background:#101d2b;border:1px solid #2c4659;border-radius:12px;padding:15px}h2{font-size:15px;margin:2px 0 9px}h3{font-size:14px;margin:1px 0 12px;color:#9fece7}
.toolbar{display:flex;flex-wrap:wrap;gap:8px;align-items:center}.toolbar label{color:#afc7cf}.toolbar select{max-width:270px}#status{font:12px ui-monospace,monospace;color:#99b2c2}
#elementList{display:grid;grid-template-columns:1fr 1fr;gap:5px;max-height:210px;overflow-y:auto}button.node{font:11px ui-monospace,monospace;text-align:left;padding:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.node.selected{border-color:#f6d97a;color:#f6d97a}
#inspector{max-height:41vh;overflow-y:auto}#inspector p{color:#afc7cf;font-size:13px;line-height:1.5}.property{display:grid;grid-template-columns:1.1fr 1.5fr;gap:12px;padding:4px 0;align-items:center}.property span{font:12px ui-monospace,monospace;color:#afc7cf}.property input,.property select,.property textarea{width:100%;font-size:12px;padding:6px}textarea{min-height:50px}.inspector-actions{display:flex;gap:8px;margin:12px 0}
footer{max-width:1500px;margin:auto;padding:5px 24px 25px;color:#9eb8c0;font-size:12px;line-height:1.5}code{color:#f1cf79}
@media(max-width:950px){.main{grid-template-columns:1fr}.stage-wrap{min-width:0}canvas{height:min(65vh,720px)}#inspector{max-height:40vh}}
'''
html=f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Baltor Spatial Studio · v0.2</title><style>{css}</style></head>
<body><header><div><h1>Baltor Spatial Studio <small>· v0.2 / 10 editable shot layouts</small></h1></div><small>Original artwork · browser preview · JSON export</small></header>
<main class="main"><div class="stage-wrap"><div class="toolbar"><label>Layout <select id="preset"></select></label><label>Safe profile <select id="profile"><option>reels</option><option>shorts</option><option>tiktok</option><option>vertical_general</option><option>landscape</option><option>square</option><option>full</option></select></label></div>
<canvas id="stage" width="540" height="960" aria-label="Interactive preview and draggable element positions"></canvas><div id="status"></div><div class="toolbar"><button id="toggleGuides">Toggle safe area + thirds</button><button id="exportPNG">Export PNG preview</button></div></div>
<div class="sidebar"><div class="card"><h2>Node Composer / Editable JSON</h2><p style="color:#aac2ca;font-size:12px">Select a visual element below or drag one on the canvas. Adjust anchoring, four-side padding, z-order, opacity, dimensions and typography. Changes update the preview immediately.</p><div class="toolbar"><button id="addText">+ Text</button><button id="addPanel">+ Panel</button><button id="exportConfig">Export selected layout JSON</button></div></div>
<div class="card"><h2>Ordered Layers & Elements</h2><div id="elementList"></div></div><div class="card"><h2>Properties Inspector</h2><div id="inspector"></div></div></div></main>
<footer>🔧 Visual editor uses approximate browser text metrics; the Python/Pillow compositor is the authoritative renderer. Offline file — no accounts, APIs, scraping or external downloads. Yellow dashed line indicates a configurable **heuristic** safe zone, not an official guarantee for any platform. All examples are original artwork and text.</footer>
<script>window.EMBEDDED_CONFIG={json.dumps(cfg,separators=(',',':'))};window.EMBEDDED_IMAGES={json.dumps(imgs,separators=(',',':'))};</script>
<script>{(ROOT/'editor_runtime.js').read_text()}</script></body></html>'''
out=ROOT/'Baltor_Spatial_Studio_Editor.html'
out.write_text(html)
print('Saved offline editor:',out,'bytes',out.stat().st_size)
