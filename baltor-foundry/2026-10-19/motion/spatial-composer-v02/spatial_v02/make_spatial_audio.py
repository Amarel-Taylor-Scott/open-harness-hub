#!/usr/bin/env python3
"""Original synthesized ambient mix with shot-specific cue points; intentionally no TTS."""
import json,math,argparse
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy.signal import butter,sosfilt
ROOT=Path(__file__).resolve().parent
CONFIG=json.loads((ROOT/'layouts.json').read_text())
SR=24000;D=float(CONFIG['duration_sec']);N=int(D*SR)

def make_audio(out):
 source=ROOT.parent/'outputs'/'original_atmosphere.wav'
 if source.exists():
  bed,src_rate=sf.read(source,dtype='float32')
  assert src_rate==SR,'Original ambient source rate differs from renderer.'
  bed=bed[:N] if len(bed)>=N else np.pad(bed,(0,N-len(bed)))
 else:bed=np.zeros(N,dtype=np.float32)
 rng=np.random.default_rng(20261018)
 a=bed.copy()*0.78

 def knock(t,amp=.14):
  i=int(t*SR);size=min(int(.21*SR),N-i);v=np.arange(size,dtype=np.float32)/SR
  if size<=0:return
  a[i:i+size]+=(amp*(np.sin(2*np.pi*(74-18*v)*v)*np.exp(-v*22)+rng.standard_normal(size)*.07*np.exp(-v*32)))
 def glass(t,frequency=550,amp=.10):
  i=int(t*SR);size=min(int(.62*SR),N-i);v=np.arange(size,dtype=np.float32)/SR
  if size<=0:return
  a[i:i+size]+=amp*(np.sin(2*np.pi*frequency*v)*.78+np.sin(2*np.pi*frequency*1.495*v)*.22)*np.exp(-v*5.4)
 def whoosh(t,amp=.11):
  i=int(t*SR);size=min(int(.38*SR),N-i);v=np.arange(size,dtype=np.float32)/SR
  if size<=0:return
  noise=rng.standard_normal(size).astype(np.float32)
  wave=sosfilt(butter(3,1800,fs=SR,output='sos'),noise)
  a[i:i+size]+=amp*wave*np.sin(np.pi*v/.38)**2
 for k,s in enumerate(CONFIG['shots']):
  t=float(s['start'])
  if k and t<D:whoosh(t+.08,.07)
  if k in (2,5,8):glass(t+.8,520+k*38,.075)
  if k==4:
   for ts in (t+1.1,t+1.46,t+1.85):knock(ts,.20)
  if k==7:glass(t+1.1,460,.08);glass(t+2.6,330,.08)
  if k==9:glass(t+4.8,700,.07)
 tt=np.arange(N)/SR
 fade=np.minimum(1,tt/1.)*np.minimum(1,(D-tt)/1.6)
 a=np.tanh(a*1.35)*fade
 p=np.max(abs(a));a=a*min(1,.75/max(p,.001))
 out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
 sf.write(out,a,SR,subtype='PCM_16')
 meta={'duration_s':D,'rate':SR,'peak':round(float(np.max(abs(a))),6),'rms':round(float(np.sqrt(np.mean(a*a))),6),'narration':'none — reserved for optional licensed neural narration','source_sound':'Original programmatically synthesized Baltor ambient bed, layered with newly synthesized cues.'}
 (out.parent/(out.stem+'_manifest.json')).write_text(json.dumps(meta,indent=2))
 print('Wrote original audio',out,meta)

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--out',default='outputs/spatial_original_audio.wav');args=p.parse_args();make_audio(ROOT/args.out)
