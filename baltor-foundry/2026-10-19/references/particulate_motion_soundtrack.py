#!/usr/bin/env python3
"""Generate an original synthesizer soundtrack for the Particulate-inspired video.
No copyrighted samples or external audio assets are used.
"""
from pathlib import Path
import subprocess
import numpy as np
from scipy.io import wavfile

FPS=24000
DUR=42
N=int(FPS*DUR)
t=np.arange(N,dtype=np.float32)/FPS
rng=np.random.default_rng(250)
# Spacious, slow-moving pad, D minor add9
mix=np.zeros(N,dtype=np.float32)
for f,amp in [(73.416,.042),(110.0,.027),(146.83,.020),(174.61,.017),(220,.010),(329.63,.006)]:
    phase=2*np.pi*(f*t + .013*np.sin(2*np.pi*.13*t))
    mix+=amp*(np.sin(phase) + .12*np.sin(2.002*phase))* (0.76+.24*np.sin(2*np.pi*.034*t+f/70))
# Gentle sequence of plucked pure tones with filtered overtones
note_f=[293.665,349.228,440.0,523.251,440.0,349.228,293.665,261.626,
       293.665,440.,523.251,587.33,523.251,440.,349.228,293.665]
for i,onset in enumerate(np.arange(.15,DUR-.25,.48)):
    start=int(onset*FPS);end=min(N,start+int(.48*FPS))
    loc=np.arange(end-start,dtype=np.float32)/FPS
    freq=note_f[(i*3)%len(note_f)]
    tone=(.031*np.sin(2*np.pi*freq*loc)+.009*np.sin(2*np.pi*(freq*2.01)*loc))
    env=(1-np.exp(-70*loc))*np.exp(-6.5*loc)
    mix[start:end]+=tone*env
# Light pulsing rhythmic bass
for onset in np.arange(0,DUR,.96):
    start=int(onset*FPS);end=min(N,start+int(.58*FPS))
    loc=np.arange(end-start,dtype=np.float32)/FPS
    mix[start:end]+= .045*np.sin(2*np.pi*(55*loc+15*loc*np.exp(-25*loc)))*np.exp(-12*loc)
# Clicky percussive texture and accent transitions
for i,onset in enumerate(np.arange(0,DUR,.24)):
    start=int(onset*FPS);end=min(N,start+int(.065*FPS))
    loc=np.arange(end-start,dtype=np.float32)/FPS
    noise=rng.normal(0,1,end-start).astype(np.float32)
    amp=.004 if i%4 else .009
    mix[start:end]+= amp*noise*np.exp(-65*loc)
for onset in [0,6,13,21,31,37]:
    start=int(onset*FPS);end=min(N,start+int(.8*FPS))
    loc=np.arange(end-start,dtype=np.float32)/FPS
    noise=rng.standard_normal(end-start).astype(np.float32)
    # synthetic ascending wash rather than sampled sfx
    from scipy.signal import butter,sosfilt
    filt=sosfilt(butter(2,[650,4200],btype='bandpass',fs=FPS,output='sos'),noise)
    env=np.sin(np.pi*loc/(loc[-1]+1e-6))**2
    mix[start:end]+=.025*filt*env
# Fade in / out; restrained mix below voiceover-ready levels
fadein=np.clip(t/1.1,0,1);fadeout=np.clip((DUR-t)/1.6,0,1)
mix*=fadein*fadeout
peak=max(np.abs(mix).max(),1e-6)
mix=mix*min(.72/peak,1.0)
# Slight stereo phase offset on high content
left=mix
right=np.roll(mix,int(FPS*.004))*.96
stereo=np.column_stack([left,right])
out='/mnt/data/particulate_soundtrack.wav'
wavfile.write(out,FPS,(np.clip(stereo,-1,1)*32767).astype(np.int16))
cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-i','/mnt/data/particulate_motion_demo_9x16.mp4','-i',out,'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart','/mnt/data/particulate_motion_demo_with_audio.mp4']
subprocess.run(cmd,check=True)
print('Created /mnt/data/particulate_motion_demo_with_audio.mp4')
