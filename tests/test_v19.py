#!/usr/bin/env python3
"""Regresiones de la V1.9 (interprete parcial, no Fuse): jefes y tanque.
- Disparo apuntado: recto desde la columna que Grit tiene encima, o en
  diagonal hacia el desde el borde mas cercano del jefe.
- Rabia a mitad de vida: parpadeo rojo, el doble de rapido, mas cadencia y
  abanico de tres.
- Aviso: el jefe destella en blanco los 4 ticks antes de disparar.
- Tanque: una casilla cada 4 ticks, casco verde y canon blanco, rojo al
  recibir un impacto.
- Colores de los graficos en 0x5D00."""
from harness import boot,invoke,tick
from mini_z80 import SYM as S
SP=S['special_shots']
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
def shots(v):return [tuple(v.m[SP+5*i+1:SP+5*i+4]) for i in range(6) if v.m[SP+5*i]]
def boss(ph):
 v=boot();st(v,'phase',ph);st(v,'sector',4);invoke(v,'scene_init')
 for i in range(30):v.m[SP+i]=0
 return v
def fire(v):
 for i in range(30):v.m[SP+i]=0
 invoke(v,'hind_fire_now');return shots(v)
def attr(v,y,x):return v.m[0x5800+y*32+x]

def check_punteria():
 v=boss(1);st(v,'boss_x',8);st(v,'player_y',15)
 st(v,'player_x',10);s=fire(v)
 assert s==[(10,7,0)],('recto desde la columna de Grit',s)
 st(v,'player_x',16);s=fire(v)
 assert s==[(11,7,2)],('diagonal derecha desde el borde',s)
 st(v,'player_x',3);s=fire(v)
 assert s==[(8,7,1)],('diagonal izquierda desde el borde',s)
 v=boss(2);st(v,'boss_x',8);st(v,'player_x',16);s=fire(v)
 assert sorted(x[2] for x in s)==[0,2],('fase 2: apuntado y recto',s)
 print('PASS disparo apuntado: recto bajo el jefe, diagonal desde el borde; fase 2 anade uno recto')

def check_rabia():
 for ph,hp in ((1,16),(2,24),(3,32)):
  v=boss(ph);assert g(v,'boss_hp')==hp and g(v,'boss_half')==hp//2
  st(v,'boss_hp',hp//2)
  tick(v);st(v,'health',4);st(v,'invuln',50)
  assert g(v,'boss_rage')==1 and g(v,'rage_flash')>10,('entra en rabia',ph)
  s=fire(v);assert sorted(x[2] for x in s)==[0,1,2],('abanico en rabia',ph,s)
 # movimiento: fase 1 normal cada 4 ticks, en rabia cada 2
 for rage,expect in ((0,6),(1,12)):
  v=boss(1);st(v,'boss_rage',rage);st(v,'rage_flash',0);st(v,'boss_x',4);st(v,'boss_dir',0)
  x0=g(v,'boss_x')
  for i in range(24):tick(v);st(v,'health',4);st(v,'invuln',50)
  moved=g(v,'boss_x')-x0
  assert abs(moved-expect)<=1,(rage,moved)
 print('PASS rabia a mitad de vida en los tres jefes: parpadeo, abanico y el doble de rapido')

def check_aviso():
 v=boss(1);st(v,'boss_mask',15);st(v,'rage_flash',0)
 res={}
 for f in range(32):
  st(v,'frame',f);st(v,'force_attr',0);invoke(v,'boss_tint')
  res[f]=g(v,'force_attr')
 warn=[f for f in range(32) if res[f]==0x47]
 assert warn and all(((f+4)&15)<4 for f in warn),('destello solo en los 4 ticks previos',warn)
 assert all(res[f]==0 for f in range(32) if f not in warn)
 st(v,'rage_flash',8);reds=0
 for f in range(8):
  st(v,'frame',f);st(v,'force_attr',0);invoke(v,'boss_tint');reds+=g(v,'force_attr')==0x42
 assert reds==4,('parpadeo rojo en rabia',reds)
 # al pintar el jefe el color forzado no se queda puesto
 invoke(v,'draw_dynamic');assert g(v,'force_attr')==0
 print('PASS aviso: destello blanco solo en los 4 ticks previos al disparo; rojo al entrar en rabia')

def check_tanque():
 v=boot();st(v,'tank_mode',1);st(v,'armor',4)
 for i in range(4):tick(v);st(v,'health',4)
 px,py=g(v,'player_x'),g(v,'player_y')
 cells=[attr(v,py+dy,px+dx) for dy in (0,1) for dx in (0,1)]
 assert cells.count(0x44)==3 and cells.count(0x47)==1,('verde con canon blanco',[hex(c) for c in cells])
 # velocidad: 1 casilla cada 4 ticks
 y0=g(v,'player_y')
 for i in range(16):tick(v,{'Q'});st(v,'health',4)
 assert y0-4<=g(v,'player_y')<=y0-3,('una casilla cada 4 ticks',y0,g(v,'player_y'))
 # impacto: parpadea en rojo
 st(v,'invuln',0);invoke(v,'damage_player')
 assert g(v,'armor')==3 and g(v,'tank_flash')==12
 reds=0
 for i in range(10):
  tick(v);st(v,'health',4)
  px,py=g(v,'player_x'),g(v,'player_y')
  reds+=attr(v,py,px)==0x42
 assert reds>=3,('parpadeo rojo',reds)
 print('PASS tanque: una casilla cada 4 ticks, casco verde y canon blanco, rojo al recibir')

def check_memoria():
 assert S['glyph_colors']==0x5d00 and S['force_attr']==0x7ff4
 assert 0x5e00+S['rle_block_end']-S['rle_block']<=0x7ff0 and S['tape_end']<0xfb00
 print('PASS memoria: colores en 0x5D00, variables en 0x7FF0, la cinta acaba antes de la pila')

if __name__=='__main__':
 check_memoria();check_punteria();check_rabia();check_aviso();check_tanque()
 print('ALL V1.9 TESTS PASSED (interprete parcial, no Fuse)')
