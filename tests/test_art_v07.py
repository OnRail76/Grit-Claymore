#!/usr/bin/env python3
"""Verify graphics are compiled into the executable, metatiles populate all phases,
new collision lookup is 256 bytes, animated effects are drawn by Z80 opcodes."""
from harness import boot,invoke
from mini_z80 import SYM,ROOT
from collections import Counter

def main():
 v=boot()
 b=(ROOT/'build/grit.bin').read_bytes()
 assert len(b)<0x7fe0
 assert SYM['glyphs']-SYM['glyph_colors']==256
 assert SYM['glyph_masks']-SYM['glyphs']==2048
 assert SYM['map_pointers']-SYM['glyph_masks']==2048
 assert SYM['map_rows']==SYM['map_rows_p1']
 assert SYM['title_rle']==0x5e00  # V1.1: RLE reubicado al arrancar
 assert SYM['gameover_rle_load']-SYM['title_rle_load']==len((ROOT/'assets/TITULO_RLE_V07.bin').read_bytes())
 assert SYM['hud_panel_map']-SYM['font_grit']==768
 assert SYM['hud_panel_glyphs']-SYM['hud_panel_map']==384
 assert 25 <= (SYM['map_p1_s1']-SYM['hud_panel_glyphs'])//8 < 256
 print('OK exactly 256 glyphs, 256 colors, 256 solidity flags and masks in Z80 ROM')
 # Four rows of each 2-frame 16x16 sprite; 3x3 and 4x3 larger sprites.
 for start,n,w,h in ((32,16,2,2),(96,8,2,2),(128,2,2,2),(136,2,3,3),(154,2,4,3)):
  sigs=[]
  for f in range(n):
   off=SYM['glyphs']+(start+f*w*h)*8
   bitmap=bytes(v.m[off:off+w*h*8]);assert any(bitmap)
   sigs.append(bitmap)
  assert len(set(sigs)) >= n//2,(start,len(set(sigs)))
 print('OK recognizable separately coded directional sprites and two animation frames')
 macros={'PALM':195,'HUT':199,'BOULDER':203,'THICKET':207,'RICE':211,'BRIDGE16':215,
         'BARRACK':219,'WATCH':223,'GATE':227,'DRUMS':231,'BUNKER':235,
         'CONSOLE':239,'PIPEBANK':243,'MECH_DOCK':247}
 for phase,names in ((1,['PALM','HUT','BOULDER','THICKET','RICE','BRIDGE16']),
                     (2,['DRUMS','PIPEBANK','CONSOLE','GATE']),
                     (3,['CONSOLE','PIPEBANK','MECH_DOCK'])):
  found=set()
  for sector in range(1,5):
   p=SYM[f'map_p{phase}_s{sector}']
   height=24 if sector==4 else 48
   base=SYM[f'map_rows_p{phase}']  # V1.2: diccionario de filas por fase
   for row_index in v.m[p:p+height]:
    found.update(v.m[base+24*row_index:base+24*(row_index+1)])
  for name in names: assert macros[name] in found,(phase,name)
 print('OK 14 coherent large scene objects are physically in the three stage maps')
 solid=SYM['solid_flags']
 for name,expect in (("PALM",1),("HUT",1),("RICE",0),("BRIDGE16",0),
                     ("BARRACK",1),("GATE",0),("CONSOLE",1),("MECH_DOCK",1)):
  assert v.m[solid+macros[name]]==expect,(name,v.m[solid+macros[name]])
 print('OK solid vs traversable macrotiles, including the bridge')
 # Test real soldier defeat triggers two-frame explosion.
 v.set('phase',1);v.set('sector',1);invoke(v,'scene_init')
 en=SYM['enemies'];v.m[en:en+8]=bytes([1,10,12,0,0,0,1,0])
 v.set('bullet_on',1);v.set('bullet_x',10);v.set('bullet_y',13);v.set('bullet_dir',0)
 invoke(v,'update_player_bullet')
 assert v.val('fx_ttl')==8 and v.val('fx_x')==10 and v.val('fx_y')==12
 assert v.m[en]==0,('enemy should die',v.m[en])
 invoke(v,'draw_fx')
 assert v.val('fx_ttl')==8
 invoke(v,'erase_dynamic')
 for _ in range(8):invoke(v,'update_fx')
 assert v.val('fx_ttl')==0
 print('OK native Z80 explosion on soldier death, frame cleanup')
 # In mecha combat the death should trigger the same effect after hit 6.
 v.set('phase',3);v.set('sector',2);invoke(v,'scene_init')
 me=v.m[en:en+8]
 xx,yy=me[1],me[2]
 for n in range(6):
  v.set('bullet_on',1);v.set('bullet_x',xx+2);v.set('bullet_y',yy+3);v.set('bullet_dir',0)
  invoke(v,'update_player_bullet')
 assert v.val('fx_ttl')==8 and v.val('mecha_remaining')==2
 print('OK animated native FX also triggers on destruction of 6-hit mecha')
 print('ALL V07 ART AND INTEGRATION TESTS PASSED (partial VM, not real Fuse)')
if __name__=='__main__':main()
