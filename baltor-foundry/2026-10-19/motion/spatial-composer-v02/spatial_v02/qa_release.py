#!/usr/bin/env python3
"""Technical checks for completed source-render MP4, layout sampler, frame audit.
Pass means technical conditions passed; not human aesthetic or publication approval.
"""
from pathlib import Path
import json,hashlib,subprocess,csv,math
import numpy as np
import cv2
from PIL import Image,ImageDraw,ImageFont
import composer_v02
ROOT=Path(__file__).resolve().parent
VIDEO=ROOT/'outputs/baltor_spatial_layout_study_65s_FINAL.mp4'

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def audit(path=VIDEO):
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(path)]))
 vid=next(s for s in info['streams'] if s['codec_type']=='video')
 audio=next((s for s in info['streams'] if s['codec_type']=='audio'),None)
 checks={'duration_65s':abs(float(info['format']['duration'])-65)<.08,'h264':vid['codec_name']=='h264','height_1920_width_1080':(vid['height'],vid['width'])==(1920,1080),'24fps':vid.get('r_frame_rate')=='24/1','has_audio':audio is not None,'aac':audio and audio['codec_name']=='aac'}
 cap=cv2.VideoCapture(str(path));fps=cap.get(cv2.CAP_PROP_FPS)
 frame_means=[];images=[];hashes=[];hists=[]
 for t in [0,1,3,6,12,18,24,31,38,45,52,58,62,64.95]:
  cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,frame=cap.read()
  if not ok:checks['frame_decode_'+str(t)]=False;continue
  small=cv2.resize(frame,(270,480),interpolation=cv2.INTER_AREA)
  frame_means.append(float(np.mean(cv2.cvtColor(small,cv2.COLOR_BGR2GRAY))))
  hashes.append(hashlib.sha256(small.tobytes()).hexdigest())
  images.append((t,cv2.cvtColor(small,cv2.COLOR_BGR2RGB)))
 cap.release()
 checks['sampled_frames_decodable']=len(images)==14
 checks['opening_not_black']=bool(frame_means and frame_means[0]>8)
 checks['ending_not_black']=bool(frame_means and frame_means[-1]>8)
 checks['visual_variation']=len(set(hashes))>=10
 # Export actual encoded-video sample frames, rather than only source previews.
 if images:
  pw,ph=270,480;cols=7
  sheet=Image.new('RGB',(pw*cols,ph*2),(12,18,30))
  for i,(t,im) in enumerate(images):
   pos=((i%cols)*pw,(i//cols)*ph)
   sheet.paste(Image.fromarray(im),pos)
   d=ImageDraw.Draw(sheet)
   d.rectangle((pos[0]+7,pos[1]+6,pos[0]+88,pos[1]+26),fill=(8,17,27))
   d.text((pos[0]+14,pos[1]+10),f'{t:05.2f}s',fill=(178,235,226))
  sheet.save(ROOT/'outputs/qa_final_mp4_contact_sheet.jpg',quality=91)
 frames_file=ROOT/'outputs/spatial_analysis/frame_spatial_metrics.csv'
 if frames_file.exists():
  with frames_file.open() as f:
   rows=list(csv.DictReader(f))
  checks['frame_audit_1560_rows']=len(rows)==1560
 else:checks['frame_audit_1560_rows']=False
 layouts=composer_v02.qa_layouts()
 checks['30_layout_samples']=len(layouts)==30
 checks['sampled_safe_zone_no_errors']=sum(len(i['errors']) for i in layouts)==0
 checks['sampled_text_box_overlap_none']=sum(len(i['warnings']) for i in layouts)==0
 output={
 'video':str(path),'hash_sha256':sha(path),'streams':{'video_codec':vid['codec_name'],'audio_codec':audio['codec_name'] if audio else None,'video_dimensions':[vid['width'],vid['height']],'fps':vid.get('r_frame_rate')},
 'duration_sec':float(info['format']['duration']),'sample_brightness_mean':frame_means,'checks':checks,
 'passed':sum(1 for x in checks.values() if x is True),'total':len(checks),'failures':[k for k,v in checks.items() if v is not True],
 'validation_scope':'Technical encoding, sampled frame continuity, sampled layout bounds, frame-metric completeness. No human creative approval, actual external reference review, or semantic face/subject collision detection.',
 'third_party_reference_status':'NOT OBTAINED or analyzed frame by frame; source material is original procedural assets.',
 'publication_status':'NOT PUBLISHED — final asset and copy require explicit approval',
 }
 (ROOT/'outputs/qa_release.json').write_text(json.dumps(output,indent=2)+'\n')
 m=['# Technical Release QA','',f'- **{output["passed"]}/{output["total"]}** checks passed.',f'- Output: `{path.name}`',f'- MP4 SHA256: `{output["hash_sha256"]}`',f'- Duration: **{output["duration_sec"]:.2f}s**, dimensions: **1080×1920**, 24fps H264/AAC.',f'- Analyzed-frame rows: **{1560 if checks.get("frame_audit_1560_rows") else "missing"}**.','', '## Checks','']
 m.extend([f'- {"PASS" if v else "FAIL"}: {k}' for k,v in checks.items()])
 m+=['','## Honest limitations','',output['validation_scope'],output['third_party_reference_status'],output['publication_status']]
 (ROOT/'outputs/QA_RELEASE.md').write_text('\n'.join(m)+'\n')
 print('QA:',output['passed'],'/',output['total'],'checks; failures',output['failures'])
 return output

if __name__=='__main__':audit()
