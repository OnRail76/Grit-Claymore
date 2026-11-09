#!/usr/bin/env python3
"""Explicit tests for v0.7.7 changes, on assembled machine instructions (partial VM)."""
from harness import boot,invoke
from mini_z80 import SYM,VM,ROOT

v=VM();v.sp=0x7ff0;v.pc=SYM['win_screen'];
for _ in range(300000):
 if v.pc==SYM['sr_wait']:break
 v.step()
else:raise AssertionError('win_screen never displayed its illustration')
assert v.m[0x4000:0x5b00]==(ROOT/'assets/VICTORIA_V077_48K.scr').read_bytes()
assert v.m[0x4000:0x5b00]!=bytes(6912)
print('PASS illustrated VICTORIA is actually displayed by assembled Z80')

src=(ROOT/'src/grit_template.asm').read_text()
assert 'update_cheat' not in src and 'cheat_invincible' not in src
assert 'cheat_state' not in src and 'cheat_previous' not in src
print('PASS invincibility cheat routines and mutable state completely removed')

v=boot();v.set('phase',1);v.set('sector',1);invoke(v,'scene_init')
v.set('tank_mode',1);v.set('armor',2);v.set('invuln',10)
X=v.val('player_x');Y=v.val('player_y');en=SYM['enemies']
for i in range(2):
 off=en+i*12
 v.m[off:off+12]=bytes((1,X+i,Y,0,0,0,0,0,0,0,0,0))
score=v.val('kills');invoke(v,'handle_collisions')
assert v.m[en]==0 and v.m[en+12]==0
assert v.val('armor')==2 and v.val('kills')==score+2
shot=SYM['special_shots']
v.set('invuln',0);v.m[shot:shot+5]=bytes((1,X,Y,0,0));invoke(v,'handle_collisions')
assert v.val('armor')==1
print('PASS tank runs over multiple infantry without losing armour, projectiles still hurt')

v.set('phase',3);v.set('sector',2);invoke(v,'scene_init')
assert v.val('tank_mode')==0 and v.val('tank_available')==0
assert v.val('ration_available')==1
assert v.val('mecha_remaining')==3
print('PASS phase 3 forbids tanks and offers a ration')

# Visual regression: check a mecha moving leaves NO image pixels behind.
v=boot();v.set('phase',3);v.set('sector',1);invoke(v,'scene_init')
en=SYM['enemies'];x=v.m[en+1];y=v.m[en+2]
assert 1<=x<=19 and 1<=y<=19
v.set('frame',0)
invoke(v,'erase_dynamic')
# Restoring background must exactly match a world without actors at their old positions.
# Snapshot a 3x3 region as tile-level shadow bytes and attrs; compare to background draw.
for yy in range(3):
 for xx in range(3):
  d=y+yy;e=x+xx
  # Compute static background tile by reading map_data and corresponding compiled glyph.
  tile=v.m[SYM['map_data']+d*32+e]
  src=SYM['glyphs']+8*tile
  for py in range(8):
   scan=(d*8+py)
   zoff=((scan&192)<<5)+((scan&7)<<8)+((scan&56)<<2)+e
   assert v.m[0x6000+zoff]==v.m[src+py],('mecha residue',d,e,py)
print('PASS first mecha restores its 24x24 background completely')
print('ALL V077 REGRESSIONS PASSED (partial VM, not Fuse)')

# Regression of the exact complaint: a 24x24 mech must never leave fragments
# behind after movement / restoration. Compare entire active shadow bitmap to
# terrain-only frame after every erase. No scrolling or animated tiles here.
v=boot();v.set('phase',3);v.set('sector',1);invoke(v,'scene_init')
invoke(v,'erase_dynamic')
terrain=bytes(v.m[0x6000:0x7800])
for i in range(28):
 assert bytes(v.m[0x6000:0x7800])==terrain,('stale mecha trail after erase',i)
 v.set('frame',i*4)
 invoke(v,'update_mechas')
 invoke(v,'draw_dynamic')
 invoke(v,'erase_dynamic')
print('PASS 28 animated three-tile mecha updates leave no residual bitmap artifacts')
