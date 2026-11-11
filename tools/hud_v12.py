#!/usr/bin/env python3
"""GRIT CLAYMORE V1.2 - panel lateral de 64x192 rehecho como panel de instrumentos.
- Bisel gris continuo (doble linea) con placas remachadas entre modulos.
- Rotulo de cada modulo en negro sobre franja de color (PAPER brillante).
- Cada contador vive en una ventana enmarcada; sus celdas quedan VACIAS para el Z80.
- Las dos calaveras salen de la ilustracion aprobada por el autor.
Formato de salida identico al de V0.7.6: hud_panel_map (glifo, atributo) x 192
y hud_panel_glyphs."""
from pathlib import Path
from PIL import Image, ImageDraw
import runpy
ROOT = Path(__file__).resolve().parents[1]
A = ROOT / 'assets'; A.mkdir(exist_ok=True)
raw = runpy.run_path(str(ROOT / 'tools/font_v07.py'))['raw']

# calavera del autor (misma extraccion que V0.7.6)
orig = Image.open(ROOT / 'assets/CALAVERA_REFERENCIA_USUARIO.jpg').convert('RGB')
msk = Image.new('1', orig.size, 0); op = orig.load(); mp = msk.load()
for y in range(orig.height):
    for x in range(orig.width):
        r, g, b = op[x, y]
        if r > 120 and g > 100 and r > b * 1.8 and g > b * 1.7: mp[x, y] = 1
skull = msk.crop(msk.getbbox()).resize((16, 17), Image.Resampling.LANCZOS).convert('L').point(lambda v: 255 if v > 107 else 0).convert('1')
skull.resize((160, 170), Image.Resampling.NEAREST).save(A / 'CALAVERA_HUD_V076.png')

W, H = 64, 192
img = Image.new('1', (W, H)); d = ImageDraw.Draw(img)

# Modulos: (fila del rotulo, fila del contador, primera fila, ultima fila, texto, PAPER del rotulo)
MODS = [(3, 5, 0, 6, 'PUNTOS', 6), (8, 10, 7, 12, 'VIDAS', 5), (14, 16, 13, 18, 'PODER', 4), (20, 22, 19, 23, 'TANQUE', 3)]
DYN = {5: range(25, 31), 10: range(25, 31), 16: range(26, 30), 22: range(26, 30)}  # V1.4: TANQUE de 4

# 1) bisel exterior: doble linea a izquierda y derecha, arriba y abajo
d.line((1, 0, 1, 191), fill=1); d.line((3, 2, 3, 189), fill=1)
d.line((62, 0, 62, 191), fill=1); d.line((60, 2, 60, 189), fill=1)
d.line((1, 0, 62, 0), fill=1); d.line((3, 2, 60, 2), fill=1)
d.line((1, 191, 62, 191), fill=1); d.line((3, 189, 60, 189), fill=1)

def rivet(x, y):
    d.rectangle((x, y, x + 1, y + 1), fill=1)

# 2) placas separadoras remachadas entre modulos
for y in (55, 103, 151):
    d.line((3, y, 60, y), fill=1); d.line((3, y + 2, 60, y + 2), fill=1)
    d.line((4, y + 1, 59, y + 1), fill=0)
for y in (5, 59, 107, 155):
    rivet(5, y); rivet(57, y)
for y in (51, 99, 147, 185):
    rivet(5, y); rivet(57, y)

# 3) ventanas de los contadores: marco alrededor de la fila dinamica,
#    dibujado solo en las celdas vecinas (nunca dentro de la fila dinamica)
def window(row, c0, c1):
    x0 = (c0 - 24) * 8 - 2; x1 = (c1 - 24 + 1) * 8 + 1
    y0 = row * 8 - 2; y1 = row * 8 + 9
    d.line((x0 + 1, y0, x1 - 1, y0), fill=1); d.line((x0 + 1, y1, x1 - 1, y1), fill=1)
    d.line((x0, y0 + 1, x0, y1 - 1), fill=1); d.line((x1, y0 + 1, x1, y1 - 1), fill=1)
for row, cols in DYN.items():
    window(row, cols[0], cols[-1])

# 4) rotulos: texto en tinta negra sobre franja de PAPER de color (celdas 25..30)
def label(text, cy):
    width = len(text) * 6 - 1; x0 = (64 - width) // 2
    for i, ch in enumerate(raw.get(c, raw[' ']) for c in text):
        for yy, ln in enumerate(ch):
            for xx, c in enumerate(ln):
                if c == '1': d.point((x0 + i * 6 + xx, cy * 8 + yy), fill=1)
for lr, dr, r0, r1, text, paper in MODS:
    label(text, lr)

# 5) calaveras del autor en la cabecera
img.paste(skull, (10, 5)); img.paste(skull, (38, 5))

# Atributos: bisel y ventanas en gris metalico; rotulos negro sobre color;
# calaveras en amarillo. Las celdas dinamicas las pinta draw_hud.
attrs = []
for cy in range(24):
    for cx in range(8):
        col = 24 + cx
        a = 0x07                                   # gris metalico
        for lr, dr, r0, r1, text, paper in MODS:
            if cy == lr and 25 <= col <= 30: a = 0x40 | (paper << 3)  # negro sobre color brillante
        if cy <= 2 and 25 <= col <= 30: a = 0x46
        attrs.append(a)

unique = []; lut = {}; mapping = []
for cy in range(24):
    for cx in range(8):
        g = bytes(sum(128 >> x for x in range(8) if img.getpixel((cx * 8 + x, cy * 8 + y))) for y in range(8))
        if cy in DYN and (24 + cx) in DYN[cy]:
            assert g == bytes(8), ('el marco invade un contador', cy, cx)
        if g not in lut: lut[g] = len(unique); unique.append(g)
        mapping.append(lut[g])
assert len(unique) < 256

lines = ['; V1.2: panel de instrumentos 64x192, bisel remachado, rotulos sobre franja de color', 'hud_panel_map:']
for i in range(0, 192, 8):
    nums = []
    for j in range(i, i + 8): nums.extend((mapping[j], attrs[j]))
    lines.append(' db ' + ','.join(map(str, nums)))
# V1.5: rotulo alternativo ARMA (fase 3), misma tipografia y centrado que el resto
alt = Image.new('1', (W, 8)); ad = ImageDraw.Draw(alt)
wdt = len('ARMA') * 6 - 1; ax0 = (64 - wdt) // 2
for i, ch in enumerate(raw.get(c, raw[' ']) for c in 'ARMA'):
    for yy, ln in enumerate(ch):
        for xx, c in enumerate(ln):
            if c == '1': ad.point((ax0 + i * 6 + xx, yy), fill=1)
arma = []
for cx in range(1, 7):
    arma.extend(sum(128 >> x for x in range(8) if alt.getpixel((cx * 8 + x, y))) for y in range(8))
lines.append('hud_panel_glyphs:')
for i in range(0, len(unique), 2):
    lines.append(' db ' + ','.join(map(str, b''.join(unique[i:i + 2]))))
lines.append('hud_arma_label:')
for i in range(0, 48, 8): lines.append(' db ' + ','.join(map(str, arma[i:i + 8])))
(ROOT / 'src/hud_generated.asm').write_text('\n'.join(lines) + '\n')

PAL = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205)]
BRI = [(0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]
prev = Image.new('RGB', (64, 192))
for i, gi in enumerate(mapping):
    a = attrs[i]; pal = BRI if a & 64 else PAL
    ink = pal[a & 7]; paper = pal[(a >> 3) & 7]
    cx = (i % 8) * 8; cy = (i // 8) * 8
    for y in range(8):
        for x in range(8):
            prev.putpixel((cx + x, cy + y), ink if unique[gi][y] & (128 >> x) else paper)
prev.save(A / 'HUD_NATIVO_V12.png')
prev.resize((384, 1152), Image.Resampling.NEAREST).save(A / 'HUD_AMPLIADO_V12.png')
print('HUD V1.2:', len(unique), 'glifos;', 384 + len(unique) * 8, 'bytes en el Z80')
