#!/usr/bin/env python3
"""Regresiones de la V1.6: Grit no queda atrapado en el escenario y el arma
especial se dispara hasta agotarse (interprete parcial, no Fuse)."""
import random
from collections import deque
from harness import boot,invoke,tick
from mini_z80 import SYM as S
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
def solid(v,d,e):return v.m[S['solid_flags']+v.m[S['map_data']+d*32+e]]

def check_scroll_never_buries_grit():
 bad=0;n=0
 for ph in (1,2,3):
  for sec in (1,2,3):
   for seed in range(2):
    v=boot();st(v,'phase',ph);st(v,'sector',sec);invoke(v,'scene_init');rnd=random.Random(seed*31+ph*7+sec);k=set()
    for i in range(220):
     if i%4==0:k=rnd.choice([{'Q'},{'Q','O'},{'Q','P'},{'O'},{'P'},{'Q'}])
     tick(v,k);st(v,'health',4);st(v,'lives',3);st(v,'invuln',10)
     if ph==3 and g(v,'mecha_remaining'):
      for kk in range(3):
       b=S['enemies']+12*kk
       if v.m[b]==2:v.r[2]=v.m[b+2];v.r[3]=v.m[b+1];invoke(v,'restore_nine');v.m[b]=0
      st(v,'mecha_remaining',0)
     if g(v,'sector')!=sec:break
     x,y=g(v,'player_x'),g(v,'player_y');n+=1
     bad+=any(solid(v,y+dy,x+dx) for dy in (0,1) for dx in (0,1))
 assert bad==0,bad
 # caso dirigido: arbusto justo encima de Grit en la fila de scroll
 v=boot();st(v,'player_x',11);st(v,'player_y',10)
 v.m[S['map_data']+9*32+11]=9   # BUSH solido en la fila que bajaria sobre Grit
 c0=g(v,'camera_top');tick(v,{'Q'})
 assert g(v,'camera_top')==c0 and not solid(v,10,11),'el scroll no debe enterrar a Grit'
 print('PASS el scroll nunca mete terreno solido encima de Grit (%d ticks en 9 sectores)'%n)

def check_maps_have_no_traps():
 m=boot().m
 D=[(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
 for ph in (1,2,3):
  for sec in (1,2,3,4):
   p=S[f'map_p{ph}_s{sec}'];h=24 if sec==4 else 48;base=S[f'map_rows_p{ph}']
   M=[[m[base+24*m[p+r]+c] for c in range(24)] for r in range(h)]
   free=lambda r,c:0<=r and r+1<h and 1<=c<=21 and not any(m[S['solid_flags']+M[r+a][c+b]] for a in (0,1) for b in (0,1))
   def bfs(starts,maxrow=99):
    seen=set(starts);q=deque(starts)
    while q:
     r,c=q.popleft()
     for a,b in D:
      nn=(r+a,c+b)
      if nn not in seen and nn[0]<=maxrow and free(*nn):seen.add(nn);q.append(nn)
    return seen
   start=(h-4,11);assert free(*start),('inicio en solido',ph,sec)
   if sec==4:continue
   R=bfs([start])
   for pos in R:
    assert any(q[0]<=2 for q in bfs([pos],pos[0]+10)),('trampa',ph,sec,pos)
 print('PASS 12 mapas: salida libre y ninguna posicion alcanzable sin camino hacia arriba')

def check_plasma_until_empty():
 v=boot();st(v,'phase',3);st(v,'sector',1);invoke(v,'scene_init')
 for i in range(48):v.m[S['enemies']+i]=0
 st(v,'mecha_remaining',0);st(v,'plasma_ammo',12);st(v,'face',0)
 powers=[]
 for i in range(200):
  before=[v.m[S['bullets']+5*b] for b in (0,1)]
  tick(v,{'SPACE'});st(v,'health',4)
  for b in (0,1):
   if v.m[S['bullets']+5*b] and not before[b]:powers.append(v.m[S['bullets']+5*b+4])
  if len(powers)>=14:break
 assert powers[:12]==[2]*12 and powers[12:14]==[0,0],powers
 assert g(v,'plasma_ammo')==0
 # a toques: cada pulsacion gasta una carga
 v=boot();st(v,'phase',3);st(v,'sector',1);invoke(v,'scene_init');st(v,'plasma_ammo',3);st(v,'face',0)
 for i in range(3):
  tick(v,{'SPACE'});
  for j in range(6):tick(v)
 assert g(v,'plasma_ammo')==0
 print('PASS el arma especial dispara sola hasta agotarse (pulsado o a toques) y despues vuelve el fusil')

if __name__=='__main__':
 check_scroll_never_buries_grit();check_maps_have_no_traps();check_plasma_until_empty()
 print('ALL V1.6 TESTS PASSED (interprete parcial, no Fuse)')
