#!/usr/bin/env python3
"""Produce a real 48K ZX Spectrum TAP with auto-run BASIC and CODE at 32768."""
from pathlib import Path
import struct, sys, json
ROOT=Path(__file__).resolve().parent
BIN=ROOT/'build/grit.bin'
OUT=ROOT/'build/GRIT_CLAYMORE_V078_48K.tap'
SYM=json.loads((ROOT/'build/grit.sym.json').read_text())
def block(flag,payload):
 raw=bytes([flag])+payload
 checksum=0
 for v in raw:checksum^=v
 raw+=bytes([checksum])
 return struct.pack('<H',len(raw))+raw
def line(n,data):
 body=data+b'\r'
 return struct.pack('>H',n)+struct.pack('<H',len(body))+body
# ZX ROM tokens: CLEAR=FD, VAL=B0, LOAD=EF, CODE=AF, RANDOMIZE=F9, USR=C0.
bas=(line(10,b'\xfd \xb0 "32767"')+
     line(20,b'\xef "" \xaf')+
     line(30,b'\xf9 \xc0 \xb0 "32768"'))
code=BIN.read_bytes()
# V1.1: binario < 0xFFE0; buffers por debajo de la sombra (0xE000);
# RLE reubicado dentro de 0x5E00..0x7FFF; pila 0xFB00..0xFFFF.
assert 0x8000+len(code)<0xffe0
assert SYM['bss_end']<=0xe000,hex(SYM['bss_end'])
assert 0x5e00+SYM['rle_block_end']-SYM['rle_block']<=0x8000
header_bas=bytes([0])+b'GRIT V160 '+struct.pack('<HHH',len(bas),10,len(bas))
header_bin=bytes([3])+b'GRIT Z80  '+struct.pack('<HHH',len(code),0x8000,0x8000)
raw=block(0,header_bas)+block(255,bas)+block(0,header_bin)+block(255,code)
OUT.write_bytes(raw)
print(f'TAP: {OUT.name}, {len(raw)} bytes, program {len(bas)} bytes, machine code {len(code)} bytes')
