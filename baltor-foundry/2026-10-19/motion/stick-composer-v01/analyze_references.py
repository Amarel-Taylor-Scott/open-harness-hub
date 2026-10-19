#!/usr/bin/env python3
"""Local-video frame-by-frame lens for learning generalized edit techniques.
Usage:
  python analyze_references.py --input my_authorized_clip.mp4 --out analysis/myclip --every 1
  python analyze_references.py --input outputs/the_last_signal.mp4 --out outputs/self_audit --every 4
Output: per-frame metrics CSV, cut candidates, contact sheet, JSON and Markdown report.
IMPORTANT: motion and cuts are algorithmic *candidates*, not verified semantic observations.
"""
import argparse,csv,hashlib,json,math,subprocess
from pathlib import Path
import cv2,numpy as np
from PIL import Image,ImageDraw,ImageFont

def ffprobe(p):
 q=subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True)
 if q.returncode:raise RuntimeError(q.stderr)
 return json.loads(q.stdout)

def estimate(prev,now):
 old=cv2.cvtColor(prev,cv2.COLOR_BGR2GRAY);new=cv2.cvtColor(now,cv2.COLOR_BGR2GRAY)
 a=cv2.goodFeaturesToTrack(old,maxCorners=260,qualityLevel=.022,minDistance=9,blockSize=5)
 if a is None or len(a)<8:return 0.,0.,1.,0.
 b,st,_=cv2.calcOpticalFlowPyrLK(old,new,a,None,winSize=(21,21),maxLevel=2)
 if b is None:return 0.,0.,1.,0.
 src=a[st.flatten()==1].reshape(-1,2);dst=b[st.flatten()==1].reshape(-1,2)
 if len(src)<9:return 0.,0.,1.,0.
 m,inliers=cv2.estimateAffinePartial2D(src,dst,method=cv2.RANSAC,ransacReprojThreshold=3,maxIters=200)
 if m is None:return 0.,0.,1.,0.
 scale=math.hypot(float(m[0,0]),float(m[0,1]))
 frac=float(np.mean(inliers)) if inliers is not None else 0
 return float(m[0,2]),float(m[1,2]),float(scale),frac

def analyze(video,out,every=1,max_frames=0):
 video=Path(video);out=Path(out);out.mkdir(parents=True,exist_ok=True)
 if not video.exists():raise FileNotFoundError(video)
 info=ffprobe(video)
 cap=cv2.VideoCapture(str(video))
 fps=float(cap.get(cv2.CAP_PROP_FPS))
 total=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
 duration=total/fps if fps else 0
 sha=hashlib.sha256()
 with open(video,'rb') as f:
  for chunk in iter(lambda:f.read(1024*1024),b''):sha.update(chunk)
 print(f'Analyzing {video.name}: fps={fps:.3f}, total frames={total}, stride={every}')
 idx=0;prior=None;rows=[];cuts=[];thumbs=[];last_cut=-999
 while True:
  ok,fr=cap.read()
  if not ok:break
  if max_frames and idx>=max_frames:break
  if idx%every:
   idx+=1;continue
  small=cv2.resize(fr,(192,342),interpolation=cv2.INTER_AREA)
  gray=cv2.cvtColor(small,cv2.COLOR_BGR2GRAY)
  hist=cv2.calcHist([small],[0,1],None,[24,24],[0,256,0,256]);cv2.normalize(hist,hist)
  if prior is not None:
   mad=float(np.mean(cv2.absdiff(small,prior['frame']))/255)
   sim=float(cv2.compareHist(hist,prior['hist'],cv2.HISTCMP_CORREL))
   dx,dy,z,conf=estimate(prior['frame'],small)
  else: mad,sim,dx,dy,z,conf=0.,1.,0.,0.,1.,0.
  cut_score=.68*mad+.32*(1-clamp(sim,-1,1))/2
  iscut=bool(cut_score>.115 and idx-last_cut>fps*.28)
  if iscut:
   cuts.append({'frame':idx,'second':round(idx/fps,3),'cut_score':round(cut_score,4),'confidence':'candidate_only'});last_cut=idx
  # optical flow is sampled-frame movement; does not independently isolate camera from characters.
  rows.append({'frame':idx,'sec':round(idx/fps,4),'pixel_difference':round(mad,4),'hist_correlation':round(sim,4), 'cut_score':round(cut_score,4), 'camera_dx_candidate_px':round(dx,3),'camera_dy_candidate_px':round(dy,3),'zoom_ratio_candidate':round(z,5),'motion_inlier_fraction':round(conf,3),'cut_candidate':int(iscut)})
  if idx==0 or iscut or (idx/fps)%5<every/fps:
   if len(thumbs)<90:thumbs.append((idx/fps,small.copy()))
  prior={'frame':small,'hist':hist}
  if idx and idx%(every*200)==0:print(' ',idx,'/',total,flush=True)
  idx+=1
 cap.release()
 if not rows:raise ValueError('No readable frames')
 fieldnames=list(rows[0]);fp=out/'frame_metrics.csv'
 with open(fp,'w',newline='') as f:
  writer=csv.DictWriter(f,fieldnames=fieldnames);writer.writeheader();writer.writerows(rows)
 # Sequence-level descriptors, not a claim of actual camera movement.
 a=np.array([[r['camera_dx_candidate_px'],r['camera_dy_candidate_px'],r['zoom_ratio_candidate'],r['pixel_difference']] for r in rows],dtype=float)
 keyidx=sorted(set([int(i) for i in np.linspace(0,len(thumbs)-1,min(len(thumbs),25))]))
 thumbnails=[thumbs[i] for i in keyidx]
 cols=5;pw,ph=192,369
 sheet=Image.new('RGB',(pw*cols,ph*math.ceil(len(thumbnails)/cols)),(15,21,32))
 dr=ImageDraw.Draw(sheet)
 for j,(time_,frm) in enumerate(thumbnails):
  x=(j%cols)*pw;y=(j//cols)*ph
  sheet.paste(Image.fromarray(cv2.cvtColor(frm,cv2.COLOR_BGR2RGB)),(x,y))
  dr.text((x+8,y+346),f'{time_:06.2f}s',fill=(222,240,245))
 sheet.save(out/'reference_contact_sheet.jpg',quality=88)
 summary={
  'input':str(video.resolve()),'source_sha256':sha.hexdigest(),'stream_info':info['streams'],
  'fps':fps,'duration_sec':duration,'frames_total':total,'frames_analyzed':len(rows),'stride':every,
  'analysis_kind':'optical-flow, histogram, sampled frame difference: camera/cut candidates only',
  'analysis_limitations':['Foreground motion may be mistaken for camera motion.', 'Zoom estimates require stable feature correspondences.', 'A low cut score does not prove absence of a cut; dissolves can be missed.', 'Effects/borrowing/style similarity require human creative review.'],
  'candidate_cuts':cuts,
  'summary_metrics':{'median_abs_horizontal_flow_px_per_sample':float(np.median(abs(a[:,0]))),'median_abs_vertical_flow_px_per_sample':float(np.median(abs(a[:,1]))),'median_candidate_zoom_ratio':float(np.median(a[:,2])),'p95_frame_difference':float(np.quantile(a[:,3],.95))}
 }
 (out/'analysis.json').write_text(json.dumps(summary,indent=2,default=str))
 report=[f'# Local reference analysis — {video.name}','',f'- Duration: **{duration:.2f}s**; frame rate: **{fps:.2f}**; analyzed **{len(rows)}** frames (every {every} source frame).',f'- Proposed cuts: **{len(cuts)}** (algorithmic candidates; review manually).',f'- Median horizontal optical flow: **{summary["summary_metrics"]["median_abs_horizontal_flow_px_per_sample"]:.2f}px** per analyzed interval.',f'- Median scale ratio candidate: **{summary["summary_metrics"]["median_candidate_zoom_ratio"]:.5f}**.',f'- SHA-256: `{summary["source_sha256"]}`','','## Candidate edit points','']
 report.extend([f'- {c["second"]:.3f}s — score {c["cut_score"]:.3f}' for c in cuts[:100]])
 report.extend(['','## Limitations','','This report measures per-frame visual change, camera-like optical flow, and abrupt transitions. It does **not** establish that a camera zoom, scene cut, or specific VFX technique truly occurred. Verify against the contact sheet and actual footage.','', 'Use original artwork and newly authored motion when reconstructing editing techniques; do not redistribute third-party video or audio without appropriate rights.'])
 (out/'report.md').write_text('\n'.join(report)+'\n')
 print('Saved:',fp,out/'analysis.json',out/'reference_contact_sheet.jpg')
 return summary

def clamp(x,lo,hi):return max(lo,min(hi,x))
if __name__=='__main__':
 p=argparse.ArgumentParser()
 p.add_argument('--input',required=True)
 p.add_argument('--out',required=True)
 p.add_argument('--every',type=int,default=1,help='1=every source frame; 4=speedier diagnostic')
 p.add_argument('--max-frames',type=int,default=0)
 x=p.parse_args();analyze(x.input,x.out,x.every,x.max_frames)
