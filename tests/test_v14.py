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
   assert not solid(v,13,g(v,'ration_x')),(ph,sec,'racion en solido')
   total+=1
   assert g(v,'ration_mid')==(1 if ph==3 and sec<4 else 0),(ph,sec)
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
   extra+=1;assert g(v,'camera_top')<=12 and g(v,'ration_y')==3
   assert not solid(v,3,g(v,'ration_x'))
 assert extra==1,extra
 print('PASS una racion en cada uno de los 12 sectores y otra de refuerzo en la fase 3 (15 por partida)')

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
 check_rations();check_tank_four_hits()
 print('ALL V1.4 TESTS PASSED (interprete parcial, no Fuse)')
