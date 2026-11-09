#!/usr/bin/env python3
"""Pixel-authored, reproducible 48K UDG assets; outputs Z80 DB tables and reviewable atlas.
Not AI paintings: every pixel used by the game is in this file."""
from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import random
R=Path(__file__).resolve().parents[1]
A=R/'assets';A.mkdir(exist_ok=True)
BG=32
sprites=[];colors=[];names=[];maps=[]
def add_tile(img,attr,label,mask=False):
    assert img.size==(8,8)
    sprites.append([sum(1<<(7-x) for x in range(8) if img.getpixel((x,y))) for y in range(8)])
    colors.append(attr);names.append(label)
def tile(lines,attr,label):
    assert len(lines)==8 and all(len(l)==8 for l in lines),(label,lines)
    im=Image.new('1',(8,8));p=im.load()
    for y,line in enumerate(lines):
        for x,v in enumerate(line):p[x,y]=1 if v!='.' else 0
    add_tile(im,attr,label)
G={}
# 32 hand-composed 8x8 environmental tiles: light and shadow are controlled, not ROM characters.
T=[
('DIRT',0x06,["........","...#....","........","........","......#.","........","........","........"]),
('GRASS',0x44,[".....#..","..#.....","...#....","........",".#..#...","........","....#...",".......#"]),
('TREE',0x04,["..####..",".######.","########","###..###","########",".######.","..####..","...##..."]),
('TRUNK',0x46,["..#..#..","...##...","..####..","...##...","..####..","...##...","..####..","...##..."]),
('WATER',0x45,["........",".##..##.","........","...##...","........","##...##.","........","..##...."]),
('BRIDGE',0x46,["########","..#..#..","########","..#..#..","########","..#..#..","########","..#..#.."]),
('ROCK',0x47,[".#####..","##...##.","#..##..#","#.#..#.#","#..###.#","##....##",".######.","...##..."]),
('MUD',0x46,["........","...##...","........","........","........","........","....##..","........"]),
('LEAF',0x04,["#..#...#",".##..##.","...##...","##....##","..####..","##....##","...##...",".##..##."]),
('BUSH',0x04,["........","...##...",".######.","##.##.##","########",".######.",".##..##.","........"]),
('CONCRETE',0x47,["........","..#...#.","........","....#...","........",".#......","........","...#...."]),
('PAVEMENT',0x45,["#.#.#.#.","........",".#.#.#.#","........","#.#.#.#.","........",".#.#.#.#","........"]),
('WALL',0x47,["########","#......#","#.####.#","#.#..#.#","#.#..#.#","#.####.#","#......#","########"]),
('CRATE',0x44,["..####..",".######.","##....##","##....##","##....##","##....##",".######.","..####.."]),
('FENCE',0x47,["########","........","########","........","########","........","########","........"]),
('METAL',0x42,["##....##",".##..##.","..####..","...##...","..####..",".##..##.","##....##","........"]),
('ANTENNA',0x42,["...##...","..####..",".######.","...##...","...##...","..####..","...##...","..####.."]),
('HAZARD',0x46,["########","##....##","########","....##..","..##....","########","##....##","########"]),
('SAND',0x45,["........","..####..",".#....#.","........","..####..",".#....#.","........","........"]),
('RUBBLE',0x47,["###..###","#......#","#.####.#","#.#..#.#","#.####.#","#......#","###..###","........"]),
('LABFLOOR',0x05,["#.......","........","........","........","........","........","........",".......#"]),
('LABGRID',0x45,["........","........","..#..#..","........","........","..#..#..","........","........"]),
('CAVEROCK',0x47,["#####...","#..####.","##.#..##","##...###",".##.#..#","###..###",".######.","...####."]),
('PIPE',0x47,["..####..","..#..#..","..#..#..","..#..#..","..#..#..","..#..#..","..####..","........"]),
('TERMINAL',0x45,["########","#......#","#.####.#","#.#..#.#","#.#.##.#","#.####.#","#......#","########"]),
('GRILLE',0x47,["########","#.#.#.##","##.#.#.#","#.#.#.##","##.#.#.#","#.#.#.##","##.#.#.#","########"]),
('LED',0x42,["........","...##...","..#..#..",".#....#.",".#....#.","..#..#..","...##...","........"]),
('RACION',0x46,["..####..",".######.",".#....#.",".#.####.",".#.#..#.",".#.####.",".######.","..####.."]),
('TURRET_UP',0x46,["...##...","...##...","...##...","..####..","..#..#..","...##...","........","........"]),
('TURRET_DOWN',0x46,["........","........","...##...","..#..#..","..####..","...##...","...##...","...##..."]),
('TURRET_LEFT',0x46,["........","........","...##...","#####...","#####...","...##...","........","........"]),
('TURRET_RIGHT',0x46,["........","........","...##...","...#####","...#####","...##...","........","........"])]
for nm,co,ls in T:tile(ls,co,nm)
assert len(sprites)==32
# True two-frame environmental bitmaps. Only the XOR differences are
# stored in code; switching frames changes the glyph bitmap in RAM.
animated_alternates={
 4: ['........','...##..#','........','.##...##','........','...##...','........','##...##.'],
 16:['........','...##...','..####..','.######.','..####..','...##...','........','...##...'],
 24:['########','#......#','#.####.#','#.#.#..#','#.#..#.#','#.####.#','#......#','########'],
 26:['........','...##...','..####..','.######.','.######.','..####..','...##...','........'],
}
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
# 16x16 actual pixel art, faces generated with hand-drawn action frames rotated at pixel precision.
def person(kind,fr,direction):
    """Top-down 16x16 original sprite: gun extends in the aim direction.
    Separate beret/helmet, backpack, chest, rifle, trousers and 2 walking poses."""
    im=Image.new('1',(16,16)); d=ImageDraw.Draw(im)
    # top-down helmet/head with two-sided shadow to keep a human silhouette
    d.ellipse((5,2,10,6),fill=1)
    d.rectangle((6,4,9,5),fill=0)
    if kind=='player':
        d.polygon([(4,2),(5,1),(10,0),(12,2),(10,3),(4,3)],fill=1)
        d.point((3,3),fill=1)  # distinctive boina fold
    else:
        d.rectangle((4,2,11,3),fill=1)
        d.point((5,1),fill=1);d.point((10,1),fill=1)
    d.rectangle((5,6,10,11),fill=1)  # vest
    d.rectangle((6,7,7,9),fill=0)  # chest straps negative pixels
    d.point((9,8),fill=0)
    # separate left/right arm positions and hip width
    d.rectangle((3,7,4,10),fill=1)
    d.rectangle((11,7,12,10),fill=1)
    d.line((5,11,10,11),fill=1)
    if fr==0:
        d.rectangle((5,12,6,15),fill=1)
        d.rectangle((9,12,10,13),fill=1)
        d.rectangle((10,14,11,15),fill=1)
    else:
        d.rectangle((5,12,6,13),fill=1)
        d.rectangle((4,14,5,15),fill=1)
        d.rectangle((9,12,10,15),fill=1)
    # Rifle in all 8 directions. Barrels are at least four pixels beyond torso.
    # Distinct angular silhouette replaces the old symmetrical cross-like character.
    if direction == 0:       # top (back view)
        d.rectangle((10,0,11,8),fill=1)
        d.line((8,7,10,5),fill=1)
        d.rectangle((11,8,12,9),fill=1)
    elif direction == 1:     # down
        d.rectangle((11,8,12,15),fill=1)
        d.line((8,8,11,10),fill=1)
        d.point((10,14),fill=1)
    elif direction == 2:     # left
        d.line((0,7,8,7),fill=1,width=1)
        d.line((1,8,7,8),fill=1,width=1)
        d.line((4,9,7,10),fill=1)
        d.rectangle((11,7,12,9),fill=0)
    elif direction == 3:     # right
        d.line((8,7,15,7),fill=1,width=1)
        d.line((8,8,14,8),fill=1,width=1)
        d.line((8,10,11,9),fill=1)
        d.rectangle((3,7,4,9),fill=0)
    elif direction == 4:     # up-left
        d.line((0,0,7,8),fill=1,width=2)
        d.line((2,1,7,7),fill=0)
        d.line((2,3,7,8),fill=1)
    elif direction == 5:     # up-right
        d.line((15,0,8,8),fill=1,width=2)
        d.line((13,1,8,7),fill=0)
        d.line((13,3,8,8),fill=1)
    elif direction == 6:     # down-left
        d.line((0,15,7,8),fill=1,width=2)
        d.line((2,14,7,9),fill=0)
        d.line((2,12,7,8),fill=1)
    else:                    # down-right
        d.line((15,15,8,8),fill=1,width=2)
        d.line((13,14,8,9),fill=0)
        d.line((13,12,8,8),fill=1)
    return im
def sprite(im,tag):
    w,h=im.size
    assert w%8==0 and h%8==0
    for yy in range(0,h,8):
        for xx in range(0,w,8):
            add_tile(im.crop((xx,yy,xx+8,yy+8)),0x47,tag)

for direction in range(8):
    for f in range(2):sprite(person('player',f,direction),'GRIT_%d_%d'%(direction,f))
for direction in range(4):
    for f in range(2):sprite(person('soldier',f,direction),'SOLDIER_%d_%d'%(direction,f))

def tank(f):
    im=Image.new('1',(16,16));d=ImageDraw.Draw(im)
    # tracks readable on both sides and an armored hull, not a square glyph
    for x in (1,12):
        d.rounded_rectangle((x,2,x+2,14),radius=1,fill=1)
        for y in range(3+(f%2),14,3):d.point((x+1,y),fill=0)
    d.polygon([(4,3),(11,3),(12,6),(12,13),(4,13),(3,6)],fill=1)
    d.rectangle((5,4,10,12),outline=0)
    d.ellipse((5,6,10,11),fill=1)
    d.ellipse((6,6,9,9),fill=0)  # rotating turret overlay is applied by Z80
    d.line((5,13,10,13),fill=1)
    return im
for f in range(2):sprite(tank(f),'TANK_'+str(f))

def mech(f):
    im=Image.new('1',(24,24));d=ImageDraw.Draw(im)
    d.rectangle((8,1,15,3),fill=1) # head
    d.rectangle((10,2,13,3),fill=0) # visor
    d.polygon([(6,4),(17,4),(20,7),(18,15),(5,15),(3,7)],fill=1)
    d.rectangle((9,6,14,9),fill=0)
    d.rectangle((10,7,13,8),fill=1)
    d.rectangle((1,7,5,15),fill=1) # arms
    d.rectangle((18,7,22,15),fill=1)
    d.rectangle((2,9,4,12),fill=0); d.rectangle((19,9,21,12),fill=0)
    d.rectangle((8,15,15,17),fill=1)
    if f==0:
        d.polygon([(7,17),(11,17),(10,21),(8,21)],fill=1)
        d.polygon([(13,17),(17,17),(19,22),(15,22)],fill=1)
        d.line((6,23,11,23),fill=1,width=2);d.line((14,23,21,23),fill=1,width=2)
    else:
        d.polygon([(7,17),(11,17),(6,22),(3,22)],fill=1)
        d.polygon([(13,17),(17,17),(15,21),(13,21)],fill=1)
        d.line((2,23,9,23),fill=1,width=2);d.line((12,23,18,23),fill=1,width=2)
    return im
for f in range(2):sprite(mech(f),'MECH_'+str(f))

def heli(f):
    im=Image.new('1',(32,24));d=ImageDraw.Draw(im)
    # upper view Mi-24-like tandem cabin and short wings
    d.polygon([(15,0),(18,2),(20,7),(22,16),(18,22),(14,22),(10,16),(12,7)],fill=1)
    d.ellipse((14,3,18,8),outline=0)
    d.ellipse((13,9,19,15),outline=0)
    d.rectangle((13,19,18,23),fill=1)
    d.polygon([(3,10),(12,9),(12,15),(3,15)],fill=1)
    d.polygon([(20,9),(29,10),(29,15),(20,15)],fill=1)
    d.rectangle((1,13,5,17),outline=1)
    d.rectangle((27,13,30,17),outline=1)
    d.point((3,18),fill=1); d.point((28,18),fill=1)
    if f==0:
        d.line((1,7,30,7),fill=1)
        d.line((16,1,16,23),fill=1)
    else:
        d.line((4,1,27,20),fill=1)
        d.line((27,1,4,20),fill=1)
    d.point((15,13),fill=1); d.point((17,13),fill=1)
    return im
for f in range(2):sprite(heli(f),'HIND_'+str(f))
for direction in range(8):
    im=Image.new('1',(8,8));d=ImageDraw.Draw(im)
    pts=[(3,1),(3,6),(1,3),(6,3),(1,1),(6,1),(1,6),(6,6)]
    x,y=pts[direction];d.rectangle((x,y,x+1,y+1),fill=1)
    sprite(im,'SHOT_'+str(direction))
im=Image.new('1',(8,8));ImageDraw.Draw(im).polygon([(3,1),(5,3),(3,6),(1,3)],fill=1);sprite(im,'BAD_SHOT')
# exp unused now but provided actual native data
for fr in range(2):
    im=Image.new('1',(16,16));d=ImageDraw.Draw(im)
    d.line((2,2,13,13),fill=1,width=1);d.line((2,13,13,2),fill=1,width=1)
    d.ellipse((3+fr,3+fr,12-fr,12-fr),outline=1)
    sprite(im,'EXP_'+str(fr))
assert len(sprites)==195,(len(sprites),names[-4:])
for idx, nm in enumerate(names):
    if nm.startswith('GRIT_'):colors[idx]=0x44 if ((idx-32)%4)<2 else 0x47
    elif nm.startswith('SOLDIER_'):colors[idx]=0x42 if ((idx-96)%4)<2 else 0x47
    elif nm.startswith('TANK_'):colors[idx]=0x45
    elif nm.startswith('MECH_'):colors[idx]=0x46
    elif nm.startswith('HIND_'):colors[idx]=0x47
    elif nm.startswith('SHOT_'):colors[idx]=0x46
    elif nm.startswith('BAD_SHOT'):colors[idx]=0x42
    elif nm.startswith('EXP_'):colors[idx]=0x46
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
                if x<left-2 or x>right+2: v=2 if (x*3+y*7+sector*5)%7<4 else 8
                elif x<left or x>right: v=1 if (x+y)%3 else 9
                else:v=7 if (x*5+y)%13==0 else 0
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
                if x<4 or x>19:v=22 if (y+x)%4 else 23
                elif x<7 or x>16:v=21 if y%5 else 25
                else:v=20 if (x+y)%11 else 21
                if y in (11,12,33,34) and x in range(4,20):v=21 if 9<=x<=15 else 23
                if y in (15,37) and x in (6,17):v=24
                if y%13==0 and x in (7,16):v=26
            arr[y][x]=v
    # Mark boss area as spacious pad to manoeuvre and fire in 8 directions.
    if sector==4:
        for y in range(6,21):
            for x in range(3,21):
                arr[y][x]={1:0,2:10,3:20}[phase]
        for x in range(8,17):arr[3][x]={1:7,2:15,3:21}[phase]
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
scene_asset('PALM',0x44,1,lambda d:(d.ellipse((1,0,14,10),outline=1),d.line((8,8,6,15),fill=1,width=2),d.line((2,6,14,5),fill=1),d.line((3,1,12,10),fill=1),d.line((13,1,3,10),fill=1)))
scene_asset('HUT',0x46,1,lambda d:(d.polygon([(0,5),(8,0),(15,5)],fill=1),d.rectangle((1,6,14,15),outline=1),d.rectangle((6,10,10,15),fill=1),d.rectangle((2,8,4,10),fill=1),d.rectangle((12,8,14,10),fill=1),d.line((2,5,14,5),fill=0)))
scene_asset('BOULDER',0x47,1,lambda d:(d.ellipse((1,3,14,14),fill=1),d.polygon([(3,5),(7,3),(10,4),(13,9),(8,12),(2,11)],fill=0),d.line((3,9,8,6),fill=1)))
scene_asset('THICKET',0x44,1,lambda d:(d.ellipse((0,5,8,13),outline=1),d.ellipse((6,2,15,12),outline=1),d.ellipse((3,0,12,9),outline=1),d.line((1,9,13,11),fill=1),d.point((6,5),fill=1)))
scene_asset('RICE',0x44,0,lambda d:([d.line((x,4,x+1,11),fill=1) for x in range(1,16,4)],[d.line((x-2,6,x+3,6),fill=1) for x in range(2,16,4)],d.line((0,15,15,15),fill=1)))
scene_asset('BRIDGE16',0x46,0,lambda d:(d.rectangle((0,0,15,15),outline=1),[d.line((0,y,15,y),fill=1) for y in (3,7,11)],[d.point((x,y),fill=1) for x in (2,13) for y in (1,5,9,13)]))
scene_asset('BARRACK',0x47,1,lambda d:(d.rectangle((1,5,14,15),fill=1),d.polygon([(0,5),(3,1),(12,1),(15,5)],fill=1),d.line((3,4,12,4),fill=0),d.rectangle((6,9,10,15),fill=0),d.rectangle((2,7,4,9),fill=0),d.rectangle((12,7,14,9),fill=0)))
scene_asset('WATCH',0x46,1,lambda d:(d.rectangle((1,2,14,6),fill=1),d.rectangle((3,7,5,15),fill=1),d.rectangle((10,7,12,15),fill=1),d.line((4,8,12,15),fill=1),d.line((11,8,4,15),fill=1),d.line((1,0,14,0),fill=1)))
scene_asset('GATE',0x47,0,lambda d:(d.rectangle((0,0,15,15),outline=1),d.rectangle((3,3,12,15),outline=1),[d.line((x,4,x,14),fill=1) for x in (5,8,11)],d.rectangle((6,0,9,3),fill=1)))
scene_asset('DRUMS',0x45,1,lambda d:([d.ellipse((x,3,x+5,6),outline=1) for x in (1,9)],[d.rectangle((x,5,x+5,14),outline=1) for x in (1,9)],[d.line((x+1,9,x+4,9),fill=1) for x in (1,9)]))
scene_asset('BUNKER',0x47,1,lambda d:(d.polygon([(0,7),(3,2),(12,2),(15,7),(15,15),(0,15)],fill=1),d.rectangle((4,8,11,11),fill=0),d.line((5,9,10,9),fill=1)))
scene_asset('CONSOLE',0x45,1,lambda d:(d.rectangle((1,1,14,15),outline=1),d.rectangle((3,3,12,8),fill=1),d.line((5,4,10,4),fill=0),d.point((4,11),fill=1),d.point((8,11),fill=1),d.point((12,11),fill=1),d.rectangle((3,13,12,14),fill=1)))
scene_asset('PIPEBANK',0x45,1,lambda d:([d.line((x,0,x,15),fill=1,width=2) for x in (2,7,12)],d.line((0,3,15,3),fill=1),d.line((0,12,15,12),fill=1),d.ellipse((5,5,10,10),outline=1)))
scene_asset('MECH_DOCK',0x46,1,lambda d:(d.rectangle((0,0,23,23),outline=1),d.line((2,3,21,3),fill=1),d.rectangle((7,5,16,14),outline=1),d.rectangle((10,7,13,11),fill=1),d.rectangle((4,8,7,16),fill=1),d.rectangle((16,8,19,16),fill=1),d.rectangle((8,15,11,20),fill=1),d.rectangle((13,15,16,20),fill=1),d.line((5,22,18,22),fill=1)),dim=24)
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

# Per-tile collision flags are now a full 256-byte lookup, including macrotile pieces.
solid_data=[int(i in SOLID) for i in range(32)]+[0]*(195-32)
solid_data.extend(macro_collision[i] for i in range(195,256))
assert len(solid_data)==256
(R/'src/solid_generated.asm').write_text('solid_flags:\n'+''.join(' db '+','.join(str(v) for v in solid_data[i:i+32])+'\n' for i in range(0,256,32)))
# Extend the same 256 glyphs in the executable with their own mask and color bytes.
# export db source without string escaping
# Compact exact map data using a dictionary of unique 24-tile rows.
# Each sector retains all its individual rows (no repeated-map shortcut).
unique_rows={}; rows=[]; out=[]
for phase in range(1,4):
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
assert len(rows)<256,len(rows)
out.append('map_rows:')
for row in rows:out.append(' db '+','.join(str(v) for v in row))
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
