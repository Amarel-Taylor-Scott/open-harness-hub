#!/usr/bin/env python3
"""Procedural, research-inspired 3D motion explainer. NOT Particulate model inference.

Dependencies: vtk, numpy, Pillow, scipy (optional for music), ffmpeg.
The articulated object is manually constructed. Replace the `set_pose` source
with transforms exported from Particulate's animated GLB for actual inference.

Usage:
    python particulate_motion_demo.py --out particulate_motion_demo_9x16.mp4
"""
import argparse
import math
import os
import subprocess
import tempfile
import time
from pathlib import Path

import numpy as np
import vtk
from vtk.util.numpy_support import vtk_to_numpy
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FPS = 24
DURATION = 42
WIDTH = 720
HEIGHT = 1280
RENDER_SIZE = 620
BG = (6, 13, 28)
CYAN = (56, 212, 255)
PINK = (235, 103, 251)
GOLD = (255, 188, 94)
WHITE = (240, 250, 255)
MUTED = (149, 176, 194)

# Internal demo stages: duration ~ 42 sec. All motion is keyframed by this script.
STAGES = [
    (0, 6, "ONE STATIC MESH", "A beautiful 3D object. But it can't move.", "INPUT MESH", CYAN),
    (6, 13, "DISCOVER THE PARTS", "Find candidate pieces hidden in the geometry.", "PART SEGMENTATION", PINK),
    (13, 21, "RECOVER THE JOINTS", "Connect components and define degrees of freedom.", "KINEMATIC GRAPH", GOLD),
    (21, 31, "GIVE THE MESH MOTION", "Animate within joint limits — not random warping.", "JOINT ANIMATION", CYAN),
    (31, 37, "EXPORT A REUSABLE RIG", "A 3D asset can power many different scenes.", "ANIMATED GLB", PINK),
    (37, 42, "ONE ASSET. MANY VIDEOS.", "Create explainers, demos, loops and simulations.", "BALTOR MOTION LAB", GOLD),
]


def lerp(a, b, x): return a + (b-a)*x

def smooth(x):
    x = max(0.0, min(1.0, x))
    return x*x*(3-2*x)

def vec(r, g, b): return (r/255., g/255., b/255.)


def actor(source, color, opacity=1, specular=0.35):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(source.GetOutputPort())
    a = vtk.vtkActor()
    a.SetMapper(mapper)
    prop = a.GetProperty()
    prop.SetColor(*vec(*color))
    prop.SetAmbient(0.30)
    prop.SetDiffuse(0.60)
    prop.SetSpecular(specular)
    prop.SetSpecularPower(28)
    prop.SetOpacity(opacity)
    return a


def sphere(radius, col):
    s=vtk.vtkSphereSource();s.SetRadius(radius);s.SetThetaResolution(28);s.SetPhiResolution(20)
    return actor(s,col)


def cylinder(radius, height, col):
    s=vtk.vtkCylinderSource();s.SetRadius(radius);s.SetHeight(height);s.SetResolution(40)
    return actor(s,col)


def move_cylinder(a, start, end):
    p=np.asarray(start, float);q=np.asarray(end,float)
    delta=q-p;norm=float(np.linalg.norm(delta))
    yy=delta/max(norm,1e-8)
    trial=np.array([0.0,0.0,1.0])
    if abs(np.dot(yy,trial))>0.96: trial=np.array([0.0,1.0,0.0])
    xx=np.cross(yy,trial);xx/=max(np.linalg.norm(xx),1e-8)
    zz=np.cross(xx,yy)
    mat=vtk.vtkMatrix4x4();mat.Identity()
    for i in range(3):
        mat.SetElement(i,0,float(xx[i]));mat.SetElement(i,1,float(yy[i]*norm));mat.SetElement(i,2,float(zz[i]));mat.SetElement(i,3,float((p[i]+q[i])/2))
    a.SetUserMatrix(mat)


def ring(center, radius, color, renderer):
    poly=vtk.vtkRegularPolygonSource();poly.SetNumberOfSides(80)
    poly.SetRadius(radius);poly.GeneratePolygonOff();poly.SetNormal(0, 1, 0)
    tube=vtk.vtkTubeFilter();tube.SetInputConnection(poly.GetOutputPort());tube.SetRadius(0.011);tube.SetNumberOfSides(8)
    a=actor(tube,color, 0.85);a.GetProperty().SetAmbient(0.85);renderer.AddActor(a)
    a.SetPosition(*center)
    return a


def main(out, clip_start=0, clip_end=DURATION):
    renderer=vtk.vtkRenderer()
    renderer.GradientBackgroundOn()
    renderer.SetBackground(0.016,0.035,0.079)
    renderer.SetBackground2(0.009,0.018,0.043)
    rw=vtk.vtkRenderWindow()
    rw.SetOffScreenRendering(True)
    rw.SetSize(RENDER_SIZE,RENDER_SIZE)
    rw.SetMultiSamples(0)
    rw.AddRenderer(renderer)
    # Floor discs and grid
    platform=cylinder(1.53, 0.035,(20,34,60));platform.SetOrientation(90,0,0);platform.SetPosition(0,0,-0.08);renderer.AddActor(platform)
    accent=cylinder(1.31,0.012,(20,83,120));accent.SetOrientation(90,0,0);accent.SetPosition(0,0,-0.054);renderer.AddActor(accent)
    ground_ring=ring((0,0,-0.04), 1.4, CYAN,renderer)
    # Ground dots enhance depth/motion, created procedurally.
    for ix in range(-4,5):
        for iy in range(-4,5):
            if ix*ix+iy*iy>24:continue
            s=sphere(0.015,(32,95,136));s.SetPosition(ix*.45,iy*.45,-0.035);renderer.AddActor(s)

    base=cylinder(0.43,0.14, (100,130,158));base.SetOrientation(90,0,0);base.SetPosition(0,0,.02);renderer.AddActor(base)
    lower=cylinder(.105,1.,(116,144,171));renderer.AddActor(lower)
    upper=cylinder(.095,1.,(105,139,174));renderer.AddActor(upper)
    lower_glow=cylinder(.045,1., CYAN);renderer.AddActor(lower_glow)
    upper_glow=cylinder(.042,1., PINK);renderer.AddActor(upper_glow)
    joint0=sphere(.145,(95,135,171));renderer.AddActor(joint0)
    joint1=sphere(.165,(95,135,171));renderer.AddActor(joint1)
    joint2=sphere(.126,(100,140,171));renderer.AddActor(joint2)
    lamphead=vtk.vtkConeSource();lamphead.SetResolution(48);lamphead.SetHeight(.64);lamphead.SetRadius(.43);lamphead.SetDirection(0,0, -1)
    shade=actor(lamphead,(125,142,169));renderer.AddActor(shade)
    bulb=sphere(.14,GOLD);renderer.AddActor(bulb)
    joint_ring0=ring((0,0,.24),.32,CYAN,renderer)
    joint_ring1=ring((0,0,0),.27,PINK,renderer)
    # cinematic rim and soft fill
    k=vtk.vtkLight();k.SetPosition(3.0,5.0,7.0);k.SetFocalPoint(0,0,1.2);k.SetColor(0.7,0.88,1.0);k.SetIntensity(1.2);renderer.AddLight(k)
    fill=vtk.vtkLight();fill.SetPosition(-4,-3,2);fill.SetColor(0.65,0.35,1.0);fill.SetIntensity(.85);renderer.AddLight(fill)
    camera=renderer.GetActiveCamera()
    camera.SetFocalPoint(0,0,1.15)
    camera.SetViewUp(0,0,1)
    camera.SetClippingRange(0.1,100)
    camera.ParallelProjectionOn(); camera.SetParallelScale(2.15)
    w2i=vtk.vtkWindowToImageFilter();w2i.SetInput(rw)
    w2i.SetInputBufferTypeToRGB();w2i.ReadFrontBufferOff()

    fonts='/usr/share/fonts/truetype/dejavu'
    F1=ImageFont.truetype(f'{fonts}/DejaVuSans-Bold.ttf', 50)
    F2=ImageFont.truetype(f'{fonts}/DejaVuSans-Bold.ttf', 26)
    F3=ImageFont.truetype(f'{fonts}/DejaVuSans.ttf', 22)
    F4=ImageFont.truetype(f'{fonts}/DejaVuSansMono-Bold.ttf', 18)
    F5=ImageFont.truetype(f'{fonts}/DejaVuSans.ttf', 18)
    pathfont=ImageFont.truetype(f'{fonts}/DejaVuSans-Bold.ttf', 21)

    # rich dark background with subtle gradient, vignette, and instrumentation marks
    imgarr=np.zeros((HEIGHT,WIDTH,3),np.uint8)
    yy,xx=np.mgrid[0:HEIGHT,0:WIDTH]
    vig=np.sqrt(((xx-WIDTH/2)/(WIDTH*.68))**2+((yy-HEIGHT*.53)/(HEIGHT*.73))**2)
    gradient=np.clip((1-vig*.42),0.58,1.02)
    for c,val in enumerate(BG):imgarr[:,:,c]=np.uint8(np.clip(val*gradient+ (c==2)*np.maximum(0,1-np.abs(yy-640)/720)*8,0,255))
    backdrop=Image.fromarray(imgarr)

    # static decorative elements, independent from research data
    stars=[]
    rng=np.random.default_rng(7)
    for i in range(165):
        x=float(rng.integers(12,708));y=float(rng.integers(70,1180));
        r=int(rng.choice([1,1,1,2,2]));ph=float(rng.random()*2*math.pi)
        stars.append((x,y,r,ph))

    video_cmd=['ffmpeg','-y','-hide_banner','-loglevel','error',
        '-f','rawvideo','-pixel_format','rgb24','-video_size',f'{WIDTH}x{HEIGHT}',
        '-framerate',str(FPS),'-i','-', '-c:v','libx264','-preset','veryfast',
        '-crf','21','-pix_fmt','yuv420p','-movflags','+faststart',str(out)]
    p=subprocess.Popen(video_cmd,stdin=subprocess.PIPE)
    tick=time.time()
    nframe=int(FPS*clip_end)
    for frame in range(int(FPS*clip_start),nframe):
        t=frame/FPS
        phase=next(i for i,(a,b,*_) in enumerate(STAGES) if a<=t<b)
        start,end,headline,subtitle,tag,stage_color=STAGES[phase]
        u=(t-start)/(end-start)
        # human-authored joint motion. No inference is performed.
        mv=smooth((t-18)/3)
        phi1=math.radians(66 + mv*(16*math.sin((t-20)*.94)+10*math.sin((t-20)*.31)))
        phi2=math.radians(148 + mv*(25*math.sin((t-22)*.68+.9)))
        # gently demonstrate a non-moving unified static mesh in opening
        if t<18:phi1=math.radians(66);phi2=math.radians(148)
        q0=np.array([0,0,.24]);q1=q0+1.35*np.array([math.cos(phi1),0,math.sin(phi1)])
        q2=q1+1.18*np.array([math.cos(phi2),0,math.sin(phi2)])
        # Explosion temporarily illustrates part identities without claiming network prediction.
        explode=0.12 * math.sin(math.pi * smooth((t-6)/7)) if 6<t<13 else 0.
        exlo=np.array([.0,explode*.3,0]);exup=np.array([0,-explode*.8,.09*explode]);exhe=np.array([-explode,0,explode*.45])
        move_cylinder(lower, q0+exlo, q1+exlo)
        move_cylinder(lower_glow,q0+exlo,q1+exlo)
        move_cylinder(upper,q1+exup,q2+exup)
        move_cylinder(upper_glow,q1+exup,q2+exup)
        joint0.SetPosition(*q0);joint1.SetPosition(*q1);joint2.SetPosition(*q2)
        shade.SetPosition(*(q2+np.array([0,0,-0.32])+exhe))
        bulb.SetPosition(*(q2+np.array([0,0,-0.60])+exhe))
        joint_ring1.SetPosition(*q1)
        # segmented-material interpolation
        material=smooth((t-6)/4)
        base_color=(100,130,158); c_low=(116,144,171);c_up=(105,139,174);c_sh=(125,142,169)
        for a,c,col in [(base,base_color,CYAN),(lower,c_low,CYAN),(upper,c_up,PINK),(shade,c_sh,GOLD)]:
            a.GetProperty().SetColor(*vec(*tuple(int(lerp(c[j],col[j],material)) for j in range(3))))
        lower_glow.SetVisibility(t>=6);upper_glow.SetVisibility(t>=6)
        joint_ring0.SetVisibility(13<=t<=31)
        joint_ring1.SetVisibility(13<=t<=31)
        joint0.GetProperty().SetColor(*vec(*(CYAN if t>=13 else (100,133,166))))
        joint1.GetProperty().SetColor(*vec(*(PINK if t>=13 else (100,133,166))))
        joint2.GetProperty().SetColor(*vec(*(GOLD if t>=13 else (100,133,166))))
        bulb.GetProperty().SetAmbient(0.65)
        az=math.radians(43 + 12*math.sin(t*.22))
        camera.SetPosition(5.8*math.cos(az),5.8*math.sin(az),3.48+.18*math.sin(t*.25))
        # the platform is intentionally large enough to anchor all poses
        renderer.ResetCameraClippingRange()
        rw.Render();w2i.Modified();w2i.Update()
        vi=w2i.GetOutput();ww,hh,_=vi.GetDimensions()
        buf=vtk_to_numpy(vi.GetPointData().GetScalars()).reshape(hh,ww,3)[::-1,:,:]
        scene=Image.fromarray(buf.copy())
        # Scene blends via matching background. Cropped to intentional central graphic viewport.
        im=backdrop.copy();d=ImageDraw.Draw(im,'RGBA')
        # energy aura behind scene
        for radius in (310,274,237):
            d.ellipse((WIDTH/2-radius,330-radius/2,WIDTH/2+radius,330+radius*1.4), outline=(*stage_color, 8),width=2)
        # studio vertical side frame
        d.rounded_rectangle([35,270,685,965],radius=26,fill=(8,21,41,195), outline=(*stage_color,80),width=2)
        im.paste(scene,((WIDTH-RENDER_SIZE)//2,292))
        d=ImageDraw.Draw(im,'RGBA')
        # grid of tiny particles with subtle twinkling
        for x,y,r,ph in stars:
            opacity=int(12+30*(.5+.5*math.sin(t*1.4+ph)))
            d.ellipse((x-r,y-r,x+r,y+r), fill=(85,205,249,opacity))
        # moving corner crops
        for x0,y0,sgnx,sgny in [(58,306,1,1),(660,306,-1,1),(58,910,1,-1),(660,910,-1,-1)]:
            d.line([(x0,y0+sgny*25),(x0,y0),(x0+sgnx*25,y0)],fill=(*stage_color,185),width=3)
        # tiny HDR scanlines
        for y in range(320,895,24):
            d.line((66,y,653,y), fill=(75,142,198,10),width=1)
        d.rounded_rectangle([51,34,360,71],radius=17,fill=(10,33,52,220),outline=(58,177,210,110),width=1)
        d.text((70,44),'BALTOR  /  MOTION LAB',font=F4,fill=WHITE)
        d.rounded_rectangle([476,39,669,70],radius=15,fill=(*stage_color,27),outline=(*stage_color,115),width=1)
        text='PROCEDURAL DEMO'
        d.text((489,48),text,font=ImageFont.truetype(f'{fonts}/DejaVuSansMono.ttf',12),fill=(*stage_color,255))
        title_font=F1
        if d.textbbox((0,0),headline,font=F1)[2]>WIDTH-108:
            trial_size=max(28,int(50*(WIDTH-108)/d.textbbox((0,0),headline,font=F1)[2]))
            title_font=ImageFont.truetype(f'{fonts}/DejaVuSans-Bold.ttf',trial_size)
        d.text((58,104),headline,font=title_font,fill=WHITE,stroke_width=0)
        d.text((59,174),subtitle,font=F3,fill=MUTED)
        d.rounded_rectangle([57,224,305,257],radius=13,fill=(*stage_color,32),outline=(*stage_color,133),width=1)
        d.text((72,231),tag,font=F4,fill=(*stage_color,255))
        # small vertical type timeline on right side
        d.text((62,927),f'STAGE {phase+1:02d} / {len(STAGES):02d}',font=F4,fill=(*stage_color,255))
        # big dynamic bottom title, stat chips and callouts
        ypos=988
        d.rounded_rectangle([45,ypos,675,1171],radius=22,fill=(9,28,49,245),outline=(67,131,180,110),width=2)
        if phase==0:
            title='A mesh cannot explain how it moves.'
            lines=['Input: one static, 3D object', 'Output: articulation is the missing layer']
        elif phase==1:
            title='Which pieces are separate?'
            lines=['Segment the object into candidate parts', 'This example uses authored geometry']
        elif phase==2:
            title='Hinges. Axes. Limits.'
            lines=['Revolute joints + part hierarchy', 'Constrain rotation to plausible angles']
        elif phase==3:
            title='Motion driven by joint angles.'
            lines=[f'LOWER ARM  {int(math.degrees(phi1)):>3d} deg', f'UPPER ARM  {int(math.degrees(phi2)):>3d} deg']
        elif phase==4:
            title='One rig. Multiple outputs.'
            lines=['ANIMATED GLB    /    URDF    /    MJCF', '3D engines can render to MP4']
        else:
            title='Scale it into a video factory.'
            lines=['EXPLAINERS  /  LOOPING CLIPS  /  VFX', 'BALTOR.AI   -   REUSABLE CAPABILITIES']
        d.text((68,ypos+26),title,font=pathfont,fill=WHITE)
        for i,ss in enumerate(lines):
            d.text((68,ypos+84+36*i),ss,font=F5,fill=(*stage_color,255) if (i==0) else MUTED)
        # tiny informational limitation label (always on frame)
        d.text((61,1183),'ILLUSTRATIVE RIG  •  NOT PARTICULATE INFERENCE',font=ImageFont.truetype(f'{fonts}/DejaVuSansMono.ttf',13),fill=(128,157,178))
        d.text((61,1219),'baltor.ai  |  based on Particulate (CVPR 2026)',font=F5,fill=WHITE)
        # progress bar
        d.rounded_rectangle([56,1253,664,1259], radius=3, fill=(32,60,86))
        d.rounded_rectangle([56,1253,56+int(608*(t/DURATION)),1259], radius=3, fill=(*stage_color,255))
        # transition emphasis sweep
        if t-start<.4 and t>0:
            alph=int(105*(1-(t-start)/.4))
            d.rectangle((0,0,WIDTH,HEIGHT),fill=(*stage_color,alph))
        try:
            p.stdin.write(im.tobytes())
        except BrokenPipeError:
            raise RuntimeError('ffmpeg encoder stopped unexpectedly')
        if frame % (FPS*5)==0:
            print(f'{t:04.0f}/{DURATION}s rendered in {time.time()-tick:.1f}s',flush=True)
    p.stdin.close();code=p.wait()
    if code:raise RuntimeError('ffmpeg failed: exit '+str(code))
    print('VIDEO_CREATED', out, 'size',out.stat().st_size,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--out',default='/mnt/data/particulate_motion_demo_9x16.mp4');parser.add_argument('--start',type=float,default=0);parser.add_argument('--end',type=float,default=DURATION);args=parser.parse_args()
    main(Path(args.out), args.start, args.end)
