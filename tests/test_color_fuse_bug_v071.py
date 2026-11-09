#!/usr/bin/env python3
"""Regression for the actual user's Fuse screenshot: V07 all attrs were 0 or 1.
Runs the real assembled Z80 instructions in the included PARTIAL VM.
"""
from collections import Counter
from harness import boot,invoke,tick
from mini_z80 import SYM

def assert_colors(v,phase,sector):
    front=bytes(v.m[0x5800:0x5b00]);shadow=bytes(v.m[0x7800:0x7b00])
    assert front == shadow, f'front/shadow attributes diverge phase {phase} sector {sector}'
    colors=set(front)
    assert colors.difference({0,1}), f'FATAL blue-on-black V07 regression phase {phase} sector {sector}'
    assert 0x45 in colors and 0x46 in colors, f'HUD cyan/yellow lost: {sorted(colors)}'
    assert front[24]==0x46, f'HUD first cell should be bright yellow, got {front[24]:02x}'
    print(f'PASS colors phase={phase} sector={sector}: {dict(Counter(front))}')

def main():
    v=boot()
    assert_colors(v,1,1)
    # Check mark_dirty preserves A in BOTH code paths: ordinary and forced full redraw.
    for full in (0,1):
        v.set('full_redraw', full)
        for a in (0x46,0x45,0x06):
            v.r[7]=a; v.r[2]=6; v.r[3]=7
            invoke(v,'mark_dirty')
            assert v.r[7]==a, f'mark_dirty destroyed A={a:02x} when full_redraw={full}'
    v.set('full_redraw',0)
    for p in range(1,4):
        for sec in (1,2,3,4):
            v.set('phase',p);v.set('sector',sec)
            invoke(v,'scene_init')
            assert_colors(v,p,sec)
    v.set('phase',1);v.set('sector',1);invoke(v,'scene_init')
    for k in (['O'],[],['Q'],['P'],['SPACE'],[],['Q','P'],[]):
        tick(v,k,limit=700000)
        assert_colors(v,1,1)
    print('ALL V07.1 ATTRIBUTES REGRESSIONS PASSED (not a Fuse execution)')
if __name__=='__main__': main()
