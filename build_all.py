#!/usr/bin/env python3
"""One command to regenerate source, machine code, TAP, and Z80 regressions."""
import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parent
for step in (
 ['tools/art_v12.py'],
 ['tools/font_v07.py'],
 ['tools/title_v07.py'],
 ['tools/hud_v12.py'],
 ['tools/gameover_v076.py'],
 ['tools/victory_v077.py'],
 ['tools/merge_assets.py'],
 ['build_asm.py','src/grit.asm','build/grit.bin'],
 ['make_tap.py'],
 ['tests/test_v07.py'],
 ['tests/test_color_fuse_bug_v071.py'],
 ['tests/test_art_v07.py'],
 ['tests/test_hud_v073.py'],
 ['tests/test_v074.py'],
 ['tests/test_v076.py'],
 ['tests/test_v077.py'],
 ['tests/test_v078.py'],
 ['tests/test_v1_hud_centered.py'],
 ['tests/test_v101_title.py'],
 ['tests/test_v110.py'],
 ['tests/test_v12.py'],
 ['tests/test_v13.py'],
 ['tests/test_v14.py'],
 ['tests/test_v15.py'],
 ['tests/test_v16.py'],
 ['tools/export_review.py'],
 ['tools/review_v07.py'],
 ['tools/preview_v076.py'],
 ['tools/demo_animation_v074.py']):
 print('+', ' '.join(step),flush=True)
 subprocess.run([sys.executable,*step],cwd=R,check=True)

from shutil import copyfile
copyfile(R/'build/GRIT_CLAYMORE_V078_48K.tap',R/'build/GRIT_CLAYMORE_V1.6_48K.tap')
print('GRIT CLAYMORE V1.6 listo en build/GRIT_CLAYMORE_V1.6_48K.tap')
