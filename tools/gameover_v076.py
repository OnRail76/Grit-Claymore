#!/usr/bin/env python3
"""ZX 48K native 6912-byte GAME OVER with user's yellow skull; deterministic RLE pack."""
from pathlib import Path
from PIL import Image,ImageDraw
import runpy
R=Path(__file__).resolve().parents[1];A=R/'assets'
raw=runpy.run_path(str(R/'tools/font_v07.py'))['raw']
source=Image.open(R/'assets/CALAVERA_REFERENCIA_USUARIO.jpg').convert('RGB')
mask=Image.new('1',source.size,0);sp=source.load();mp=mask.load()
for y in range(source.height):
 for x in range(source.width):
  rr,gg,bb=sp[x,y]
  if rr>120 and gg>100 and rr>bb*1.8 and gg>bb*1.7:mp[x,y]=1
bbox=mask.getbbox();assert bbox
skull=mask.crop(bbox).resize((104,108),Image.Resampling.LANCZOS).convert('L').point(lambda z:255 if z>110 else 0).convert('1')
mono=Image.new('1',(256,192));d=ImageDraw.Draw(mono)
def txt(s,y,scale):
 aw=6*scale;start=(256-len(s)*aw)//2
 for i,ch in enumerate(s):
  glyph=raw.get(ch,raw[' '])
  for py,row in enumerate(glyph):
   for px,bit in enumerate(row):
    if bit=='1': d.rectangle((start+i*aw+px*scale,y+py*scale,start+i*aw+(px+1)*scale-1,y+(py+1)*scale-1),fill=1)
txt('GAME OVER',14,3)
mono.paste(skull,((256-skull.width)//2,69))
# screen colour: red text, yellow skull; every attribute legal; black background.
attrs=bytearray(768)
for cy in range(24):
 for cx in range(32):attrs[cy*32+cx]=0x42 if cy<7 else 0x46
out=bytearray(6912)
for y in range(192):
 for bx in range(32):
  b=0
  for bit in range(8):b=(b<<1)|int(bool(mono.getpixel((bx*8+bit,y))))
  ofs=((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+bx
  out[ofs]=b
out[6144:]=attrs
# PackBits compatible with project's unpack_title: runs >=3; literals max127
enc=bytearray();i=0
while i<len(out):
 run=1
 while i+run<len(out) and out[i+run]==out[i] and run<128:run+=1
 if run>=3:
  enc.extend((127+run,out[i]));i+=run;continue
 lit=bytearray()
 while i<len(out) and len(lit)<127:
  run=1
  while i+run<len(out) and out[i+run]==out[i] and run<128:run+=1
  if run>=3:break
  lit.append(out[i]);i+=1
 if lit:enc.append(len(lit));enc.extend(lit)
 else:enc.extend((127+run,out[i]));i+=run
enc.append(0)
rev=bytearray();i=0
while True:
 n=enc[i];i+=1
 if n==0:break
 if n<128:rev.extend(enc[i:i+n]);i+=n
 else:rev.extend([enc[i]]*(n-127));i+=1
assert rev==out
(A/'GAME_OVER_ZX48_V076.scr').write_bytes(out)
(A/'GAME_OVER_RLE_V076.bin').write_bytes(enc)
pr=Image.new('RGB',(256,192),'black')
for y in range(192):
 for x in range(256):
  if mono.getpixel((x,y)):pr.putpixel((x,y),(255,50,60) if y<56 else (255,230,0))
pr.resize((768,576),Image.Resampling.NEAREST).save(A/'GAME_OVER_V076.png')
lines=['gameover_rle:']
for j in range(0,len(enc),24):lines.append(' db '+','.join(map(str,enc[j:j+24])))
(R/'src/gameover_generated.asm').write_text('\n'.join(lines)+'\n')
print('GAME OVER v076',len(enc),'compressed bytes, skull source user artwork')
