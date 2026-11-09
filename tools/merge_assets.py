#!/usr/bin/env python3
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'src/grit_template.asm').read_text()
assert s.count(';%%GENERATED_ASSETS%%')==1
assets=(R/'src/sprites_generated.asm').read_text()
assets+='\nmap_pointers:\n dw map_p1_s1,map_p1_s2,map_p1_s3,map_p1_s4\n dw map_p2_s1,map_p2_s2,map_p2_s3,map_p2_s4\n dw map_p3_s1,map_p3_s2,map_p3_s3,map_p3_s4\n'
assets+=(R/'src/solid_generated.asm').read_text()
assets+=(R/'src/title_generated.asm').read_text()
assets+=(R/'src/font_generated.asm').read_text()
assets+=(R/'src/hud_generated.asm').read_text()
assets+=(R/'src/maps_generated.asm').read_text()
assets+=(R/'src/tile_animation_generated.asm').read_text()
assets+=(R/'src/gameover_generated.asm').read_text()
assets+=(R/'src/victory_generated.asm').read_text()
(R/'src/grit.asm').write_text(s.replace(';%%GENERATED_ASSETS%%',assets))
print('Merged 256 graphics and solid map',len(assets))
