#!/usr/bin/env python3
"""Encode user's APPROVED clean victory artwork as a genuine ZX Spectrum 48K SCR.
The picture is static 256x192 with legal per-8x8 attributes; no external formats
are needed at runtime. PackBits output is decoded by Z80 code unchanged.
"""
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1]; A=R/'assets'
source=A/'VICTORIA_APROBADA_V078.png'
assert source.is_file(),source
original=Image.open(source).convert('RGB')
scaled=original.resize((256,192),Image.Resampling.LANCZOS)
px=scaled.load()
buf=bytearray(6912)
inkrows=[]
for cy in range(24):
 for cx in range(32):
  red=yellow=0
  for y in range(cy*8,cy*8+8):
   for x in range(cx*8,cx*8+8):
    r,g,b=px[x,y]
    if r>128 and g<100 and r>g*1.8:red+=1
    elif r>125 and g>94 and r>b*1.6:yellow+=1
  # Preserve red footer marks, otherwise yellow on black across the whole screen.
  ink=2 if red>yellow and red>1 else 6
  buf[6144+cy*32+cx]=0x40|ink
for y in range(192):
 for col in range(32):
  val=0
  for bx in range(8):
   x=col*8+bx;r,g,b=px[x,y]
   is_ink=(r>130 and (g>85 or (g<125 and r>g*1.8)))
   val=(val<<1)|int(is_ink)
  off=((y&192)<<5)+((y&7)<<8)+((y&56)<<2)+col
  buf[off]=val
assert len(buf)==6912
# Compress using same lossless PackBits dialect as unpack_title.
enc=bytearray();i=0
while i<len(buf):
 run=1
 while i+run<len(buf) and run<128 and buf[i+run]==buf[i]:run+=1
 if run>=3:
  enc.extend((127+run,buf[i]));i+=run;continue
 literal=bytearray()
 while i<len(buf) and len(literal)<127:
  k=1
  while i+k<len(buf) and k<128 and buf[i+k]==buf[i]:k+=1
  if k>=3:break
  literal.append(buf[i]);i+=1
 if literal:enc.append(len(literal));enc.extend(literal)
 else:enc.extend((127+run,buf[i]));i+=run
enc.append(0)
verify=bytearray();i=0
while True:
 n=enc[i];i+=1
 if n==0:break
 if n<128:verify.extend(enc[i:i+n]);i+=n
 else:verify.extend([enc[i]]*(n-127));i+=1
assert verify==buf
(A/'VICTORIA_V078_48K.scr').write_bytes(buf)
(A/'VICTORIA_RLE_V078.bin').write_bytes(enc)
(A/'VICTORIA_V077_48K.scr').write_bytes(buf)  # legacy filename for existing tests
p=R/'src/victory_generated.asm'
with p.open('w') as out:
 out.write('victory_rle:\n')
 for j in range(0,len(enc),24):out.write(' db '+','.join(map(str,enc[j:j+24]))+'\n')
# Render exact SCR for visual QA, not an estimated mockup.
from PIL import Image
im=Image.new('RGB',(256,192),'black');o=im.load()
pal={2:(255,68,43),6:(255,230,0)}
for y in range(192):
 for col in range(32):
  ink=pal[buf[6144+(y//8)*32+col]&7]
  off=((y&192)<<5)+((y&7)<<8)+((y&56)<<2)+col
  b=buf[off]
  for bit in range(8):
   if b & (128>>bit):o[col*8+bit,y]=ink
im.resize((768,576),Image.Resampling.NEAREST).save(A/'VICTORIA_V078_PREVIEW.png')
print('Victory final SCR',len(buf),'bytes; packed',len(enc),'bytes')
