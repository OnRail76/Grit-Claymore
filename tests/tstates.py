#!/usr/bin/env python3
"""Estimador de T-states para el interprete parcial (V1.1).
Suma el coste nominal de cada instruccion Z80 ejecutada en un tick. NO modela
la contencion de memoria de la ULA ni la interrupcion de la ROM: sirve para
comparar versiones y vigilar presupuestos, no para certificar tiempos reales."""
from harness import boot
from mini_z80 import SYM as S
M=[4,10,7,6,4,4,7,4,4,11,7,6,4,4,7,4, 13,10,7,6,4,4,7,4,12,11,7,6,4,4,7,4,
   12,10,16,6,4,4,7,4,12,11,16,6,4,4,7,4, 12,10,13,6,11,11,10,4,12,11,13,6,4,4,7,4]
for o in range(0x40,0xc0): M.append(7 if (o&7)==6 or (0x70<=o<=0x77) else 4)
M+=[11,10,10,10,17,11,7,11,11,10,10,8,17,17,7,11, 11,10,10,11,17,11,7,11,11,4,10,11,17,0,7,11,
    11,10,10,19,17,11,7,11,11,4,10,4,17,0,7,11, 11,10,10,4,17,11,7,11,11,6,10,4,17,0,7,11]
assert len(M)==256
def cost(v):
    m=v.m;pc=v.pc;o=m[pc]
    if o==0x76:return 0
    if o in (0xdd,0xfd):
        p=m[pc+1]
        if p in (0x34,0x35):return 23
        if p==0x21:return 14
        if p==0xe5:return 15
        if p==0xe1:return 14
        if p in (0x23,0x2b):return 10
        if p in (0x09,0x19,0x29,0x39):return 15
        return 19
    if o==0xed:
        p=m[pc+1]
        if p in (0xb0,0xb8):
            bc=(v.r[0]<<8)|v.r[1] or 65536
            return 21*bc-5
        if p==0x78 or p==0x79:return 12
        if p==0xa0:return 16
        if p==0x44:return 8
        return 20
    if o==0xcb:return 8
    t=M[o]
    if o&0xc7==0xc0:  # ret cc
        t=11 if v.cond((o>>3)&7) else 5
    elif o&0xc7==0xc4:
        t=17 if v.cond((o>>3)&7) else 10
    elif o==0x10:
        t=13 if v.r[0]!=1 else 8
    return t
def tick(v,keys=(),limit=600000,prof=None):
    assert v.pc==S['main_loop']
    v.keys=set(keys);T=cost(v);v.step()
    for n in range(limit):
        if v.pc in (S['main_loop'],S['handle_end']):return T
        c=cost(v)
        if prof is not None:
            prof[v.pc]=prof.get(v.pc,0)+c
        T+=c;v.step()
    raise AssertionError
