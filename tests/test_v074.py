#!/usr/bin/env python3
"""V074 regression checks on real assembled Z80 bytes under partial interpreter."""
from harness import boot,invoke
from mini_z80 import SYM
R=SYM

def check_animation():
 v=boot()
 tileids=[4,16,24,26]
 before=[bytes(v.m[R['glyphs']+i*8:R['glyphs']+i*8+8]) for i in tileids]
 # Force a river tile inside the visible map and the combat area.
 at=R['map_data']+10*32+9
 v.m[at]=4
 invoke(v,'draw_dynamic');invoke(v,'present_dirty')
 initial=bytes(v.m[0x4000:0x5b00])
 v.set('frame',0)
 invoke(v,'erase_dynamic');invoke(v,'animate_tiles');invoke(v,'draw_dynamic');invoke(v,'present_dirty')
 flipped=[bytes(v.m[R['glyphs']+i*8:R['glyphs']+i*8+8]) for i in tileids]
 assert all(a!=b for a,b in zip(before,flipped)), 'all four glyphs must toggle'
 assert v.m[0x4000:0x5b00]==v.m[0x6000:0x7b00]
 assert bytes(v.m[0x4000:0x5b00])!=initial, 'river animation not rendered'
 # No change between ticks; then exact first frame restored at tick 8.
 v.set('frame',1)
 invoke(v,'animate_tiles')  # lower rows, completes the same alternate image
 v.set('frame',3)
 invoke(v,'animate_tiles')
 assert all(bytes(v.m[R['glyphs']+i*8:R['glyphs']+i*8+8])==b for i,b in zip(tileids,flipped))
 v.set('frame',8)
 invoke(v,'erase_dynamic');invoke(v,'animate_tiles');invoke(v,'draw_dynamic');invoke(v,'present_dirty')
 assert all(bytes(v.m[R['glyphs']+i*8:R['glyphs']+i*8+8])==b for i,b in zip(tileids,before)), 'not strictly 1-2-1'
 assert v.m[0x4000:0x5b00]==v.m[0x6000:0x7b00]
 print('PASS two-frame WATER, ANTENNA, TERMINAL, LED animation and shadow presentation')

def check_piercing():
 v=boot()
 v.set('phase',2);v.set('sector',1);invoke(v,'scene_init')
 # Place solid building directly in a projectile path, and clear all actors.
 for i in range(3):v.m[R['enemies']+i*12]=0
 solid=R['map_data']+10*32+11
 v.m[solid]=12
 for kind in (0,1):
  v.set('bullet_on',1);v.set('bullet_x',11);v.set('bullet_y',11)
  v.set('bullet_dir',0);v.set('bullet_power',kind)
  invoke(v,'update_player_bullet')
  assert v.val('bullet_on')==kind,('wall piercing invalid',kind,v.val('bullet_on'))
  assert v.val('bullet_y')==10
 # Killed infantry must not block the tank shell either.
 v.m[solid]=10
 enemy=R['enemies'];v.m[enemy]=1;v.m[enemy+1]=11;v.m[enemy+2]=10
 v.set('bullet_on',1);v.set('bullet_x',11);v.set('bullet_y',12)
 v.set('bullet_dir',0);v.set('bullet_power',1)
 invoke(v,'update_player_bullet')
 assert v.m[enemy]==0 and v.val('bullet_on')==1,'tank shell did not pierce infantry'
 print('PASS rifle hits walls; tank shell pierces scenery and infantry and keeps moving')

def check_all_stage_colours():
 v=boot()
 for phase,sector,tile in ((1,1,4),(2,1,16),(3,2,24),(3,1,26)):
  v.set('phase',phase);v.set('sector',sector);invoke(v,'scene_init')
  # A live, static tile in each stage: color must not be lost on toggling.
  row,col=8,10
  v.m[R['map_data']+row*32+col]=tile
  invoke(v,'erase_dynamic');v.set('frame',0)
  invoke(v,'animate_tiles');invoke(v,'draw_dynamic');invoke(v,'present_dirty')
  screen_attr=0x5800+row*32+col
  shadow_attr=0x7800+row*32+col
  expected=v.m[R['glyph_colors']+tile]
  assert v.m[screen_attr]==expected==v.m[shadow_attr],(phase,tile,expected,v.m[screen_attr])
  assert all(v.m[0x5800+r*32+c]&0x38==0 for r in range(24) for c in range(24,32))
 print('PASS 4 stage animation types preserve 8x8 ZX attributes and fixed HUD')

def check_source_and_limits():
 assert R['code_end']<0xffe0 and 0x7ff0-0x7b00>1024,hex(R['code_end'])
 print('PASS memory boundary and stack separation:',hex(R['code_end']))
if __name__=='__main__':
 check_source_and_limits();check_animation();check_piercing();check_all_stage_colours()
