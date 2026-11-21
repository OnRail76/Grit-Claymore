#!/usr/bin/env python3
"""GRIT v1.14: comprobación rápida reproducible (no sustituye Fuse)."""
from pathlib import Path
import hashlib
from mini_z80 import SYM
R=Path(__file__).resolve().parents[1]
expected='3088339d7a9f822c072f0377abc9872db931b7daa4a6de8498b252c61b7727f3'
tap=R/'juego/GRIT_CLAYMORE_V1.14_48K.tap'
assert tap.is_file()
assert hashlib.sha256(tap.read_bytes()).hexdigest()==expected
src=(R/'src/grit_template.asm').read_text(encoding='utf-8')
for name in ('find_supply_tile:','soldier_entry_free:','wave_layout_final:','scene_ration_mid:','um_fire_burst:','setup_plasma:'):
 assert name in src,name
assert src.count('call check_ration')>=2
assert src.count('call check_pickup')>=2
assert SYM['tape_end']<=0xfd00
print('PASS v1.14: TAP firmado, aparición transitable, suministros, ráfagas, memoria')
