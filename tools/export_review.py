#!/usr/bin/env python3
"""Export full 48K SCR screenshots, all 256 glyphs and machine-readable metadata.
Screenshots are produced by bundled partial Z80 simulator, not Fuse.
"""
import json,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from harness import boot,invoke
from mini_z80 import SYM
A=R/'assets';A.mkdir(exist_ok=True)
v=boot()
for phase in (1,2,3):
 v.set('phase',phase);v.set('sector',2)
 invoke(v,'scene_init',limit=600000)
 (A/f'FASE_{phase}_ESTADO_Z80_SIMULADO.scr').write_bytes(v.m[0x4000:0x5b00])
 assert (A/f'FASE_{phase}_ESTADO_Z80_SIMULADO.scr').stat().st_size==6912
# Read the exact compiled glyph bytes and ink attributes.
glyph=SYM['glyphs'];clr=SYM['glyph_colors']
inks={0:'#000000',1:'#306aff',2:'#ff5555',3:'#f057cb',4:'#61e75c',5:'#50d8f0',6:'#f3d65a',7:'#f4f4f4'}
font=ImageFont.load_default()
sc=4;tile=8*sc;cell=tile+13
out=Image.new('RGB',(16*cell+15,16*cell+37),'#101923');d=ImageDraw.Draw(out)
d.text((7,7),'BANCO NATIVO DE 256 GRAFICOS 8X8 / GRIT CLAYMORE V0.7',font=font,fill='#eee9a6')
for i in range(256):
 x=(i%16)*cell+5;y=(i//16)*cell+35
 d.rectangle((x-2,y-2,x+tile+2,y+tile+2),outline='#3a5663')
 for yy in range(8):
  b=v.m[glyph+i*8+yy]
  for xx in range(8):
   if b & (128>>xx):
    d.rectangle((x+xx*sc,y+yy*sc,x+(xx+1)*sc-1,y+(yy+1)*sc-1),fill=inks[v.m[clr+i]&7])
 d.text((x+3,y+tile+3),f'{i:03}',font=font,fill='#d5dce2')
out.save(A/'BANCO_256_GRAFICOS_Z80_V07.png')
# Reproducible group map by stable offsets; direct references to graphic bank.
manifest={
 'machine':'ZX Spectrum 48K PAL', 'graphics_count':256, 'tile_dimensions':[8,8],
 'actor_sprite_bank':{'grit_8dir_2frames':{'start':32,'count':64,'width':16,'height':16},
     'soldier_4dir_2frames':{'start':96,'count':32,'width':16,'height':16},
     'tank_2frames':{'start':128,'count':8,'width':16,'height':16},
     'mech_2frames':{'start':136,'count':18,'width':24,'height':24},
     'hind_2frames':{'start':154,'count':24,'width':32,'height':24},
     'player_8way_bullets':{'start':178,'count':8},
     'enemy_bullet':{'start':186,'count':1},
     'explosion_2frames':{'start':187,'count':8}},
 'terrain_metatiles':{'PALM':195,'HUT':199,'BOULDER':203,'THICKET':207,
                      'RICE':211,'BRIDGE':215,'BARRACK':219,'WATCH':223,
                      'GATE':227,'DRUMS':231,'BUNKER':235,'CONSOLE':239,
                      'PIPEBANK':243,'MECH_DOCK':247},
 'source_files':['src/grit_template.asm','tools/art_v07.py','src/maps_generated.asm',
                 'src/sprites_generated.asm','src/solid_generated.asm'],
 'compiled_symbols':{k:SYM[k] for k in ('glyph_colors','glyphs','glyph_masks','solid_flags','map_data','code_end')},
 'screen_exports':'These .SCR files were reconstructed from a partial-Z80 VM, not tested in Fuse.',
 'rights':'Original project pixel assets and code licensed MIT; no third-party reference sprites included.'}
# Raw lossless Z80 binary asset packs, exactly the bytes assembled into the TAP.
bin_dir=A/'binarios_Z80';bin_dir.mkdir(exist_ok=True)
for filename,label,length in (
 ('GRAFICOS_256x8.bin','glyphs',2048),
 ('MASCARAS_256x8.bin','glyph_masks',2048),
 ('COLORES_256.bin','glyph_colors',256),
 ('COLISIONES_256.bin','solid_flags',256)):
 addr=SYM[label]
 (bin_dir/filename).write_bytes(v.m[addr:addr+length])
for phase in (1,2,3):
 for sector in (1,2,3,4):
  label=f'map_p{phase}_s{sector}';height=24 if sector==4 else 48
  # Export uncompressed original 24-column tiles, not the compiled row IDs.
  ids=v.m[SYM[label]:SYM[label]+height];bank=SYM['map_rows']
  payload=b''.join(v.m[bank+24*rid:bank+24*(rid+1)] for rid in ids)
  assert len(payload)==height*24
  (bin_dir/f'MAPA_F{phase}_S{sector}_{24}x{height}.bin').write_bytes(payload)
(A/'GRAFICOS_V07_MANIFIESTO.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print('Exported 3 SCR, all 256 graphics, 4 native binary asset tables, 12 ROM stage maps, JSON manifest')
