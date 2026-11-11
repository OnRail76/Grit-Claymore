#!/usr/bin/env python3
"""Pixel-authored, reproducible 48K UDG assets; outputs Z80 DB tables and reviewable atlas.
Not AI paintings: every pixel used by the game is in this file."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import random
R=Path(__file__).resolve().parents[1]
A=R/'assets';A.mkdir(exist_ok=True)
BG=32
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import gfx_v12 as GFX
sprites=[];colors=[];names=[];maps=[]
def rows2bytes(rows):
    return [sum(128>>x for x,c in enumerate(r) if c!='.') for r in rows]
def add_rows(rows,attr,label):
    assert len(rows)==8 and all(len(r)==8 for r in rows),label
    sprites.append(rows2bytes(rows));colors.append(attr);names.append(label)
def add_tile(img,attr,label,mask=False):
    assert img.size==(8,8)
    sprites.append([sum(1<<(7-x) for x in range(8) if img.getpixel((x,y))) for y in range(8)])
    colors.append(attr);names.append(label)
def add_art(rows,attrs,label):
    """Trocea un dibujo en celdas 8x8 (fila a fila) con un atributo por celda."""
    h=len(rows)//8;w=len(rows[0])//8
    for cy in range(h):
        for cx in range(w):
            a=attrs if isinstance(attrs,int) else attrs[cy*w+cx]
            add_rows([rows[cy*8+y][cx*8:cx*8+8] for y in range(8)],a,label)
G={}
T=[(n,c,r) for n,c,r in GFX.TILES]
for nm,co,ls in T:add_rows(ls,co,nm)
assert len(sprites)==32
animated_alternates={k:v for k,v in GFX.ANIM_ALT.items()}
assert [T[k][0] for k in animated_alternates]==['WATER','ANTENNA','TERMINAL','LED']
anim_names={4:'water',16:'beacon',24:'terminal',26:'led'}
lines_anim=['; Original 2-frame tiles: bytewise XOR masks toggled at runtime.']
for idx,alt in animated_alternates.items():
    target=[sum(128>>x for x,c in enumerate(row) if c!='.') for row in alt]
    diff=[a^b for a,b in zip(sprites[idx],target)]
    assert len(diff)==8 and any(diff)
    lines_anim.append(f'anim_{anim_names[idx]}_xor:')
    lines_anim.append(' db '+','.join(str(x) for x in diff))
(R/'src/tile_animation_generated.asm').write_text('\n'.join(lines_anim)+'\n')
# V1.2: personajes dibujados a mano en gfx_v12.py
for direction in range(8):
    for f in range(2):add_art(GFX.grit(direction,f),[0x44,0x44,0x47,0x47],'GRIT_%d_%d'%(direction,f))
for direction in range(4):
    for f in range(2):add_art(GFX.soldier(direction,f),[0x42,0x42,0x46,0x46],'SOLDIER_%d_%d'%(direction,f))
for f in range(2):add_art(GFX.TANK[f],0x46,'TANK_'+str(f))
for f in range(2):add_art(GFX.MECH[f],[0x46,0x42,0x46,0x46,0x46,0x46,0x47,0x47,0x47],'MECH_'+str(f))
for f in range(2):add_art(GFX.HIND[f],GFX.BOSS_ATTRS['HIND'],'HIND_'+str(f))
for direction in range(8):add_rows(GFX.SHOTS[direction],0x46,'SHOT_'+str(direction))
add_rows(GFX.BAD_SHOT,0x42,'BAD_SHOT')
add_art(GFX.EXPLOSION[0],0x46,'EXP_0')
add_art(GFX.EXPLOSION[1],0x42,'EXP_1')
assert len(sprites)==195,(len(sprites),names[-4:])
sprite_dims=[(27,5,1,1),(32,16,2,2),(96,8,2,2),(128,2,2,2),(136,2,3,3),(154,2,4,3),(178,8,1,1),(186,1,1,1),(187,2,2,2)]
mask=[[0xff]*8 for _ in sprites]
for start,count,w,h in sprite_dims:
    for f in range(count):
        pos=start+f*w*h
        im=Image.new('1',(w*8,h*8))
        for row in range(h):
            for col in range(w):
                for y,byte in enumerate(sprites[pos+row*w+col]):
                    for x in range(8):
                        if byte&(128>>x):im.putpixel((col*8+x,row*8+y),1)
        dil=Image.new('1',im.size)
        for y in range(im.height):
            for x in range(im.width):
                if im.getpixel((x,y)):
                    for ry in range(max(0,y-1),min(im.height,y+2)):
                        for rx in range(max(0,x-1),min(im.width,x+2)):dil.putpixel((rx,ry),1)
        for row in range(h):
            for col in range(w):
                mask[pos+row*w+col]=[sum(1<<(7-x) for x in range(8) if not dil.getpixel((col*8+x,row*8+y))) for y in range(8)]
# Boss masks don't hide other sprites, and all colors use white on black for safe movement.
# Hand-edited level layouts: 48x24 cell maps, 3 scrollable sectors and a 24x24 boss room per stage.
W=24; H=48
SOLID={2,3,4,6,9,12,13,14,15,19,22,23,24,25,27,28,30}

def level(phase,sector):
    height=24 if sector==4 else H
    base={1:0,2:10,3:20}[phase]
    arr=[[base for x in range(W)] for y in range(height)]
    for y in range(height):
        wave=((y//9+sector)%3)-1
        left=6+wave;right=17+wave
        for x in range(W):
            if phase==1:
                if x<left-2 or x>right+2: v=2 if (x*3+(y%4)*7+sector*5)%7<5 else 8
                elif x<left or x>right: v=1 if (x+(y%2))%3 else 9
                else:v=7 if (x*5+(y%6)*3)%29==0 else 0
                if y in (13+sector%2,14+sector%2,31+sector%2,32+sector%2) and 3<=x<=20:v=5 if 9<=x<=15 else 4
                if y%17==4 and (x in (left-1,right+1)):v=3
            elif phase==2:
                if x<2 or x>21: v=12
                elif x<6 or x>17: v=11
                else: v=10
                if y in (7,8,23,24,39,40) and 3<=x<=20:
                    v=14 if (x<8 or x>15) else 15
                if y in (15,31) and x in (6,17): v=16
                if y in (12,28,44) and x in (4,5,18,19): v=24
                if y in (18,34) and x in (8,9,14,15): v=13
                if y%12==5 and x in (7,16): v=26
            else:
                if x<4 or x>19:v=23 if x in (3,20) else 22
                elif x<7 or x>16:v=21 if y%5 else 25
                else:v=20
                if y in (11,12,33,34) and x in range(4,20):v=21 if 9<=x<=15 else 23
                if y in (15,37) and x in (6,17):v=24
                if y%13==0 and x in (7,16):v=26
            arr[y][x]=v
    # Mark boss area as spacious pad to manoeuvre and fire in 8 directions.
    if sector==4:
        for y in range(6,21):
            for x in range(3,21):
                arr[y][x]={1:0,2:10,3:20}[phase]
        # V1.2: cada jefe tiene su escenario. Grit no pasa de la fila 9.
        for y in range(0,9):
            for x in range(W):
                if phase==1:
                    if y<=1: v=2 if x%3 else 8
                    elif y==2 or y==8: v=1 if x%3 else 9
                    else: v=4
                    if y==8 and 3<=x<=20: v=1 if x%2 else 0
                elif phase==2:
                    if y<=1: v=12
                    elif y==8: v=17
                    else: v=10
                    if y in (2,3) and x in (1,2,21,22): v=13
                else:
                    if y<=1: v=22 if x%4 else 23
                    elif y==8: v=21
                    else: v=20
                    if y==2 and x in (2,21): v=24
                    if y==5 and x in (1,22): v=26
                if x<1 or x>22:
                    v={1:2,2:12,3:22}[phase]
                arr[y][x]=v
    # two wide uninterrupted traversable corridors in every sector, to avoid impossible 2x2 movement.
    for y in range(height):
        if sector!=4:
            for x in range(10,15):
                if arr[y][x] in SOLID:arr[y][x]=base
    # The first playable viewport is the bottom 24 rows.
    return [v for row in arr for v in row]
all_maps=[]
for ph in range(1,4):
    for sec in range(1,5):all_maps.append(level(ph,sec))
assert [len(m) for m in all_maps]==[1152,1152,1152,576]*3
# --- V07: coherent architectural metatiles, 13 original 16x16 + 24x24 hangar ---
# Pixel indices 195..255, retaining stable assembly bases for Grit and enemies.
macros={}
macro_collision={}
def add_macro(label, im, attr,solid):
    assert im.width%8==0 and im.height%8==0
    start=len(sprites); w,h=im.width//8,im.height//8
    for by in range(h):
        for bx in range(w):
            add_tile(im.crop((bx*8,by*8,(bx+1)*8,(by+1)*8)),attr,f'{label}:{by},{bx}')
            mask.append([255]*8)
    macros[label]=(start,w,h)
    for k in range(w*h):macro_collision[start+k]=int(solid)

def scene_asset(label, attr,solid,drawfn,dim=16):
    im=Image.new('1',(dim,dim)); d=ImageDraw.Draw(im);drawfn(d)
    add_macro(label,im,attr,solid)
# 16x16 1 palm, 2 hut, 3 rock, 4 thicket, 5 rice, 6 bridge,
# 7 barrack, 8 watchtower, 9 gate, 10 drums, 11 bunker,
# 12 console, 13 conduit; 24x24 14 giant mech berth.
def add_macro_rows(label,rows,attrs,solid):
    start=len(sprites);w,h=len(rows[0])//8,len(rows)//8
    add_art(rows,attrs,label)
    for k in range(w*h):mask.append([255]*8);macro_collision[start+k]=int(solid)
    macros[label]=(start,w,h)
for nm,solid,attrs,rows in GFX.MACROS:add_macro_rows(nm,rows,attrs,solid)
nm,solid,attrs,rows=GFX.MECH_DOCK;add_macro_rows(nm,rows,attrs,solid)
assert len(sprites)==256,(len(sprites),len(macros))

def place(arr,width,label,x,y):
    start,w,h=macros[label]
    assert 0<=x<=width-w and 0<=y<=len(arr)//width-h
    for yy in range(h):
        for xx in range(w):arr[(y+yy)*width+x+xx]=start+yy*w+xx

# Decorate every playable map with genuinely large recognizable features.
for ph in range(1,4):
    for sec in range(1,5):
        arr=all_maps[(ph-1)*4+sec-1];h=len(arr)//24
        if ph==1:
            for y in range(3,h-2,8):
                place(arr,24,'PALM',1+(y//8)%2,y)
                place(arr,24,'HUT',20-(y//8)%2,y+2)
            for y in range(7,h-2,9):place(arr,24,'THICKET',3,y)
            for y in range(13,h-2,13):place(arr,24,'BOULDER',18,y)
            if h==48:place(arr,24,'WATCH',3,40)
            if h==48:
                place(arr,24,'RICE',11,30)
                # bridge sits on river in the central traversable strip
                place(arr,24,'BRIDGE16',11,34)
        elif ph==2:
            for y in range(4,h-2,10):
                place(arr,24,'DRUMS',2+(y//10)%2,y)
                place(arr,24,'PIPEBANK',19-(y//10)%2,y+1)
            for y in range(11,h-2,16):
                place(arr,24,'CONSOLE',2,y)
            if h==48:
                place(arr,24,'BARRACK',3,24)
                place(arr,24,'BARRACK',19,8)
            for y in range(17,h-2,18):
                place(arr,24,'GATE',19,y)
            if h==48:
                place(arr,24,'CONSOLE',11,30)
                place(arr,24,'PIPEBANK',11,34)
        else:
            for y in range(3,h-2,8):
                place(arr,24,'CONSOLE',1+(y//8)%2,y)
                place(arr,24,'PIPEBANK',20-(y//8)%2,y+2)
            # Mech berth visible in the third-stage environment but not a separate enemy.
            if sec in (2,3):place(arr,24,'MECH_DOCK',19,18)
            if h==48 and sec!=2:place(arr,24,'BUNKER',4,22)

# Per-tile collision flags are now a full 256-byte lookup, including macrotile pieces.
solid_data=[int(i in SOLID) for i in range(32)]+[0]*(195-32)
solid_data.extend(macro_collision[i] for i in range(195,256))
assert len(solid_data)==256
(R/'src/solid_generated.asm').write_text('solid_flags:\n'+''.join(' db '+','.join(str(v) for v in solid_data[i:i+32])+'\n' for i in range(0,256,32)))
# Extend the same 256 glyphs in the executable with their own mask and color bytes.
# export db source without string escaping
# Compact exact map data using a dictionary of unique 24-tile rows.
# Each sector retains all its individual rows (no repeated-map shortcut).
# V1.2: un diccionario de filas por fase (cada uno < 256 filas).
out=[];dict_rows=[]
for phase in range(1,4):
 unique_rows={}; rows=[]
 for sec in range(1,5):
    data=all_maps[(phase-1)*4+sec-1]
    ids=[]
    for i in range(0,len(data),24):
        row=tuple(data[i:i+24])
        if row not in unique_rows:
            unique_rows[row]=len(rows);rows.append(row)
        ids.append(unique_rows[row])
    out.append(f'map_p{phase}_s{sec}:')
    for i in range(0,len(ids),24):out.append(' db '+','.join(str(v) for v in ids[i:i+24]))
 assert len(rows)<256,(phase,len(rows))
 dict_rows.append(rows)
out.append('map_rows_bases:')
out.append(' dw map_rows_p1,map_rows_p2,map_rows_p3')
for phase,rows in enumerate(dict_rows,1):
 out.append(f'map_rows_p{phase}:' + ('\nmap_rows:' if phase==1 else ''))
 for row in rows:out.append(' db '+','.join(str(v) for v in row))
print('filas por fase',[len(r) for r in dict_rows])
(R/'src/maps_generated.asm').write_text('\n'.join(out)+'\n')
# color table and byte assets; mask preserves scenery under dynamic sprites.
lines=['glyph_colors:']
for i in range(0,len(colors),16):lines.append(' db '+','.join(hex(a) for a in colors[i:i+16]))
lines+=['glyphs:']
for row in sprites:lines.append(' db '+','.join(hex(v) for v in row))
lines+=['glyph_masks:']
for row in mask:lines.append(' db '+','.join(hex(v) for v in row))
(R/'src/sprites_generated.asm').write_text('\n'.join(lines)+'\n')
# sprite atlas PNG must contain exactly the binary tiles used by the game (no font rendering).
selected=[(0,0,8,8,'JUNGLA: SUELO'),(2,0,8,8,'ARBOL'),(4,0,8,8,'AGUA'),(10,0,8,8,'BASE'),(12,0,8,8,'MURO'),(20,0,8,8,'SUBTERRANEO'),(24,0,8,8,'TERMINAL'),
          (32,0,16,16,'GRIT ARRIBA'),(40,0,16,16,'GRIT ABAJO'),(64,0,16,16,'GRIT DIAGONAL'),(96,0,16,16,'SOLDADO'),(128,0,16,16,'TANQUE'),(136,0,24,24,'MECHA'),(154,0,32,24,'HIND')]
font=ImageFont.load_default();atlas=Image.new('RGB',(1300,655),'#101920');d=ImageDraw.Draw(atlas)
d.text((20,12),'GRIT CLAYMORE - SPRITES Z80 V07 / DATOS REALES 48K',font=font,fill='#ffffff')
for j,(st,_,w,h,nam) in enumerate(selected):
    xx=20+(j%7)*180;yy=65+(j//7)*282
    d.rectangle((xx-2,yy-2,xx+171,yy+246),outline='#395769',width=2)
    scale=4 if w>16 else 7
    for y in range(h):
        for x in range(w):
            n=st+(y//8)*(w//8)+x//8
            if sprites[n][y%8]&(128>>(x%8)):
                d.rectangle((xx+10+x*scale,yy+10+y*scale,xx+10+(x+1)*scale-1,yy+10+(y+1)*scale-1),fill='#eef5ec')
    d.text((xx+5,yy+208),nam,font=font,fill='#f9d45c')
atlas.save(A/'UDG_SPRITES_Z80_V07.png')
# 3 full playable area scene mockups from actual game tiles, no imagined details
for ph in range(1,4):
 sec=2 if ph!=3 else 1
 data=all_maps[(ph-1)*4+sec-1];img=Image.new('RGB',(192,192),'black');pix=img.load()
 pal={0:(220,220,220),1:(60,175,76),2:(70,170,88),3:(170,170,170),4:(80,210,220),5:(220,210,140),6:(230,230,230),8:(60,170,60),9:(65,170,76),10:(230,230,230),11:(95,210,230),12:(245,245,245),13:(70,220,90),14:(250,250,250),15:(245,200,60),20:(210,210,210),21:(185,185,185),22:(235,235,235),23:(180,180,180),24:(95,210,230),26:(240,90,80)}
 for ty in range(24):
  for tx in range(24):
   idx=data[(ty+24)*24+tx];col=pal.get(idx,(220,220,220));rows=sprites[idx]
   for yy in range(8):
    for xx in range(8):
     if rows[yy]&(128>>xx):pix[tx*8+xx,ty*8+yy]=col
 img.resize((768,768),Image.Resampling.NEAREST).save(A/f'FASE_{ph}_TILESET_REAL.png')
# Review sheet rendered pixel-for-pixel from the same glyph arrays as the TAP.
from PIL import ImageDraw
font=ImageFont.load_default()
def get_bitmap(start,w,h):
    im=Image.new('RGB',(w*8,h*8),'#101820');px=im.load()
    inks={0:(25,25,25),2:(252,80,80),4:(91,231,87),5:(72,217,235),6:(250,212,73),7:(235,244,247)}
    for yc in range(h):
        for xc in range(w):
            k=start+yc*w+xc; fg=inks[colors[k]&7]
            for yy,b in enumerate(sprites[k]):
                for xx in range(8):
                    if b&(128>>xx):px[xc*8+xx,yc*8+yy]=fg
    return im
items=[]
for direction,label in enumerate(('ARRIBA','ABAJO','IZQ','DCHA','ARR-IZQ','ARR-DCHA','ABA-IZQ','ABA-DCHA')):
    items.append((f'GRIT {label}',get_bitmap(32+direction*8,2,2)))
for direction,label in enumerate(('ARRIBA','ABAJO','IZQUIERDA','DERECHA')):
    items.append((f'ENEMIGO {label}',get_bitmap(96+direction*8,2,2)))
for base,wh,label in ((128,(2,2),'TANQUE'),(136,(3,3),'MECHA'),(154,(4,3),'HIND')):
    items.append((label,get_bitmap(base,*wh)))
for name,(base,w,h) in macros.items():items.append((name,get_bitmap(base,w,h)))
columns=6;cw=180;ch=163;rows=(len(items)+columns-1)//columns
sheet=Image.new('RGB',(columns*cw,rows*ch+45),'#111721');dr=ImageDraw.Draw(sheet)
dr.text((15,9),'GRIT CLAYMORE / GRAFICOS NATIVOS Z80 V07',font=font,fill='#fff6a5')
for i,(label,im) in enumerate(items):
    cx=(i%columns)*cw;cy=45+(i//columns)*ch
    dr.rectangle((cx+4,cy+4,cx+cw-5,cy+ch-5),outline='#395566',width=1)
    scale=min(5,112//max(im.size));im=im.resize((im.width*scale,im.height*scale),Image.Resampling.NEAREST)
    sheet.paste(im,(cx+(cw-im.width)//2,cy+10))
    dr.text((cx+9,cy+ch-28),label,font=font,fill='#ffdc71')
sheet.save(A/'ATLAS_NATIVO_V07.png')
print('Generated',len(sprites),'native 8x8 glyphs (195 sprites plus 61 original scenery glyphs), 12 maps')

# ---------------------------------------------------------------------------
# V1.2: banco de jefes (lancha, camion, Hind) y marco de la tarjeta de fase
# ---------------------------------------------------------------------------
def dilated_masks(rows):
    h=len(rows);w=len(rows[0])
    on=lambda x,y:0<=x<w and 0<=y<h and rows[y][x]!='.'
    out=[]
    for cy in range(h//8):
        for cx in range(w//8):
            m=[]
            for y in range(8):
                b=0
                for x in range(8):
                    X,Y=cx*8+x,cy*8+y
                    near=any(on(X+dx,Y+dy) for dx in (-1,0,1) for dy in (-1,0,1))
                    if not near:b|=128>>x
                m.append(b)
            out.append(m)
    return out
def cells(rows):
    h=len(rows)//8;w=len(rows[0])//8
    return [rows2bytes([rows[cy*8+y][cx*8:cx*8+8] for y in range(8)]) for cy in range(h) for cx in range(w)]
bl=['; V1.2: tres jefes de 32x24, dos fotogramas. Cada bloque: 24 glifos, 24 mascaras, 24 atributos.','boss_bank:']
for nm,frames in GFX.BOSSES:
    g=cells(frames[0])+cells(frames[1])
    m=dilated_masks(frames[0])+dilated_masks(frames[1])
    at=GFX.BOSS_ATTRS[nm]*2
    bl.append(f'; {nm}')
    for c in g:bl.append(' db '+','.join(str(v) for v in c))
    for c in m:bl.append(' db '+','.join(str(v) for v in c))
    bl.append(' db '+','.join(hex(v) for v in at))
# comprobacion: el Hind del banco es identico al del banco general
hind_now=[sprites[154+i] for i in range(24)]
assert hind_now==cells(GFX.HIND[0])+cells(GFX.HIND[1])
bl.append('card_frame_glyphs:')
for k in ('corner','hline','vline'):bl.append(' db '+','.join(str(v) for v in rows2bytes(GFX.FRAME[k])))
(R/'src/boss_generated.asm').write_text('\n'.join(bl)+'\n')

# ---------------------------------------------------------------------------
# Hojas de revision V1.2 con atributos reales (papel negro, tinta por celda)
# ---------------------------------------------------------------------------
PAL=[(0,0,0),(0,0,205),(205,0,0),(205,0,205),(0,205,0),(0,205,205),(205,205,0),(205,205,205)]
BRI=[(0,0,0),(0,0,255),(255,0,0),(255,0,255),(0,255,0),(0,255,255),(255,255,0),(255,255,255)]
def ink(a):return (BRI if a&64 else PAL)[a&7]
def render_map(data,top,rows=24):
    im=Image.new('RGB',(192,rows*8));px=im.load()
    for ty in range(rows):
        for tx in range(24):
            idx=data[(top+ty)*24+tx];c=ink(colors[idx])
            for y,b in enumerate(sprites[idx]):
                for x in range(8):
                    if b&(128>>x):px[tx*8+x,ty*8+y]=c
    return im
def paste_sprite(im,glyph_rows,attrs,cx,cy,masks=None):
    """Pinta un sprite con mascara sobre la imagen, con el atributo de cada celda."""
    px=im.load();h=len(glyph_rows)//8;w=len(glyph_rows[0])//8
    m=dilated_masks(glyph_rows);g=cells(glyph_rows)
    for j in range(h):
        for i in range(w):
            k=j*w+i;a=attrs if isinstance(attrs,int) else attrs[k]
            X0,Y0=(cx+i)*8,(cy+j)*8
            for y in range(8):
                for x in range(8):
                    bg=px[X0+x,Y0+y]!=(0,0,0)
                    on=(bg and m[k][y]&(128>>x)) or (g[k][y]&(128>>x))
                    px[X0+x,Y0+y]=ink(a) if on else (0,0,0)
            # el atributo manda en toda la celda: el fondo cambia de color
            for y in range(8):
                for x in range(8):
                    if px[X0+x,Y0+y]!=(0,0,0):px[X0+x,Y0+y]=ink(a)
REV=R/'assets/v12';REV.mkdir(exist_ok=True)
for ph in range(1,4):
    for sec in range(1,5):
        data=all_maps[(ph-1)*4+sec-1];h=len(data)//24
        im=render_map(data,h-24)
        if sec==4:
            fr=GFX.BOSSES[ph-1][1][0];paste_sprite(im,fr,GFX.BOSS_ATTRS[GFX.BOSSES[ph-1][0]],10,4)
            paste_sprite(im,GFX.grit(0,0),[0x44,0x44,0x47,0x47],11,12)
        else:
            paste_sprite(im,GFX.grit(0,0),[0x44,0x44,0x47,0x47],11,20)
            if ph<3:
                paste_sprite(im,GFX.soldier(1,0),[0x42,0x42,0x46,0x46],8,6)
                paste_sprite(im,GFX.soldier(3,1),[0x42,0x42,0x46,0x46],15,10)
            else:
                paste_sprite(im,GFX.MECH[0],[0x46,0x42,0x46,0x46,0x46,0x46,0x47,0x47,0x47],7,5)
        im.resize((576,576),Image.Resampling.NEAREST).save(REV/f'F{ph}_S{sec}.png')
print('V1.2: banco de jefes y hojas de revision en assets/v12')
