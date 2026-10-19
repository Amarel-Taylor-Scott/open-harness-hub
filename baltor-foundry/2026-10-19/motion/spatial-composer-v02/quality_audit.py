#!/usr/bin/env python3
"""Media-level checks; not a substitute for visual editorial review."""
from pathlib import Path
import subprocess,json,cv2,numpy as np,hashlib
ROOT=Path(__file__).resolve().parent

def audit(path):
 path=Path(path); assert path.exists(),path
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(path)]))
 video=next(s for s in probe['streams'] if s['codec_type']=='video')
 audios=[s for s in probe['streams'] if s['codec_type']=='audio']
 dur=float(probe['format']['duration']); fps=eval(video['r_frame_rate'])
 cap=cv2.VideoCapture(str(path));count=int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
 indices=[0,1,int(fps*1),int(fps*19),int(fps*30),int(fps*58),max(0,count-1)]
 samples=[]
 for idx in indices:
  cap.set(cv2.CAP_PROP_POS_FRAMES,idx)
  ok,fr=cap.read()
  if not ok:raise ValueError('Undecodable sample frame '+str(idx))
  samples.append(cv2.cvtColor(cv2.resize(fr,(128,224)),cv2.COLOR_BGR2GRAY))
 cap.release()
 means=[float(x.mean()) for x in samples]
 diffs=[float(np.mean(abs(a.astype(np.float32)-b.astype(np.float32)))) for a,b in zip(samples[:-1],samples[1:])]
 data={
  'file':str(path),'duration_sec':dur,'dimensions':[video['width'],video['height']],
  'fps':fps,'frames':count,'video_codec':video['codec_name'], 'audio_codec':audios[0]['codec_name'] if audios else None,
  'sample_brightness':means,'adjacent_sample_differences':diffs,
  'assertions':{'duration_70s':abs(dur-70)<.15,'dimensions_vertical_1080x1920':(video['width'],video['height'])==(1080,1920),'fps_24':abs(fps-24)<.01,'audio_present':len(audios)>0,'first_frame_not_black':means[0]>8,'last_frame_not_black':means[-1]>8,'non_static_across_scenes':sum(d>4 for d in diffs)>=3,'frame_count_expected':abs(count-1680)<=1},
  'limitations':'Spot frame checks, NOT complete visual quality, rights or motion correctness.'
 }
 (ROOT/'outputs'/'delivery_qa.json').write_text(json.dumps(data,indent=2))
 return data
if __name__=='__main__':
 p=ROOT/'outputs'/'the_last_signal_70s_FINAL.mp4'
 j=audit(p)
 print(json.dumps(j,indent=2))
 if not all(j['assertions'].values()):raise SystemExit(2)
