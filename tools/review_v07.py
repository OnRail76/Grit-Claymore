#!/usr/bin/env python3
"""Real compiled-Z80 RAM screenshots, explicitly simulator not Fuse."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tests'))
from harness import boot,invoke
v=boot()
shots=[]
for phase,name in [(1,'JUNGLA'),(2,'EL LABORATORIO'),(3,'COMPLEJO SUBTERRANEO')]:
 v.set('phase',phase);v.set('sector',2);invoke(v,'scene_init',limit=1500000)
 path=R/f'build/FASE_{phase}_Z80_SIMULADA_V076.png';v.render(path);shots.append((name,path))
vt=Image.open(R/'assets/TITULO_Z80_V07.png').convert('RGB').resize((768,576),Image.Resampling.NEAREST)
w,h=768,576
out=Image.new('RGB',(w*2+60,h*2+110),'#14121d');d=ImageDraw.Draw(out)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',23)
items=[('TITULO ARTISTICO SPECTRUM',vt)]+[(label,Image.open(fn).convert('RGB').resize((w,h),Image.Resampling.NEAREST)) for label,fn in shots]
for i,(label,im) in enumerate(items):
 x=20+(i%2)*(w+20);y=25+(i//2)*(h+40)
 d.rectangle((x-3,y-3,x+w+3,y+h+30),outline='#a3cdd6',width=2)
 out.paste(im,(x,y));d.text((x+5,y+h+2),label,font=font,fill='#ffe26a')
d.text((20,h*2+90),'Capturas de memoria de video Z80 simulada; sin verificacion de Fuse ni hardware.',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',15),fill='#c8d7db')
out.save(R/'assets/REVISION_GRAFICA_INTEGRADA_V07.png')
print('Review sheet assembled from compiled Z80 framebuffer, not imagined mockups')
