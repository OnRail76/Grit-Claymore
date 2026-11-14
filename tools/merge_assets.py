#!/usr/bin/env python3
"""Une la plantilla con los recursos generados.
V1.1: las tres pantallas RLE (titulo, game over, victoria) van AL FINAL del
binario. Al arrancar se copian a 0x5E00 y su hueco queda para los buffers
(map_data, dirty_*) y la pantalla sombra, que ya no viajan en la cinta."""
from pathlib import Path
R=Path(__file__).resolve().parents[1]
s=(R/'src/grit_template.asm').read_text()
assert s.count(';%%GENERATED_ASSETS%%')==1 and s.count(';%%RLE_ASSETS%%')==1
spr=(R/'src/sprites_generated.asm').read_text()
# V1.9: los colores de los 256 graficos tambien viajan al final y se bajan a
# 0x5D00 (zona del cargador BASIC, libre en cuanto arranca el juego).
_i=spr.index('glyphs:')
colors=spr[:_i];assets=spr[_i:]
assert colors.startswith('glyph_colors:')
assets+='\nmap_pointers:\n dw map_p1_s1,map_p1_s2,map_p1_s3,map_p1_s4\n dw map_p2_s1,map_p2_s2,map_p2_s3,map_p2_s4\n dw map_p3_s1,map_p3_s2,map_p3_s3,map_p3_s4\n'
assets+=(R/'src/font_generated.asm').read_text()
assets+=(R/'src/hud_generated.asm').read_text()
assets+=(R/'src/maps_generated.asm').read_text()
assets+=(R/'src/tile_animation_generated.asm').read_text()
assets+=(R/'src/boss_generated.asm').read_text()
rle='rle_block:\n'
for name in ('title','gameover','victory'):
 t=(R/f'src/{name}_generated.asm').read_text()
 assert t.count(f'{name}_rle:')==1
 rle+=t.replace(f'{name}_rle:',f'{name}_rle_load:')
rle+='rle_block_end:\n'
# V1.8: la tabla de colisiones (256 bytes) tambien viaja al final y se baja a
# 0x5B00 (bufer de impresora, libre en el 48K): deja sitio al codigo nuevo.
rle+=(R/'src/solid_generated.asm').read_text().replace('solid_flags:','solid_flags_load:')
rle+=colors.replace('glyph_colors:','glyph_colors_load:')
rle+='tape_end:\nsolid_flags: equ 0x5b00\nglyph_colors: equ 0x5d00\n'
for name in ('title','gameover','victory'):
 rle+=f'{name}_rle: equ 0x5e00+{name}_rle_load-rle_block\n'
rle+='bss_base: equ (rle_block+255)&0xff00\n'
rle+='map_data: equ bss_base\n'
rle+='dirty_flags: equ bss_base+0x300\n'
rle+='dirty_pairs: equ bss_base+0x600\n'
rle+='bss_end: equ bss_base+0x800\n'
(R/'src/grit.asm').write_text(s.replace(';%%GENERATED_ASSETS%%',assets).replace(';%%RLE_ASSETS%%',rle))
print('Merged 256 graphics and solid map',len(assets),'+ RLE block',len(rle))
