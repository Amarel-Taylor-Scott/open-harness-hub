#!/usr/bin/env python3
"""Original 30s motion graphics spot; no references or third-party footage.
Usage: python render_last_tab.py --style kinetic --output DIR
Requires Pillow/Numpy/FFmpeg as external nonbundled dependencies.
"""
import argparse, pathlib, subprocess, math, random, wave, json, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W,H,FPS,DURATION=720,1280,24,30
FONT_REG='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
FONT_BOLD='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
try:
    import glob
    opts=glob.glob('/usr/share/fonts/truetype/**/InterDisplay-Bold.otf',recursive=True)+glob.glob('/usr/share/fonts/opentype/inter/InterDisplay-Bold.otf')
    if opts: FONT_BOLD=opts[0]
    opts=glob.glob('/usr/share/fonts/opentype/inter/InterDisplay-Regular.otf')
    if opts: FONT_REG=opts[0]
except Exception: pass

def font(n,bold=False):return ImageFont.truetype(FONT_BOLD if bold else FONT_REG,int(n))
def clamp(v,a=0,b=1):return max(a,min(b,v))
def ease(t):t=clamp(t);return t*t*(3-2*t)
def colorhex(s):return tuple(int(s[i:i+2],16) for i in (1,3,5))
def bg_topography(mode):
    if mode=='kinetic':
        a,b=('#081124','#152945')
    else:a,b=('#f9f0e6','#e2d7c9')
    r,g,bv=np.array(colorhex(a)),np.array(colorhex(b)),0
    y=np.linspace(0,1,H,dtype=np.float32)[:,None,None]
    x=np.linspace(0,1,W,dtype=np.float32)[None,:,None]
    v=(r[None,None,:]*(1-y)+g[None,None,:]*y).astype(np.uint8)
    v=np.broadcast_to(v,(H,W,3)).copy()
    yy,xx=np.mgrid[0:H,0:W]
    vignette=np.clip(1-0.18*np.sqrt(((xx/W)-.5)**2+((yy/H)-.42)**2),.8,1)
    v=(v.astype(np.float32)*vignette[:,:,None]).clip(0,255).astype('uint8')
    return Image.fromarray(v,'RGB')
def draw_text(draw,xy,text,sz,fill,bold=True,anchor='mm',stroke=0,strokefill=None):
    draw.text(xy,text,font=font(sz,bold),fill=fill,anchor=anchor,stroke_width=stroke,stroke_fill=strokefill)
def centered(draw,y,lines,sz,fill,dy=None):
    if isinstance(lines,str):lines=lines.split('\n')
    if dy is None:dy=round(sz*1.25)
    for i,line in enumerate(lines):draw_text(draw,(W//2,y+i*dy),line,sz,fill)
def pill(draw,box,fill,outline=None,radius=16,width=2):draw.rounded_rectangle(box,radius=radius,fill=fill,outline=outline,width=width)
def draw_laptop(d,mode,t):
    col='#D8EAFD' if mode=='kinetic' else '#2E2730'; glow='#4EACE8' if mode=='kinetic' else '#A5A0A0'
    # monitor in one consistent perspective
    pill(d,(142,465,592,770),'#152039' if mode=='kinetic' else '#403941','#51769B',18,4)
    pill(d,(160,480,575,744),'#0E172C' if mode=='kinetic' else '#FAF2E8',radius=10)
    d.rectangle((137,774,605,791),fill='#899AB3')
    d.polygon([(137,791),(606,791),(645,813),(95,813)],fill='#455A72')
    for j in range(5):
        yy=530+j*34
        d.line((188,yy,395+int(math.sin(t*2+j)*20),yy),fill=('#4CD6C2' if j==2 else '#477395'),width=5)
    d.ellipse((230,814,285,870),fill='#212D42')
    # character side silhouette
    d.ellipse((90,678,157,755),fill='#27394D')
    d.line((123,740,140,920),fill='#263649',width=35)
    d.line((130,793,235,805),fill='#263649',width=25)

def draw_browser(draw,x,y,w,h,label,mode,alpha=1,accent=False):
    fill='#172944' if mode=='kinetic' else '#F5EDE3'
    line='#6A92AC' if mode=='kinetic' else '#8C695B'
    head='#1F3856' if mode=='kinetic' else '#D4B5A9'
    x,y,w,h=map(int,(x,y,w,h));
    if x+w<-1 or x>W+1 or y+h<-1 or y>H+1:return
    pill(draw,(x,y,x+w,y+h),fill,outline=line,radius=12,width=2)
    draw.rounded_rectangle((x,y,x+w,y+35),radius=12,fill=head)
    for j,c in enumerate(['#E26768','#D7B16D','#5EBCA5']):draw.ellipse((x+12+j*20,y+10,x+20+j*20,y+18),fill=c)
    sz=15 if len(label)>18 else 17
    draw_text(draw,(x+14,y+59),label,sz,'#EFF7FF' if mode=='kinetic' else '#211E21',True,anchor='la')
    for j in range(3):draw.line((x+15,y+95+j*24,x+int(w*(.58+.08*math.sin(j))),y+95+j*24),fill=line,width=4)

def draw_graph(d,t,mode,stage):
    coords=[(180,620),(365,500),(545,650),(335,780),(185,930),(540,940)]
    labels=['DISCOVER','CLASSIFY','VERIFY','COMPOSE','TEST','REUSE']
    accent='#70DCC4' if mode=='kinetic' else '#B15331'
    edge='#355B77' if mode=='kinetic' else '#C4AA9B'
    for a,b in [(0,1),(1,2),(2,3),(3,4),(3,5),(4,0),(5,2)]:
        x1,y1=coords[a];x2,y2=coords[b];d.line((x1,y1,x2,y2),fill=edge,width=5)
        pos=(t*.32+a*.16)%1
        if pos<1:
            xx=x1+(x2-x1)*pos;yy=y1+(y2-y1)*pos
            d.ellipse((xx-8,yy-8,xx+8,yy+8),fill=accent)
    for i,(x,y) in enumerate(coords):
        s=46+int(3*math.sin(t*2+i))
        d.ellipse((x-s,y-s,x+s,y+s),fill='#1C3853' if mode=='kinetic' else '#FCF6EE',outline=accent,width=4)
        d.ellipse((x-8,y-8,x+8,y+8),fill=accent)
        draw_text(d,(x,y+66),labels[i],15,'#BFD1E2' if mode=='kinetic' else '#5F413E',True)

def frame(t,mode,bg):
    if mode=="paper": return frame_paper(t,bg)
    im=bg.copy();d=ImageDraw.Draw(im)
    dark='#F7F7F5' if mode=='kinetic' else '#27242A'
    sub='#99B6CE' if mode=='kinetic' else '#725B58'
    accent='#70DCC4' if mode=='kinetic' else '#BE532E'
    for i in range(0,16):
        y=((i*97+int(t*16))%1440)-80
        d.line((20,y,700,y-50),fill=('#13243A' if mode=='kinetic' else '#E8DBCE'),width=1)
    # Shot 1: single task + human character
    if t<4:
        u=t/4
        centered(d,175,'ONE SIMPLE TASK.',49,dark)
        d.line((160,222,560,222),fill=accent,width=5)
        draw_laptop(d,mode,t)
        centered(d,1000,'Find one useful AI skill.',29,sub)
        centered(d,1110,'2:13 AM',24,sub)
    # Shot 2: tab proliferation, comic energy
    elif t<12:
        u=t-4
        count=min(26,3+int(u*3.4))
        for i in range(count):
            dx=36+(i%4)*23+90*math.sin(i*1.7+u*.9)
            dy=315+(i%8)*70+16*math.cos(i*.9+u*1.1)
            w=300+(i%3)*40
            draw_browser(d,dx,dy,w,230,['Best AI Skills','MCP Tool Finder','Agent Skills DB','What is a harness?'][i%4],mode)
        if t>7:
            pill(d,(54,170,666,295),'#8B2440' if mode=='kinetic' else '#A4513D',radius=14)
            centered(d,230,'47 TABS LATER.',43,'#FFFFFF')
        if t>9.6:
            pill(d,(72,1010,648,1120),'#102039' if mode=='kinetic' else '#ECE1D5',outline=accent)
            centered(d,1060,'STILL SEARCHING...',29,dark)
    # Shot 3: sudden pause
    elif t<16:
        u=t-12
        pill(d,(72,500,648,704),'#101A2D' if mode=='kinetic' else '#EEE4DA',outline=accent,radius=18,width=4)
        centered(d,552,'WAIT.',72,dark)
        centered(d,644,'WHAT IF IT FOUND YOU?',30,accent)
        if int(u*3)%2: d.rectangle((W//2-3,747,W//2+3,818),fill=accent)
        centered(d,1060,'No more endless searches.',24,sub)
    # Shot 4: graph assembling, transform
    elif t<25:
        u=t-16
        centered(d,152,'DISCOVER. VERIFY. COMPOSE.',29,dark)
        d.line((74,212,646,212),fill=accent,width=4)
        draw_graph(d,u,mode,u)
        for i,l in enumerate(['1  Discover capabilities','2  Test reliability','3  Build with evidence']):
            x=85;y=1040+i*57
            d.rounded_rectangle((x,y,x+550,y+45),radius=9,fill='#193149' if mode=='kinetic' else '#EEE1D2',outline='#316A79' if mode=='kinetic' else '#C7ADA0',width=1)
            draw_text(d,(x+18,y+22),l,23,dark,False,anchor='lm')
    # Shot 5: resolved signature and CTA
    else:
        u=t-25
        d.rounded_rectangle((130,310,590,730),radius=90,fill='#122941' if mode=='kinetic' else '#EBD9CD',outline=accent,width=5)
        cx,cy=360,520
        for i in range(7):
            angle=i*math.pi*2/7+u*.35
            x=cx+148*math.cos(angle);y=cy+148*math.sin(angle)
            d.ellipse((x-13,y-13,x+13,y+13),fill=accent)
            d.line((cx,cy,x,y),fill='#315D6E' if mode=='kinetic' else '#A98679',width=5)
        d.ellipse((cx-49,cy-49,cx+49,cy+49),fill=accent)
        centered(d,805,'BALTOR.AI',70,dark)
        centered(d,911,'BUILD ON WHAT EXISTS.',35,accent)
        centered(d,1030,'Reusable capabilities. Real possibilities.',20,sub)
        if u>3:
            centered(d,1160,'baltor.ai',26,dark)
    # Minimal, non-distracting framing system
    d.rectangle((26,28,694,1252),outline='#42647F' if mode=='kinetic' else '#B9A699',width=2)
    d.line((35,53,125,53),fill=accent,width=5)
    d.line((595,1226,684,1226),fill=accent,width=5)
    d.text((49,59),'B  /  MOTION FOUNDRY',font=font(14,True),fill=sub)
    return im

def frame_paper(t,bg):
    """Second directorial treatment: hand-drawn paper collage with illustrated diagrams."""
    im=bg.copy(); d=ImageDraw.Draw(im)
    ink='#2D2930'; red='#BC4D36'; muted='#7E625B'; card='#FFF9EE';warm='#F6E6D1'
    r=random.Random(4021)
    # Perforations and printed flecks, no retro UI rectangle frame
    for k in range(28):
        x=r.randrange(30,W-30);y=r.randrange(30,H-30)
        d.ellipse((x,y,x+2,y+2),fill='#CAB8AC')
    for x in range(50,701,46):
        d.ellipse((x,36,x+8,44),fill='#DDCBC2')
    d.line((42,92,678,92),fill=muted,width=2)
    draw_text(d,(48,62),'BALTOR  /  DESIGN NOTES',17,muted,True,anchor='lm')
    if t<4:
        centered(d,190,['ONE TINY TASK.','ONE HUGE DETOUR.'],47,ink,72)
        d.arc((110,360,610,975),start=188,end=356,fill=red,width=10)
        # Workspace as ink drawing, character at desk
        d.line((95,850,615,850),fill=ink,width=9)
        d.rounded_rectangle((260,540,545,790),radius=15,fill=card,outline=ink,width=5)
        d.line((292,588,495,588),fill=red,width=8)
        for j in range(3): d.line((292,635+40*j,455,635+40*j),fill='#AB9B92',width=6)
        d.line((215,800,310,915),fill=ink,width=18)
        d.ellipse((135,710,218,795),fill=warm,outline=ink,width=7)
        d.line((175,785,200,940),fill=ink,width=15)
        draw_text(d,(W//2,1070),'FIND ONE REUSABLE SKILL',32,red)
        centered(d,1150,'Sounds easy, right?',23,muted)
    elif t<12:
        u=t-4
        count=4+int(u*3)
        for i in range(count):
            x=int(36+(i%4)*40+35*math.sin(u*.8+i));y=int(242+(i%7)*100)
            w=310;h=212
            # sticky-note geometry with offset paper drop shadow
            d.polygon([(x+8,y+9),(x+w+8,y+18),(x+w,y+h+12),(x,y+h)],fill='#D5C8B8')
            d.polygon([(x,y),(x+w,y+7),(x+w-8,y+h),(x+4,y+h-8)],fill=card,outline=ink,width=3)
            d.polygon([(x+120,y-8),(x+190,y-8),(x+184,y+20),(x+128,y+20)],fill='#E3CA82')
            draw_text(d,(x+18,y+48),['IS THIS THE ONE?','TRY ANOTHER TOOL','ANOTHER LOGIN?','WHERE IS THE DOC?'][i%4],17,ink,True,anchor='la')
            for j in range(2):d.line((x+22,y+75+j*28,x+245,y+75+j*28),fill='#B4A39A',width=4)
        if t>7:
            d.polygon([(44,128),(682,125),(659,287),(57,301)],fill=red)
            centered(d,210,'47 TABS LATER!',55,'#FFFFFF')
        if t>9.5:
            d.rounded_rectangle((110,1070,610,1152),radius=8,fill=ink)
            centered(d,1110,'STILL LOOKING...',30,card)
    elif t<16:
        u=t-12
        d.polygon([(92,380),(627,358),(643,922),(103,943)],fill=card,outline=ink,width=6)
        d.line((90,382,625,359),fill=red,width=16)
        centered(d,525,'HOLD ON.',70,ink)
        centered(d,640,['WHAT IF YOUR AGENT','COULD FIND IT?'],34,red,58)
        if int(u*2.2)%2:d.ellipse((320,819,401,900),fill=red)
        centered(d,1080,'STOP SCROLLING. START BUILDING.',23,muted)
    elif t<25:
        u=t-16
        centered(d,173,'A BETTER WAY TO BUILD',38,ink)
        d.line((75,235,645,235),fill=red,width=5)
        coords=[(175,540),(515,460),(353,755),(192,1003),(537,1037)]
        titles=['DISCOVER','REVIEW','COMPOSE','TEST','REUSE']
        for k,(a,b) in enumerate([(0,1),(1,2),(2,3),(2,4),(4,1)]):
            x,y=coords[a];xx,yy=coords[b];d.line((x,y,xx,yy),fill=muted,width=7)
            angle=u*.36+k*.31
            px=x+(xx-x)*((angle)%1);py=y+(yy-y)*((angle)%1)
            d.ellipse((px-11,py-11,px+11,py+11),fill=red)
        for k,(x,y) in enumerate(coords):
            r0=65 if k==2 else 55
            d.ellipse((x-r0,y-r0,x+r0,y+r0),fill=card,outline=ink,width=5)
            centered_k=titles[k]
            draw_text(d,(x,y),centered_k,17,ink)
        d.polygon([(90,318),(300,335),(300,393),(84,381)],fill='#E6BE7E')
        d.text((105,352),'SKILL INDEX',font=font(18,True),fill=ink,anchor='lm')
    else:
        u=t-25
        d.rounded_rectangle((109,295,609,770),radius=28,fill=card,outline=ink,width=8)
        d.ellipse((182,355,530,703),outline=red,width=15)
        for k in range(8):
            ang=math.pi*2*k/8+u*.17
            x=355+135*math.cos(ang);y=528+135*math.sin(ang)
            d.line((355,528,x,y),fill=ink,width=5)
            d.ellipse((x-13,y-13,x+13,y+13),fill=red)
        d.ellipse((320,494,390,564),fill=red)
        centered(d,838,'BALTOR.AI',71,ink)
        d.polygon([(66,919),(655,911),(661,996),(61,1000)],fill=red)
        centered(d,956,'BUILD ON WHAT EXISTS.',35,'#FFFFFF')
        centered(d,1062,['Original capabilities.','Composed for real work.'],24,muted,42)
        if u>2.8:centered(d,1195,'baltor.ai',31,ink)
    return im

def synth_audio(path,duration=30,sr=48000):
    n=duration*sr;t=np.arange(n,dtype=np.float64)/sr
    a=np.zeros(n,dtype=np.float64)
    # Warm restrained original harmonic bed, fades to silence for the 12s pivot.
    for i,f in enumerate([110,164.81,196,329.63]):
        a+=.025*np.sin(2*np.pi*f*t+0.06*np.sin(t*1.8+i))
    env=np.minimum(1,t/1.5)*np.minimum(1,(duration-t)/2.0)
    a*=env
    beat=(np.sin(np.pi*((t*2.0)%1))**26)*.022
    a+=beat*(t>3)*(t<12)
    for sec in [4,5,6,7,8,9,10,11,16,17,18,19,20,21,22,23,24,25]:
        idx=int(sec*sr);stop=min(n,idx+int(.18*sr));tt=np.arange(stop-idx)/sr
        ch=.04*np.exp(-tt*27)*np.sin(2*np.pi*(160+sec%4*70)*tt)
        a[idx:stop]+=ch
    a[(t>11.9)&(t<15.8)]*=.04
    for sec in [16,25]:
        idx=int(sec*sr);stop=min(n,idx+int(2*sr));tt=np.arange(stop-idx)/sr
        a[idx:stop]+=0.04*np.sin(2*np.pi*330*tt)*np.exp(-tt/1.5)
    a=np.tanh(a*1.5)/1.3
    buf=np.clip(a*32767,-32768,32767).astype('<i2')
    with wave.open(str(path),'wb') as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes(buf.tobytes())

def run(output,mode):
    root=pathlib.Path(output);root.mkdir(parents=True,exist_ok=True)
    bg=bg_topography(mode)
    silent=root/f'last_tab_{mode}_silent.mp4';sound=root/f'last_tab_{mode}_score.wav';final=root/f'last_tab_{mode}_30s.mp4'
    synth_audio(sound)
    cmd=['ffmpeg','-nostdin','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',str(silent)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
    assert proc.stdin
    contact=[]
    for i in range(DURATION*FPS):
        im=frame(i/FPS,mode,bg)
        proc.stdin.write(np.asarray(im).tobytes())
        if i in [24,100,180,245,320,403,540,630,699]:
            im.thumbnail((270,480)); contact.append(im.copy())
    proc.stdin.close();err=proc.stderr.read();code=proc.wait()
    if code:raise RuntimeError(f'FFmpeg failed: {err[:300]!r}')
    subprocess.run(['ffmpeg','-nostdin','-y','-loglevel','error','-i',str(silent),'-i',str(sound),'-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(final)],check=True)
    # Create contact montage with source screenshots (no external material).
    sheet=Image.new('RGB',(270*3,480*3),(18,20,25))
    for j,im in enumerate(contact):sheet.paste(im,((j%3)*270,(j//3)*480))
    sheet.save(root/f'last_tab_{mode}_contact.jpg',quality=91)
    silent.unlink(missing_ok=True)
    meta={'duration_seconds':DURATION,'resolution':[W,H],'fps':FPS,'style':mode,'narration':False,'source':'original_procedural_artwork','rendered':True,'label':'motion-graphics spec ad, not human-approved broadcast-ready commercial'}
    (root/f'last_tab_{mode}_manifest.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(final,final.stat().st_size)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--style',choices=['kinetic','paper'],default='kinetic');ap.add_argument('--output',default='outputs/commercial');args=ap.parse_args();run(args.output,args.style)
