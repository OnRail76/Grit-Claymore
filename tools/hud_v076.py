#!/usr/bin/env python3
"""Compact 64x192 ZX 48K HUD. Static text and dynamic regions do NOT overlap.
Two tiny skulls are silhouettes resampled from user's approved yellow skull artwork.
The executable receives genuine 8x8 monochrome tiles and legal colour attributes.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import runpy
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'assets'; A.mkdir(exist_ok=True)
raw=runpy.run_path(str(ROOT/'tools/font_v07.py'))['raw']
source=ROOT/'assets/CALAVERA_REFERENCIA_USUARIO.jpg'
orig=Image.open(source).convert('RGB')
msk=Image.new('1',orig.size,0);op=orig.load();mp=msk.load()
for y in range(orig.height):
 for x in range(orig.width):
  r,g,b=op[x,y]
  if r>120 and g>100 and r>b*1.8 and g>b*1.7:mp[x,y]=1
bbox=msk.getbbox();assert bbox is not None
skull=msk.crop(bbox).resize((16,17),Image.Resampling.LANCZOS).convert('L').point(lambda v:255 if v>107 else 0).convert('1')
skull.resize((160,170),Image.Resampling.NEAREST).save(A/'CALAVERA_HUD_V076.png')
W,H=64,192
img=Image.new('1',(W,H));d=ImageDraw.Draw(img)
def label(string,cy):
 # 5x7 glyphs with 1px inter-letter spacing, centered BY PIXEL in the 64px column.
 # This corrects previous labels appearing 4-8px too far left.
 width=len(string)*6-1
 x0=(64-width)//2
 assert 6<=x0 and x0+width<=58
 for i,ch in enumerate(string):
  glyph=raw.get(ch,raw[' '])
  for yy,line in enumerate(glyph):
   for xx,c in enumerate(line):
    if c=='1':d.point((x0+i*6+xx,cy*8+yy),fill=1)

def frame(y0,y1):
 # 1-pixel frame 2px inset, top/bottom outside all dynamic cells.
 d.line((5,y0,58,y0),fill=1)
 d.line((2,y0+3,2,y1-3),fill=1)
 d.line((61,y0+3,61,y1-3),fill=1)
 d.line((5,y1,58,y1),fill=1)
 d.line((2,y0+3,5,y0),fill=1);d.line((58,y0,61,y0+3),fill=1)
 d.line((2,y1-3,5,y1),fill=1);d.line((58,y1,61,y1-3),fill=1)
# Large, legible four modules with the only permitted text labels.
frame(0,55);frame(56,103);frame(104,151);frame(152,191)
# 16x17 cropped/resampled skulls without overlap with title.
img.paste(skull,(10,4));img.paste(skull,(38,4))
label('PUNTOS',3)     # rows 24..31, score row 5 (40..47)
label('VIDAS',8)      # rows 64..71, smileys row 10 (80..87)
label('PODER',14)     # rows 112..119, energy row 16 (128..135)
label('TANQUE',20)    # rows 160..167, armor row 22 (176..183)
# No decorations within rows 5,10,16,22, to guarantee clean dynamic rendering.
# One constant ink per 8-pixel row means no colour clash at borders.
inks=[6]*7+[5]*6+[6]*6+[3]*5
assert len(inks)==24
unique=[];lut={};mapping=[];attrs=[]
for cy in range(24):
 for cx in range(8):
  g=[]
  for yy in range(cy*8,cy*8+8):
   bits=0
   for xx in range(cx*8,cx*8+8):bits=(bits<<1)|int(bool(img.getpixel((xx,yy))))
   g.append(bits)
  g=bytes(g)
  if g not in lut:
   lut[g]=len(unique);unique.append(g)
  mapping.append(lut[g]);attrs.append(0x40|inks[cy])
assert len(unique)<256
lines=['; V076: accurate 64x192 HUD, 4 boxes, 2 skulls, no fields overlap','hud_panel_map:']
for i in range(0,192,8):
 nums=[]
 for j in range(i,i+8):nums.extend((mapping[j],attrs[j]))
 lines.append(' db '+','.join(map(str,nums)))
lines.append('hud_panel_glyphs:')
for i in range(0,len(unique),2):
 vals=b''.join(unique[i:i+2]);lines.append(' db '+','.join(map(str,vals)))
(ROOT/'src/hud_generated.asm').write_text('\n'.join(lines)+'\n')
P={3:(245,60,205),4:(50,235,65),5:(40,215,235),6:(255,225,45),7:(250,250,250)}
preview=Image.new('RGB',(64,192),'black')
for i,g in enumerate(mapping):
 cx=(i%8)*8;cy=(i//8)*8;color=P[attrs[i]&7]
 for y in range(8):
  for x in range(8):
   if unique[g][y] & (128>>x):preview.putpixel((cx+x,cy+y),color)
preview.save(A/'HUD_NATIVO_V076.png')
preview.resize((384,1152),Image.Resampling.NEAREST).save(A/'HUD_AMPLIADO_V076.png')
print('HUD V076:',len(unique),'glyphs;',384+len(unique)*8,'bytes in Z80; skulls from approved artwork')
