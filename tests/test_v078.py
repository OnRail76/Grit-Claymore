#!/usr/bin/env python3
"""V078 executable Z80 regressions: mandatory victory delay, no cheat, 8-way inputs.
Partial Z80 interpreter; do not use as evidence of Fuse timing/framerate.
"""
from mini_z80 import VM,SYM,ROOT
from harness import boot,invoke,tick

assert all(x not in SYM for x in ('cheat_invincible','update_cheat','cheat_state','cheat_previous','cheat_prev_space'))
print('PASS no invincibility cheat symbols remain')
# Force enter victory, including a held SPACE from the battle.
v=VM();v.sp=0;v.pc=SYM['win_screen'];v.keys={'SPACE'}
v.run_to(lambda v:v.pc==SYM['win_hold'],steps=200000)
assert v.m[0x4000:0x5b00]==(ROOT/'assets/VICTORIA_V078_48K.scr').read_bytes()
assert v.r[0]==150, v.r[0]
# 149 full HALT-DJNZ frames may not skip the picture.
for frame in range(149):
 assert v.pc==SYM['win_hold'],(frame,hex(v.pc))
 v.step();v.step()
assert v.pc==SYM['win_hold'] and v.r[0]==1,(hex(v.pc),v.r[0])
# The 150th HALT exits into space_release. With SPACE still held,
# it must not accept input and go to the title.
v.step();v.step()
assert v.pc!=SYM['title_screen']
for _ in range(20):v.step()
assert v.pc!=SYM['title_screen']
assert v.m[0x4000:0x5b00]==(ROOT/'assets/VICTORIA_V078_48K.scr').read_bytes()
# Releasing lets space_release return, but no new press yet.
v.keys=set()
v.run_to(lambda w:w.pc==SYM['sp_wait'],steps=100)
assert v.m[0x4000:0x5b00]==(ROOT/'assets/VICTORIA_V078_48K.scr').read_bytes()
v.keys={'SPACE'}
v.run_to(lambda w:w.pc==SYM['sr_wait'],steps=500000)
assert v.m[0x4000:0x5b00]==(ROOT/'assets/TITULO_ESPECTRUM_V072.scr').read_bytes()
print('PASS victory 150 mandatory PAL HALTs, held SPACE ignored, release + new press to TITLE')
# No movement animating when idle, eight directions for player.
for keys,dx,dy in [({'Q'},0,-1),({'A'},0,1),({'O'},-1,0),({'P'},1,0),
                   ({'Q','O'},-1,-1),({'Q','P'},1,-1),({'A','O'},-1,1),({'A','P'},1,1)]:
 c=boot();c.set('tank_mode',0);c.set('phase',1);c.set('sector',1)
 c.set('player_x',11);c.set('player_y',15);c.set('move_cool',0)
 # Clear 2x2 traversable area for this controlled input test.
 for yy in range(11,20):
  for xx in range(7,17):c.m[SYM['map_data']+yy*32+xx]=0
 c.keys=set(keys);invoke(c,'read_controls')
 assert (c.val('player_x'),c.val('player_y'))==(11+dx,15+dy),(keys,c.val('player_x'),c.val('player_y'))
 assert c.val('player_moving')==1
 c.keys=set();c.set('move_cool',0);invoke(c,'read_controls')
 assert c.val('player_moving')==0,('idle anim error',keys)
print('PASS Grit all 8 movement directions and stationary animation state')
# Diagonal controls in tank must resolve to exactly one cardinal axis.
for keys,dx,dy in [({'Q','O'},0,-1),({'A','P'},0,1),({'O'},-1,0),({'P'},1,0)]:
 c=boot();c.set('tank_mode',1);c.set('armor',2)
 c.set('player_x',11);c.set('player_y',15);c.set('move_cool',0)
 for yy in range(11,20):
  for xx in range(7,17):c.m[SYM['map_data']+yy*32+xx]=0
 c.keys=set(keys);invoke(c,'read_controls')
 assert (c.val('player_x'),c.val('player_y'))==(11+dx,15+dy),(keys,c.val('player_x'),c.val('player_y'))
print('PASS tank controls stay cardinal when simultaneous keys are pressed')
print('ALL V078 EXTRA TESTS PASSED (partial VM, not Fuse)')
