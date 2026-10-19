#!/usr/bin/env python3
"""Baltor Stick Shot Composer: original, image-layer-to-video demo driven by a verifiable DAG.
The reference clips in reference_manifest.json were NOT available; this is an original motion-study.
Dependencies: Pillow, numpy, ffmpeg. No commercial video assets or paid services.
"""
import argparse, json, math, os, subprocess, sys, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageOps
import numpy as np

ROOT=Path(__file__).resolve().parent
W,H=540,960
WORLD=3920
FPS=24
BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT=ImageFont.truetype(BOLD,28)
SUBFONT=ImageFont.truetype(BOLD,14)
SMALL=ImageFont.truetype(REG,13)
TINY=ImageFont.truetype(BOLD,10)
HERO=(229,235,230)
CORAL=(245,114,113)
CYAN=(115,232,226)
STORY=json.loads((ROOT/'storyboard.json').read_text())
SHOTS=STORY['shots']
ASSETS={f.stem:Image.open(f).convert('RGBA') for f in (ROOT/'assets').glob('*.png')}
GRAPH=json.loads((ROOT/'graph.json').read_text())


def topological_order(nodes):
 by_id={x['id']:x for x in nodes}; assert len(by_id)==len(nodes), 'Duplicate nodes'
 for n in nodes:
  assert set(n['deps'])<=set(by_id),'Missing dependency for '+n['id']
 todo=set(by_id);done=[]
 while todo:
  ready=sorted(n for n in todo if set(by_id[n]['deps'])<=set(done))
  if not ready:raise ValueError('Cycle in composer DAG')
  done.extend(ready); todo.difference_update(ready)
 return done
ORDER=topological_order(GRAPH['nodes'])
assert ORDER.index('parallax')>ORDER.index('camera')


def clamp(a,b,c):return max(b,min(c,a))
def ease(v):v=clamp(v,0,1); return v*v*(3-2*v)
def find_shot(t):
 return next((s for s in SHOTS if s['start']<=t<s['end']),SHOTS[-1])

def camera(sh, t):
 u=clamp((t-sh['start'])/(sh['end']-sh['start']),0,1);e=ease(u)
 mode=sh['mode']; x=sh['world_x'];zoom=1.03; shake=0
 if mode=='establish':x+=100*e;zoom=1.00+.11*e
 elif mode=='follow':x+=125*e;zoom=1.09
 elif mode=='push':x+=28*e;zoom=1.11+.36*e
 elif mode=='cover':x+=22*e;zoom=1.13+.13*e
 elif mode=='split':x+=30*e;zoom=1.04
 elif mode=='reveal':x+=75*e;zoom=1.02+.20*e
 elif mode=='whip':x+=105*ease(clamp(u*3,0,1));zoom=1.15;shake=(1-u)*5
 elif mode=='chase':x+=200*e;zoom=1.11; shake=1.2
 elif mode=='close':x+=35*e;zoom=1.21+.22*e
 elif mode=='flare':x+=50*e;zoom=1.14
 elif mode=='pull':x+=10*e;zoom=1.37-.28*e
 elif mode=='end':x+=40*e;zoom=1.15-.12*e
 if sh['fx']=='shake':shake=4*abs(math.sin(36*t))
 return x, zoom, shake, u


def paste_parallax(canvas,key,xc,factor):
 plate=ASSETS[key]; width=plate.width
 crop_x=int(clamp(xc*factor-W/2,0,width-W))
 tile=plate.crop((crop_x,0,crop_x+W,H))
 canvas.paste(tile,(0,0),tile)


def draw_outline_line(d,xy,width=7,inside=HERO):
 d.line(xy, fill=(8,17,25,255),width=width+6,joint='curve')
 d.line(xy, fill=(*inside,255),width=width,joint='curve')

def draw_hero(im,sh, t, xc):
 mode=sh['actor']; u=clamp((t-sh['start'])/(sh['end']-sh['start']),0,1)
 # Keep subject close to a rule-of-thirds point, but allow independent world locomotion.
 cammove=40*ease(u) if mode in ('walk','run','sprint') else 0
 x=int(W/2-25+cammove); base=730
 if mode in ('walk','run','sprint'):
  freq=1.8 if mode=='walk' else (3.6 if mode=='run' else 5.5)
  s=math.sin(2*math.pi*freq*(t-sh['start'])); swing=(18 if mode=='walk' else 33)*s
  bob=5*abs(s)
 elif mode=='hide':s=math.sin(t*2);swing=3*s; bob=21
 else:s=0;swing=0;bob=0
 d=ImageDraw.Draw(im,'RGBA')
 d.ellipse((x-35,base-5,x+36,base+6),fill=(0,0,0,95))
 hy=base-79+bob
 head_y=hy-75
 if mode=='hide':hy+=20;head_y+=25
 if mode=='startled':head_y-=7
 shoulder_y=hy-44
 # torso, hips, pose-stable point; do not use generative limb bends
 draw_outline_line(d,[(x,shoulder_y),(x,hy)],8)
 # rigid segmented legs with coherent hip/knee/ankle joints
 leg_amp=clamp(swing,-35,35)
 for side in (-1,1):
  knee=(x+side*8+leg_amp*side*.57,hy+39)
  ankle=(x+side*6+leg_amp*side,base-1)
  draw_outline_line(d,[(x,hy),(int(knee[0]),int(knee[1])),(int(ankle[0]),int(ankle[1]))],7)
  d.line((int(ankle[0])-5,base,int(ankle[0])+9,base),fill=(*HERO,255),width=5)
 # arms and gesture
 for side in (-1,1):
  elbow=(x+side*17-int(leg_amp*side*.35),shoulder_y+24)
  hand=(x+side*22-int(leg_amp*side*.5),shoulder_y+48)
  if mode=='point' and side==1:elbow=(x+25,shoulder_y-5);hand=(x+63,shoulder_y-23)
  if mode=='signal' and side==1:elbow=(x+32,shoulder_y+3);hand=(x+45,shoulder_y-28)
  if mode=='throw' and side==1:elbow=(x+22,shoulder_y-18);hand=(x+41,shoulder_y-47)
  if mode=='knock' and side==1:elbow=(x+32,shoulder_y+6);hand=(x+48+6*math.sin(t*13),shoulder_y-13)
  if mode=='hide':elbow=(x+side*19,shoulder_y+22);hand=(x+side*20,shoulder_y+42)
  draw_outline_line(d,[(x,shoulder_y),(int(elbow[0]),int(elbow[1])),(int(hand[0]),int(hand[1]))],6)
 # head and face: clean stick aesthetic, reproducible consistent design
 d.ellipse((x-25,head_y-23,x+25,head_y+26),fill=(9,17,28,255))
 d.ellipse((x-21,head_y-19,x+21,head_y+22),fill=(*HERO,255))
 d.ellipse((x-8,head_y-2,x-5,head_y+1),fill=(13,26,32,255))
 d.ellipse((x+7,head_y-2,x+10,head_y+1),fill=(13,26,32,255))
 # iconic single diagonal coral scarf, drifting subtly but never changing design
 shoulder=(x-6,shoulder_y-4)
 d.polygon([(x-16,shoulder_y-13),(x+17,shoulder_y-9),(x+13,shoulder_y-2),(x-14,shoulder_y-5)],fill=(*CORAL,255))
 wind=7*math.sin(t*2.6)
 d.polygon([(x+10,shoulder_y-6),(x+23,shoulder_y-6),(x+34+wind,shoulder_y+24),(x+21+wind,shoulder_y+17)],fill=(*CORAL,242))
 return x,int(head_y)


def draw_extras(img, sh, t,xc,hero):
 d=ImageDraw.Draw(img,'RGBA'); mode=sh['fx'];xx,hy=hero
 u=clamp((t-sh['start'])/(sh['end']-sh['start']),0,1)
 if mode in ('signal','alarm'):
  tower_world=2740 if sh['world_x']>2300 else 1700
  sx=tower_world-xc+W/2
  cy=375
  for i in range(3):
   phase=((t*.34+i/3)%1)
   r=9+phase*150
   alpha=int(110*(1-phase))
   d.ellipse((sx-r,cy-r,sx+r,cy+r),outline=(CORAL if mode=='alarm' else CYAN)+(alpha,),width=3)
 if mode=='eyes' and u>.35:
  alpha=int(230*(.6+.4*math.sin(t*4)**2))
  for px in [xx+135,xx+154]:d.ellipse((px,hy+16,px+8,hy+20),fill=(*CORAL,alpha))
 if mode=='flare':
  if u>.13:
   p=(u-.13)/.87;bx=xx+18+180*p;by=hy-57-160*math.sin(math.pi*p)+62*p
   for rr,a in [(60,8),(31,17),(14,60)]:d.ellipse((bx-rr,by-rr,bx+rr,by+rr),fill=(255,160,96,a))
   d.ellipse((bx-5,by-5,bx+5,by+5),fill=(255,225,153,250))
   for j in range(13):
    a=j*2.2+t*.8;rr=10+((j*17+int(t*40))%33)
    d.ellipse((bx+math.cos(a)*rr,by+math.sin(a)*rr,bx+math.cos(a)*rr+2,by+math.sin(a)*rr+2),fill=(251,147,86,145))
 if mode in ('impact','shake'):
  if (mode=='impact' and int((t-sh['start'])*2.5)%3==1) or (mode=='shake' and .38<u<.47):
   px=xx+57;py=hy+47
   for a in range(0,360,36):
    rad=math.radians(a);d.line((px+15*math.cos(rad),py+15*math.sin(rad),px+32*math.cos(rad),py+32*math.sin(rad)),fill=(*CORAL,190),width=2)
 if mode=='glitch' and u>.45:
  d.polygon([(W/2-25,555),(W/2-88,555),(W/2-76,543)],fill=(106,221,220,240))
  d.polygon([(W/2+25,555),(W/2+88,555),(W/2+76,543)],fill=(244,115,114,230))
 # rain is independently animated, not an overlay moving with camera
 if mode in ('rain','alarm','shake'):
  for j in range(36):
   rx=(j*89+int(t*125)*(1+j%3))% (W+60)-30
   ry=(j*173+int(t*215))%H
   d.line((rx,ry,rx-7,ry+24),fill=(119,166,196,28+j%4*9),width=1)
 # dust in medium shots
 if mode=='mist':
  for i in range(18):
   px=(i*73+int(t*9))%W;py=480+(i*67)%220
   d.ellipse((px,py,px+3,py+3),fill=(149,201,202,27))


def zoom_and_shake(im, zoom, shake, t):
 if abs(zoom-1)<.01 and shake<.1:return im
 zw=int(W/zoom); zh=int(H/zoom)
 dx=int(shake*math.sin(47*t));dy=int(shake*.6*math.sin(63*t))
 cx=W//2+dx;cy=H//2+dy
 a=clamp(cx-zw//2,0,W-zw);b=clamp(cy-zh//2,0,H-zh)
 return im.crop((int(a),int(b),int(a)+zw,int(b)+zh)).resize((W,H),Image.Resampling.BICUBIC)

# Run operational DAG: node outputs are made available to dependent operations.
def compose(t, intermediary=False):
 ctx={'t':t}
 output={}
 for node_id in ORDER:
  if node_id=='timeline':
   ctx['shot']=find_shot(t)
   ctx['u']=(t-ctx['shot']['start'])/(ctx['shot']['end']-ctx['shot']['start'])
  elif node_id=='camera':ctx['cx'],ctx['zoom'],ctx['shake'],ctx['progress']=camera(ctx['shot'],t)
  elif node_id=='sky':ctx['img']=ASSETS['sky'].copy()
  elif node_id=='parallax':
   for k,r in [('mountains',.15),('city',.25),('pines_far',.47)]:paste_parallax(ctx['img'],k,ctx['cx'],r)
  elif node_id=='landmarks':
   for k,r in [('ground',1.0),('props',1.0)]:paste_parallax(ctx['img'],k,ctx['cx'],r)
  elif node_id=='rig':ctx['hero']=draw_hero(ctx['img'],ctx['shot'],t,ctx['cx'])
  elif node_id=='foreground':paste_parallax(ctx['img'],'foreground',ctx['cx'],1.12)
  elif node_id=='atmosphere':draw_extras(ctx['img'],ctx['shot'],t,ctx['cx'],ctx['hero'])
  elif node_id=='grade':
   # Precomputed edge vignette; preserve midframe legibility.
   if 'vignette' in ASSETS:ctx['img'].alpha_composite(ASSETS['vignette'])
  elif node_id=='framing':ctx['img']=zoom_and_shake(ctx['img'],ctx['zoom'],ctx['shake'],t)
  elif node_id=='split_panel':
   sh=ctx['shot'];u=ctx['progress']
   if sh['mode']=='split':
    im=ctx['img'];base=im.copy();d=ImageDraw.Draw(im,'RGBA')
    # Actual composited 1x2 visual comparison, generated from the same original art.
    paneltop,panelbottom=313,751
    for k,(left,right,color) in enumerate([(27,265,CYAN),(275,513,CORAL)]):
     x0,y0,x1,y1=left,paneltop,right,panelbottom
     crop=base.resize((x1-x0,y1-y0),Image.Resampling.BICUBIC)
     if k==1:crop=ImageOps.mirror(crop)
     if k==1:
      red=Image.new('RGBA',crop.size,(*CORAL,38))
      crop=Image.alpha_composite(crop,red)
     im.paste(crop,(x0,y0))
     d.rounded_rectangle((x0-2,y0-2,x1+2,y1+2),radius=5,outline=(*color,245),width=3)
     d.rounded_rectangle((x0+8,y0+8,x1-8,y0+47),radius=4,fill=(12,22,36,217))
     d.text((x0+19,y0+17),'LEFT  /  COVER' if k==0 else 'RIGHT  /  RUN',font=TINY,fill=(*color,245))
    d.line((W//2,304,W//2,763),fill=(244,240,217,150),width=2)
  elif node_id=='picture_in_picture':
   sh=ctx['shot'];u=ctx['progress']
   if sh['mode'] in ('push','close') and u>.36:
    # Cropped independent close-up appears as a diegetic camera inset.
    im=ctx['img'];d=ImageDraw.Draw(im,'RGBA')
    x0,y0,x1,y1=328,345,504,543
    sx=int(182+7*ease(u));sy=528
    crop=im.crop((sx,sy,sx+125,sy+145)).resize((x1-x0,y1-y0),Image.Resampling.BICUBIC)
    im.paste(crop,(x0,y0))
    d.rounded_rectangle((x0-2,y0-2,x1+2,y1+2),radius=4,outline=(*CYAN,220),width=3)
    d.text((x0+8,y0+9),'DETAIL  /  02',font=TINY,fill=(*CYAN,230),stroke_width=1,stroke_fill=(7,11,21,255))
  elif node_id=='transition':
   sh=ctx['shot'];secs=t-sh['start'];fade=0
   if secs<.08 and sh['id'] not in ['01']:
    fade=int(120*(1-secs/.08));col=255 if sh['mode']=='whip' else 4
    ctx['img']=Image.blend(ctx['img'],Image.new('RGBA',(W,H),(col,col,col,255)),fade/255)
  elif node_id=='caption':
   im=ctx['img'];d=ImageDraw.Draw(im,'RGBA');sh=ctx['shot'];u=ctx['progress']
   # high-contrast compact caption block anchored within mobile platform safe area
   label=f"FIELD NOTES  /  {sh['id']}"
   d.rounded_rectangle((28,84,191,111),radius=8,fill=(12,22,31,205),outline=(106,200,203,85),width=1)
   d.text((39,91),label,font=TINY,fill=(*CYAN,250))
   # scene titles are always original copy, never taken from references
   ttl=sh['title']
   if sh['id']=='01':ttl='THE LAST SIGNAL'
   d.text((29,139),ttl,font=FONT,fill=(246,244,232,255),stroke_width=1,stroke_fill=(9,18,29,255))
   d.text((30,187),sh['line'],font=SUBFONT,fill=(151,208,207,235))
   # subtle progress ticks rather than large non-value overlays
   d.rounded_rectangle((30,H-119,W-30,H-116),radius=2,fill=(119,151,160,65))
   d.rounded_rectangle((30,H-119,30+int((W-60)*(t/70)),H-116),radius=2,fill=(*CYAN,210))
   if sh['id']=='15':
    d.text((31,737),'ORIGINAL 2D MOTION STUDY',font=SUBFONT,fill=(245,228,212,240))
  elif node_id=='border':
   d=ImageDraw.Draw(ctx['img'],'RGBA');sh=ctx['shot']
   # graphite corner marks and left cyan trim; variants for risk/pulse scenes
   accent=CORAL if sh['fx'] in ('alarm','eyes','impact') else CYAN
   d.rounded_rectangle((13,47,W-13,H-45),radius=6,outline=(*accent,95),width=2)
   d.line((13,47,85,47),fill=(*accent,220),width=4)
   d.line((W-80,H-45,W-13,H-45),fill=(*accent,180),width=3)
   d.text((30,H-91),'BALTOR  /  SHOT COMPOSER  /  ORIGINAL',font=TINY,fill=(198,217,218,145))
  elif node_id in ('encode','audio','mux','qa'):continue # per-frame stages stop at border
  if intermediary and node_id in ('sky','parallax','landmarks','rig','atmosphere','framing','caption','border'):
   output[node_id]=ctx['img'].convert('RGB').copy()
 return (ctx['img'].convert('RGB'),output) if intermediary else ctx['img'].convert('RGB')


def render(out:Path, duration:float, fps:int, lowres=False):
 assert ASSETS,'Run python build_assets.py first'
 out.parent.mkdir(parents=True,exist_ok=True)
 framecount=int(duration*fps)
 wout,hout=(540,960) if lowres else (1080,1920)
 scale=[] if lowres else ['-vf','scale=1080:1920:flags=lanczos']
 cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pixel_format','rgb24','-video_size','540x960','-framerate',str(fps),'-i','pipe:0',*scale,'-c:v','libx264','-preset','veryfast','-crf','21','-pix_fmt','yuv420p','-movflags','+faststart','-an',str(out)]
 print('Encoding:',out,framecount,'frames, canvas 540x960, output',wout,hout,flush=True)
 proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
 started=time.monotonic()
 try:
  for i in range(framecount):
   f=compose(i/fps)
   proc.stdin.write(f.tobytes())
   if i and i%(fps*5)==0:print(f'  {i/fps:.1f}s / {duration}s  |  wall {time.monotonic()-started:.1f}s',flush=True)
  proc.stdin.close()
  err=proc.stderr.read().decode()
  code=proc.wait()
  if code:raise RuntimeError('FFmpeg error: '+err)
 except BaseException:
  proc.kill();raise
 print('Encoded',out.stat().st_size,'bytes in',round(time.monotonic()-started,1),'s',flush=True)


def contact_sheet(path:Path,times=None):
 times=times or [1.0,7.0,11.3,19.7,25.1,29.8,33.2,39.5,44.0,49.6,53.1,58.2,64.5,68]
 pw,ph=270,480
 sheet=Image.new('RGB',(pw*7,ph*2),(12,17,26))
 for n,t in enumerate(times):
  img=compose(t).resize((pw,ph),Image.Resampling.LANCZOS)
  sheet.paste(img,((n%7)*pw,(n//7)*ph))
 sheet.save(path,quality=90)
 print('Contact sheet',path)

if __name__=='__main__':
 ap=argparse.ArgumentParser()
 ap.add_argument('--out',default='outputs/the_last_signal_video_only.mp4')
 ap.add_argument('--duration',type=float,default=70)
 ap.add_argument('--fps',type=int,default=24)
 ap.add_argument('--preview',type=float,help='Render single time (seconds) to PNG instead of video')
 ap.add_argument('--layers',action='store_true',help='Dump major DAG frames for --preview')
 ap.add_argument('--lowres',action='store_true')
 args=ap.parse_args();dest=ROOT/args.out
 if args.preview is not None:
  dest.parent.mkdir(parents=True,exist_ok=True)
  f,states=compose(args.preview,True); f.save(dest)
  if args.layers:
   for k,im in states.items():im.save(dest.parent/(dest.stem+'-'+k+'.png'))
  print('Saved',dest)
 else:
  render(dest,args.duration,args.fps,args.lowres)
  contact_sheet(ROOT/'outputs'/'original_story_contact_sheet.jpg')
