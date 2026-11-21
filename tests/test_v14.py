#!/usr/bin/env python3
"""Regresiones de la V1.4: raciones y tanque de cuatro impactos (interprete parcial, no Fuse)."""
from harness import boot,invoke,tick
from mini_z80 import SYM as S
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
def solid(v,d,e):return v.m[S['solid_flags']+v.m[S['map_data']+d*32+e]]

def check_rations():
 total=0
 for ph in (1,2,3):
  for sec in (1,2,3,4):
   v=boot();st(v,'phase',ph);st(v,'sector',sec);invoke(v,'scene_init')
   assert g(v,'ration_available')==1,(ph,sec)
   assert 13<=g(v,'ration_y')<=16
   assert_ration_space(v)
   total+=1
   assert g(v,'ration_mid')==int(sec<4 and (ph==3 or ph==2 and sec in (1,3))),(ph,sec)
 # refuerzo de la fase 3: aparece al pasar la fila 12 si no hay otra
 v=boot();st(v,'phase',3);st(v,'sector',2);invoke(v,'scene_init');st(v,'ration_available',0)
 extra=0
 for i in range(300):
  if g(v,'mecha_remaining'):
   for k in range(3):
    b=S['enemies']+12*k
    if v.m[b]==2:v.r[2]=v.m[b+2];v.r[3]=v.m[b+1];invoke(v,'restore_nine');v.m[b]=0
   st(v,'mecha_remaining',0)
  a0=g(v,'ration_available');tick(v,{'Q'});st(v,'health',4);st(v,'lives',3)
  if g(v,'sector')!=2:break
  if g(v,'ration_available') and not a0:
   extra+=1;assert g(v,'camera_top')<=12 and 3<=g(v,'ration_y')<=6
   assert_ration_space(v)
 assert extra==1,extra
 print('PASS raciones accesibles: doce iniciales, dos refuerzos en Laboratorio y tres en Complejo')

def assert_ration_space(v):
 x,y=g(v,'ration_x'),g(v,'ration_y')
 assert not any(solid(v,y+dy,x+dx) for dx in (0,1) for dy in (0,1))

def check_ration_placement_and_pickup():
 v=boot()
 # Simula tres filas sin hueco 2x2: solo queda disponible la cuarta.
 m=S['map_data']
 for y in range(13,18):
  v.m[m+32*y:m+32*y+24]=bytes([12])*24
 for y in (16,17):
  v.m[m+32*y+10:m+32*y+12]=bytes(2)
 st(v,'ration_y',13);st(v,'ration_available',0);invoke(v,'place_ration')
 assert (g(v,'ration_y'),g(v,'ration_x'),g(v,'ration_available'))==(16,10,1)
 st(v,'player_y',16);st(v,'player_x',10);st(v,'health',1);st(v,'tank_mode',1)
 invoke(v,'check_ration')
 assert g(v,'health')==3 and g(v,'tank_mode')==1 and g(v,'ration_available')==0
 v.m[m+16*32+10]=12
 st(v,'ration_y',13);invoke(v,'place_ration')
 assert g(v,'ration_available')==0
 print('PASS la busqueda cambia de fila, descarta terreno cerrado y permite recoger desde el tanque')

def check_tank_four_hits():
 v=boot()
 for i in range(48):v.m[S['enemies']+i]=0
 st(v,'tank_available',1);st(v,'tank_y',g(v,'player_y'));st(v,'player_x',14);st(v,'tank_y',g(v,'player_y'))
 invoke(v,'controls_check_pickup')
 assert g(v,'tank_mode')==1 and g(v,'armor')==4
 for n in range(4):
  assert g(v,'tank_mode')==1,n
  st(v,'invuln',0);invoke(v,'damage_player',limit=4000000)
 assert g(v,'tank_mode')==0 and g(v,'armor')==0
 v=boot();st(v,'tank_mode',1);st(v,'armor',2);invoke(v,'draw_hud');invoke(v,'present_dirty')
 assert [v.m[0x5800+22*32+c] for c in range(26,30)]==[0x46,0x46,0x42,0x42]
 print('PASS tanque de cuatro impactos con marcador de cuatro celdas, como PODER')

if __name__=='__main__':
 check_rations();check_ration_placement_and_pickup();check_tank_four_hits()
 print('ALL V1.4 TESTS PASSED (interprete parcial, no Fuse)')
