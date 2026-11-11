#!/usr/bin/env python3
"""Regresiones de la V1.5: canon de plasma de la fase 3 (interprete parcial, no Fuse)."""
from harness import boot,invoke,tick
from mini_z80 import SYM as S
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
EN=S['enemies']
def solid(v,d,e):return v.m[S['solid_flags']+v.m[S['map_data']+d*32+e]]
def scr_attr(v,r,c):return v.m[0x5800+r*32+c]

def check_crates():
 for ph in (1,2,3):
  for sec in (1,2,3,4):
   v=boot();st(v,'phase',ph);st(v,'sector',sec);invoke(v,'scene_init')
   want=1 if ph==3 and sec in (1,3) else 0
   assert g(v,'pickup_on')==want,(ph,sec)
   if want:
    x,y=g(v,'pickup_x'),g(v,'pickup_y')
    assert y==15 and not any(solid(v,y+dy,x+dx) for dy in (0,1) for dx in (0,1)),(sec,x,y)
    invoke(v,'draw_dynamic');invoke(v,'present_frame')
    assert all(scr_attr(v,y+dy,x+dx)==0xc3 for dy in (0,1) for dx in (0,1)),'la caja parpadea (FLASH)'
 print('PASS dos cajas de plasma en la fase 3 (sectores 1 y 3), sobre suelo, con FLASH')

def check_pickup_and_fire():
 v=boot();st(v,'phase',3);st(v,'sector',1);invoke(v,'scene_init')
 # rotulo ARMA en la franja magenta, municion vacia
 assert all(scr_attr(v,20,c)==0x58 for c in range(25,31))
 st(v,'player_x',g(v,'pickup_x'));st(v,'player_y',g(v,'pickup_y'))
 invoke(v,'check_pickup');invoke(v,'present_frame')
 assert g(v,'plasma_ammo')==12 and g(v,'pickup_on')==0
 assert [scr_attr(v,22,c) for c in range(26,30)]==[0x43]*4
 # cada disparo gasta una carga y sale con potencia 2
 for i in range(48):v.m[EN+i]=0
 st(v,'player_y',18);st(v,'face',0);st(v,'cool',0)
 invoke(v,'controls_check_fire') if 'controls_check_fire' in S else None
 assert g(v,'plasma_ammo')==11 and v.m[S['bullets']+4]==2,(g(v,'plasma_ammo'),v.m[S['bullets']+4])
 # dos disparos de plasma derriban un mecha de seis impactos
 v=boot();st(v,'phase',3);st(v,'sector',2);invoke(v,'scene_init')
 x,y=v.m[EN+1],v.m[EN+2]
 for n in range(2):
  st(v,'bullet_on',1);st(v,'bullet_x',x+1);st(v,'bullet_y',y+3);st(v,'bullet_dir',0);st(v,'bullet_power',2)
  invoke(v,'update_player_bullet')
 assert v.m[EN]==0 and g(v,'mecha_remaining')==2,'el mecha no cae con dos disparos de plasma'
 # contra el Hind quita dos
 v=boot();st(v,'phase',3);st(v,'sector',4);invoke(v,'scene_init');hp=g(v,'boss_hp')
 st(v,'bullet_on',1);st(v,'bullet_x',g(v,'boss_x')+1);st(v,'bullet_y',6);st(v,'bullet_dir',0);st(v,'bullet_power',2)
 invoke(v,'update_player_bullet');assert g(v,'boss_hp')==hp-2
 # se pierde al perder una vida
 v=boot();st(v,'phase',3);st(v,'plasma_ammo',7);st(v,'health',1);st(v,'lives',3);st(v,'invuln',0)
 invoke(v,'damage_player',limit=4000000);assert g(v,'plasma_ammo')==0
 # fuera de la fase 3 el modulo sigue siendo TANQUE (franja intacta, celdas amarillas)
 v=boot();assert all(scr_attr(v,20,c)==0x58 for c in range(25,31))
 st(v,'tank_mode',1);st(v,'armor',4);invoke(v,'draw_hud');invoke(v,'present_dirty')
 assert [scr_attr(v,22,c) for c in range(26,30)]==[0x46]*4
 print('PASS plasma: 12 cargas, marcador ARMA magenta, mecha en dos disparos, Hind -2, se pierde al morir')

def check_play():
 # partida dirigida: recoger la caja y destruir el grupo con plasma
 v=boot();st(v,'phase',3);st(v,'sector',1);invoke(v,'scene_init')
 px,py=g(v,'pickup_x'),g(v,'pickup_y')
 for i in range(60):
  k=set()
  if g(v,'pickup_on'):
   if g(v,'player_x')<px:k.add('P')
   elif g(v,'player_x')>px:k.add('O')
   elif g(v,'player_y')>py:k.add('Q')
   elif g(v,'player_y')<py:k.add('A')
  tick(v,k);st(v,'health',4);st(v,'lives',3)
  if not g(v,'pickup_on'):break
 assert g(v,'plasma_ammo')==12,'no se pudo recoger la caja jugando'
 assert v.shadow()==bytes(v.m[0x4000:0x5b00])
 print('PASS la caja se recoge jugando y la pantalla queda limpia')

if __name__=='__main__':
 check_crates();check_pickup_and_fire();check_play()
 print('ALL V1.5 TESTS PASSED (interprete parcial, no Fuse)')
