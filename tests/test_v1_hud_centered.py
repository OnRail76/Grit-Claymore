"""Exact pixel-level symmetry of VIDAS in the compiled Z80 screen, not a mock-up.
Run from project root: python3 tests/test_v1_hud_centered.py
"""
from harness import boot,invoke
from mini_z80 import ROOT
v=boot()
v.set('lives',3)
invoke(v,'draw_hud')
invoke(v,'present_dirty')
xs=[]
for row_in_tile in range(8):
    y=10*8+row_in_tile
    row_start=0x4000+((y&0xc0)<<5)+((y&7)<<8)+((y&0x38)<<2)
    for x in range(8,56):
        # HUD local X=0..63, screen starts at x=192, bytes 24..31.
        absolute_x=192+x
        byt=v.m[row_start+absolute_x//8]
        if byt & (128>>(absolute_x%8)):
            xs.append(x)
assert xs, 'VIDAS has no visible pixels'
assert min(xs)==12 and max(xs)==51, (min(xs),max(xs))
assert (min(xs)+max(xs))/2==31.5, 'VIDAS group not centered at the HUD midpoint'
assert all(v.m[0x5800+10*32+c] == 0x46 for c in range(25,31))
print('PASS VIDAS centered to exact x=31.5 midpoint of 64px sidebar; 3 smileys within 48px')
# Ensure other indicators are unaffected by the precise offset.
assert [v.m[0x5800+16*32+c] for c in range(26,30)]==[0x44]*4
assert [v.m[0x5800+22*32+c] for c in range(27,29)]==[0x42]*2
print('PASS PODER and TANQUE indicators unchanged')
