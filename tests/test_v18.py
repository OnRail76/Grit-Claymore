#!/usr/bin/env python3
"""Regresiones de la V1.8 (interprete parcial, no Fuse): soldados.
- Generador xorshift de 16 bits: columnas variadas, sin rachas de la misma.
- Tres entradas: arriba, por un lado y emboscada por detras si Grit corre;
  siempre en suelo libre y nunca encima de Grit.
- El rojo (fijo) solo se queda donde ve 4 filas libres; ve a 12 columnas.
- Las balas hacia arriba van a una fila por tick y corrigen hacia Grit.
- Correr hasta el jefe de la fase 1 ya no sale gratis."""
import json
from pathlib import Path
from harness import boot,invoke,tick
from mini_z80 import VM,SYM as S
R=Path(__file__).resolve().parents[1]
E=S['enemies']
def g(v,n):return v.m[S[n]]
def st(v,n,x):v.m[S[n]]=x
def solid(v,d,e):return v.m[S['solid_flags']+v.m[S['map_data']+d*32+e]]
def clear(v):
 for i in range(48):v.m[E+i]=0

def check_memoria():
 assert 0x5e00+S['rle_block_end']-S['rle_block']<=S['rng16'],'las variables nuevas pisan las pantallas RLE'
 assert S['bss_end']<=0xe000
 src=(R/'src/solid_generated.asm').read_text().split('\n')[1:]
 table=[int(x) for l in src if l.strip() for x in l.replace('db','').split(',')]
 v=boot()
 assert list(v.m[0x5b00:0x5c00])==table,'tabla de colisiones en 0x5B00'
 print('PASS memoria: colisiones en 0x5B00, variables en 0x7FF0 sin pisar las pantallas RLE')

def spawns(v,n=200,meter=0,py=None):
 out=[]
 for i in range(n):
  clear(v);st(v,'run_meter',meter)
  if py is not None:st(v,'player_y',py)
  invoke(v,'spawn_soldier')
  if v.m[E]==1:out.append(tuple(v.m[E:E+12]))
 return out

def check_apariciones():
 v=boot();st(v,'phase',1);st(v,'sector',2);invoke(v,'scene_init')
 px,py=g(v,'player_x'),g(v,'player_y')
 s=spawns(v)
 assert len(s)>150
 top=[x for x in s if x[2]==4 and 4<=x[1]<=19];side=[x for x in s if x not in top]
 cols=[x[1] for x in top]
 assert len(set(cols))>=10,('columnas',sorted(set(cols)))
 runs=max(len(list(gr)) for k,gr in __import__('itertools').groupby(cols))
 assert runs<=3,('racha en la misma columna',runs)
 assert len(side)>=20,'tambien entran por los lados'
 for a,x,y,*_ in s:
  for dy in (0,1):
   for dx in (0,1):assert not solid(v,y+dy,x+dx),('soldado en solido',x,y)
  assert not (abs(x-px)<2 and abs(y-py)<2),'encima de Grit'
 roles={r:sum(1 for t in s if t[8]==r) for r in (0,1,2)}
 for t in s:
  if t[8]==0:
   assert all(not solid(v,t[2]+k,t[1]) for k in range(2,6)),('tirador sin vista',t[1],t[2])
 assert roles[0]>10 and roles[1]>10 and roles[2]>10,roles
 # Emboscada: con el medidor de carrera lleno salen por detras de Grit.
 py=8;st(v,'player_y',py)
 amb=spawns(v,120,meter=200,py=py)
 behind=[t for t in amb if t[2]>py]
 assert len(behind)>=40,('emboscadas por detras',len(behind))
 for t in behind:assert 3<=t[2]-py<=6 and not (abs(t[1]-g(v,'player_x'))<2),t
 print('PASS apariciones variadas (%d columnas, racha max %d), %d por los lados, %d emboscadas; roles %s; el rojo siempre con vista'%(len(set(cols)),runs,len(side),len(behind),roles))

def check_tirador_y_balas():
 v=boot();clear(v)
 px,py=g(v,'player_x'),g(v,'player_y')
 # tirador a 10 columnas y 6 filas por encima: dispara (antes no lo veia)
 x=px-10 if px>=11 else px+10
 v.m[E:E+12]=bytes([1,x,py-6,0,0,0,1,0,0,0,0,x])
 fired=False
 for i in range(40):
  tick(v);st(v,'health',4);st(v,'invuln',50)
  if v.m[E+3]:fired=True;break
 assert fired,'el tirador ve a 12 columnas'
 # bala hacia arriba: una fila por tick y corrige la columna hacia Grit
 v=boot();clear(v);px,py=g(v,'player_x'),g(v,'player_y')
 v.m[E:E+12]=bytes([1,px+4,py+3,1,px+4,py+2,0,4,2,99,0,px+4])
 ys=[];xs=[]
 for i in range(4):
  tick(v);st(v,'health',4);st(v,'invuln',50)
  if v.m[E+3]:ys.append(v.m[E+5]);xs.append(v.m[E+4])
 assert ys and all(a-b==1 for a,b in zip([py+2]+ys,ys)),('una fila por tick',ys)
 assert xs[-1]<px+4,('corrige hacia Grit',xs)
 print('PASS el tirador ve a 12 columnas; balas hacia arriba a 1 fila/tick que corrigen hacia Grit')

def check_correr():
 hits=[]
 for seed in (1,5,42):
  v=boot();v.m[S['rng16']]=seed;v.m[S['rng16']+1]=7
  hp=(g(v,'lives'),g(v,'health'));n=0
  for t in range(176):
   tick(v,{'Q'})
   cur=(g(v,'lives'),g(v,'health'))
   if cur<hp:n+=1
   hp=cur
   if g(v,'sector')==4:break
  hits.append(n)
 assert min(hits)>=3,('correr sin luchar sale casi gratis',hits)
 print('PASS correr hasta el jefe de la fase 1 sin luchar cuesta %s golpes (V1.7: 1-5)'%hits)

if __name__=='__main__':
 check_memoria();check_apariciones();check_tirador_y_balas();check_correr()
 print('ALL V1.8 TESTS PASSED (interprete parcial, no Fuse)')
