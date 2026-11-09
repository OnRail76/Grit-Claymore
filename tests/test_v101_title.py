#!/usr/bin/env python3
"""Regresión V1.0.1: título intacto, controles visibles y SPACE arranca.
El intérprete Z80 es parcial (no equivale a una prueba real en Fuse).
"""
from pathlib import Path
import hashlib
from mini_z80 import VM, SYM, ROOT
from harness import boot

scr=(ROOT/'assets/TITULO_ESPECTRUM_V07.scr').read_bytes()
assert len(scr)==6912

def off(y,bx):
    return ((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)+bx

# SHA256 de las primeras 184 líneas de píxeles y las primeras 23 filas de
# atributos de la versión 1.0 publicada, calculado antes de cambiar el título.
# Asegura que la ilustración Y=0..183 y créditos permanecen byte a byte igual.
art=bytes(scr[off(y,bx)] for y in range(184) for bx in range(32))
assert hashlib.sha256(art).hexdigest()==('bffc3416e7fbb623c1d0bc200c524c60'
                                      'f215cd9197a6ba10d3aa3b52749e836c')
assert hashlib.sha256(scr[6144:6144+23*32]).hexdigest()==('be65cc4f35e9d3da'
                                      'a90c3d0322d21e4f357b144a2aebcb52ea393d6f4a7b460b')
assert scr[6144+23*32:]==bytes([0x47])*32
assert any(scr[off(y,bx)] for y in range(184,191) for bx in range(32))
assert all(scr[off(191,bx)]==0 for bx in range(32))

# La CPU real del TAP interpreta la imagen RLE desde ROM y la vuelca en VRAM.
vm=VM();vm.run_to(lambda v:v.pc==SYM['sr_wait'],steps=500000)
assert vm.m[0x4000:0x5b00]==scr
assert vm.pc==SYM['sr_wait']

# SPACE sigue permitiendo pasar de título a juego; la mecánica no cambia.
start=boot()
assert start.pc==SYM['main_loop']
assert start.val('lives')==3 and start.val('health')==4

print('PASS V1.0.1: arte original 184 líneas y 23 filas de atributos idénticos a V1.0')
print('PASS V1.0.1: texto únicamente en última fila negra, blanco BRIGHT')
print('PASS V1.0.1: Z80 descomprime la pantalla y SPACE inicia la partida')
