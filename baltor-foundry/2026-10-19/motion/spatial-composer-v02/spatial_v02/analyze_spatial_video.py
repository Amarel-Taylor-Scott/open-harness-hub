#!/usr/bin/env python3
"""Spatial reference-video inspector — no OCR, no attribution of unverified edits.

Computes activity/edge/detail in normalized spatial zones and suggests lower-activity
text regions. Outputs raw frame metrics and explainable candidate placements.
One-per-frame analysis: --stride 1. Uses only local video files that are authorized.
It does NOT reconstruct source layers, verify text, infer rights, or identify objects.
"""
import argparse,csv,json,math,hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from layout_engine import _screen_safe,Rect

COLNAMES=[f'{r}{c}' for r in range(3) for c in range(3)]

def sha256_file(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def zones(image):
 h,w=image.shape[:2]
 return [image[round(i*h/3):round((i+1)*h/3),round(j*w/3):round((j+1)*w/3)] for i in range(3) for j in range(3)]

def rank_placements(detail,motion,variance,w,h,profile='reels',num=10,exclude=None):
 # low activity is preferred, not established as editable source or guaranteed legibility.
 safe=_screen_safe(w,h,profile)
 ww=round(.57*safe.w);hh=round(.145*safe.h)
 cand=[]
 for xfactor in (0,.20,.43):
  for yfactor in (0,.14,.28,.42,.55,.70,.84):
   x=round(safe.x+xfactor*safe.w)
   y=round(safe.y+yfactor*safe.h)
   rr=Rect(x,y,ww,hh)
   if not safe.contains(rr):continue
   xx=slice(x,x+ww);yy=slice(y,y+hh)
   d=float(np.mean(detail[yy,xx]));m=float(np.mean(motion[yy,xx]));v=float(np.mean(variance[yy,xx]))
   penalty=0.
   if exclude:
    er=Rect(round(exclude[0]*w),round(exclude[1]*h),round(exclude[2]*w),round(exclude[3]*h))
    penalty=min(2.0,rr.intersection(er)/max(1,ww*hh))*1.8
   score=round(.54*d+.29*m+.17*v+penalty,5)
   cand.append({'rect_px':rr.bounds(),'rect_normalized':[round(x/w,4),round(y/h,4),round(ww/w,4),round(hh/h,4)],'activity_score_lower_is_quieter':score,'activity_breakdown':{'edge':round(d,4),'motion':round(m,4),'luminance_variation':round(v,4)},'candidate_only':True})
 return sorted(cand,key=lambda x:x['activity_score_lower_is_quieter'])[:num]

def analyze(video,out,stride=1,profile='reels',exclude=None,max_frames=0,shots=None):
 video=Path(video).resolve();out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if not video.exists():raise FileNotFoundError(video)
 cap=cv2.VideoCapture(str(video))
 if not cap.isOpened():raise RuntimeError('Cannot decode '+str(video))
 fps=float(cap.get(cv2.CAP_PROP_FPS));total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
 if fps<=0:raise ValueError('Cannot determine fps')
 w,h=270,480;prev=None;metrics=[];sum_detail=np.zeros((h,w),dtype=np.float64);sum_motion=np.zeros((h,w),dtype=np.float64);sum_var=np.zeros((h,w),dtype=np.float64)
 f=0;count=0; segment_data={}; segment_frames={}
 while True:
  ok,img=cap.read()
  if not ok or (max_frames and f>=max_frames):break
  if f%stride:
   f+=1;continue
  image=cv2.resize(img,(w,h),interpolation=cv2.INTER_AREA)
  g=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY).astype(np.float32)
  dx=cv2.Sobel(g,cv2.CV_32F,1,0,ksize=3);dy=cv2.Sobel(g,cv2.CV_32F,0,1,ksize=3)
  detail=np.clip(cv2.magnitude(dx,dy)/680,0,1)
  change=np.zeros((h,w),dtype=np.float32) if prev is None else np.clip(np.abs(g-prev)/100,0,1)
  # Local standard deviation supplies texture and contrast independent of mean brightness.
  blur=cv2.GaussianBlur(g,(11,11),0);square=cv2.GaussianBlur(g*g,(11,11),0)
  localstd=np.clip(np.sqrt(np.maximum(0,square-blur*blur))/70,0,1)
  ed=[float(z.mean()) for z in zones(detail)];mv=[float(z.mean()) for z in zones(change)];vv=[float(z.mean()) for z in zones(localstd)]
  row={'frame':f,'seconds':round(f/fps,4),'edge_activity':round(float(detail.mean()),5),'motion_activity':round(float(change.mean()),5),'luminance_variation':round(float(localstd.mean()),5)}
  for i,name in enumerate(COLNAMES):
   row.update({f'edge_{name}':round(ed[i],5),f'motion_{name}':round(mv[i],5),f'variation_{name}':round(vv[i],5)})
  metrics.append(row);prev=g
  sum_detail+=detail;sum_motion+=change;sum_var+=localstd;count+=1
  if shots:
   sec=f/fps
   sid=next((str(s['id']) for s in shots if s['start']<=sec<s['end']),None)
   if sid:
    if sid not in segment_data:segment_data[sid]={'detail':np.zeros((h,w),dtype=np.float64),'motion':np.zeros((h,w),dtype=np.float64),'variance':np.zeros((h,w),dtype=np.float64),'n':0}
    seg=segment_data[sid];seg['detail']+=detail;seg['motion']+=change;seg['variance']+=localstd;seg['n']+=1
    if sid not in segment_frames or abs(sec-float(next(s['start'] for s in shots if str(s['id'])==sid))-3.0)<abs(segment_frames[sid][0]-float(next(s['start'] for s in shots if str(s['id'])==sid))-3.0):
     segment_frames[sid]=(sec,cv2.cvtColor(image,cv2.COLOR_BGR2RGB))
  if f and f%(stride*400)==0:print(' analyzed',f,'of',total,flush=True)
  f+=1
 cap.release()
 if not count:raise ValueError('No frames')
 with open(out/'frame_spatial_metrics.csv','w',newline='') as file:
  d=csv.DictWriter(file,fieldnames=list(metrics[0]));d.writeheader();d.writerows(metrics)
 detail=(sum_detail/count).astype(np.float32);motion=(sum_motion/count).astype(np.float32);variance=(sum_var/count).astype(np.float32)
 ranked=rank_placements(detail,motion,variance,w,h,profile,num=10,exclude=exclude)
 # Analytic heat map, not an artistic recreation of the footage.
 energy=np.clip(.54*detail+.29*motion+.17*variance,0,1)
 heat=np.stack((np.uint8(np.clip(energy*4,0,1)*220+22),np.uint8(np.clip((1-energy*3),0,1)*170+27),np.uint8(np.clip((1-energy*5),0,1)*144+22)),axis=-1)
 vis=Image.fromarray(heat,'RGB').resize((540,960))
 d=ImageDraw.Draw(vis);s=_screen_safe(540,960,profile)
 d.rectangle(s.bounds(),outline=(255,231,119),width=3)
 font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf';font=ImageFont.truetype(font_path,16)
 for i,c in enumerate(ranked[:3]):
  x,y,r,b=c['rect_px'];r*=2;b*=2;x*=2;y*=2
  color=(140,246,220) if i==0 else (209,232,181)
  d.rectangle((x,y,r,b),outline=color,width=3)
  d.rectangle((x,y,x+115,y+22),fill=(7,17,27))
  d.text((x+5,y+3),f'LOW ACTIVITY #{i+1}',font=ImageFont.truetype(font_path,10),fill=color)
 vis.save(out/'placement_candidates.png')
 avg={'edge_activity':round(float(detail.mean()),5),'motion_activity':round(float(motion.mean()),5),'luminance_variation':round(float(variance.mean()),5)}
 summary={'video':str(video),'source_sha256':sha256_file(video),'duration_sec':round(total/fps,3),'fps':fps,'frame_count_total':total,'frames_measured':count,'stride':stride,'analysis_status':'MEASURED pixels; placement SUGGESTIONS only',
          'safe_profile_heuristic':profile,'region_names':[f'row{i+1}_col{j+1}' for i in range(3) for j in range(3)],
          'mean_activities':avg,'ranked_text_regions':ranked,
          'important_limitations':['Quiet image regions are candidates, not verified text-safe areas.','Motion changes may reflect animation, weather, camera movement or transitions.','Gradient features do not identify existing text, character faces or focal objects.','Frame-level layers and original effects are not recoverable from flattened MP4 alone.','Platform UI safe zones are editable design approximations rather than official layouts.','Reference copyrights, image reuse and permission require separate review.']}
 if segment_data:
  previews=[];segment_reports=[]
  for s in shots:
   sid=str(s['id'])
   if sid not in segment_data:continue
   z=segment_data[sid]
   ranked_shot=rank_placements((z['detail']/z['n']).astype('float32'),(z['motion']/z['n']).astype('float32'),(z['variance']/z['n']).astype('float32'),w,h,profile,num=4,exclude=exclude)
   segment_reports.append({'shot_id':sid,'start':s['start'],'end':s['end'],'frames':z['n'],'best_text_regions':ranked_shot,'layout_name':s.get('layout','unknown')})
   im=Image.fromarray(segment_frames[sid][1]).convert('RGB')
   dr=ImageDraw.Draw(im)
   for i,rr in enumerate(ranked_shot[:2]):
    rec=rr['rect_px'];clr=(150,255,207) if i==0 else (245,208,119)
    dr.rectangle(rec,outline=clr,width=2)
    tx,ty=rec[0],rec[1];dr.rectangle((tx,ty,tx+117,ty+19),fill=(7,17,26))
    dr.text((tx+4,ty+4),f'QUIET REGION {i+1}',font=ImageFont.truetype(font_path,10),fill=clr)
   previews.append((sid,im))
  (out/'per_shot_spatial_suggestions.json').write_text(json.dumps(segment_reports,indent=2)+'\n')
  if previews:
   dw,dh=270,480;cols=5;rows=math.ceil(len(previews)/cols)
   sheet=Image.new('RGB',(cols*dw,rows*dh),(9,19,29))
   for i,(sid,im) in enumerate(previews):sheet.paste(im,((i%cols)*dw,(i//cols)*dh))
   sheet.save(out/'per_shot_placement_sheet.jpg',quality=88)
   summary['per_shot_available']=True
 (out/'spatial_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 md=['# Spatial analysis: '+video.name,'',f'- Frames measured: **{count}** of {total} (stride {stride})',f'- Approximate mean edge activity: **{avg["edge_activity"]}**',f'- Mean frame-change activity: **{avg["motion_activity"]}**',f'- Safe profile (heuristic): **{profile}**','','## Ten suggested lower-activity caption regions','']
 for j,p in enumerate(ranked,1):
  md.append(f'{j}. Relative (x, y, w, h) `{p["rect_normalized"]}`; activity {p["activity_score_lower_is_quieter"]:.4f}.')
 md+=['','## Interpretation','',*['- '+x for x in summary['important_limitations']]]
 (out/'spatial_report.md').write_text('\n'.join(md)+'\n')
 print('Wrote',count,'frame rows and',len(ranked),'candidate regions to',out,flush=True)
 return summary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--out',required=True)
 p.add_argument('--stride',type=int,default=1);p.add_argument('--max-frames',type=int,default=0);p.add_argument('--safe-profile',default='reels')
 p.add_argument('--exclude',nargs=4,type=float,default=None,metavar=('X','Y','W','H'),help='Optional known subject bbox in normalized coords')
 p.add_argument('--timeline',help='Optional storyboard layouts.json to calculate per-shot recommendations')
 a=p.parse_args();assert a.stride>=1
 timeline=json.loads(Path(a.timeline).read_text())['shots'] if a.timeline else None
 analyze(a.input,a.out,a.stride,a.safe_profile,a.exclude,a.max_frames,timeline)
