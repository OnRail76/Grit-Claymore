#!/usr/bin/env python3
"""Executable Z80 logic checks. Partial interpreter, NOT cycle exact or Fuse."""
from harness import boot,invoke,tick
from mini_z80 import VM,SYM,ROOT
from pathlib import Path
import struct
R=ROOT
EN=SYM['enemies'];SP=SYM['special_shots']
def slots(v,n=6):return [tuple(v.m[SP+i*5:SP+i*5+5]) for i in range(n)]
def both(v):
 assert v.shadow()==bytes(v.m[0x4000:0x5b00]), 'shadow/display mismatch after presentation'
def main():
 tap=(R/'build/GRIT_CLAYMORE_V078_48K.tap').read_bytes()
 i=0;blocks=[]
 while i<len(tap):
  k=struct.unpack_from('<H',tap,i)[0];i+=2
  block=tap[i:i+k];i+=k
  assert len(block)==k and not __import__('functools').reduce(lambda a,b:a^b,block,0)
  blocks.append(block)
 assert i==len(tap) and len(blocks)==4 and blocks[-1][1:-1]==(R/'build/grit.bin').read_bytes()
 assert SYM['code_end']<0xffe0 and SYM['bss_end']<=0xe000  # V1.1: sombra 0xE000, pila 0xFB00+
 print('PASS TAP blocks, checksums, code end and stack safety margin')
 vt=VM();vt.run_to(lambda v:v.pc==SYM['sr_wait'],steps=500000)
 assert vt.m[0x4000:0x5b00]==(R/'assets/TITULO_ESPECTRUM_V07.scr').read_bytes()
 print('PASS original illustrated title decoded by real assembled Z80 bytes')
 v=boot();both(v)
 assert v.val('health')==4 and v.val('lives')==3
 for keys in [['Q','P'],[],['O'],['P']]:
  tick(v,keys,limit=400000);both(v)
 print('PASS shadow RAM is identical to displayed video after every assembled tick')
 # Whole previous display stays intact between erasing and redrawing objects.
 snap=bytes(v.m[0x4000:0x5b00])
 invoke(v,'erase_dynamic')
 assert bytes(v.m[0x4000:0x5b00])==snap, 'flicker: sprites erased on visible screen'
 invoke(v,'draw_dynamic');invoke(v,'present_dirty');both(v)
 print('PASS offscreen erasure does not blank visible sprites')
 # Three distinct floor colours and custom font, explicit no objective/kills HUD fields.
 clr=SYM['glyph_colors'];assert [v.m[clr+i] for i in (0,10,20)]==[6,3,1]  # V1.2: tierra, baldosa magenta, placa azul
 src=(R/'src/grit_template.asm').read_text()
 assert 'hud_panel_map' in src and 'hud_panel_glyphs' in (R/'src/hud_generated.asm').read_text()
 assert 'OBJETIVO' not in src and 'BAJAS' not in src
 assert v.m[SYM['font_grit']:SYM['font_grit']+768] != bytes(768)
 print('PASS 3 floor ink palettes, pixel-art HUD and independent bitmap font')
 # Stage 3 mecha staggering, autonomous lateral movement and independent volleys.
 v.set('phase',3);v.set('sector',2);invoke(v,'scene_init')
 enemies=[tuple(v.m[EN+i*12:EN+i*12+12]) for i in range(3)]
 assert [e[2] for e in enemies]==[4,8,12]
 assert v.val('mecha_remaining')==3 and all(e[0]==2 for e in enemies)  # V1.3: tipo 2 = mecha
 assert all(e[6]==6 for e in enemies)
 for f in range(80):
  v.set('frame',f)
  invoke(v,'update_mechas');invoke(v,'update_special_shots')
 moved=[tuple(v.m[EN+i*12:EN+i*12+12]) for i in range(3)]
 assert any(a[1]!=b[1] for a,b in zip(enemies,moved))
 assert any(x[0] for x in slots(v)), 'mechas did not fire independently'
 print('PASS 3 staggered 6-hit mechas, autonomous movement and projectiles')
 # Eliminate middle mecha: survivors must keep moving and shooting.
 v.m[EN+12]=0;v.set('mecha_remaining',2)
 old_left,old_right=v.m[EN+1],v.m[EN+25]
 for f in range(80,110):
  v.set('frame',f);invoke(v,'update_mechas');invoke(v,'update_special_shots')
 assert v.val('mecha_remaining')==2
 assert (v.m[EN+1],v.m[EN+25])!=(old_left,old_right),'survivors are static after killing middle'
 # Phase 3 group sizes must be precisely 2, 3, 3: no fourth ghost slot.
 for sec,n in ((1,2),(2,3),(3,3)):
  v.set('phase',3);v.set('sector',sec);invoke(v,'scene_init')
  assert v.val('mecha_remaining')==n
  assert sum(v.m[EN+i*12]!=0 for i in range(3))==n
 print('PASS mecha survivors remain aggressive; each wave is exactly 2/3/3')
 # In phase 3 boss must shoot and bullets advance in all three directions.
 for phase,n in ((1,1),(2,2),(3,3)):
  v.set('phase',phase);v.set('sector',4);invoke(v,'scene_init')
  v.set('frame',0);invoke(v,'update_hind')
  shots=slots(v)
  assert sum(bool(x[0]) for x in shots)==n,(phase,shots)
  old=[x for x in shots if x[0]]
  v.set('frame',2);invoke(v,'update_special_shots')
  new=[x for x in slots(v) if x[0]]
  assert all(y[2]==x[2]+1 for x,y in zip(old,new)),(phase,old,new)
  if phase==3:assert sorted(y[1]-x[1] for x,y in zip(old,new))==[-1,0,1]
 print('PASS Hind now fires moving 1/2/3-shot spreads in phases 1/2/3')
 # Moving down the camera also must leave the complete fixed HUD unchanged.
 v.set('phase',1);v.set('sector',1);invoke(v,'scene_init')
 old=[v.m[0x5800+y*32+x] for y in range(24) for x in range(24,32)]
 v.set('player_y',10);v.set('player_x',11);v.set('move_cool',0)
 tick(v,['Q'],limit=600000);both(v)
 new=[v.m[0x5800+y*32+x] for y in range(24) for x in range(24,32)]
 assert old==new and v.val('camera_top')==23
 print('PASS scroll preserves the 64px right HUD and shadow consistency')
 print('ALL V07 FUNCTIONAL TESTS PASSED (not hardware/timing certification)')
if __name__=='__main__':main()
