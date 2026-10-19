#!/usr/bin/env python3
"""Baltor Motion Composer v0.2 — deterministic multi-layout study.
10 shot recipes, 10 genuinely different spatial design systems, 65 seconds.
Run: python composer_v02.py --preview 14.2
     python composer_v02.py --out outputs/spatial_layout_study_65s_video.mp4
All source artwork is procedural from the existing original Baltor Motion Foundry.
"""
from __future__ import annotations
import argparse,json,math,sys,time,subprocess,hashlib
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parent
UP=ROOT.parent
sys.path.insert(0,str(UP))
import composer as original
from layout_engine import Engine, inspect_layout, resolve_box
CONF=json.loads((ROOT/'layouts.json').read_text())
W,H=original.W,original.H
ENG=Engine(W,H,profile=CONF['safe_profile'])

def shot_at(t):
 for i,s in enumerate(CONF['shots']):
  if s['start']<=t<s['end']:return i,s
 return len(CONF['shots'])-1,CONF['shots'][-1]

def background(t):
 """Compose original illustration but NO prior version's fixed title, subtitles or border."""
 idx,plan=shot_at(t)
 local=max(0,t-plan['start'])
 length=plan['end']-plan['start']
 src=plan['source_shot_seconds'] + (local/length-.5)*plan['source_sample_span']
 src=max(0,min(original.STORY['format']['duration_sec']-.01,src))
 sh=original.find_shot(src)
 cx,zoom,shake,u=original.camera(sh,src)
 im=original.ASSETS['sky'].copy()
 for k,r in [('mountains',.15),('city',.25),('pines_far',.47)]:original.paste_parallax(im,k,cx,r)
 for k,r in [('ground',1.),('props',1.)]:original.paste_parallax(im,k,cx,r)
 hero=original.draw_hero(im,sh,src,cx)
 original.paste_parallax(im,'foreground',cx,1.12)
 original.draw_extras(im,sh,src,cx,hero)
 if 'vignette' in original.ASSETS:im.alpha_composite(original.ASSETS['vignette'])
 # 1st and last shot: pull back slightly. A different zoom for every layout is intentional.
 zoom=zoom*({0:.98,1:1.,2:1.025,3:1.08,4:1.02,5:.97,6:.99,7:1.,8:1.01,9:.96}.get(idx,1))
 im=original.zoom_and_shake(im,zoom,shake,src)
 return im,sh,hero

def compose(t,debug=False):
 idx,plan=shot_at(t);t=min(t,float(CONF['duration_sec'])-.000001)
 scene,oldshot,hero=background(t)
 spec=CONF['layouts'][plan['layout']]
 local=t-plan['start'];fraction=local/(plan['end']-plan['start'])
 subject=original.Rect if False else None
 from layout_engine import Rect
 vars={
  'day':idx+1,'shot':idx+1,'n':idx+1,'progress':t/CONF['duration_sec'],
  'resource_level':.18+.02*math.cos(t*.40), 'signal_strength':.24+.08*math.sin(t*.9)**2,
  'source_shot':oldshot['id'],'chapter_progress':fraction,'subject_rect':Rect(int(W*.39),int(H*.55),int(W*.25),int(H*.29))
 }
 # Shift the temporal scope of ALL entries into the current scene's time.
 elements=[]
 for node in spec['elements']:
  nn=dict(node)
  if 'start' in nn:nn['start']=plan['start']+float(nn['start'])
  else:nn['start']=plan['start']
  if 'end' in nn:nn['end']=plan['start']+float(nn['end'])
  else:nn['end']=plan['end']
  elements.append(nn)
 res,trace=ENG.render(scene,{'elements':elements},t,vars,debug)
 # discreet project identity, placed OUTSIDE creative safe area, always original
 if not debug:
  dd=ImageDraw.Draw(res,'RGBA')
  label='BALTOR   /   SPATIAL MOTION STUDY   /   ORIGINAL'
  fo=ENG.font('mono',9)
  dd.text((int(W*.052),H-36),label,font=fo,fill=(179,216,217,135))
  # tiny unintrusive chapter index in lower left safe region
  dd.text((int(W*.052),H-52),f'{idx+1:02d} / {len(CONF["shots"]):02d}',font=fo,fill=(136,199,203,160))
 return res.convert('RGB'),trace

def qa_layouts():
 checks=[]
 for i,plan in enumerate(CONF['shots']):
  spec=CONF['layouts'][plan['layout']]
  for d in (.32,2.3,5.7):
   t=plan['start']+d
   if t>=plan['end']:continue
   # direct inspection uses global t with translated timelines.
   nodes=[]
   for e in spec['elements']:
    n=dict(e);n['start']=plan['start']+float(n.get('start',0));n['end']=plan['start']+float(n.get('end',plan['end']-plan['start']))
    nodes.append(n)
   report=inspect_layout(ENG,{'elements':nodes},t,{'resource_level':.18,'signal_strength':.24,'progress':t/CONF['duration_sec'], 'scene_image':Image.new('RGBA',(W,H))})
   checks.append({'shot':plan['id'],'layout':plan['layout'],'time':t,'errors':report['errors'],'warnings':report['warnings'],'elements':report['elements'],'trace':report['trace']})
 return checks

def build_contact_sheet(out, debug=False):
 n=len(CONF['shots']);sw,sh=270,480
 sheet=Image.new('RGB',(sw*5,sh*2),'#101927')
 for i,s in enumerate(CONF['shots']):
  im,_=compose(s['start']+2.9,debug=debug)
  sheet.paste(im.resize((sw,sh),Image.Resampling.LANCZOS),((i%5)*sw,(i//5)*sh))
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=94)
 print('Contact sheet:',out,flush=True)
 return out

def run_render(out, fps=24, internal=False):
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
 fps=int(fps);duration=float(CONF['duration_sec']);count=round(fps*duration)
 resize=[] if internal else ['-vf','scale=1080:1920:flags=lanczos']
 args=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',f'{W}x{H}','-framerate',str(fps),'-i','pipe:0',*resize,'-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(out)]
 print('Rendering',count,'frames →',out,flush=True)
 proc=subprocess.Popen(args,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 start=time.monotonic()
 try:
  for i in range(count):
   frame,_=compose(i/fps)
   proc.stdin.write(frame.tobytes())
   if i and i%(fps*10)==0:print(f'  {i/fps:.1f}/{duration:.1f}s video time / {time.monotonic()-start:.1f}s render',flush=True)
  proc.stdin.close();err=proc.stderr.read().decode();code=proc.wait()
  if code:raise RuntimeError(err)
 except BaseException:
  proc.kill();raise
 print('Completed in',round(time.monotonic()-start,1),'sec; bytes',out.stat().st_size,flush=True)
 return out

def validate_graph(path=None):
 graph=json.loads((path or ROOT/'spatial_graph.json').read_text())
 return original.topological_order(graph['nodes'])

if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--out',default='outputs/baltor_spatial_layout_study_65s_video.mp4')
 p.add_argument('--preview',type=float)
 p.add_argument('--debug-layout',action='store_true')
 p.add_argument('--fps',type=int,default=24)
 p.add_argument('--internal',action='store_true')
 p.add_argument('--contact-sheet',action='store_true')
 opts=p.parse_args()
 dst=ROOT/opts.out
 if opts.preview is not None:
  dst.parent.mkdir(parents=True,exist_ok=True)
  im,_=compose(opts.preview,debug=opts.debug_layout);im.save(dst)
  print('Preview',dst)
 elif opts.contact_sheet:
  build_contact_sheet(dst,debug=opts.debug_layout)
 else:
  run_render(dst,opts.fps,opts.internal)
  build_contact_sheet(ROOT/'outputs'/'spatial_10_style_contact_sheet.jpg')
