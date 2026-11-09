#!/usr/bin/env python3
"""Capture two real Z80 composite frames (partial Z80 VM); create 1-2-1-2 GIF.
NOT a Fuse capture. No graphics are manually pasted into the VRAM snapshots."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'tests'))
from harness import boot,invoke
A=R/'assets';v=boot()
v.set('phase',1);v.set('sector',1);invoke(v,'scene_init')
# Avoid spurious animated foreground over water for clean side-by-side sampling.
v.set('frame',8)
v.render(A/'V074_RIO_FRAME_1_SIMULADO.png')
invoke(v,'erase_dynamic');v.set('frame',0);invoke(v,'animate_tiles')
invoke(v,'draw_dynamic');invoke(v,'present_dirty')
# The lower half is updated on the next logic tick to avoid a costly spike.
invoke(v,'erase_dynamic');v.set('frame',1);invoke(v,'animate_tiles')
invoke(v,'draw_dynamic');invoke(v,'present_dirty')
v.render(A/'V074_RIO_FRAME_2_SIMULADO.png')
images=[Image.open(A/f'V074_RIO_FRAME_{i}_SIMULADO.png').convert('RGB') for i in (1,2)]
assert images[0].tobytes()!=images[1].tobytes(), 'expected visible differences in animated river'
big=[im.resize((768,576),Image.Resampling.NEAREST) for im in images]
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',18)
canvas=Image.new('RGB',(1580,630),'#14181d');d=ImageDraw.Draw(canvas)
for j,im in enumerate(big):
    x=14+j*782
    canvas.paste(im,(x,15));d.text((x+18,593),f'RÍO - FOTOGRAMA {j+1}  /  ZX 48K (simulado)',font=font,fill='#f8e69c')
canvas.save(A/'V074_RIO_DOS_FOTOGRAMAS.png')
big[0].save(A/'V074_AGUA_ANIMADA_1_2.gif',save_all=True,append_images=[big[1]],duration=[320,320],loop=0,optimize=False)
print('Real assembled-Z80 partial-VM tile animation preview: frame A, frame B, GIF')
