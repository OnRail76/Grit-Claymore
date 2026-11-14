#!/usr/bin/env python3
"""Regresion de la V1.7: la melodia del titulo suena UNA vez cada vez que se
llega al titulo y despues hay silencio hasta pulsar fuego (interprete parcial,
no Fuse)."""
from mini_z80 import VM,SYM as S
def g(v,n):return v.m[S[n]]

def play_until_silence(v):
 w0=v.port_writes
 for i in range(20_000_000):
  if not g(v,'music_on'):break
  v.step()
 assert not g(v,'music_on'),'la melodia no termina'
 return v.port_writes-w0

def check_title_tune_once():
 v=VM();v.run_to(lambda w:w.pc==S['sp_wait'],steps=600000)
 assert g(v,'music_on')==1
 n=play_until_silence(v)
 assert n>200,('la melodia no suena',n)
 w=v.port_writes
 for i in range(2_000_000):v.step()
 assert v.port_writes==w,'despues de la melodia el titulo queda en silencio'
 assert g(v,'music_on')==0
 # sigue esperando el fuego, y con fuego empieza la partida
 v.keys={'SPACE'}
 for i in range(600000):
  if v.pc==S['main_loop']:break
  v.step()
 assert v.pc==S['main_loop']
 # al volver al titulo (fin de partida) vuelve a sonar una vez
 v.keys=set();v.pc=S['title_screen']
 v.run_to(lambda w:w.pc==S['sp_wait'],steps=900000)
 assert g(v,'music_on')==1
 n2=play_until_silence(v)
 assert n2==n,(n,n2)
 print('PASS la melodia del titulo suena una vez (%d cambios del altavoz) y luego silencio; vuelve a sonar al volver al titulo'%n)

if __name__=='__main__':
 check_title_tune_once()
 print('ALL V1.7 TESTS PASSED (interprete parcial, no Fuse)')
