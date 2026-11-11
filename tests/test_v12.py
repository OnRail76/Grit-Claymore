#!/usr/bin/env python3
"""Regresiones de la V1.2 (interprete parcial, no Fuse)."""
import sys
from harness import boot,invoke,tick
from mini_z80 import SYM as S,ROOT
sys.path.insert(0,str(ROOT/'tools'))
import gfx_v12 as GFX
def g(v,n):return v.m[S[n]]

def check_bullets_outrun_scroll():
 v=boot()
 for i in range(14):tick(v,{'Q'});v.m[S['health']]=4   # llegar a la zona de scroll
 prev={};moves=[];scrolls=0;ticks=0
 for i in range(60):
  c0=g(v,'camera_top');s0=g(v,'sector')
  before={k:(v.m[S['bullets']+5*k],v.m[S['bullets']+5*k+2]) for k in (0,1)}
  tick(v,{'Q','SPACE'});v.m[S['health']]=4;v.m[S['lives']]=3
  if g(v,'sector')!=s0:break
  ticks+=1;scrolls+=(c0!=g(v,'camera_top'))
  for k in (0,1):
   on0,y0=before[k];on1,y1=v.m[S['bullets']+5*k],v.m[S['bullets']+5*k+2]
   if on0 and on1 and v.m[S['bullets']+5*k+3]==0 and y1<y0:moves.append(y0-y1)  # descarta balas nuevas en el mismo hueco
 bullet=sum(moves)/len(moves);scroll=scrolls/ticks
 assert scroll>0.3,scroll
 assert bullet>=1.9 and bullet>=2*scroll,(bullet,scroll)
 print('PASS al avanzar, la bala sube %.2f celdas/tick por pantalla y el terreno baja %.2f: %.1f veces mas rapida (V1.1: bala quieta)'%(bullet,scroll,bullet/scroll))

def check_hind_is_a_helicopter():
 v=boot();v.m[S['phase']]=3;v.m[S['sector']]=4;invoke(v,'scene_init')
 base=S['glyphs']+154*8
 cells=[bytes(v.m[base+k*8:base+k*8+8]) for k in range(24)]
 def px(f,x,y):return cells[f*12+(y//8)*4+x//8][y%8]>>(7-x%8)&1
 for f in (0,1):
  assert px(f,15,0) and px(f,16,0),'botalon de cola'
  assert sum(px(f,x,y) for x in range(5,9) for y in range(11,16))>=12,'contenedor de cohetes izq'
  assert sum(px(f,x,y) for x in range(23,27) for y in range(11,16))>=12,'contenedor de cohetes dcha'
  assert px(f,15,22),'morro'
 # el rotor cambia entre fotogramas (X / cruz)
 assert px(0,0,1) and not px(1,0,1) and px(1,0,8) and not px(0,0,8)
 assert [v.m[S['glyph_colors']+154+k] for k in range(12)]==GFX.BOSS_ATTRS['HIND']
 print('PASS Hind: cola con rotor, alas con cohetes, morro y rotor en dos posiciones')

def check_hud_frame():
 v=boot();v.m[S['lives']]=1;invoke(v,'draw_hud');invoke(v,'present_dirty')
 att=lambda r,c:v.m[0x5800+r*32+c]
 assert [att(10,c) for c in range(25,31)]==[0x44,0x44,0x05,0x05,0x05,0x05]
 for r,paper in ((3,6),(8,5),(14,4),(20,3)):
  assert all(att(r,c)==0x40|(paper<<3) for c in range(25,31))
 assert all(att(r,24)==0x07 and att(r,31)==0x07 for r in range(3,24)),'bisel continuo'
 print('PASS HUD: bisel gris continuo, rotulos sobre franja de color, vidas como cabezas de Grit')

if __name__=='__main__':
 check_bullets_outrun_scroll();check_hind_is_a_helicopter();check_hud_frame()
 print('ALL V1.2 TESTS PASSED (interprete parcial, no Fuse)')
