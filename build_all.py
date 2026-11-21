#!/usr/bin/env python3
"""One command to regenerate source, machine code, TAP, and Z80 regressions."""
import argparse, subprocess, sys
from pathlib import Path
R=Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description="GRIT CLAYMORE v1.14: reconstrucción y regresiones")
parser.add_argument("--ci", action="store_true", help="Validación rápida de publicación: motor, suministros, enemigos, jefes y TAP")
args = parser.parse_args()
all_steps = (
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
 ['tests/test_v17.py'],
 ['tests/test_v18.py'],
 ['tests/test_v19.py'],
 ['tests/test_v114.py'],
 ['tools/export_review.py'],
 ['tools/review_v07.py'],
 ['tools/preview_v076.py'],
 ['tools/demo_animation_v074.py'])

# El modo habitual conserva TODA la batería histórica, incluidos los ensayos largos.
# El modo --ci se usa para bloquear publicaciones con pruebas recientes y de suministros,
# evitando que el test exhaustivo de la v1.1 retenga Actions durante decenas de minutos.
CI_TESTS = {
 'tests/test_v13.py', 'tests/test_v14.py', 'tests/test_v15.py',
 'tests/test_v17.py', 'tests/test_v18.py', 'tests/test_v19.py',
 'tests/test_v114.py',
}
if args.ci:
 steps = [s for s in all_steps if (s[0] in CI_TESTS or not s[0].startswith(('tests/', 'tools/export_review.py','tools/review_v07.py','tools/preview_v076.py','tools/demo_animation_v074.py')))]
 print('CI v1.14: compilar + %s pruebas específicas; el modo completo sigue disponible sin --ci' % len(CI_TESTS), flush=True)
else:
 steps = all_steps
for step in steps:
 print('+', ' '.join(step),flush=True)
 subprocess.run([sys.executable,*step],cwd=R,check=True)

from shutil import copyfile
copyfile(R/'build/GRIT_CLAYMORE_V078_48K.tap',R/'build/GRIT_CLAYMORE_V1.14_48K.tap')
print('GRIT CLAYMORE V1.14 listo en build/GRIT_CLAYMORE_V1.14_48K.tap')
