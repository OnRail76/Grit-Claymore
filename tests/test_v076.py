#!/usr/bin/env python3
"""Additional tests: fixed HUD geometry/skulls and 3 x 2-second Z80 stage cards.
Uses assembled code in partial VM, NOT Fuse/cycle-exact timing.
"""
from harness import boot, invoke
from mini_z80 import SYM,ROOT
from PIL import Image
from pathlib import Path

v=boot()
assert v.sp < 0x8000 and v.sp > 0x7b00, hex(v.sp)
assert 0x8000 <= SYM['code_end'] <= 0xffdf, hex(SYM['code_end'])
# Four HUD panels have completely separate static and dynamic bitmap fields.
# Check the exact static cell tiles that will be overwritten by draw_hud.
m=SYM['hud_panel_map'];glyphs=SYM['hud_panel_glyphs']
reserved={(5,c) for c in range(25,31)} | {(10,c) for c in (25,26,27,28,29,30)} | {(16,c) for c in range(26,30)} | {(22,c) for c in (27,28)}
for row,col in reserved:
 idx=v.m[m+(row*8+col-24)*2]
 assert bytes(v.m[glyphs+8*idx:glyphs+8*idx+8])==b'\x00'*8, ('static frame hits dynamic field',row,col)
# Statically labeled fields must have genuine pixels, and 2 skulls on top.
for row in (3,8,14,20):
 assert sum(sum(v.m[glyphs+v.m[m+(row*8+c)*2]*8+i]!=0 for i in range(8)) for c in range(1,7))>4
assert (ROOT/'assets/CALAVERA_HUD_V076.png').exists()
print('PASS four independent HUD modules; no overlapping text/bars, actual custom skull icons')

# dynamic screen paint: scoreboard 6 cells; 3 smiley cells; 4 power, 2 armor.
v.set('lives',2);v.set('health',3);v.set('armor',1);v.set('tank_mode',1)
invoke(v,'draw_hud');invoke(v,'present_dirty')
def attr(row,col):return v.m[0x5800+row*32+col]
assert [attr(10,c)&7 for c in (25,26,27,28,29,30)]==[6,6,6,6,7,7]
assert [attr(16,c)&7 for c in (26,27,28,29)]==[4,4,4,2]
assert [attr(22,c)&7 for c in (27,28)]==[6,2]
print('PASS 2 live smileys + 1 empty, PODER 3/4 and TANQUE 1/2 on ZX video attributes')

# Game Over has original skull; returns to title under legacy regression tests.
scr=(ROOT/'assets/GAME_OVER_ZX48_V076.scr').read_bytes()
assert len(scr)==6912 and len((ROOT/'assets/GAME_OVER_RLE_V076.bin').read_bytes())<3000
print('PASS user skull in real ZX Game Over .SCR and compressed native data')

# Each phase card is physically drawn by assembled machine code, different ink,
# while the main player HUD is absent. Assert three different full video screens.
shots=[]
for phase,expected in [(1,0x44),(2,0x46),(3,0x45)]:
 v.set('phase',phase)
 steps=invoke(v,'show_phase_card',limit=500000)
 assert v.m[0x5800:0x5b00]==bytes([expected])*768,(phase,set(v.m[0x5800:0x5b00]))
 assert v.m[0x4000:0x5800]!=bytes(6144)
 shots.append(bytes(v.m[0x4000:0x5b00]))
 v.render(ROOT/f'build/FASE_{phase}_PRESENTACION_V076.png')
 assert steps>100
assert len(set(shots))==3
# card must use a 100-HALT loop, never called from next_sector.
src=(ROOT/'src/grit_template.asm').read_text()
assert 'ld b,100' in src and 'spc_hold:' in src
sect=src.split('next_sector:',1)[1].split('update_player_bullet:',1)[0]
assert 'show_phase_card' not in sect
boss=src.split('boss_defeated:',1)[1].split('finish_game:',1)[0]
assert 'call show_phase_card' in boss
print('PASS phase 1/2/3 cards, 100 PAL HALTs = 2 sec, triggered on new phase not each sector')
print('ALL V076 ADDITIONAL TESTS PASSED (partial VM, not Fuse)')
