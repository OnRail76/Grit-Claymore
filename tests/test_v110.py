#!/usr/bin/env python3
"""Regresiones de la V1.1 sobre el Z80 ensamblado (interprete parcial, no Fuse)."""
import math,random
from harness import boot,invoke,tick
from mini_z80 import VM,SYM as S
import tstates
F=69888
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
def score(v):return int(''.join(str(d) for d in v.m[S['score']:S['score']+6]))
def solid(v,d,e):return v.m[S['solid_flags']+v.m[S['map_data']+d*32+e]]
def clear_enemies(v):
 for i in range(36):v.m[S['enemies']+i]=0
 for i in range(30):v.m[S['special_shots']+i]=0

def check_boss_no_safe_zone():
 for ph in (1,2,3):
  v=boot();st(v,'phase',ph);st(v,'sector',4);invoke(v,'scene_init')
  hp=g(v,'boss_hp')
  for i in range(80):
   tick(v,{'Q'})
   if g(v,'state'):break
   st(v,'health',4);st(v,'lives',3);st(v,'invuln',0)
  assert g(v,'player_y')==9,('Grit sube por encima de la fila 9',ph,g(v,'player_y'))
  # Desde la fila 9, mirando arriba, las balas siguen llegando al jefe.
  for i in range(400):
   tick(v,{'SPACE'});st(v,'health',4);st(v,'lives',3)
   if g(v,'boss_hp')<hp or g(v,'phase')!=ph:break
  assert g(v,'boss_hp')<hp or g(v,'phase')!=ph,('el jefe no recibe impactos desde la fila 9',ph)
 print('PASS jefes: sin zona segura (fila minima 9) y siguen siendo alcanzables')

def check_score():
 v=boot();clear_enemies(v)
 assert score(v)==0
 v.r[7]=1;invoke(v,'add_score');assert score(v)==100
 v.r[7]=99;invoke(v,'add_score');assert score(v)==10000,score(v)
 # baja 100 con el tanque: antes se pintaba un caracter invalido
 st(v,'tank_mode',1);st(v,'armor',2)
 b=S['enemies'];v.m[b]=1;v.m[b+1]=g(v,'player_x');v.m[b+2]=g(v,'player_y')
 invoke(v,'handle_collisions');assert score(v)==10100 and all(d<10 for d in v.m[S['score']:S['score']+6])
 # vida extra al cruzar 10.000 solo si faltan vidas
 v=boot();st(v,'lives',2);v.r[7]=100;invoke(v,'add_score');assert g(v,'lives')==3
 v.r[7]=100;invoke(v,'add_score');assert g(v,'lives')==3 and score(v)==20000
 # el jefe puntua
 v=boot();st(v,'phase',1);st(v,'sector',4);invoke(v,'scene_init');s0=score(v)
 st(v,'boss_hp',1);st(v,'bullet_on',1);st(v,'bullet_x',g(v,'boss_x')+1);st(v,'bullet_y',6);st(v,'bullet_dir',0);st(v,'bullet_power',0)
 invoke(v,'update_player_bullet',limit=4000000)
 assert score(v)==s0+2000 and g(v,'phase')==2,(score(v),g(v,'phase'))
 # record de sesion
 v=boot();v.r[7]=37;invoke(v,'add_score');invoke(v,'update_hiscore')
 assert bytes(v.m[S['hiscore']:S['hiscore']+6])==bytes(v.m[S['score']:S['score']+6])
 for i in range(6):v.m[S['score']+i]=0
 invoke(v,'update_hiscore');assert int(''.join(map(str,v.m[S['hiscore']:S['hiscore']+6])))==3700
 print('PASS marcador de 6 cifras, tope del tanque, vida extra, puntos de jefe y record')

def check_terrain_rules():
 v=boot();bad=tot=0
 for i in range(900):
  tick(v);st(v,'health',4);st(v,'lives',3)
  for k in range(3):
   b=S['enemies']+12*k
   if v.m[b]:
    tot+=1;x,y=v.m[b+1],v.m[b+2]
    bad+=any(solid(v,y+dy,x+dx) for dy in (0,1) for dx in (0,1))
 assert tot>500 and bad==0,(tot,bad)
 # bala enemiga contra muro y sobre agua
 for tile,alive in ((12,0),(4,1),(0,1)):
  v=boot();clear_enemies(v);st(v,'frame',0)
  b=S['enemies'];v.m[b+3]=1;v.m[b+4]=5;v.m[b+5]=8;v.m[b+7]=0
  v.m[S['map_data']+9*32+5]=tile
  v.ix=b;invoke(v,'move_hostile_bullet')
  assert v.m[b+3]==alive,('bala enemiga',tile,v.m[b+3])
 # bala propia: cruza el agua, no el muro
 for tile,alive in ((12,0),(4,1)):
  v=boot();clear_enemies(v);v.m[S['map_data']+10*32+11]=tile
  st(v,'bullet_on',1);st(v,'bullet_x',11);st(v,'bullet_y',11);st(v,'bullet_dir',0);st(v,'bullet_power',0)
  invoke(v,'update_player_bullet');assert g(v,'bullet_on')==alive,('bala propia',tile)
 print('PASS soldados solo pisan suelo (%d muestras); muros paran balas de ambos bandos; el agua no'%tot)

def check_two_bullets():
 v=boot();seen=0
 for i in range(12):
  tick(v,{'SPACE'});st(v,'health',4)
  n=(v.m[S['bullets']]!=0)+(v.m[S['bullets']+5]!=0);seen=max(seen,n)
 assert seen==2,seen
 assert v.shadow()==bytes(v.m[0x4000:0x5b00])
 for i in range(30):tick(v);st(v,'health',4)
 while g(v,'frame')&7:tick(v);st(v,'health',4)   # V1.3: ciclo de 8 bandas de animacion completo
 assert v.m[S['bullets']]==0 and v.m[S['bullets']+5]==0
 invoke(v,'erase_dynamic');a=v.shadow();invoke(v,'generate_map')
 pf=lambda s:bytes(s[i] for i in range(6912) if i%32<24)
 assert pf(a)==pf(v.shadow()),'restos de bala'
 print('PASS dos balas propias simultaneas, sin restos graficos')

def start(vm):
 pressed=False
 for i in range(900000):
  if vm.pc==S['sp_wait']:pressed=True
  vm.keys={'SPACE'} if pressed else set()
  if vm.pc==S['main_loop']:vm.keys=set();return vm
  vm.step()
 raise AssertionError('boot')

def check_inputs():
 v=boot();assert g(v,'kempston_ok')==0,'Kempston fantasma sin interfaz (0xFF)'
 for junk in (0xff,0x3f,0x03,0x20):
  k=VM();k.kempston=junk;k.pc=S['detect_kempston'];k.push(0xf010)
  k.run_to(lambda w:w.pc==0xf010,steps=20000);assert k.m[S['kempston_ok']]==0,hex(junk)
 # V1.3: Kempston solo si la partida se empieza con SU fuego.
 kb=VM();kb.kempston=0x00;start(kb);assert g(kb,'kempston_ok')==0,'SPACE en el titulo = teclado'
 x,y=g(kb,'player_x'),g(kb,'player_y');kb.kempston=0x01;tick(kb);tick(kb)
 assert g(kb,'player_x')==x,'en modo teclado el Kempston no se lee'
 k=VM();k.kempston=0x00
 for i in range(900000):
  if k.pc==S['sp_wait']:k.kempston=0x10
  if k.pc==S['main_loop']:break
  k.step()
 k.kempston=0x00;assert g(k,'kempston_ok')==1,'FUEGO del Kempston en el titulo = joystick'
 x,y=g(k,'player_x'),g(k,'player_y')
 k.kempston=0x01;tick(k);tick(k);assert g(k,'player_x')>x,'Kempston derecha'
 k.kempston=0x08;tick(k);tick(k);assert g(k,'player_y')<y,'Kempston arriba'
 k.kempston=0x10;tick(k);assert k.m[S['bullets']]==1,'Kempston fuego'
 k.kempston=0x00
 # Sinclair: 6 izda, 7 dcha, 8 abajo, 9 arriba, 0 fuego
 v=boot();clear_enemies(v);x,y=g(v,'player_x'),g(v,'player_y')
 tick(v,{'6'});tick(v);assert g(v,'player_x')==x-1
 tick(v,{'7'});tick(v);tick(v,{'7'});tick(v);assert g(v,'player_x')==x+1
 tick(v,{'9'});tick(v);assert g(v,'player_y')==y-1
 tick(v,{'8'});tick(v);assert g(v,'player_y')==y
 tick(v,{'9'});tick(v);tick(v,{'0'});assert v.m[S['bullets']]==1  # V1.2: hacia arriba (abajo sale en el mismo tick)
 # El titulo arranca tambien con el fuego del joystick
 t=VM();t.kempston=0
 for i in range(900000):
  if t.pc==S['sp_wait']:t.kempston=0x10
  if t.pc==S['main_loop']:break
  t.step()
 assert t.pc==S['main_loop']
 print('PASS Kempston solo si se empieza con su fuego (si no, teclado); Sinclair 6-7-8-9-0 siempre')

def check_pause():
 v=boot();f0=g(v,'frame')
 v.keys={'H'};v.step()
 for i in range(3000):v.step()
 assert S['cp_release']<=v.pc<S['present_frame'],hex(v.pc)
 v.keys=set()
 for i in range(3000):v.step()
 assert S['cp_press']<=v.pc<S['cp_release2'] and g(v,'frame')==f0,'la pausa no congela'
 v.keys={'H'}
 for i in range(300):v.step()
 v.keys=set()
 for i in range(400000):
  if g(v,'frame')!=f0:break
  v.step()
 assert g(v,'frame')==f0+1
 print('PASS pausa con H: congela la logica y reanuda con otra pulsacion')

def check_death_and_ration():
 v=boot();clear_enemies(v);st(v,'health',1);st(v,'lives',3);st(v,'invuln',0)
 invoke(v,'damage_player',limit=4000000)
 assert g(v,'lives')==2 and g(v,'health')==4 and g(v,'invuln')==50 and g(v,'state')==0
 st(v,'health',1);st(v,'lives',1);st(v,'invuln',0);invoke(v,'damage_player',limit=4000000)
 assert g(v,'state')==2
 hits=set()
 for seed in range(40):
  v=boot();v.m[S['rng16']]=(seed*7+1)&255;v.m[S['rng16']+1]=seed;st(v,'sector',2);invoke(v,'scene_init')  # V1.8: generador de 16 bits
  assert g(v,'ration_available')==1
  x=g(v,'ration_x');hits.add(x);assert 3<=x<=20 and not solid(v,13,x),('racion en solido',x)
 assert len(hits)>3,hits
 st(v,'health',1);st(v,'player_x',g(v,'ration_x')-1);st(v,'player_y',12)
 invoke(v,'check_ration');assert g(v,'health')==3 and g(v,'ration_available')==0
 print('PASS secuencia de muerte, game over y racion en columna variable (%d columnas vistas)'%len(hits))

def check_ring_scroll():
 v=boot()
 for i in range(60):
  tick(v,{'Q'});st(v,'health',4);st(v,'lives',3)
  assert v.shadow()==bytes(v.m[0x4000:0x5b00]),('pantalla != sombra',i)
 assert g(v,'sector')>=1
 v=boot()
 for i in range(30):tick(v,{'Q'})
 while g(v,'frame')&7:tick(v)   # V1.3: ciclo de animacion completo
 assert g(v,'shadow_top')!=0
 invoke(v,'erase_dynamic');a=v.shadow();invoke(v,'generate_map')
 pf=lambda s:bytes(s[i] for i in range(6912) if i%32<24)
 assert pf(a)==pf(v.shadow()),'el anillo no equivale a repintar el mapa'
 # el HUD se actualiza aunque el tick haya hecho scroll
 v=boot()
 st(v,'health',4);invoke(v,'draw_hud');invoke(v,'present_frame')
 before=bytes(v.m[0x5800+16*32+26:0x5800+16*32+30])
 st(v,'full_redraw',1);st(v,'health',1);invoke(v,'draw_hud');invoke(v,'present_frame')
 after=bytes(v.m[0x5800+16*32+26:0x5800+16*32+30])
 assert after!=before and g(v,'full_redraw')==0,'HUD perdido en tick de scroll'
 print('PASS scroll en anillo: pantalla = sombra en 60 ticks, igual que repintar; HUD intacto')

def check_ram_independence():
 def run(dirty):
  v=VM()
  if dirty:
   for a in list(range(0x4000,0x5c00))+list(range(S.get('tape_end',S['rle_block_end']),0x10000)):v.m[a]=0xaa
  start(v);rnd=random.Random(5)
  for i in range(150):tick(v,rnd.choice([(),{'Q'},{'O'},{'P'},{'SPACE'},{'Q','SPACE'}]))
  return bytes(v.m[0x4000:0x5b00]),[g(v,n) for n in ('player_x','player_y','camera_top','health','lives')]
 assert run(False)==run(True)
 print('PASS no depende de RAM a cero: buffers y sombra fuera de la cinta, mismo resultado con basura')

def check_budget():
 v=boot();idle=[tstates.tick(v) for _ in range(64)]
 assert max(idle)<2*F,max(idle)
 fire=[tstates.tick(v,{'SPACE'}) for _ in range(24)]
 assert max(fire)<2*F,('el disparo ya no congela el juego',max(fire))
 v=boot();sc=[]
 for i in range(60):
  c0=g(v,'camera_top');s0=g(v,'sector');t=tstates.tick(v,{'Q'})
  if c0!=g(v,'camera_top') and s0==g(v,'sector'):sc.append(t)
 assert len(sc)>15 and max(sc)<3.7*F,(len(sc),max(sc))
 print('PASS presupuesto estimado: reposo max %.0f kT (<2 fotogramas), scroll %.0f-%.0f kT (<4 fotogramas)'%(max(idle)/1000,min(sc)/1000,max(sc)/1000))

def check_soak():
 rnd=random.Random(11);keys=[(),{'Q'},{'A'},{'O'},{'P'},{'SPACE'},{'Q','O'},{'Q','P','SPACE'},{'A','SPACE'},{'Q','SPACE'}]
 n=0
 for ph in (1,2,3):
  for sec in (1,2,3,4):
   v=boot();st(v,'phase',ph);st(v,'sector',sec);invoke(v,'scene_init')
   k=()
   for i in range(260):
    if i%6==0:k=rnd.choice(keys)
    tick(v,k,limit=1500000);n+=1
    if g(v,'state'):break
    if i%40==0:st(v,'health',4)
    assert v.shadow()==bytes(v.m[0x4000:0x5b00]),(ph,sec,i)
    assert v.sp==0,hex(v.sp)
 print('PASS %d ticks aleatorios en las 12 pantallas: pila equilibrada y pantalla = sombra'%n)

def check_title_music():
 v=VM();v.run_to(lambda w:w.pc==S['sp_wait'],steps=600000)
 assert g(v,'music_on')==1
 w0=v.port_writes
 for i in range(400000):v.step()
 assert v.port_writes-w0>200,'la melodia no suena'
 v.keys={'SPACE'}
 for i in range(600000):
  if v.pc==S['main_loop']:break
  v.step()
 assert v.pc==S['main_loop'] and g(v,'music_on')==0
 print('PASS melodia en el titulo, se corta al pulsar fuego')

if __name__=='__main__':
 check_boss_no_safe_zone();check_score();check_terrain_rules();check_two_bullets();check_inputs()
 check_pause();check_death_and_ration();check_ring_scroll();check_ram_independence();check_budget()
 check_soak();check_title_music()
 print('ALL V1.1 TESTS PASSED (interprete parcial, no Fuse)')
