#!/usr/bin/env python3
"""Create ORIGINAL transparent hand-procedural 2D image plates. No reference images."""
from PIL import Image, ImageDraw, ImageFilter
from pathlib import Path
import math, random
random.seed(20261018)
O=Path(__file__).resolve().parent/'assets'; O.mkdir(exist_ok=True)
W,H,WORLD=540,960,3920
INK=(11,18,32); SKYTOP=(7,13,33); SKYLOW=(44,60,79)

def save(im,name):
 p=O/(name+'.png'); im.save(p); print(name,im.size,p.stat().st_size)

sky=Image.new('RGB',(W,H)); px=sky.load()
for y in range(H):
 u=min(1,y/680); glow=max(0,1-abs(y-485)/560)
 col=tuple(int(a*(1-u)+b*u+glow*4) for a,b in zip(SKYTOP,SKYLOW))
 for x in range(W):px[x,y]=col
sky=sky.convert('RGBA'); d=ImageDraw.Draw(sky)
for i in range(150):
 x=random.randrange(W); y=random.randrange(20,530); rr=random.choice([1,1,1,2]);
 d.ellipse([x-rr,y-rr,x+rr,y+rr],fill=random.choice([(154,202,235,110),(207,223,255,90),(104,159,188,140)]))
d.ellipse([424,161,484,221], fill=(173,226,236,35))
d.ellipse([433,170,473,210], fill=(227,236,235,170))
d.ellipse([441,169,475,204], fill=(242,238,222,240))
# Blue-green horizon haze bands
for k in range(25):
 y=570+k*11; d.line([(0,y),(W,y)],fill=(55,106,124,max(0,20-k)),width=3)
save(sky,'sky')

m=Image.new('RGBA',(WORLD,H),(0,0,0,0)); d=ImageDraw.Draw(m)
pts=[(0,H)]
for x in range(0,WORLD+61,60):
 y=540+int(55*math.sin(x/235)+24*math.sin(x/83)+12*math.cos(x/45))
 pts.append((x,y))
pts.extend([(WORLD,H),(0,H)])
d.polygon(pts,fill=(31,56,80,245))
pts=[(0,H)]
for x in range(0,WORLD+56,55):
 y=620+int(42*math.sin(x/190+1.4)+16*math.cos(x/49))
 pts.append((x,y))
pts.extend([(WORLD,H),(0,H)])
d.polygon(pts,fill=(28,49,71,255))
save(m,'mountains')

city=Image.new('RGBA',(WORLD,H),(0,0,0,0)); d=ImageDraw.Draw(city)
for j,x in enumerate(range(40,WORLD,65)):
 ht=random.randrange(70,220); y=690-ht
 c=(20+random.randrange(7),39+random.randrange(10),55+random.randrange(10),240)
 d.rectangle((x,y,x+random.randrange(30,70),720),fill=c)
 if j%8==2: d.line((x+15,y,x+15,y-45),fill=(22,43,62,230),width=3)
 for wy in range(y+14,680,23):
  if random.random()>.75:
   for wx in range(x+9,x+33,13):d.rectangle((wx,wy,wx+3,wy+6),fill=(76,156,159,65))
save(city,'city')

far=Image.new('RGBA',(WORLD,H),(0,0,0,0));d=ImageDraw.Draw(far)
for i,x in enumerate(range(0,WORLD,38)):
 h=random.randint(55,145); yy=729
 d.line((x,yy,x,yy-h),fill=(12,39,52,245),width=8)
 d.polygon([(x-26,yy-h/5),(x,yy-h-14),(x+26,yy-h/5)],fill=(12,38,51,246))
 d.polygon([(x-23,yy-h*0.03),(x,yy-h*0.7),(x+23,yy-h*0.03)],fill=(12,39,53,246))
save(far,'pines_far')

ground=Image.new('RGBA',(WORLD,H),(0,0,0,0)); d=ImageDraw.Draw(ground)
pts=[(0,H)]
for x in range(0,WORLD+16,16):
 y=728+int(6*math.sin(x/43)+7*math.cos(x/91))
 pts.append((x,y))
pts.extend([(WORLD,H),(0,H)])
d.polygon(pts,fill=(21,34,43,255))
for i in range(430):
 x=random.randrange(WORLD);y=random.randrange(742,958); radius=random.randrange(1,5)
 d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=random.choice([(52,72,69,200),(65,87,79,100),(15,24,35,200)]))
for i in range(200):
 x=random.randrange(WORLD); y=727+int(6*math.sin(x/43)+7*math.cos(x/91));
 d.line((x,y,x+random.randrange(-12,13),y-random.randint(4,20)),fill=(48,71,69,150),width=1)
save(ground,'ground')

props=Image.new('RGBA',(WORLD,H),(0,0,0,0)); d=ImageDraw.Draw(props)
# Broken footbridge, on path by x=1450
def line(co,fill=(17,27,41,255),width=5):d.line(co,fill=fill,width=width,joint='curve')
for bx in [1290,1370,1480,1550]:
 line((bx,720,bx+10,650),width=7)
line((1280,650,1380,670),width=10)
line((1485,684,1600,650),width=10)
for bx in range(1278,1384,19):line((bx,660,bx+10,730),width=3)
for bx in range(1478,1600,19):line((bx,680,bx+8,730),width=3)
# Hanging wires, tower
for towerx in [1700,2740]:
 line((towerx,725,towerx-18,381),width=8)
 line((towerx-18,381,towerx+6,720),width=8)
 for yy in [450,515,578,635]:
  line((towerx-15,yy,towerx+3,yy+11),width=5)
  line((towerx-16,yy,towerx+9,yy+70),width=3)
  line((towerx+6,yy,towerx-14,yy+65),width=3)
 d.ellipse((towerx-22,369,towerx-12,379),fill=(71,211,212,220))
 d.line((towerx-100,457,towerx-14,409,towerx+50,450),fill=(24,43,56,220),width=2)
# Outpost at 2320..2510
d.polygon([(2270,615),(2392,541),(2515,616)],fill=(16,27,41,255))
d.rectangle((2293,615,2494,742),fill=(18,28,41,255))
d.rectangle((2366,660,2425,739),fill=(9,15,25,255),outline=(68,93,98,180),width=3)
d.rectangle((2320,642,2350,665),fill=(62,162,163,80))
d.rectangle((2450,639,2482,666),fill=(60,145,154,85))
line((2482,615,2498,537),width=6)
d.ellipse((2491,530,2503,542),fill=(233,104,107,220))
# Dead street light
def pole(x):
 line((x,725,x,538),width=6)
 line((x,539,x+35,524,x+54,530),width=5)
 d.ellipse((x+40,527,x+59,533),fill=(82,165,179,70))
for x in [480,930,2150,3060]:pole(x)
# Roadway debris
for x in [740,802,1880,2000,2170,2635,3120]:
 d.polygon([(x,730),(x+12,714),(x+34,734)],fill=(55,69,72,255))
save(props,'props')

fg=Image.new('RGBA',(WORLD,H),(0,0,0,0)); d=ImageDraw.Draw(fg)
for i,x in enumerate(range(30,WORLD,130)):
 if i%4==2:continue
 y=742; h=random.randint(100,230)
 d.line((x,y,x-8,y-h),fill=(11,22,30,230),width=random.randint(8,16))
 d.polygon([(x-64,y-h/4),(x-8,y-h-24),(x+35,y-h/4)],fill=(11,23,31,213))
 d.polygon([(x-50,y-h*0.55),(x-8,y-h-38),(x+34,y-h*0.55)],fill=(11,22,31,190))
for x in range(100,WORLD,240):
 y=740
 d.ellipse((x-36,y-15,x+25,y+23),fill=(10,24,30,190))
save(fg,'foreground')
print('ORIGINAL plates written:',len(list(O.glob('*.png'))))
