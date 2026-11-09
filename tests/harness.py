#!/usr/bin/env python3
"""Reusable boot/invoke helpers for the partial Z80 instruction interpreter."""
from mini_z80 import VM,SYM,ROOT
import struct

def boot():
 v=VM();pressed=False
 for i in range(500000):
  if v.pc==SYM['sp_wait']:pressed=True
  v.keys={'SPACE'} if pressed else set()
  if v.pc==SYM['main_loop']:
   v.keys=set();return v
  v.step()
 raise AssertionError(f'boot hang {v.pc:04x}')
def invoke(v,fn,limit=1800000):
 v.push(0xf010);v.pc=SYM[fn]
 for n in range(limit):
  if v.pc==0xf010:
   v.pc=SYM['main_loop'];return n
  v.step()
 raise AssertionError(f'{fn} timeout at {v.pc:04x} after {limit} instructions')
def tick(v,keys=(),limit=400000):
 assert v.pc==SYM['main_loop'],hex(v.pc)
 v.keys=set(keys);v.step()
 for n in range(limit):
  if v.pc in (SYM['main_loop'],SYM['handle_end']):return n
  v.step()
 raise AssertionError(f'frame timeout at pc={v.pc:04x} after {limit}')
def assert_panel_preserved(v,before):
 for row in range(24):
  for x in range(24,32):
   addr=0x5800+row*32+x
   assert v.m[addr]==before[addr],('HUD attribute corrupted',row,x)

