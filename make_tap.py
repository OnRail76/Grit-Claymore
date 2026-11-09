#!/usr/bin/env python3
"""Produce a real 48K ZX Spectrum TAP with auto-run BASIC and CODE at 32768."""
from pathlib import Path
import struct, sys
ROOT=Path(__file__).resolve().parent
BIN=ROOT/'build/grit.bin'
OUT=ROOT/'build/GRIT_CLAYMORE_V078_48K.tap'
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
assert 0x8000+len(code)<0xffe0 and 0x7ff0-0x7b00>1024
header_bas=bytes([0])+b'GRIT V078 '+struct.pack('<HHH',len(bas),10,len(bas))
header_bin=bytes([3])+b'GRIT Z80  '+struct.pack('<HHH',len(code),0x8000,0x8000)
raw=block(0,header_bas)+block(255,bas)+block(0,header_bin)+block(255,code)
OUT.write_bytes(raw)
print(f'TAP: {OUT.name}, {len(raw)} bytes, program {len(bas)} bytes, machine code {len(code)} bytes')
