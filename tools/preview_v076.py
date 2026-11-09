#!/usr/bin/env python3
"""Contact sheet from compiled Z80 simulated memory; no hand-painted gameplay."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
imgs=[
 ('JUEGO / HUD NUEVO',ROOT/'build/FASE_1_Z80_SIMULADA_V076.png'),
 ('LABORATORIO',ROOT/'build/FASE_2_Z80_SIMULADA_V076.png'),
 ('FASE 2 / 2 SEGUNDOS',ROOT/'build/FASE_2_PRESENTACION_V076.png'),
 ('GAME OVER / CALAVERA',ROOT/'assets/GAME_OVER_V076.png'),
]
W,H=768,576;ow=W*2+48;oh=H*2+125
out=Image.new('RGB',(ow,oh),'#101319');d=ImageDraw.Draw(out)
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',22)
for i,(label,path) in enumerate(imgs):
 im=Image.open(path).convert('RGB').resize((W,H),Image.Resampling.NEAREST)
 x=16+(i%2)*(W+16);y=16+(i//2)*(H+46)
 out.paste(im,(x,y))
 d.text((x+5,y+H+4),label,font=font,fill='#ffe456')
foot='Capturas de RAM simulada del Z80 ensamblado; NO son capturas de Fuse.'
d.text((16,oh-24),foot,font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',16),fill='#d0dadf')
out.save(ROOT/'assets/V076_RESUMEN_HUD_FASES_GAMEOVER.png')
print('Created four-panel review from compiled machine-code VM')
