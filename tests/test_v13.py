#!/usr/bin/env python3
"""Regresiones de la V1.3: mas enemigos, dificultad, oleadas de mechas, soldados
en la fase 3, motor del tanque (interprete parcial, no Fuse)."""
from harness import boot,invoke,tick
from mini_z80 import VM,SYM as S
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
EN=S['enemies']

def check_rear_fire():
 # disparo hacia arriba dirigido: soldado por debajo de Grit
 v=boot()
 for i in range(48):v.m[EN+i]=0
 st(v,'player_x',11);st(v,'player_y',8);st(v,'frame',1)
 v.m[S['map_data']+14*32+11]=0
 v.m[S['map_data']+13*32+11]=0
 v.m[EN:EN+12]=bytes([1,11,15,0,0,0,1,0,0,0,0,11])
 for i in range(14):
  tick(v);st(v,'player_x',11);st(v,'player_y',8);st(v,'health',4)
  if v.m[EN+3]:break
 assert v.m[EN+3]==1 and v.m[EN+7]==3 and v.m[EN+6]==0,'el soldado no se gira'
 y0=v.m[EN+5];tick(v);tick(v)
 assert v.m[EN+5]<y0,'la bala no sube'
 print('PASS el soldado se gira y dispara hacia atras')

def check_role_colors():
 for role,att in ((0,0x42),(1,0x43),(2,0x45)):
  v=boot()
  for i in range(48):v.m[EN+i]=0
  v.m[EN:EN+12]=bytes([1,10,6,0,0,0,1,0,role,50,0,10])
  invoke(v,'draw_dynamic');invoke(v,'present_frame')
  top=[v.m[0x5800+6*32+10],v.m[0x5800+6*32+11]];bottom=[v.m[0x5800+7*32+10],v.m[0x5800+7*32+11]]
  assert top==[att,att] and bottom==[0x46,0x46],(role,top,bottom)
  assert g(v,'actor_attr')==0
 print('PASS tres tipos de soldado distinguibles: fijo rojo, patrulla magenta, asalto cian')

def check_phase3():
 v=boot();st(v,'phase',3);st(v,'sector',2);invoke(v,'scene_init')
 total=g(v,'mecha_remaining');soldier=0
 for i in range(900):
  if g(v,'mecha_remaining'):
   for k in range(3):
    if v.m[EN+12*k]==2:v.m[EN+12*k]=0
   st(v,'mecha_remaining',0)
  m0=g(v,'mecha_remaining');tick(v,{'Q'});st(v,'health',4);st(v,'lives',3);st(v,'invuln',0)
  if g(v,'sector')!=2:break
  if g(v,'mecha_remaining')>m0:
   total+=g(v,'mecha_remaining')
   expected = [(2,6,2),(2,11,5),(2,16,2)] if g(v,'mecha_waves') else [(2,6,6),(2,11,2),(2,16,7)]
   assert [tuple(v.m[EN+12*k:EN+12*k+3]) for k in range(3)]==expected
  # ningun par de mechas se solapa nunca
  ms=[(v.m[EN+12*k+1],v.m[EN+12*k+2]) for k in range(3) if v.m[EN+12*k]==2]
  for a in range(len(ms)):
   for b in range(a+1,len(ms)):
    assert abs(ms[a][0]-ms[b][0])>=3 or abs(ms[a][1]-ms[b][1])>=3,('mechas solapados',ms)
  soldier+=v.m[EN+36]==1
  assert all(v.m[EN+12*k]!=1 for k in range(3)),'un soldado ocupo un hueco de mecha'
 assert total==9,total
 assert soldier>30,soldier  # presente la mayor parte del sector (~60 ticks)
 print('PASS fase 3: nueve mechas por sector (grupo + dos oleadas) y un soldado de apoyo')

def check_bosses():
 for ph,hp in ((1,16),(2,24),(3,32)):
  v=boot();st(v,'phase',ph);st(v,'sector',4);invoke(v,'scene_init');assert g(v,'boss_hp')==hp
 print('PASS jefes mas duros: 16 / 24 / 32 impactos')

def check_tank_engine():
 def writes(moving):
  v=boot()
  for i in range(48):v.m[EN+i]=0
  st(v,'tank_mode',1);st(v,'armor',2);st(v,'phase',1);w0=v.port_writes
  for i in range(24):
   tick(v,{'O'} if moving and i%2==0 else ({'P'} if moving else ()))
   for k in range(48):v.m[EN+k]=0
  return v.port_writes-w0
 quiet,move=writes(False),writes(True)
 assert move>quiet+20,(quiet,move)
 print('PASS el tanque ruge al moverse (%d escrituras al altavoz frente a %d parado)'%(move,quiet))

if __name__=='__main__':
 check_rear_fire();check_role_colors();check_phase3();check_bosses();check_tank_engine()
 print('ALL V1.3 TESTS PASSED (interprete parcial, no Fuse)')
