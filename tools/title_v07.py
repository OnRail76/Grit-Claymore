#!/usr/bin/env python3
"""Adaptación reproducible de la ilustración aprobada a pantalla .SCR ZX Spectrum 48K.
Bitmap de 256x192 y 32x24 celdas de atributos 8x8: PAPER negro, INK BRIGHT rojo/amarillo/blanco.
Inserta los 6912 bytes en forma RLE en el juego Z80, sin simular un modo gráfico inexistente.
"""
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[1]; A=R/'assets'
source=A/'TITULO_ILUSTRACION_APROBADA.png'
assert source.is_file(), 'Falta la ilustración aprobada del título'
orig=Image.open(source).convert('RGB')
assert orig.width/orig.height > 1.2
img=np.asarray(orig.resize((256,192), Image.Resampling.LANCZOS),dtype=np.float32)
# Establecer paleta Spectrum BRIGHT. Negros preservados; INK = rojo / amarillo / blanco.
PAL=np.array([[0,0,0],[0,0,255],[255,0,0],[255,0,255],
              [0,255,0],[0,255,255],[255,255,0],[255,255,255]],dtype=np.float32)
CANDIDATES=(2,6,7)
weights=np.array([0.27,0.63,0.1],dtype=np.float32)
bitmap=np.zeros((192,256),np.uint8)
attrs=np.zeros((24,32),np.uint8)
for cy in range(24):
 for cx in range(32):
  block=img[cy*8:cy*8+8,cx*8:cx*8+8]
  black_error=np.sum(block*block*weights,axis=2)
  opts=[]
  for ink in CANDIDATES:
   ink_error=np.sum((block-PAL[ink])**2*weights,axis=2)
   mask=ink_error < black_error
   opts.append((float(np.where(mask,ink_error,black_error).sum()),ink,mask))
  _,ink,mask=min(opts,key=lambda item:item[0])
  bitmap[cy*8:cy*8+8,cx*8:cx*8+8]=mask
  attrs[cy,cx]=0x40+ink
# V1.0.1 — Instrucciones en la última fila negra de la pantalla.
# Preservamos íntegramente las 184 primeras líneas de la ilustración aprobada;
# los siete píxeles de alto del texto ocupan únicamente Y=184..190.
# Fuente de 5x7: cada glifo son cinco bits por fila y una columna de separación.
TITLE_CONTROLS = "Q/A/O/P MOVER  SPACE FUEGO  PULSA SPACE"
FONT_5X7 = {
 'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
 'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
 'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
 'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
 'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
 'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
 'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
 'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
 'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
 'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
 'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
 'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
 'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
 'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
 '/': ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
 ' ': ("00000",)*7,
}
assert set(TITLE_CONTROLS) <= set(FONT_5X7), 'Faltan caracteres en la fuente'
assert not np.any(bitmap[184:192,:]), 'Franja inferior ocupada: no invadir ilustración'
width = 6*len(TITLE_CONTROLS)-1
assert width <= 240, f'La línea no cabe en la franja: {width} píxeles'
x0 = (256-width)//2
for i,c in enumerate(TITLE_CONTROLS):
 for dy, row in enumerate(FONT_5X7[c]):
  for dx, bit in enumerate(row):
   if bit == '1':
    bitmap[184+dy, x0+6*i+dx] = 1
# 24ª fila de atributos: blanco BRIGHT sobre negro, sin afectar filas anteriores.
attrs[23,:] = 0x47
assert not np.any(bitmap[191,:]), 'La línea debe dejar margen inferior de un píxel'
# Distribución entrelazada real de la VRAM 0x4000..0x57FF.
output=bytearray(6912)
for y in range(192):
 for bx in range(32):
  v=0
  for x in range(8):v=(v<<1)|int(bitmap[y,bx*8+x])
  output[((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+bx]=v
output[6144:]=attrs.tobytes()
# RLE compatible con unpack_title en grit_template.asm: literales 1..127, repeticiones 128..255.
enc=bytearray();i=0
while i<len(output):
 run=1
 while i+run<len(output) and output[i+run]==output[i] and run<128:run+=1
 if run>=3:
  enc.extend((127+run,output[i]));i+=run;continue
 literal=bytearray()
 while i<len(output) and len(literal)<127:
  run=1
  while i+run<len(output) and output[i+run]==output[i] and run<128:run+=1
  if run>=3:break
  literal.append(output[i]);i+=1
 if literal:enc.append(len(literal));enc.extend(literal)
 else:enc.extend((127+run,output[i]));i+=run
enc.append(0)
verify=bytearray();k=0
while True:
 n=enc[k];k+=1
 if not n:break
 if n<128:verify.extend(enc[k:k+n]);k+=n
 else:verify.extend([enc[k]]*(n-127));k+=1
assert verify==output and len(output)==6912
assert len(enc)<6000, f'Título excede presupuesto estimado: {len(enc)} bytes'
for name in ('TITULO_ESPECTRUM_V07.scr','TITULO_ESPECTRUM_V072.scr'):
 (A/name).write_bytes(output)
for name in ('TITULO_RLE_V07.bin','TITULO_RLE_V072.bin'):
 (A/name).write_bytes(enc)
# Vista exacta, sin suavizado: un píxel del PNG corresponde a un píxel de la memoria Spectrum.
preview=np.zeros((192,256,3),np.uint8)
for cy in range(24):
 for cx in range(32):
  bitblock=bitmap[cy*8:cy*8+8,cx*8:cx*8+8]
  preview[cy*8:cy*8+8,cx*8:cx*8+8]=np.where(bitblock[:,:,None]>0,PAL[attrs[cy,cx]&7],PAL[0])
previewimg=Image.fromarray(preview,'RGB')
previewimg.save(A/'TITULO_SPECTRUM_256x192_V072.png')
for name in ('TITULO_Z80_V07.png','TITULO_Z80_V072.png'):
 previewimg.resize((1024,768),Image.Resampling.NEAREST).save(A/name)
lines=['title_rle:']
for q in range(0,len(enc),24):lines.append(' db '+','.join(str(v) for v in enc[q:q+24]))
(R/'src/title_generated.asm').write_text('\n'.join(lines)+'\n')
print(f'TITULO V1.0.1: 6912 bytes .SCR, {len(enc)} bytes RLE, controles en Y=184..190, imagen original intacta')
