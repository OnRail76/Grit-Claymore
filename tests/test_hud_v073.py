#!/usr/bin/env python3
"""Regression tests for actual HUD Z80 cells and energy changes (not Fuse hardware)."""
from harness import boot,invoke
from mini_z80 import SYM,ROOT
from PIL import Image

def get_glyph_cell(v,row,col):
    # Spectrum bitmap: interleaved, 8 byte planes for one character cell.
    return bytes(v.m[0x6000+(((row*8+y)&0xC0)<<5)+(((row*8+y)&7)<<8)+((((row*8+y)&0x38)<<2))+col] for y in range(8))

v=boot()
assert len((ROOT/'assets/TITULO_ESPECTRUM_V072.scr').read_bytes())==6912
assert 'hud_panel_map' in SYM and 'hud_panel_glyphs' in SYM
print('PASS native HUD ROM tile bank is included in assembled executable')
# All side columns preserve BLACK paper and different bright ink values.
for row in range(24):
 for col in range(24,32):
  attr=v.m[0x5800+row*32+col]
  assert attr&0x38==0 and attr&0x40, (row,col,attr)
print('PASS static HUD attributes are ZX-legal and not the former ASCII border')
# 4 HP full -> green four cells. 2 HP -> exactly 2 green, 2 red.
for hp,n_green in [(4,4),(2,2),(1,1),(0,0)]:
 v.set('health',hp);invoke(v,'draw_hud');invoke(v,'present_dirty')
 colors=[v.m[0x5800+16*32+x] for x in range(26,30)]
 assert colors.count(0x44)==n_green and colors.count(0x42)==4-n_green,(hp,colors)
print('PASS genuine 4-segment coloured PODER BAR responds to Z80 health state')
# Integrity of panel when 8px scroll is executed.
v.set('health',4);invoke(v,'draw_hud');invoke(v,'present_dirty')
snap=bytes(v.m[0x5800+r*32+c] for r in range(24) for c in range(24,32))
from harness import tick
v.set('move_cool',0);v.set('player_y',10)
tick(v,['Q'],limit=700000)
post=bytes(v.m[0x5800+r*32+c] for r in range(24) for c in range(24,32))
assert snap==post, 'scroll has overwritten HUD'
print('PASS scrolling remains isolated from the 64-pixel sidebar')
print('ALL HUD V0.7.3 TESTS PASSED (partial VM, not Fuse)')

# GAME OVER is actual native Z80 screen, 150 PAL HALTs, then TITLE via call.
from mini_z80 import VM
g=VM();g.pc=SYM['lose_screen'];g.sp=0x7ff0
for i in range(25000):
 if g.pc==SYM['lose_hold']:break
 g.step()
else:raise AssertionError('Game Over screen failed to initialise')
assert g.m[0x4000:0x5b00]==(ROOT/'assets/GAME_OVER_ZX48_V076.scr').read_bytes()
assert g.r[0]==150, g.r[0]
for i in range(50000):
 if g.pc==SYM['sr_wait']:break
 g.step()
else:raise AssertionError('After the three-second countdown, game did not reach title')
assert g.m[0x4000:0x5b00]==(ROOT/'assets/TITULO_ESPECTRUM_V072.scr').read_bytes()
print('PASS 150 HALT GAME OVER, then the illustrated title (not phase-one restart)')
