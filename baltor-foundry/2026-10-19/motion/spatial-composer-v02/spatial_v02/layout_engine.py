#!/usr/bin/env python3
"""Baltor Spatial Layout Engine v0.2.

Data-driven object positioning, four-edge padding, typography, grids and layer compositing.
Coordinates: normalized dimensions and anchor offsets against safe/full canvas/parent.
Fonts are resolved from common OS system fonts, no font binaries are distributed.
See README.md for supported op schemas. Requires Pillow and numpy.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import math
import re
import copy
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops, ImageFilter

FONTS={
 'sans':'/usr/share/fonts/truetype/lato/Lato-Regular.ttf',
 'bold':'/usr/share/fonts/truetype/lato/Lato-Heavy.ttf',
 'condensed':'/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf',
 'mono':'/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
 'serif':'/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
}
BASE_W=540
BASE_H=960

@dataclass(frozen=True)
class Rect:
 x: int
 y: int
 w: int
 h: int
 @property
 def x1(self):return self.x+self.w
 @property
 def y1(self):return self.y+self.h
 def bounds(self):return (self.x,self.y,self.x1,self.y1)
 def contains(self,other):return other.x>=self.x and other.y>=self.y and other.x1<=self.x1 and other.y1<=self.y1
 def intersection(self,other):
  w=max(0,min(self.x1,other.x1)-max(self.x,other.x));h=max(0,min(self.y1,other.y1)-max(self.y,other.y))
  return w*h

ANCHOR_FACTORS={
 'top_left':(0,0),'top_center':(.5,0),'top_right':(1,0),
 'middle_left':(0,.5),'center':(.5,.5),'middle_right':(1,.5),
 'bottom_left':(0,1),'bottom_center':(.5,1),'bottom_right':(1,1),
 'upper_third_left':(0,.333),'upper_third_center':(.5,.333),'upper_third_right':(1,.333),
 'lower_third_left':(0,.667),'lower_third_center':(.5,.667),'lower_third_right':(1,.667)
}

def rgba(value, fallback=(0,0,0,0)):
 if value is None:return fallback
 if isinstance(value,(tuple,list)):
  if len(value)==3:return tuple(int(v) for v in value)+(255,)
  if len(value)==4:return tuple(int(v) for v in value)
 if isinstance(value,str):
  value=value.strip().lstrip('#')
  if len(value)==6:return tuple(int(value[i:i+2],16) for i in (0,2,4))+(255,)
  if len(value)==8:return tuple(int(value[i:i+2],16) for i in (0,2,4,6))
 raise ValueError('Unsupported RGBA '+str(value))

def mix(a,b,p):return a+(b-a)*p
def clamp(x,lo=0,hi=1):return max(lo,min(hi,x))
def smooth(x):x=clamp(x);return x*x*(3-2*x)

def _screen_safe(w,h,profile):
 """Suggested *editable heuristics*, not official guarantees about platform UI."""
 presets={
  'reels':(.095,.105,.185,.060), # top/right/bottom/left proportional
  'shorts':(.095,.115,.195,.055),
  'tiktok':(.105,.135,.210,.055),
  'vertical_general':(.075,.075,.145,.055),
  'landscape':(.072,.065,.110,.065),
  'square':(.075,.070,.105,.070),
  'full':(.030,.030,.045,.030)
 }
 top,right,bottom,left=presets.get(profile,presets['vertical_general'])
 return Rect(round(left*w),round(top*h),round((1-left-right)*w),round((1-top-bottom)*h))

def resolve_padding(pad,scale=1):
 if isinstance(pad,(float,int)):return (round(pad*scale),)*4
 if isinstance(pad,(tuple,list)):
  vals=[float(v)*scale for v in pad]
  if len(vals)==2:vals=[vals[0],vals[1],vals[0],vals[1]]
  if len(vals)==4:return tuple(round(x) for x in vals)
  raise ValueError('Padding arrays must contain exactly 2 or 4 numbers')
 if isinstance(pad,dict):return tuple(round(float(pad.get(side,0))*scale) for side in ('top','right','bottom','left'))
 return (0,0,0,0)

def inset(rect,padding):
 t,r,b,l=padding
 return Rect(rect.x+l,rect.y+t,max(1,rect.w-l-r),max(1,rect.h-t-b))

def resolve_box(spec:dict, w:int,h:int,safe:Rect,parents=None, subject:Rect|None=None)->Rect:
 """Absolute sizes can be specified by w_px/h_px. All x/y/dx/dy/w/h are relative."""
 parents=parents or {}
 box=spec.get('box',{})
 space=box.get('space','safe')
 if space=='safe':parent=safe
 elif space=='canvas':parent=Rect(0,0,w,h)
 elif space=='subject':parent=subject or Rect(int(w*.4),int(h*.46),int(w*.2),int(h*.33))
 elif space in parents:parent=parents[space]
 else:raise ValueError(f'Unknown coordinate space {space}')
 anchor=box.get('anchor','top_left')
 if anchor not in ANCHOR_FACTORS:raise ValueError('Unknown anchor: '+anchor)
 ax,ay=ANCHOR_FACTORS[anchor]
 bw=round(float(box.get('w',.3))*parent.w) if 'w_px' not in box else round(float(box['w_px'])*w/BASE_W)
 bh=round(float(box.get('h',.07))*parent.h) if 'h_px' not in box else round(float(box['h_px'])*h/BASE_H)
 if bw<=0 or bh<=0:raise ValueError('Nonpositive box dimensions: '+str(box))
 dx=float(box.get('dx',0))*parent.w
 dy=float(box.get('dy',0))*parent.h
 x=round(parent.x+parent.w*ax -bw*ax +dx)
 y=round(parent.y+parent.h*ay -bh*ay +dy)
 return Rect(x,y,bw,bh)

class Engine:
 """Instance remains reusable across frames; all per-frame state is local."""
 def __init__(self, width=540,height=960,profile='reels'):
  self.w=width;self.h=height;self.profile=profile
  self.safe=_screen_safe(width,height,profile)
  self.scale=min(width/BASE_W,height/BASE_H)
  self._font_cache={}
 def font(self,name,size):
  size=max(5,int(size));key=(name,size)
  if key not in self._font_cache:
   p=Path(FONTS.get(name,FONTS['bold']))
   if not p.exists():p=Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
   self._font_cache[key]=ImageFont.truetype(str(p),size)
  return self._font_cache[key]
 def _active_alpha(self,node,t):
  at=float(node.get('start',0));en=float(node.get('end',1e10))
  if not at<=t<en:return 0.,0.
  ent=max(0.,float(node.get('in',0.24)));ext=max(0.,float(node.get('out',0.2)))
  ain=smooth((t-at)/ent) if ent else 1
  aout=smooth((en-t)/ext) if ext else 1
  return min(ain,aout),smooth((t-at)/max(ent,.0001))
 def _format(self,value,vars):
  if not isinstance(value,str):return str(value)
  # The content is author-supplied; no execution/evaluation of input expressions.
  class D(dict):
   def __missing__(self,key):return '{'+key+'}'
  try:return value.format_map(D(vars))
  except (ValueError,KeyError,TypeError):return value
 def _wrap(self,txt,font,avail_w,tracking=0):
  if '\n' in txt:
   blocks=txt.split('\n');lines=[]
   for b in blocks:lines.extend(self._wrap(b,font,avail_w,tracking))
   return lines
  if not txt:return ['']
  d=ImageDraw.Draw(Image.new('RGBA',(2,2)))
  def width(s):
   return d.textbbox((0,0),s,font=font,stroke_width=0)[2] +max(0,len(s)-1)*tracking
  parts=txt.split(' ');lines=[];current=''
  for token in parts:
   candidate=(current+' '+token).strip()
   if width(candidate)<=avail_w:current=candidate;continue
   if current:lines.append(current);current=''
   if width(token)<=avail_w:current=token;continue
   # split long strings to avoid silently overflowing
   chunk=''
   for letter in token:
    if chunk and width(chunk+letter)>avail_w:lines.append(chunk);chunk=letter
    else:chunk+=letter
   current=chunk
  if current:lines.append(current)
  return lines or ['']
 def _textfit(self,node,text,area):
  nominal=max(7,int(float(node.get('font_size',26))*self.scale))
  min_size=max(6,int(float(node.get('min_font_size',11))*self.scale))
  tracking=round(float(node.get('tracking',0))*self.scale)
  maxlines=int(node.get('max_lines',5));spacing=float(node.get('line_spacing',1.18))
  for sz in range(nominal,min_size-1,-1):
   font=self.font(node.get('font','bold'),sz)
   lines=self._wrap(text,font,max(3,area.w),tracking)
   lineh=round(sz*spacing)
   if len(lines)<=maxlines and lineh*len(lines)<=area.h:return font,lines,lineh,tracking,False
  font=self.font(node.get('font','bold'),min_size)
  lines=self._wrap(text,font,max(3,area.w),tracking)
  truncated=len(lines)>maxlines
  if truncated:
   lines=lines[:maxlines]
   while lines[-1] and font.getlength(lines[-1]+'…')>area.w:lines[-1]=lines[-1][:-1]
   lines[-1]+='…'
  lineh=round(min_size*spacing)
  while len(lines)>1 and lineh*len(lines)>area.h:lines.pop()
  return font,lines,lineh,tracking,truncated
 def _draw_text_line(self,draw,pos,text,font,fill,stroke,tracking=0,stroke_width=0):
  if not tracking:
   draw.text(pos,text,font=font,fill=fill,stroke_width=stroke_width,stroke_fill=stroke)
  else:
   px=pos[0]
   for ch in text:
    draw.text((px,pos[1]),ch,font=font,fill=fill,stroke_width=stroke_width,stroke_fill=stroke)
    px+=font.getlength(ch)+tracking
 def _draw_node(self,base,node,rect,t,vars,alpha):
  """Rasterize into rect-sized patch then composite by blend/opacity."""
  if rect.x1<=0 or rect.y1<=0 or rect.x>=self.w or rect.y>=self.h:return {}
  kind=node.get('kind','text')
  if kind=='pointer':
   # Leader lines must be composed on the *full canvas*, not cropped inside
   # their tiny anchor rectangle. The target is an authored normalized point.
   dest=node.get('target',[.5,.5]);ex=round(float(dest[0])*self.w);ey=round(float(dest[1])*self.h)
   sx=rect.x+rect.w//2;sy=rect.y+rect.h//2
   lay=Image.new('RGBA',(self.w,self.h),(0,0,0,0));ld=ImageDraw.Draw(lay,'RGBA')
   col=rgba(node.get('color','#85F4E8'))
   co=(*col[:3],round(col[3]*clamp(alpha*float(node.get('opacity',1)))))
   ld.line((sx,sy,ex,ey),fill=co,width=max(1,round(float(node.get('width',2))*self.scale)))
   ld.ellipse((ex-4,ey-4,ex+4,ey+4),fill=co)
   base.alpha_composite(lay)
   return {'target_px':[ex,ey]}
  pix=Image.new('RGBA',(rect.w,rect.h),(0,0,0,0));d=ImageDraw.Draw(pix,'RGBA')
  pw=max(0,rect.w);ph=max(0,rect.h)
  pen=rgba(node.get('color','#F4F4EB'))
  accent=rgba(node.get('accent','#78E8E2'))
  background=rgba(node.get('fill','#091A27DC'))
  brd=rgba(node.get('border','#75E8E299'))
  radius=round(float(node.get('radius',10))*self.scale)
  stroke=round(float(node.get('border_width',1))*self.scale)
  diagnostics={}
  if kind in ('box','text','pill','metric','tag','button') and (node.get('background',kind not in ('text',)) or node.get('outline',False)):
   d.rounded_rectangle((0,0,pw-1,ph-1),radius=min(radius,pw//2,ph//2),fill=background if node.get('background',kind not in ('text',)) else None,outline=brd if node.get('outline',False) else None,width=max(stroke,1))
  if kind in ('text','pill','metric','tag','button'):
   pad=resolve_padding(node.get('padding',[2,5,2,5]),self.scale)
   area=inset(Rect(0,0,pw,ph),pad)
   txt=self._format(node.get('text',''),vars)
   font,lines,lineh,tracking,trunc=self._textfit(node,txt,area)
   diagnostics={'font_size':font.size,'lines':lines,'truncated':trunc,'text':txt}
   color=pen
   valign=node.get('valign','center' if kind!='text' else 'top')
   y=area.y+({'top':0,'center':(area.h-lineh*len(lines))//2,'bottom':area.h-lineh*len(lines)}.get(valign,0))
   y=max(area.y,y)
   for line in lines:
    line_w=font.getlength(line)+max(0,len(line)-1)*tracking
    align=node.get('align','left')
    x=area.x+({'left':0,'center':(area.w-line_w)/2,'right':area.w-line_w}.get(align,0))
    x=max(area.x,x)
    if node.get('shadow',False):self._draw_text_line(d,(round(x+1*self.scale),round(y+2*self.scale)),line,font,(0,0,0,160),(0,0,0,200),tracking)
    self._draw_text_line(d,(round(x),round(y)),line,font,color,rgba(node.get('stroke_color','#07111FFF')),tracking,round(float(node.get('stroke_width',0))*self.scale))
    y+=lineh
  elif kind=='box':
   if node.get('edge_marks',False):
    length=int(min(pw,ph)*.20)
    d.line([(0,0),(length,0)],fill=accent,width=max(2,stroke*2));d.line([(pw-length,ph-1),(pw-1,ph-1)],fill=accent,width=max(2,stroke*2))
  elif kind=='line':
   d.line([(0,ph//2),(pw,ph//2)],fill=pen,width=max(1,round(float(node.get('width',2))*self.scale)))
  elif kind=='progress':
   p=clamp(float(vars.get(node.get('value','progress'),node.get('progress',.5))))
   bg=rgba(node.get('track','#6F839344'))
   d.rounded_rectangle((0,0,pw-1,ph-1),radius=min(ph//2,8),fill=bg)
   d.rounded_rectangle((0,0,max(1,int(pw*p)),ph-1),radius=min(ph//2,8),fill=pen)
  elif kind=='circle':
   width=max(1,round(float(node.get('width',2))*self.scale))
   d.ellipse((width,width,pw-width,ph-width),fill=background if node.get('filled',False) else None,outline=pen,width=width)
  elif kind=='reticle':
   cx,cy=pw//2,ph//2; r=int(min(pw,ph)*.28)
   for s in (.65,1,1.25):
    rr=int(r*s);d.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=(*pen[:3],130),width=2)
   d.line((cx-14,cy,cx+14,cy),fill=pen,width=2);d.line((cx,cy-14,cx,cy+14),fill=pen,width=2)
  elif kind=='waveform':
   steps=max(8,int(node.get('bars',35)))
   for j in range(steps):
    phs=t*2.6+j*.74
    amp=.24+.70*abs(math.sin(phs)*math.sin(phs*.27+1.2))
    hh=max(3,int((ph-6)*amp));xx=int((j+.5)*pw/steps);bw=max(1,int(pw/(steps*2.0)))
    d.rounded_rectangle((xx,ph//2-hh//2,xx+bw,ph//2+hh//2),radius=1,fill=(*pen[:3],170))
  elif kind=='image':
   source=vars.get('scene_image')
   if node.get('src') and isinstance(vars.get('assets'),dict):source=vars['assets'].get(node['src'],source)
   if source is None:raise ValueError('Image node '+node.get('id','')+' has no input')
   if node.get('mirror',False):source=ImageOps.mirror(source)
   crop=node.get('crop',[0,0,1,1])
   if crop!=[0,0,1,1]:
    a,b,c,e=crop;source=source.crop((int(a*source.width),int(b*source.height),int(c*source.width),int(e*source.height)))
   cover=node.get('fit','cover')=='cover'
   pic=ImageOps.fit(source,(pw,ph),method=Image.Resampling.BICUBIC) if cover else ImageOps.contain(source,(pw,ph))
   if pic.size!=(pw,ph):
    p2=Image.new('RGBA',(pw,ph),(0,0,0,0));p2.alpha_composite(pic.convert('RGBA'),((pw-pic.width)//2,(ph-pic.height)//2));pic=p2
   tint=rgba(node.get('tint','#00000000'))
   if tint[3]:pic=Image.alpha_composite(pic.convert('RGBA'),Image.new('RGBA',pic.size,tint))
   mask=Image.new('L',(pw,ph),0);ImageDraw.Draw(mask).rounded_rectangle((0,0,pw-1,ph-1),radius=min(radius,pw//2,ph//2),fill=255)
   pix.paste(pic,(0,0),mask)
   if stroke:d.rounded_rectangle((0,0,pw-1,ph-1),radius=min(radius,pw//2,ph//2),outline=brd,width=stroke)
  elif kind=='pointer':
   # Leader line between an anchored label and measured or authored point on scene.
   x2=float(node.get('target',[.65,.65])[0])*self.w-rect.x
   y2=float(node.get('target',[.65,.65])[1])*self.h-rect.y
   a=(pw//2,ph//2)
   d.line((a[0],a[1],x2,y2),fill=pen,width=max(1,stroke))
   d.ellipse((x2-3,y2-3,x2+3,y2+3),fill=pen)
  elif kind=='panel_grid':
   rows=max(1,int(node.get('rows',2)));cols=max(1,int(node.get('cols',2)))
   gap=max(0,round(float(node.get('gap',8))*self.scale))
   parent_img=vars.get('scene_image')
   if parent_img is None:raise ValueError('panel_grid needs scene_image')
   cell_w=int((pw-gap*(cols-1))/cols);cell_h=int((ph-gap*(rows-1))/rows)
   labels=node.get('labels',[]);crops=node.get('crops',[])
   for j in range(rows*cols):
    x=(j%cols)*(cell_w+gap);y=(j//cols)*(cell_h+gap)
    ss=parent_img
    if j<len(crops):
     a,b,c,e=crops[j];ss=ss.crop((int(a*ss.width),int(b*ss.height),int(c*ss.width),int(e*ss.height)))
    ss=ImageOps.fit(ss,(cell_w,cell_h),method=Image.Resampling.BICUBIC,centering=(.5,.5)).convert('RGBA')
    # differentiate crops, not only palette
    if j%2 and node.get('mirror_alternate',False):ss=ImageOps.mirror(ss)
    pix.alpha_composite(ss,(x,y))
    d.rectangle((x,y,x+cell_w-1,y+cell_h-1),outline=accent if j%2==0 else brd,width=2)
    if j<len(labels):
     label=self._format(labels[j],vars)
     fo=self.font('bold',round(12*self.scale))
     tw=round(fo.getlength(label))+12
     d.rounded_rectangle((x+5,y+5,x+min(cell_w-5,tw+5),y+24),radius=3,fill=(8,17,27,220))
     d.text((x+11,y+7),label,font=fo,fill=pen)
  else:raise ValueError('Unsupported drawable node kind '+kind)
  # Animate entrance/exit while keeping authored geometry constant.
  opacity=clamp(float(node.get('opacity',1))*alpha)
  if opacity<=0:return diagnostics
  if opacity<.999:
   aa=pix.getchannel('A').point(lambda a:round(a*opacity));pix.putalpha(aa)
  shift=(0,0)
  motion=node.get('enter','fade')
  if motion=='slide_up':shift=(0,round((1-alpha)*16*self.scale))
  elif motion=='slide_left':shift=(round((1-alpha)*22*self.scale),0)
  elif motion=='slide_right':shift=(-round((1-alpha)*22*self.scale),0)
  rx=rect.x+shift[0];ry=rect.y+shift[1]
  blend=node.get('blend','normal')
  if blend=='normal':base.alpha_composite(pix,(rx,ry))
  else:
   # local patch blend respects transparency and the destination canvas bounds
   dst=Rect(0,0,self.w,self.h);src=Rect(rx,ry,pw,ph)
   xi=max(0,rx);yi=max(0,ry);xe=min(self.w,rx+pw);ye=min(self.h,ry+ph)
   if xe>xi and ye>yi:
    fg=pix.crop((xi-rx,yi-ry,xe-rx,ye-ry))
    under=base.crop((xi,yi,xe,ye))
    if blend=='screen':mixim=ImageChops.screen(under,fg)
    elif blend=='multiply':mixim=ImageChops.multiply(under,fg)
    elif blend=='add':mixim=ImageChops.add(under,fg,scale=1.0)
    else:raise ValueError('Unsupported blend mode: '+blend)
    final=Image.composite(mixim,under,fg.getchannel('A'))
    base.paste(final,(xi,yi))
  return diagnostics
 def render(self,background:Image.Image, spec:dict, t:float, vars:dict|None=None, debug=False):
  vars=dict(vars or {})
  base=background.convert('RGBA')
  if base.size!=(self.w,self.h):base=ImageOps.fit(base,(self.w,self.h),method=Image.Resampling.BICUBIC)
  vars['scene_image']=background.convert('RGBA').resize((self.w,self.h))
  parents={};rects=[];trace=[]
  elements=sorted(enumerate(spec.get('elements',[])),key=lambda p:(int(p[1].get('z',0)),p[0]))
  for _,node in elements:
   alpha,entrant=self._active_alpha(node,t)
   if alpha<=0:continue
   region=resolve_box(node,self.w,self.h,self.safe,parents,vars.get('subject_rect'))
   parents[node.get('id','node_'+str(len(parents)))]=region
   d=self._draw_node(base,node,region,t,vars,alpha)
   rec={'id':node.get('id',''),'kind':node.get('kind','text'),'layer':node.get('layer','misc'),'z':int(node.get('z',0)), 'box':region.bounds(), 'alpha':round(alpha,3),'safe':self.safe.contains(region),'must_safe':bool(node.get('must_safe',True)),**d}
   trace.append(rec)
   rects.append((node,region))
  if debug:
   dd=ImageDraw.Draw(base,'RGBA');dd.rectangle(self.safe.bounds(),outline=(250,219,96,180),width=2)
   for node,rr in rects:
    dd.rectangle(rr.bounds(),outline=(125,233,229,145),width=1)
  return base,trace


def inspect_layout(engine,spec,t=1,vars=None):
 """Check dimensions/safe bounds and overlapping text; note deliberately stacked elements."""
 dummy=Image.new('RGBA',(engine.w,engine.h),(10,17,28,255))
 _,trace=engine.render(dummy,spec,t,vars)
 errors=[];warnings=[]
 for a in trace:
  if a['must_safe'] and not a['safe']:errors.append({'type':'safe_zone','id':a['id'],'box':a['box']})
  if a.get('truncated'):warnings.append({'type':'text_truncated','id':a['id']})
 texts=[r for r in trace if r['kind'] in ('text','pill','tag','metric','button')]
 for k,a in enumerate(texts):
  r1=Rect(a['box'][0],a['box'][1],a['box'][2]-a['box'][0],a['box'][3]-a['box'][1])
  for b in texts[k+1:]:
   if a['id']==b['id']:continue
   r2=Rect(b['box'][0],b['box'][1],b['box'][2]-b['box'][0],b['box'][3]-b['box'][1])
   overlap=r1.intersection(r2)
   if overlap>min(r1.w*r1.h,r2.w*r2.h)*.08:
    warnings.append({'type':'text_overlap','ids':[a['id'],b['id']],'area':overlap})
 return {'errors':errors,'warnings':warnings,'elements':len(trace),'safe_rect':engine.safe.bounds(),'trace':trace}
