#!/usr/bin/env python3
"""Original atmospheric score/SFX; no third-party music or voice synthesis."""
import math, json, argparse
from pathlib import Path
import numpy as np
from scipy.signal import butter,sosfilt
import soundfile as sf
ROOT=Path(__file__).resolve().parent
STORY=json.loads((ROOT/'storyboard.json').read_text())
SR=24000;DUR=70

def make_audio(path):
 rng=np.random.default_rng(21337)
 n=int(DUR*SR);t=np.arange(n,dtype=np.float32)/SR
 a=np.zeros(n,dtype=np.float32)
 def note(f, start, end, amp=.01, vib=.3):
  nonlocal a
  i=max(0,int(start*SR));j=min(n,int(end*SR));p=t[i:j]-start
  if len(p)==0:return
  envelope=np.minimum(1,np.maximum(0,p)*.22)*np.minimum(1,np.maximum(0,end-t[i:j])*.8)
  a[i:j]+= (amp*(.80*np.sin(2*np.pi*f*p)+.15*np.sin(2*np.pi*f*2.002*p)) *envelope*(.87+.13*np.sin(2*np.pi*vib*p))).astype(np.float32)
 # Gentle evolving harmonic drones, not intrusive synth music.
 for k in range(0,70,10):
  root=[55.,65.41,48.99,55.,58.27,43.65,55.][k//10]
  for f,q in [(root,.022),(root*1.5,.009),(root*2,.007)]:note(f,k,k+11,min(q,.027),.07)
 # Low rain/wind wash: filtered rather than piercing white noise.
 noise=rng.standard_normal(n).astype(np.float32)
 wind=sosfilt(butter(3,160,fs=SR,output='sos'),noise).astype(np.float32)
 wind/=max(.000001,np.max(abs(wind)))
 a+=wind*.025*(.75+.25*np.sin(2*np.pi*.09*t))
 # Footstep/tick waves with envelope.
 def hit(when,kind='foot',ampl=.1):
  nonlocal a
  i=int(when*SR)
  if i<0 or i>=n:return
  length={'foot':.16,'thud':.34,'ping':1.3,'whoosh':.6,'knock':.2,'flare':1.1}.get(kind,.25)
  j=min(n,i+int(length*SR));tt=np.arange(j-i)/SR
  if len(tt)==0:return
  noise=rng.standard_normal(len(tt)).astype(np.float32)
  if kind=='foot':sig=(np.sin(2*np.pi*(98-32*tt)*tt)*np.exp(-tt*21)+noise*.3*np.exp(-tt*45))
  elif kind in ('thud','knock'):sig=np.sin(2*np.pi*(65-23*tt)*tt)*np.exp(-tt*15)+noise*.16*np.exp(-tt*44)
  elif kind=='ping':sig=(np.sin(2*np.pi*622*tt)+.35*np.sin(2*np.pi*933*tt))*np.exp(-tt*3)
  elif kind=='whoosh':sig=sosfilt(butter(2,900,fs=SR,output='sos'),noise)*np.sin(np.pi*tt/length)**2
  elif kind=='flare':sig=np.sin(2*np.pi*(170+480*tt)*tt)*np.exp(-tt*2.5)+noise*.06
  a[i:j]+=ampl*sig.astype(np.float32)
 for sh in STORY['shots']:
  if sh['actor'] in ('walk','run','sprint'):
   period={'walk':.48,'run':.29,'sprint':.21}[sh['actor']]
   for ts in np.arange(sh['start']+.35,sh['end']-.2,period):hit(float(ts),'foot',.065)
  if sh['mode'] in ('whip','reveal','push'):hit(sh['start']+.12,'whoosh',.22)
  if sh['fx']=='signal':
   for s in [sh['start']+.65,sh['start']+2.25]:hit(s,'ping',.10)
  if sh['fx']=='shake':hit(sh['start']+1.4,'thud',.22)
  if sh['fx']=='impact':hit(sh['start']+1.1,'knock',.16);hit(sh['start']+1.67,'knock',.21)
  if sh['fx']=='flare':hit(sh['start']+.8,'flare',.19);hit(sh['start']+1.5,'whoosh',.12)
  if sh['fx']=='alarm':hit(sh['start']+.4,'thud',.12)
 # One original short finale note
 hit(67,'ping',.1)
 # Master gentle attack/release and limiter: avoid high-level/muddy music.
 fade=np.minimum(1,t/1.5)*np.minimum(1,(DUR-t)/1.7)
 a*=fade
 a=np.tanh(a*1.7).astype('float32')
 peak=np.max(abs(a));a*=min(1,.75/max(.01,peak))
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 sf.write(path,a,SR,subtype='PCM_16')
 print('Original audio',path,'rms',float(np.sqrt(np.mean(a*a))),'peak',float(np.max(abs(a))))

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--out',default='outputs/original_atmosphere.wav');args=ap.parse_args();make_audio(ROOT/args.out)
