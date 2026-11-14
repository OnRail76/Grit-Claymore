#!/usr/bin/env python3
"""Partial Z80 interpreter for *headless smoke testing*, not a cycle-accurate emulator.
Only covers instructions emitted by the bundled mini assembler. The actual TAP needs Fuse testing.
"""
from pathlib import Path
import json,sys
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
SYM=json.loads((ROOT/'build/grit.sym.json').read_text())
class VM:
 def __init__(self):
  self.m=bytearray(65536);binary=(ROOT/'build/grit.bin').read_bytes();self.m[32768:32768+len(binary)]=binary
  # V1.1: 'entry' baja las pantallas RLE a 0x5E00. Se deja hecho de antemano para
  # las pruebas que saltan directamente a una rutina sin pasar por 'entry'.
  n=SYM['rle_block_end']-SYM['rle_block'];self.m[0x5e00:0x5e00+n]=self.m[SYM['rle_block']:SYM['rle_block']+n]
  self.kempston=0xff  # sin interfaz: bus flotante
  self.r=[0]*8 # B,C,D,E,H,L,(HL),A
  self.sp=0xffff;self.pc=32768;self.f=0;self.ix=0;self.iy=0;self.steps=0;self.keys=set();self.port_writes=0
  # ROM font mock for static analysis and proof of tile drawing, not Sinclair ROM pixels.
  font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',8)
  for ch in range(32,128):
   im=Image.new('1',(8,8),0);d=ImageDraw.Draw(im);d.text((1,-1),chr(ch),font=font,fill=1)
   for y in range(8):
    b=0
    for x in range(8):b=(b<<1)|int(im.getpixel((x,y))>0)
    self.m[0x3d00+(ch-32)*8+y]=b
 def rd(self):
  x=self.m[self.pc];self.pc=(self.pc+1)&65535;return x
 def word(self):
  l=self.rd();return l|self.rd()<<8
 def r16(self,rr):
  if rr==3:return self.sp
  i=rr*2;return (self.r[i]<<8)|self.r[i+1]
 def set16(self,rr,v):
  v&=65535
  if rr==3:self.sp=v;return
  i=rr*2;self.r[i]=v>>8;self.r[i+1]=v&255
 def hl(self):return self.r16(2)
 def sethl(self,v):self.set16(2,v)
 def reg(self,n):return self.m[self.hl()] if n==6 else self.r[n]
 def setreg(self,n,v):
  if n==6:self.m[self.hl()]=v&255
  else:self.r[n]=v&255
 def push(self,v):
  self.sp=(self.sp-1)&65535;self.m[self.sp]=(v>>8)&255
  self.sp=(self.sp-1)&65535;self.m[self.sp]=v&255
 def pop(self):
  v=self.m[self.sp]|self.m[(self.sp+1)&65535]<<8;self.sp=(self.sp+2)&65535;return v
 def flags(self,v,carry=0):self.f=(0x40 if (v&255)==0 else 0) | (1 if carry else 0)
 def cond(self,idx):
  z=bool(self.f&0x40);c=bool(self.f&1)
  return [not z,z,not c,c,False,False,False,False][idx]
 def alu(self,which,v):
  a=self.r[7]
  if which==0:res=a+v;self.flags(res,res>255);self.r[7]=res&255
  elif which==2:res=a-v;self.flags(res,res<0);self.r[7]=res&255
  elif which==4:self.r[7]=a&v;self.flags(self.r[7])
  elif which==5:self.r[7]=a^v;self.flags(self.r[7])
  elif which==6:self.r[7]=a|v;self.flags(self.r[7])
  elif which==7:self.flags(a-v,a<v)
  else:raise RuntimeError('alu mode '+str(which))
 def portread(self):
  b=self.r[0];v=0xff
  if b==0xfb and 'Q' in self.keys:v&=~1
  if b==0xfd and 'A' in self.keys:v&=~1
  if b==0xdf:
   if 'P' in self.keys:v&=~1
   if 'O' in self.keys:v&=~2
  if b==0x7f and 'SPACE' in self.keys:v&=~1
  if b==0xef:
   for bit,k in enumerate('09876'):
    if k in self.keys:v&=~(1<<bit)
  if b==0xbf and 'H' in self.keys:v&=~16
  return v
 def signed(self,v):return v-256 if v&128 else v
 def step(self):
  at=self.pc;op=self.rd();self.steps+=1
  if op==0x76:self.m[0x5c78]=(self.m[0x5c78]+1)&255;return  # HALT = una interrupcion: FRAMES+1
  if op in (0x00,0xf3,0xfb):return
  if op==0xc9:self.pc=self.pop();return
  if op==0xeb:
   d=self.r16(1);self.set16(1,self.hl());self.sethl(d);return
  if op in (0x1f,0x17):  # V1.8: RRA / RLA (generador xorshift)
   a=self.r[7];c=self.f&1
   self.r[7]=((a>>1)|(c<<7)) if op==0x1f else (((a<<1)|c)&255)
   self.f=(self.f&0x40)|(a&1 if op==0x1f else a>>7);return
  if op in (0x0f,0x07):
   a=self.r[7];self.r[7]=((a>>1)|(a<<7))&255 if op==0xf else ((a<<1)|(a>>7))&255
   self.f=(self.f&0x40)|(a&1 if op==0xf else a>>7);return
  if op in (0xc5,0xd5,0xe5,0xf5):
   self.push(self.r16((op>>4)&3) if op!=0xf5 else (self.r[7]<<8)|self.f);return
  if op in (0xc1,0xd1,0xe1,0xf1):
   v=self.pop()
   if op==0xf1:self.r[7]=v>>8;self.f=v&255
   else:self.set16((op>>4)&3,v)
   return
  if op&0xcf==0x01:self.set16((op>>4)&3,self.word());return
  if op&0xcf==0x03:self.set16((op>>4)&3,self.r16((op>>4)&3)+1);return
  if op&0xcf==0x0b:self.set16((op>>4)&3,self.r16((op>>4)&3)-1);return
  if op&0xcf==0x09:
   rr=(op>>4)&3;value=self.hl()+self.r16(rr);self.sethl(value);self.f=(self.f&0x40)|(1 if value>65535 else 0);return
  if op in (0x3a,0x32,0x2a,0x22):
   addr=self.word()
   if op==0x3a:self.r[7]=self.m[addr]
   elif op==0x32:self.m[addr]=self.r[7]
   elif op==0x2a:self.sethl(self.m[addr]|(self.m[(addr+1)&65535]<<8))
   else:self.m[addr]=self.r[5];self.m[(addr+1)&65535]=self.r[4]
   return
  if op in (0x0a,0x1a):self.r[7]=self.m[self.r16(0 if op==0x0a else 1)];return
  if op in (0x02,0x12):self.m[self.r16(0 if op==0x02 else 1)]=self.r[7];return
  if op&0xc7==0x06:
   r=(op>>3)&7;self.setreg(r,self.rd());return
  if op&0xc7 in (0x04,0x05):
   r=(op>>3)&7;v=(self.reg(r)+(1 if op&7==4 else -1))&255
   self.setreg(r,v);self.f=(self.f&1)|(0x40 if v==0 else 0);return
  if 0x40<=op<=0x7f:
   if op==0x76:return
   self.setreg((op>>3)&7,self.reg(op&7));return
  if 0x80<=op<=0xbf:self.alu((op>>3)&7,self.reg(op&7));return
  if op in (0xc6,0xd6,0xe6,0xee,0xf6,0xfe):
   self.alu({0xc6:0,0xd6:2,0xe6:4,0xee:5,0xf6:6,0xfe:7}[op],self.rd());return
  if op==0xc3:self.pc=self.word();return
  if op&0xc7==0xc2:
   addr=self.word()
   if self.cond((op>>3)&7):self.pc=addr
   return
  if op==0xcd:
   addr=self.word();self.push(self.pc);self.pc=addr;return
  if op&0xc7==0xc4:
   addr=self.word()
   if self.cond((op>>3)&7):self.push(self.pc);self.pc=addr
   return
  if op&0xc7==0xc0:
   if self.cond((op>>3)&7):self.pc=self.pop()
   return
  if op==0x10:
   j=self.signed(self.rd());self.r[0]=(self.r[0]-1)&255
   if self.r[0]:self.pc=(self.pc+j)&65535
   return
  if op in (0x18,0x20,0x28,0x30,0x38):
   j=self.signed(self.rd());which={0x20:0,0x28:1,0x30:2,0x38:3}.get(op)
   if which is None or self.cond(which):self.pc=(self.pc+j)&65535
   return
  if op==0xd3:self.rd();self.port_writes+=1;return
  if op==0xdb:
   port=self.rd();self.r[7]=self.kempston if port==0x1f else 0xff;return
  if op==0xed:
   x=self.rd()
   if x==0x78:self.r[7]=self.portread();return
   if x==0xa0:
    src=self.hl();dst=self.r16(1);self.m[dst]=self.m[src]
    self.sethl(src+1);self.set16(1,dst+1);self.set16(0,self.r16(0)-1);return
   if x in (0x4b,0x5b,0x6b,0x7b):
    addr=self.word();rr={0x4b:0,0x5b:1,0x6b:2,0x7b:3}[x];self.set16(rr,self.m[addr]|(self.m[(addr+1)&65535]<<8));return
   if x==0xb8:
    n=self.r16(0);src=self.hl();dst=self.r16(1)
    for i in range(n):self.m[(dst-i)&65535]=self.m[(src-i)&65535]
    self.sethl(src-n);self.set16(1,dst-n);self.set16(0,0)
    return
   if x==0xb0:
    n=self.r16(0);src=self.hl();dst=self.r16(1)
    if dst==src+1 and n:val=self.m[src];self.m[dst:dst+n]=bytes([val])*n
    else:self.m[dst:dst+n]=self.m[src:src+n]
    self.sethl(src+n);self.set16(1,dst+n);self.set16(0,0)
    return
   raise RuntimeError(f'unknown ED {x:02x} at {at:04x}')
  if op==0xcb:
   x=self.rd();r=x&7
   if 0x40<=x<0x80:
    v=self.reg(r);b=(x>>3)&7;self.f=(self.f&1)|(0x40 if (v&(1<<b))==0 else 0);return
   raise RuntimeError(f'unknown CB {x:02x} at {at:04x}')
  if op in (0xdd,0xfd):
   x=self.rd();prefix='ix' if op==0xdd else 'iy';idx=getattr(self,prefix)
   if x==0x21:setattr(self,prefix,self.word());return
   if x==0x23:setattr(self,prefix,(idx+1)&65535);return
   if x==0x19:setattr(self,prefix,(idx+self.r16(1))&65535);return
   if x in (0xe1,0xe5):
    if x==0xe1:setattr(self,prefix,self.pop())
    else:self.push(idx)
    return
   off=self.signed(self.rd());addr=(idx+off)&65535
   if x==0x36:self.m[addr]=self.rd();return
   if x==0x34:self.m[addr]=(self.m[addr]+1)&255;return
   if x==0x35:self.m[addr]=(self.m[addr]-1)&255;return
   if 0x46<=x<=0x7e and x&7==6:self.r[(x>>3)&7]=self.m[addr];return
   if 0x70<=x<=0x77:self.m[addr]=self.reg(x&7);return
   if 0x80<=x<=0xbf and x&7==6:self.alu((x>>3)&7,self.m[addr]);return
   raise RuntimeError(f'unknown {prefix} {x:02x} at {at:04x}')
  raise RuntimeError(f'unknown opcode {op:02x} @ {at:04x} after {self.steps} steps')
 def run_to(self,check,steps=1_000_000):
  for _ in range(steps):
   if check(self):return self.steps
   self.step()
  raise TimeoutError(f'at {self.pc:04x} after {self.steps}, waiting for {check}')
 def shadow(self):
  """V1.1: pantalla sombra (0xE000) reordenada como la pantalla real. La zona de
  juego (columnas 0..23) es un anillo: fila logica d = fila fisica (d+shadow_top)%24."""
  top=self.m[SYM['shadow_top']];out=bytearray(6912)
  for d in range(24):
   for c in range(32):
    p=(d+top)%24 if c<24 else d
    for y in range(8):
     out[((d&24)<<8)+y*256+((d&7)<<5)+c]=self.m[0xe000+((p&24)<<8)+y*256+((p&7)<<5)+c]
    out[6144+d*32+c]=self.m[0xf800+p*32+c]
  return bytes(out)
 def val(self,label):return self.m[SYM[label]]
 def set(self,label,val):self.m[SYM[label]]=val
 def render(self,out,scale=3):
  palette=[(0,0,0),(0,0,180),(180,0,0),(175,0,175),(0,140,0),(0,150,150),(170,150,0),(180,180,180)]
  bright=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
  im=Image.new('RGB',(256,192));pixels=im.load()
  for y in range(192):
   for x in range(256):
    byte_addr=0x4000+((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+(x>>3)
    bit=(self.m[byte_addr]>>(7-(x&7)))&1
    attr=self.m[0x5800+(y//8)*32+x//8];colors=bright if attr&0x40 else palette
    ink=attr&7;paper=(attr>>3)&7
    pixels[x,y]=colors[ink if bit else paper]
  im.resize((256*scale,192*scale),Image.Resampling.NEAREST).save(out)
if __name__=='__main__':
 v=VM()
 # Emulated keyboard: idle to release, then press only at title wait.
 def boot_keys(m):
  return m.pc==SYM['sp_wait']
 pressed=False
 for i in range(2_000_000):
  if boot_keys(v):pressed=True
  v.keys={'SPACE'} if pressed else set()
  if v.pc==SYM['main_loop']:
   print('game started after',i,'instructions', 'phase',v.val('phase'),'sector',v.val('sector'))
   v.render(ROOT/'build/ACTUAL_Z80_SIMULATED.png')
   break
  v.step()
 else:raise RuntimeError(f'failed boot at pc {v.pc:04x} after 2M steps')
