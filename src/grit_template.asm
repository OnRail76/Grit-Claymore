; GRIT CLAYMORE - motor v0.7.1 - tiles dibujados / scroll vertical / 8 direcciones
; ZX Spectrum 48K, Z80A. Plain code at 0x8000. BASIC is only a tape loader.
; Scrolling top-down game. Q/A/O/P incl diagonals, SPACE fires in last direction.
; MIT licence, (c) 2026 Tony C. Ware. See README and LIMITATIONS.
org 0x8000
entry:
 xor a
 out (0xfe),a
 di
 ld sp,0x7ff0
 ei
 call title_screen
main_new_game:
 ld a,1
 ld (phase),a
 ld (sector),a
 ld a,3
 ld (lives),a
 ld a,4
 ld (health),a
 xor a
 ld (kills),a
 ld (frame),a
 ld (state),a
 call show_phase_card
 call scene_init
main_loop:
 xor a
 out (0xfe),a
 halt
 halt                   ; target 25 logic ticks/s (PAL interrupts)
 ld a,(state)
 or a
 jp nz,handle_end
 call erase_dynamic
 call animate_tiles
 call update_fx
 call read_controls
 call update_player_bullet
 call update_soldiers
 call update_special
 call update_special_shots
 call handle_collisions
 ld a,(state)
 or a
 jp nz,handle_end
 call draw_dynamic
 ld a,(full_redraw)
 or a
 jp z,main_present_dirty
 xor a
 ld (full_redraw),a
 call present_full
 jp main_present_done
main_present_dirty:
 call present_dirty
main_present_done:
 ld a,(frame)
 inc a
 ld (frame),a
 jp main_loop
handle_end:
 cp 1
 jp z,win_screen
 jp lose_screen

; --- title & screens --------------------------------------------------------
title_screen:
 xor a
 out (0xfe),a
 ld hl,title_rle
 ld de,0x4000
 call unpack_title
 call space_release
 call space_press
 ret
; PackBits-like pixel-art title decompression. 0=end, 1..127 literal,
; 128..255 repeat lengths 1..128. Exactly 6912 bytes written to video RAM.
unpack_title:
 ld a,(hl)
 inc hl
 or a
 ret z
 bit 7,a
 jp nz,title_rle_run
 ld c,a
 ld b,0
 ldir
 jp unpack_title
title_rle_run:
 and 127
 inc a
 ld b,a
 ld a,(hl)
 inc hl
title_rle_repeat:
 ld (de),a
 inc de
 djnz title_rle_repeat
 jp unpack_title

win_screen:
 xor a
 out (0xfe),a
 ld hl,victory_rle
 ld de,0x4000
 call unpack_title
 ; Mandatory 3 seconds at 50 PAL HALTs per second. Space is ignored.
 ld b,150
win_hold:
 halt
 djnz win_hold
 ; Require a release after the hold and a fresh SPACE press.
 call space_release
 call space_press
 call title_screen
 jp main_new_game
lose_screen:
 xor a
 out (0xfe),a
 ; Large ZX-native GAME OVER for 3 seconds, then return to TITLE (not phase 1).
 ld hl,gameover_rle
 ld de,0x4000
 call unpack_title
 ld b,150                  ; 50 Hz PAL, 3-second hold
lose_hold:
 halt
 djnz lose_hold
 call title_screen
 jp main_new_game
space_release:
 ld bc,0x7ffe
sr_wait:
 halt
 in a,(c)
 bit 0,a
 jp z,sr_wait
 ret
space_press:
 ld bc,0x7ffe
sp_wait:
 halt
 in a,(c)
 bit 0,a
 jp nz,sp_wait
 ret

; --- 2-second pre-stage title cards, text rendered from the 8x8 arcade font ---
; Runs ONCE per phase, not every individual scrolling sector.
show_phase_card:
 xor a
 out (0xfe),a
 call screen_clear
 ld a,(phase)
 cp 1
 jp z,spc_jungle
 cp 2
 jp z,spc_lab
 ld hl,spc_3a
 ld d,10
 ld e,13
 call print_text
 ld hl,spc_3b
 ld d,13
 ld e,12
 call print_text
 ld a,0x45
 jp spc_finish
spc_jungle:
 ld hl,spc_1a
 ld d,10
 ld e,13
 call print_text
 ld hl,spc_1b
 ld d,13
 ld e,11
 call print_text
 ld a,0x44
 jp spc_finish
spc_lab:
 ld hl,spc_2a
 ld d,10
 ld e,13
 call print_text
 ld hl,spc_2b
 ld d,13
 ld e,9
 call print_text
 ld a,0x46
spc_finish:
 ; Colour card across all 768 native ZX attribute cells; bitmap stays still.
 ld hl,0x7800
 ld de,0x7801
 ld bc,767
 ld (hl),a
 ldir
 call present_full
 ld b,100            ; 100 PAL 50Hz interrupts = 2 seconds.
spc_hold:
 halt
 djnz spc_hold
 ret

; --- reset and screen construction -----------------------------------------
scene_init:
 call screen_clear
 xor a
 ld (bullet_on),a
 ld (bullet_power),a
 ld (cool),a
 ld (move_cool),a
 ld (tank_mode),a
 ld (invuln),a
 ld (boss_dir),a
 ld (tank_available),a
 ld (mecha_remaining),a
 ld (boss_hp),a
 ld (fx_ttl),a
 ld (ration_available),a
 ld (player_moving),a
 ld (full_redraw),a
 ld hl,special_shots
 ld de,special_shots+1
 ld bc,29
 ld (hl),a
 ldir
 ld hl,enemies
 ld de,enemies+1
 ld bc,35
 ld (hl),0
 ldir
 ld a,11
 ld (player_x),a
 ld a,20
 ld (player_y),a
 xor a
 ld (face),a
 ld a,(sector)
 cp 4
 jp nz,init_not_boss
 ld a,(phase)
 cp 1
 jp nz,boss_init2
 ld a,12
 jp boss_init_hp
boss_init2:
 cp 2
 jp nz,boss_init3
 ld a,18
 jp boss_init_hp
boss_init3:
 ld a,24
boss_init_hp:
 ld (boss_hp),a
 ld a,14
 ld (boss_x),a
init_not_boss:
 ld a,(phase)
 cp 3
 jp z,init_no_tank
 ld a,(sector)
 cp 3
 jp z,init_tank
 cp 2
 jp nz,init_no_tank
 ld a,(phase)
 cp 2
 jp nz,init_no_tank
init_tank:
 ld a,1
 ld (tank_available),a
init_no_tank:
 ld a,24
 ld (camera_top),a
 ld a,13
 ld (tank_y),a
 ld a,(sector)
 cp 4
 jp nz,scene_camera_ready
 xor a
 ld (camera_top),a
scene_camera_ready:
 call select_level_map
 call generate_map
 call draw_panel_base
 ld a,(phase)
 cp 3
 jp nz,scene_no_mechas
 ld a,(sector)
 cp 4
 jp z,scene_no_mechas
 call spawn_mecha_group
scene_no_mechas:
 ld a,(sector)
 cp 2
 jp nz,scene_ration_done
 ld a,1
 ld (ration_available),a
 ld a,13
 ld (ration_y),a
scene_ration_done:
 ld a,(phase)
 cp 3
 jp z,scene_no_soldier_setup
 ld a,(sector)
 cp 4
 jp z,scene_no_soldier_setup
 call spawn_soldier
 call spawn_soldier
scene_no_soldier_setup:
 call draw_hud
 call draw_dynamic
 call present_full
 ret

screen_clear:
 ; Shadow video: complete 6912-byte Spectrum screen at 0x6000..0x7AFF.
 ; Shadow video uses 0x6000..0x7AFF; Z80 stack is in free RAM 0x7B00..0x7FFF.
 xor a
 ld hl,0x6000
 ld de,0x6001
 ld bc,6143
 ld (hl),a
 ldir
 ld a,7
 ld hl,0x7800
 ld de,0x7801
 ld bc,767
 ld (hl),a
 ldir
 call clear_dirty
 ret

; Dirty cells are composited in shadow RAM; the visible screen never sees
; an erase-and-wait gap between separate enemy updates.
clear_dirty:
 xor a
 ld (dirty_count),a
 ld hl,dirty_flags
 ld de,dirty_flags+1
 ld bc,767
 ld (hl),a
 ldir
 ret

; Deduplicated dirty queue: up to 240 tile coordinates (D=row, E=column).
; Overflow falls back to a full copy safely, without corrupting the queue.
mark_dirty:
 ; CRITICAL V07.1 FIX: A is the INK/PAPER attribute passed to the blitter.
 ; Saving AF AFTER testing full_redraw replaced every attribute with 0 or 1!
 ; Preserve AF *before* touching A, including on the early exit branch.
 push af
 ld a,(full_redraw)
 or a
 jp z,md_continue
 pop af
 ret
md_continue:
 push bc
 push de
 push hl
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld c,e
 ld b,0
 add hl,bc
 ld bc,dirty_flags
 add hl,bc
 ld a,(hl)
 or a
 jp nz,md_done
 ld (hl),1
 ld a,(dirty_count)
 cp 240
 jp nc,md_overflow
 ld c,a
 ld b,0
 ld hl,dirty_pairs
 add hl,bc
 add hl,bc
 ld (hl),d
 inc hl
 ld (hl),e
 ld a,(dirty_count)
 inc a
 ld (dirty_count),a
 jp md_done
md_overflow:
 ld a,1
 ld (full_redraw),a
md_done:
 pop hl
 pop de
 pop bc
 pop af
 ret

clear_dirty_one:
 push bc
 push de
 push hl
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld c,e
 ld b,0
 add hl,bc
 ld bc,dirty_flags
 add hl,bc
 ld (hl),0
 pop hl
 pop de
 pop bc
 ret

; Called ONCE when an arena enters or the 8px viewport strip scrolls.
; Full screen copy is necessarily costlier, but ordinary animation uses only
; dirty 8x8 cells instead of showing the blanked background to the ULA.
present_full:
 ld hl,0x6000
 ld de,0x4000
 ld bc,6144
 ldir
 ld hl,0x7800
 ld de,0x5800
 ld bc,768
 ldir
 xor a
 ld (full_redraw),a
 jp clear_dirty

; Sparse presentation, ONLY the tiles changed by actor movement or the HUD.
; Ordinary frames never scan all 768 dirty flags or copy a blanked actor.
present_dirty:
 ld a,(dirty_count)
 or a
 ret z
 ld b,a
 ld hl,dirty_pairs
pd_next:
 push bc
 ld d,(hl)
 inc hl
 ld e,(hl)
 inc hl
 push hl
 call clear_dirty_one
 call present_cell
 pop hl
 pop bc
 djnz pd_next
 xor a
 ld (dirty_count),a
 ret

; D = tile row E = column. Copy 8 actual pixel bytes AND its attribute.
present_cell:
 push de
 call playfield_addr
 ld a,h
 xor 0x20
 ld d,a
 ld e,l
 ld b,8
pc_pix:
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 djnz pc_pix
 pop de
 call attribute_addr
 ld a,h
 xor 0x20
 ld d,a
 ld e,l
 ld a,(hl)
 ld (de),a
 ret

; --- V074 environmental tile animation (two frames, 1-2-1-2) ---
; Only 8-pixel tiles in the *current* 24x24 playfield are repainted.
; The HUD never enters this loop. Sprites were erased in SHADOW RAM first.
; XOR masks toggle the same 8-byte glyph between two frames: very low RAM.
animate_tiles:
 ld a,(frame)
 and 7
 cp 2
 ret nc                  ; only two 25Hz updates out of every eight
 or a
 jp nz,anim_lower_half
 ; First half: switch global 8-byte glyphs, update top twelve tile rows.
 ld hl,glyphs+32          ; #4 WATER
 ld de,anim_water_xor
 call anim_xor_glyph
 ld hl,glyphs+128         ; #16 ANTENNA / base light
 ld de,anim_beacon_xor
 call anim_xor_glyph
 ld hl,glyphs+192         ; #24 TERMINAL / sci-fi display
 ld de,anim_terminal_xor
 call anim_xor_glyph
 ld hl,glyphs+208         ; #26 LED / pulsing light
 ld de,anim_led_xor
 call anim_xor_glyph
 ld d,0
 ld a,12
 ld (anim_stop_row),a
 jp anim_row
anim_lower_half:
 ; Complete lower 12 rows on the next tick, distributing the draw cost.
 ld d,12
 ld a,24
 ld (anim_stop_row),a
anim_row:
 ld e,0
anim_col:
 call map_address
 ld a,(hl)
 cp 4
 jp z,anim_repaint
 cp 16
 jp z,anim_repaint
 cp 24
 jp z,anim_repaint
 cp 26
 jp nz,anim_skip
anim_repaint:
 call paint_tile
anim_skip:
 inc e
 ld a,e
 cp 24
 jp nz,anim_col
 inc d
 ld a,(anim_stop_row)
 cp d
 jp nz,anim_row
 ret
anim_xor_glyph:
 ld b,8
anim_xor_byte:
 ld a,(de)
 ld c,a
 ld a,(hl)
 xor c
 ld (hl),a
 inc hl
 inc de
 djnz anim_xor_byte
 ret

; Twelve hand-authored stage maps; 48x24 tile rows for scrolling,
; boss arenas 24x24. A room is scrollable for 24 new 8px rows.
select_level_map:
 ld a,(phase)
 dec a
 add a,a
 add a,a
 ld b,a
 ld a,(sector)
 dec a
 add a,b
 add a,a
 ld l,a
 ld h,0
 ld bc,map_pointers
 add hl,bc
 ld e,(hl)
 inc hl
 ld d,(hl)
 ex de,hl
 ld (level_ptr),hl
 ret

; Input D=onscreen tile row, E=column (0..23), A=tile ID;
; preserves D/E. Each map points to its 24/48 byte row-index table;
; the unique 24-byte rows are shared in map_rows (lossless compression).
read_map_rom:
 push bc
 push de
 push hl
 ld a,(camera_top)
 add a,d
 ld l,a
 ld h,0
 ld bc,(level_ptr)
 add hl,bc
 ld a,(hl)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld b,h
 ld c,l
 add hl,hl
 add hl,bc
 ld bc,map_rows
 add hl,bc
 ld c,e
 ld b,0
 add hl,bc
 ld a,(hl)
 pop hl
 pop de
 pop bc
 ret

generate_map:
 ld d,0
render_map_row:
 ld e,0
render_map_col:
 call read_map_rom
 push af
 call map_address
 pop af
 ld (hl),a
 call paint_tile
 inc e
 ld a,e
 cp 24
 jp nz,render_map_col
 inc d
 ld a,d
 cp 24
 jp nz,render_map_row
 ret

; Real camera scroll: shift 192x192 playfield bitmap 8 px down,
; move 192 attribute bytes and 24x24 collision tilemap, paint new top strip.
; HUD columns 24..31 are never copied or overwritten.
scroll_scene:
 ld a,1
 ld (full_redraw),a
 ld a,(camera_top)
 or a
 ret z
 dec a
 ld (camera_top),a
 call scroll_bitmap_down
 ld hl,map_data+735
 ld de,map_data+767
 ld bc,736
 lddr
 ld d,0
 ld e,0
scroll_top_loop:
 call read_map_rom
 push af
 call map_address
 pop af
 ld (hl),a
 call paint_tile
 inc e
 ld a,e
 cp 24
 jp nz,scroll_top_loop
 ; Shift actors and bullets to match scrolled terrain.
 ld a,(bullet_on)
 or a
 jp z,scroll_bullet_done
 ld a,(bullet_y)
 inc a
 ld (bullet_y),a
 cp 23
 jp c,scroll_bullet_done
 xor a
 ld (bullet_on),a
scroll_bullet_done:
 ld ix,enemies
 ld b,3
scroll_actor_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,scroll_actor_shot
 inc (ix+2)
 ld a,(ix+2)
 cp 21
 jp c,scroll_actor_shot
 xor a
 ld (ix+0),a
scroll_actor_shot:
 ld a,(ix+3)
 or a
 jp z,scroll_actor_next
 inc (ix+5)
 ld a,(ix+5)
 cp 23
 jp c,scroll_actor_next
 xor a
 ld (ix+3),a
scroll_actor_next:
 ld de,12
 add ix,de
 pop bc
 djnz scroll_actor_loop
 ld a,(ration_available)
 or a
 jp z,scroll_no_ration
 ld a,(ration_y)
 inc a
 ld (ration_y),a
 cp 22
 jp c,scroll_no_ration
 xor a
 ld (ration_available),a
scroll_no_ration:
 ; Special bullets scroll with the visible world, not the fixed HUD.
 ld hl,special_shots
 ld b,6
sc_shot_loop:
 ld a,(hl)
 or a
 jp z,sc_shot_skip
 push hl
 inc hl
 inc hl
 inc (hl)
 ld a,(hl)
 cp 23
 jp c,sc_shot_alive
 pop hl
 xor a
 ld (hl),a
 jp sc_shot_skip
sc_shot_alive:
 pop hl
sc_shot_skip:
 ld de,5
 add hl,de
 djnz sc_shot_loop
 ld a,(tank_available)
 or a
 ret z
 ld a,(tank_y)
 inc a
 ld (tank_y),a
 cp 21
 ret c
 xor a
 ld (tank_available),a
 ret

scroll_bitmap_down:
 ld a,23
scroll_bitmap_row:
 ld (scroll_row),a
 ld d,a
 ld e,0
 call playfield_addr
 ld (scroll_dst),hl
 dec d
 call playfield_addr
 ld (scroll_src),hl
 ld b,8
scroll_scanline:
 push bc
 ld hl,(scroll_src)
 ld de,(scroll_dst)
 ld bc,24
 ldir
 ld hl,(scroll_src)
 inc h
 ld (scroll_src),hl
 ld hl,(scroll_dst)
 inc h
 ld (scroll_dst),hl
 pop bc
 djnz scroll_scanline
 ld a,(scroll_row)
 ld d,a
 ld e,0
 call attribute_addr
 ld (scroll_dst),hl
 dec d
 call attribute_addr
 ld de,(scroll_dst)
 ld bc,24
 ldir
 ld a,(scroll_row)
 dec a
 jp nz,scroll_bitmap_row
 ret
; D/E are Spectrum 8px char coordinates, HL points to top bitmap line
playfield_addr:
 ld a,d
 and 24
 add a,0x60
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ret
attribute_addr:
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,0x7800
 add hl,bc
 ld c,e
 ld b,0
 add hl,bc
 ret


; --- independent 8-column HUD at x=24..31, full height ---------------------
; Full 8x24 panel is drawn ONCE on entering a sector, never scrolled.
; Changes draw only 2-digit numbers or a few labels. No gameplay can reach x>=24.
; The palette is applied per row to monochrome font on PAPER 0.
draw_panel_base:
 ; 64x192px bitmap HUD designed as genuine ZX Spectrum cells (192 individual 8x8 tiles).
 ; Distinct tile glyph bank + per-cell attribute: no faux ASCII frame, no ROM charset.
 ; Render directly to SHADOW, which is copied once to visible VRAM during scene_init.
 ld ix,hud_panel_map
 ld d,0
dpb_row:
 ld e,24
dpb_cell:
 ld a,(ix+0)                 ; unique 8x8 bitmap tile ID
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,hud_panel_glyphs
 add hl,bc
 ld a,(ix+1)                 ; ZX attribute PAPER 0, INK + BRIGHT
 call blit_cell
 inc ix
 inc ix
 inc e
 ld a,e
 cp 32
 jp nz,dpb_cell
 inc d
 ld a,d
 cp 24
 jp nz,dpb_row
 ret

; Dynamic HUD: only numerals and energy cells are redrawn.
draw_hud:
 ld a,0x47                   ; white numbers for PUNTOS
 ld (hud_color),a
 ; PUNTOS: six digits = 00 + kills (two digits) + 00, i.e. 100 points per kill.
 ld a,0
 ld d,5
 ld e,25
 call put_two_digit
 ld a,(kills)
 ld d,5
 ld e,27
 call put_two_digit
 xor a
 ld d,5
 ld e,29
 call put_two_digit
 ; VIDAS: 3 smileys exactly centered in the 64px wide HUD.
 ; Smileys span two cells each, with 4 blank pixels on both outer edges.
 ; The complete group is 48px centered at x=8..55 (screen cols 25..30).
 ld a,(lives)
 ld c,a
 ld b,3
 ld d,10
 ld e,25
hud_life_loop:
 push bc
 ld a,c
 or a
 jp z,hud_life_empty
 ld hl,hud_smiley_left
 ld a,0x46
 jp hud_life_draw
hud_life_empty:
 ld hl,hud_smiley_empty
 ld a,0x47
hud_life_draw:
 call blit_cell
 inc e
 ld a,c
 or a
 jp z,hud_life_right_empty
 ld hl,hud_smiley_right
 ld a,0x46
 jp hud_life_right_draw
hud_life_right_empty:
 ld hl,hud_smiley_empty
 ld a,0x47
hud_life_right_draw:
 call blit_cell
 inc e
 pop bc
 ld a,c
 or a
 jp z,hud_life_keep
 dec c
hud_life_keep:
 djnz hud_life_loop
 ; PODER: four chunky battery cells.
 ld a,(health)
 ld c,a
 ld b,4
 ld d,16
 ld e,26
hud_bar_loop:
 push bc
 ld a,c
 or a
 jp z,hud_bar_empty_draw
 ld hl,hud_bar_full
 ld a,0x44
 jp hud_bar_draw
hud_bar_empty_draw:
 ld hl,hud_bar_empty
 ld a,0x42
hud_bar_draw:
 call blit_cell
 inc e
 pop bc
 ld a,c
 or a
 jp z,hud_bar_keep
 dec c
hud_bar_keep:
 djnz hud_bar_loop
 ; TANQUE: two armour cells, same style as PODER.
 ld a,(tank_mode)
 or a
 jp z,hud_tank_none
 ld a,(armor)
 ld c,a
 jp hud_tank_setup
hud_tank_none:
 xor a
 ld c,a
hud_tank_setup:
 ld b,2
 ld d,22
 ld e,27
hud_tank_loop:
 push bc
 ld a,c
 or a
 jp z,hud_tank_empty
 ld hl,hud_bar_full
 ld a,0x46
 jp hud_tank_draw
hud_tank_empty:
 ld hl,hud_bar_empty
 ld a,0x42
hud_tank_draw:
 call blit_cell
 inc e
 pop bc
 ld a,c
 or a
 jp z,hud_tank_keep
 dec c
hud_tank_keep:
 djnz hud_tank_loop
 ret

put_digit:
 add a,48
 jp paint_ascii
put_two_digit:
 ld b,0
ptd_loop:
 cp 10
 jp c,ptd_next
 sub 10
 inc b
 jp ptd_loop
ptd_next:
 push af
 ld a,b
 call put_digit
 inc e
 pop af
 call put_digit
 ret


; --- player and keyboard ----------------------------------------------------
read_controls:
 xor a
 ld (player_moving),a
 ld a,(invuln)
 or a
 jp z,controls_no_inv
 dec a
 ld (invuln),a
controls_no_inv:
 ld a,(move_cool)
 or a
 jp z,controls_ready
 dec a
 ld (move_cool),a
 jp controls_fire
controls_ready:
 ld a,(player_x)
 ld (target_x),a
 ld a,(player_y)
 ld (target_y),a
 xor a
 ld (axis_x),a
 ld (axis_y),a
 ; Both keyboard axes can be held simultaneously. Up-left = Q+O etc.
 ld bc,0xfbfe
 in a,(c)
 bit 0,a
 jp nz,controls_a
 ld a,1
 ld (axis_y),a
 ld a,(target_y)
 dec a
 ld (target_y),a
 jp controls_horizontal
controls_a:
 ld bc,0xfdfe
 in a,(c)
 bit 0,a
 jp nz,controls_horizontal
 ld a,2
 ld (axis_y),a
 ld a,(target_y)
 inc a
 ld (target_y),a
controls_horizontal:
 ld bc,0xdffe
 in a,(c)
 bit 1,a
 jp nz,controls_p
 ld a,1
 ld (axis_x),a
 ld a,(target_x)
 dec a
 ld (target_x),a
 jp controls_direction
controls_p:
 bit 0,a
 jp nz,controls_direction
 ld a,2
 ld (axis_x),a
 ld a,(target_x)
 inc a
 ld (target_x),a
controls_direction:
 ld a,(tank_mode)
 or a
 jp z,controls_foot_dir
 ; Tank is strictly four-directional: simultaneous vertical+horizontal
 ; keys keep vertical priority and cannot move the chassis diagonally.
 ld a,(axis_y)
 or a
 jp z,tank_horizontal_input
 ld a,(player_x)
 ld (target_x),a
tank_horizontal_input:
 ld a,(axis_y)
 cp 1
 jp z,tank_face_up
 cp 2
 jp z,tank_face_down
 ld a,(axis_x)
 cp 1
 jp z,tank_face_left
 cp 2
 jp z,tank_face_right
 jp controls_fire
tank_face_up:
 xor a
 jp face_set
tank_face_down:
 ld a,1
 jp face_set
tank_face_left:
 ld a,2
 jp face_set
tank_face_right:
 ld a,3
 jp face_set
controls_foot_dir:
 ld a,(axis_y)
 or a
 jp z,face_horizontal
 cp 1
 jp nz,face_down
 ld a,(axis_x)
 cp 1
 jp z,face_up_left
 cp 2
 jp z,face_up_right
 xor a
 jp face_set
face_up_left:
 ld a,4
 jp face_set
face_up_right:
 ld a,5
 jp face_set
face_down:
 ld a,(axis_x)
 cp 1
 jp z,face_down_left
 cp 2
 jp z,face_down_right
 ld a,1
 jp face_set
face_down_left:
 ld a,6
 jp face_set
face_down_right:
 ld a,7
 jp face_set
face_horizontal:
 ld a,(axis_x)
 cp 1
 jp z,face_left
 cp 2
 jp nz,controls_fire
 ld a,3
 jp face_set
face_left:
 ld a,2
face_set:
 ld (face),a
controls_movement:
 ld a,(target_x)
 cp 1
 jp c,controls_fire
 cp 22
 jp nc,controls_fire
 ld a,(target_y)
 cp 10
 jp nc,controls_y_ok
 ld a,(axis_y)
 cp 1
 jp nz,controls_y_ok
 ld a,(sector)
 cp 4
 jp z,controls_y_ok
 ld a,(camera_top)
 or a
 jp z,controls_y_ok
 ; Do not allow the phase-3 mechas to scroll offscreen un-killed.
 ld a,(phase)
 cp 3
 jp nz,controls_scroll_now
 ld a,(mecha_remaining)
 or a
 jp nz,controls_y_ok
controls_scroll_now:
 ld a,1
 ld (player_moving),a
 call scroll_scene
 jp controls_fire
controls_y_ok:
 ld a,(target_y)
 cp 3
 jp nc,controls_y_below
 ld a,(sector)
 cp 4
 jp z,controls_fire
 ld a,(phase)
 cp 3
 jp nz,control_next_screen
 ld a,(mecha_remaining)
 or a
 jp nz,controls_fire
control_next_screen:
 call next_sector
 jp controls_fire
controls_y_below:
 cp 21
 jp nc,controls_fire
 ld a,(target_y)
 ld d,a
 ld a,(target_x)
 ld e,a
 call tile_solid
 or a
 jp nz,controls_fire
 inc e
 call tile_solid
 or a
 jp nz,controls_fire
 inc d
 call tile_solid
 or a
 jp nz,controls_fire
 dec e
 call tile_solid
 or a
 jp nz,controls_fire
 ld a,(target_x)
 ld (player_x),a
 ld a,(target_y)
 ld (player_y),a
 ld a,1
 ld (player_moving),a
 ld a,(tank_mode)
 or a
 jp z,ctrl_speed_foot
 ld a,2
 ld (move_cool),a
 jp controls_check_pickup
ctrl_speed_foot:
 ld a,1
 ld (move_cool),a
controls_check_pickup:
 call check_ration
 ld a,(tank_available)
 or a
 jp z,controls_fire
 ld a,(player_y)
 ld b,a
 ld a,(tank_y)
 cp b
 jp nz,controls_fire
 ld a,(player_x)
 cp 14
 jp c,controls_fire
 cp 16
 jp nc,controls_fire
 xor a
 ld (tank_available),a
 ld a,1
 ld (tank_mode),a
 ld a,2
 ld (armor),a
 call draw_hud
 call sound_pickup
controls_fire:
 ld a,(cool)
 or a
 jp z,controls_check_fire
 dec a
 ld (cool),a
controls_check_fire:
 ld bc,0x7ffe
 in a,(c)
 bit 0,a
 ret nz
 ld a,(bullet_on)
 or a
 ret nz
 ld a,(cool)
 or a
 ret nz
 ld a,(tank_mode)
 or a
 jp z,fire_foot
 ld a,5
 jp fire_set_cool
fire_foot:
 ld a,3
fire_set_cool:
 ld (cool),a
 ld a,1
 ld (bullet_on),a
 ld a,(tank_mode)
 ld (bullet_power),a
 ld a,(face)
 ld (bullet_dir),a
 ld a,(player_x)
 inc a
 ld (bullet_x),a
 ld a,(player_y)
 inc a
 ld (bullet_y),a
 call sound_fire
 ret


; A single visible RACION tin restores up to 2 energy, maximum 4.
check_ration:
 ld a,(ration_available)
 or a
 ret z
 ld a,(tank_mode)
 or a
 ret nz
 ld a,(player_y)
 ld b,a
 ld a,(ration_y)
 cp b
 ret nz
 ld a,(player_x)
 cp 11
 ret c
 cp 13
 ret nc
 xor a
 ld (ration_available),a
 ld a,(health)
 add a,2
 cp 5
 jp c,ration_store
 ld a,4
ration_store:
 ld (health),a
 call draw_hud
 call sound_pickup
 ret

next_sector:
 ld a,(sector)
 inc a
 ld (sector),a
 call scene_init
 ret

; --- bullets and soldiers --------------------------------------------------
update_player_bullet:
 ld a,(bullet_on)
 or a
 ret z
 ; 8 directional shots; 4 diagonal velocities change both axes per tick.
 ld a,(bullet_dir)
 cp 0
 jp z,pb_up
 cp 1
 jp z,pb_down
 cp 2
 jp z,pb_left
 cp 3
 jp z,pb_right
 cp 4
 jp z,pb_up_left
 cp 5
 jp z,pb_up_right
 cp 6
 jp z,pb_down_left
 jp pb_down_right
pb_up:
 ld a,(bullet_y)
 dec a
 ld (bullet_y),a
 jp pb_test
pb_down:
 ld a,(bullet_y)
 inc a
 ld (bullet_y),a
 jp pb_test
pb_left:
 ld a,(bullet_x)
 dec a
 ld (bullet_x),a
 jp pb_test
pb_right:
 ld a,(bullet_x)
 inc a
 ld (bullet_x),a
 jp pb_test
pb_up_left:
 ld a,(bullet_y)
 dec a
 ld (bullet_y),a
 ld a,(bullet_x)
 dec a
 ld (bullet_x),a
 jp pb_test
pb_up_right:
 ld a,(bullet_y)
 dec a
 ld (bullet_y),a
 ld a,(bullet_x)
 inc a
 ld (bullet_x),a
 jp pb_test
pb_down_left:
 ld a,(bullet_y)
 inc a
 ld (bullet_y),a
 ld a,(bullet_x)
 dec a
 ld (bullet_x),a
 jp pb_test
pb_down_right:
 ld a,(bullet_y)
 inc a
 ld (bullet_y),a
 ld a,(bullet_x)
 inc a
 ld (bullet_x),a
pb_test:
 ld a,(bullet_x)
 cp 1
 jp c,pb_remove
 cp 23
 jp nc,pb_remove
 ld a,(bullet_y)
 cp 2
 jp c,pb_remove
 cp 23
 jp nc,pb_remove
 ld d,a
 ld a,(bullet_x)
 ld e,a
 call tile_solid
 or a
 jp z,pb_terrain_ok
 ld a,(bullet_power)
 or a
 jp z,pb_remove       ; Grit's rifle still stops at any solid obstacle
pb_terrain_ok:
 ; Tank shells pierce ALL terrain: walls, huts, bridges, trunks, etc.

 ; hit Hind, special mecha, then conventional soldiers
 ld a,(sector)
 cp 4
 jp nz,pb_mecha
 ld a,(bullet_y)
 cp 4
 ret c
 cp 7
 ret nc
 ld a,(boss_x)
 ld b,a
 ld a,(bullet_x)
 cp b
 ret c
 ld c,a
 ld a,b
 add a,4
 ld b,a
 ld a,c
 cp b
 ret nc
 ld a,(boss_hp)
 or a
 ret z
 dec a
 ld (boss_hp),a
 xor a
 ld (bullet_on),a
 call sound_hit
 ld a,(boss_hp)
 or a
 jp z,boss_defeated
 call draw_hud
 ret
pb_mecha:
 ld a,(phase)
 cp 3
 jp nz,pb_soldiers
 ld a,(sector)
 cp 4
 jp z,pb_soldiers
 ld ix,enemies
 ld b,3
pb_mecha_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,pb_mecha_next
 ld a,(bullet_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp z,pb_mecha_x_yes
 inc a
 cp c
 jp z,pb_mecha_x_yes
 inc a
 cp c
 jp nz,pb_mecha_next
pb_mecha_x_yes:
 ld a,(bullet_y)
 ld c,a
 ld a,(ix+2)
 cp c
 jp z,pb_mecha_hit
 inc a
 cp c
 jp z,pb_mecha_hit
 inc a
 cp c
 jp nz,pb_mecha_next
pb_mecha_hit:
 xor a
 ld (bullet_on),a
 ld a,(ix+6)
 dec a
 ld (ix+6),a
 jp nz,pb_mecha_damaged
 xor a
 ld (ix+0),a
 call spawn_fx
 ld a,(mecha_remaining)
 dec a
 ld (mecha_remaining),a
 ld a,(kills)
 inc a
 cp 100
 jp c,pb_mecha_score_ok
 xor a
pb_mecha_score_ok:
 ld (kills),a
 call draw_hud
 call sound_mecha_down
 pop bc
 ret
pb_mecha_damaged:
 call sound_hit
 pop bc
 ret
pb_mecha_next:
 ld de,12
 add ix,de
 pop bc
 djnz pb_mecha_loop
 ret
pb_soldiers:
 ld ix,enemies
 ld b,3
pbs_loop:
 ld a,(ix+0)
 or a
 jp z,pbs_next
 ld a,(bullet_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp z,pbs_check_y
 inc a
 cp c
 jp nz,pbs_next
pbs_check_y:
 ld a,(bullet_y)
 ld c,a
 ld a,(ix+2)
 cp c
 jp z,pbs_hit
 inc a
 cp c
 jp nz,pbs_next
pbs_hit:
 call spawn_fx
 xor a
 ld (ix+0),a
 ld a,(bullet_power)
 or a
 jp nz,pbs_shell_keeps_flying
 xor a
 ld (bullet_on),a
pbs_shell_keeps_flying:
 ld a,(kills)
 inc a
 cp 100
 jp c,pbs_score_ok
 xor a
pbs_score_ok:
 ld (kills),a
 call sound_hit
 call draw_hud
 ret
pbs_next:
 ld de,12
 add ix,de
 djnz pbs_loop
 ret
pb_remove:
 xor a
 ld (bullet_on),a
 ret

; Fixed / patrol / assault soldiers. Only one third of soldiers chase.
; IX+8 role (0 fixed, 1 patrol, 2 assault); IX+9 reload;
; IX+10 reaction warning; IX+11 patrol anchor.
update_soldiers:
 ld a,(phase)
 cp 3
 jp z,update_mechas
 ld ix,enemies
 ld b,3
us_loop:
 push bc
 call move_hostile_bullet
 ld a,(ix+0)
 or a
 jp z,us_next
 ld a,(ix+9)
 or a
 jp z,us_no_reload
 dec (ix+9)
us_no_reload:
 ld a,(frame)
 and 7
 jp nz,us_detect
 ld a,(ix+8)
 or a
 jp z,us_detect
 cp 1
 jp z,us_patrol
 ; Assault: follows a corridor but never changes direction instantaneously.
 ld a,(player_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp z,us_assault_advance
 jp c,us_assault_right
 cp 4
 jp c,us_assault_advance
 dec (ix+1)
 ld a,2
 ld (ix+6),a
 jp us_assault_advance
us_assault_right:
 cp 19
 jp nc,us_assault_advance
 inc (ix+1)
 ld a,3
 ld (ix+6),a
us_assault_advance:
 ld a,(player_y)
 cp 9
 jp c,us_detect
 sub 7
 ld c,a
 ld a,(ix+2)
 cp c
 jp nc,us_detect
 inc (ix+2)
 jp us_detect
us_patrol:
 ; Patrol a small ±2 tile arc around a fixed anchor.
 ld a,(frame)
 and 32
 jp nz,us_patrol_left
 ld a,(ix+11)
 add a,2
 ld c,a
 ld a,(ix+1)
 cp c
 jp nc,us_detect
 inc (ix+1)
 ld a,3
 ld (ix+6),a
 jp us_detect
us_patrol_left:
 ld a,(ix+11)
 sub 2
 ld c,a
 ld a,(ix+1)
 cp c
 jp c,us_detect
 jp z,us_detect
 dec (ix+1)
 ld a,2
 ld (ix+6),a
us_detect:
 ; Do not shoot at the back of the character or from off-range.
 ld a,(player_y)
 ld c,a
 ld a,(ix+2)
 add a,2
 cp c
 jp nc,us_not_visible
 ld a,(ix+2)
 add a,12
 cp c
 jp c,us_not_visible
 ld a,(player_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp nc,us_dx_positive
 ld b,a
 ld a,c
 sub b
 jp us_dx_ready
us_dx_positive:
 sub c
us_dx_ready:
 cp 8
 jp nc,us_not_visible
 ld a,(ix+9)
 or a
 jp nz,us_not_visible
 ld a,(ix+3)
 or a
 jp nz,us_not_visible
 ld a,(ix+10)
 or a
 jp nz,us_countdown
 ld a,10
 ld (ix+10),a
 jp us_next
us_countdown:
 dec a
 ld (ix+10),a
 jp nz,us_next
 ; No more than 2 visible hostile bullets, to avoid instant bullet walls.
 ld a,(enemies+3)
 ld c,a
 ld a,(enemies+15)
 add a,c
 ld c,a
 ld a,(enemies+27)
 add a,c
 cp 2
 jp nc,us_next
 ld a,(player_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp z,us_shot_straight
 jp c,us_shot_right
 ld a,1
 jp us_set_shot_dir
us_shot_right:
 ld a,2
 jp us_set_shot_dir
us_shot_straight:
 xor a
us_set_shot_dir:
 ld (ix+7),a
 ld a,(ix+1)
 ld (ix+4),a
 ld a,(ix+2)
 inc a
 inc a
 ld (ix+5),a
 ld a,1
 ld (ix+3),a
 ld a,(phase)
 cp 1
 jp z,us_set_easy_cool
 ld a,26
 jp us_set_cool
us_set_easy_cool:
 ld a,36
us_set_cool:
 ld (ix+9),a
 jp us_next
us_not_visible:
 xor a
 ld (ix+10),a
us_next:
 ld de,12
 add ix,de
 pop bc
 dec b
 jp nz,us_loop
 ld a,(sector)
 cp 4
 ret z
 ld a,(frame)
 ld b,a
 ld a,(phase)
 cp 1
 jp nz,us_spawn_fast
 ld a,b
 and 31
 ret nz
 jp spawn_soldier
us_spawn_fast:
 ld a,b
 and 15
 ret nz
 jp spawn_soldier

move_hostile_bullet:
 ld a,(ix+3)
 or a
 ret z
 ld a,(frame)
 and 1
 ret nz                  ; one tile per two frames: visibly dodgeable
 ld a,(phase)
 cp 3
 jp z,mb_advance_y
 ld a,(sector)
 cp 4
 jp z,mb_advance_y
 ld a,(ix+7)
 cp 1
 jp z,mb_left
 cp 2
 jp nz,mb_advance_y
 inc (ix+4)
 jp mb_test_x
mb_left:
 dec (ix+4)
mb_test_x:
 ld a,(ix+4)
 cp 1
 jp c,mb_remove
 cp 23
 jp nc,mb_remove
mb_advance_y:
 ld a,(ix+5)
 inc a
 ld (ix+5),a
 cp 22
 ret c
mb_remove:
 xor a
 ld (ix+3),a
 ret

spawn_soldier:
 ld ix,enemies
 ld b,3
ss_find:
 ld a,(ix+0)
 or a
 jp z,ss_found
 ld de,12
 add ix,de
 djnz ss_find
 ret
ss_found:
 ld a,(rng)
 add a,37
 rlca
 ld (rng),a
 and 15                 ; keep both 8px columns inside the 24-column playfield
 add a,4                ; spawn at x=4..19
ss_col_ok:
 ld (ix+1),a
 ld e,a
 ld a,1
 ld (ix+6),a
 ld d,4
 call tile_solid
 or a
 ret nz
 ld a,4
 ld (ix+2),a
 ld a,1
 ld (ix+0),a
 xor a
 ld (ix+3),a
 ld (ix+9),a
 ld (ix+10),a
 ld a,(ix+1)
 ld (ix+11),a
 ld a,(rng)
 and 3
 cp 0
 jp z,ss_stationary
 cp 1
 jp z,ss_patrol
 ld a,2
 jp ss_role_store
ss_stationary:
 xor a
 jp ss_role_store
ss_patrol:
 ld a,1
ss_role_store:
 ld (ix+8),a
 ret

; Fase 3: exclusivamente 2 / 3 mechas de seis impactos.
; 1 grupo por pantalla. El acceso a la siguiente se bloquea hasta eliminarlos.
spawn_mecha_group:
 ld a,(sector)
 cp 1
 jp nz,mecha_group_three
 ld a,8
 ld (mecha_spawn_x),a
 ld a,5
 ld (mecha_spawn_y),a
 ld a,2
 jp mecha_group_count
mecha_group_three:
 ld a,7
 ld (mecha_spawn_x),a
 ld a,4
 ld (mecha_spawn_y),a
 ld a,3
mecha_group_count:
 ld (mecha_remaining),a
 ld b,a
 ld ix,enemies
mecha_group_loop:
 ld (ix+0),1
 ld a,(mecha_spawn_x)
 ld (ix+1),a
 ld (ix+7),a             ; independent home x coordinate
 ld a,(mecha_spawn_y)
 ld (ix+2),a
 ld (ix+6),6             ; SIX actual impacts to destroy
 xor a
 ld (ix+3),a
 ld (ix+10),a           ; burst shots remaining
 ld a,b
 and 1
 ld (ix+8),a            ; independent direction
 ld a,b
 add a,a
 add a,10
 ld (ix+9),a            ; staggered initial shot timers
 ld a,(mecha_spawn_x)
 ld c,a
 ld a,(mecha_remaining)
 cp 2
 jp nz,mecha_next_x3
 ld a,c
 add a,6
 jp mecha_set_x
mecha_next_x3:
 ld a,c
 add a,4
mecha_set_x:
 ld (mecha_spawn_x),a
 ld a,(mecha_spawn_y)
 ld c,a
 ld a,(mecha_remaining)
 cp 2
 ld a,c
 jp nz,mecha_y_three
 add a,6
 jp mecha_y_set
mecha_y_three:
 add a,4
mecha_y_set:
 ld (mecha_spawn_y),a
 ld de,12
 add ix,de
 djnz mecha_group_loop
 ret

update_mechas:
 ld a,(sector)
 cp 4
 ret z
 ld ix,enemies
 ld b,3
um_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,um_next
 ; Two different heights, independent left/right sweeps.
 ld a,(frame)
 and 3
 jp nz,um_fire
 ld a,(ix+8)
 or a
 jp nz,um_go_left
 ld a,(ix+1)
 ld c,a
 ld a,(ix+7)
 add a,3
 cp c
 jp c,um_reverse_left
 jp z,um_reverse_left
 ld a,c
 cp 17
 jp nc,um_reverse_left
 inc (ix+1)
 jp um_fire
um_reverse_left:
 ld (ix+8),1
 jp um_fire
um_go_left:
 ld a,(ix+1)
 ld c,a
 ld a,(ix+7)
 sub 3
 cp c
 jp nc,um_reverse_right
 ld a,c
 cp 6
 jp c,um_reverse_right
 jp z,um_reverse_right
 dec (ix+1)
 jp um_fire
um_reverse_right:
 ld (ix+8),0
um_fire:
 ld a,(ix+9)
 or a
 jp z,um_fire_ready
 dec (ix+9)
 jp um_next
um_fire_ready:
 ld a,(ix+10)
 or a
 jp nz,um_fire_burst
 ld (ix+10),3
 ; Determine aim ONCE per three-shot burst. No tracking the player
 ; between individual bullets; strafing allows a fair dodge.
 ld a,(player_x)
 ld c,a
 ld a,(ix+1)
 cp c
 jp z,um_aim_center
 jp c,um_aim_right
 ld a,1
 jp um_set_aim
um_aim_right:
 ld a,2
 jp um_set_aim
um_aim_center:
 xor a
um_set_aim:
 ld (ix+11),a
um_fire_burst:
 ld a,(ix+1)
 inc a
 ld (shot_origin_x),a
 ld a,(ix+2)
 add a,3
 ld (shot_origin_y),a
 ld a,(ix+11)
 ld (shot_variant),a
 call emit_special_shot
 dec (ix+10)
 ld a,(ix+10)
 or a
 jp nz,um_fire_short
 ; 32+id stagger between complete 3-projectile bursts.
 ld a,(ix+7)
 add a,26
 ld (ix+9),a
 jp um_next
um_fire_short:
 ld (ix+9),5
um_next:
 ld de,12
 add ix,de
 pop bc
 dec b
 jp nz,um_loop
 ret

update_special:
 ld a,(sector)
 cp 4
 ret nz
 jp update_hind
update_hind:
 ld a,(frame)
 ld b,a
 ld a,(phase)
 cp 3
 jp z,hind_move_fast
 ld a,b
 and 3
 jp nz,hind_shoot
 jp hind_move
hind_move_fast:
 ld a,b
 and 1
 jp nz,hind_shoot
hind_move:
 ld a,(boss_dir)
 or a
 jp nz,hind_go_left
 ld a,(boss_x)
 inc a
 ld (boss_x),a
 cp 17
 jp c,hind_shoot
 ld a,1
 ld (boss_dir),a
 jp hind_shoot
hind_go_left:
 ld a,(boss_x)
 dec a
 ld (boss_x),a
 cp 3
 jp nc,hind_shoot
 xor a
 ld (boss_dir),a
hind_shoot:
 ld a,(phase)
 cp 1
 jp z,hind_slow_fire
 cp 2
 jp z,hind_medium_fire
 ld a,(frame)
 and 7
 ret nz
 jp hind_fire_now
hind_medium_fire:
 ld a,(frame)
 and 15
 ret nz
 jp hind_fire_now
hind_slow_fire:
 ld a,(frame)
 and 31
 ret nz
hind_fire_now:
 ld a,(boss_x)
 add a,2
 ld (shot_origin_x),a
 ld a,7
 ld (shot_origin_y),a
 xor a
 ld (shot_variant),a
 call emit_special_shot
 ld a,(phase)
 cp 1
 ret z
 ld a,1
 ld (shot_variant),a
 call emit_special_shot
 ld a,(phase)
 cp 3
 ret nz
 ld a,2
 ld (shot_variant),a
 jp emit_special_shot

; Hind projectiles use the separate six-slot pool and advance in all phases.
emit_special_shot:
 ld hl,special_shots
 ld b,6
spec_find:
 ld a,(hl)
 or a
 jp z,spec_free
 ld de,5
 add hl,de
 djnz spec_find
 ret
spec_free:
 ld (hl),1
 inc hl
 ld a,(shot_origin_x)
 ld (hl),a
 inc hl
 ld a,(shot_origin_y)
 ld (hl),a
 inc hl
 ld a,(shot_variant)
 ld (hl),a
 ret

; Six projectile slots for mecha bursts AND all Hind phases.
; 0=down, 1=down-left, 2=down-right. Fixed trajectories after firing.
update_special_shots:
 ld a,(frame)
 and 1
 ret nz
 ld hl,special_shots
 ld b,6
uss_loop:
 push bc
 ld a,(hl)
 or a
 jp z,uss_next
 push hl
 inc hl
 ld a,(hl)
 ld c,a
 inc hl
 ld a,(hl)
 inc a
 ld (hl),a
 cp 23
 jp nc,uss_kill
 inc hl
 ld a,(hl)
 or a
 jp z,uss_alive
 cp 1
 jp z,uss_left
 ; right diagonal
 dec hl
 dec hl
 inc (hl)
 ld a,(hl)
 cp 23
 jp nc,uss_kill
 jp uss_alive
uss_left:
 dec hl
 dec hl
 dec (hl)
 ld a,(hl)
 cp 1
 jp c,uss_kill
 jp uss_alive
uss_alive:
 pop hl
 jp uss_next
uss_kill:
 pop hl
 ld (hl),0
uss_next:
 ld de,5
 add hl,de
 pop bc
 djnz uss_loop
 ret

boss_defeated:
 ld a,(phase)
 cp 3
 jp z,finish_game
 inc a
 ld (phase),a
 ld a,1
 ld (sector),a
 call show_phase_card
 call scene_init
 ret
finish_game:
 ld a,1
 ld (state),a
 ret

; Tank ramming is processed FIRST: it also works during the grace period
; after a projectile has hit the tank, without charging any armour for contact.
handle_collisions:
 ld a,(tank_mode)
 or a
 call nz,tank_ram_enemies
 ld a,(invuln)
 or a
 ret nz
 ld hl,special_shots
 ld b,6
collision_special_loop:
 push bc
 ld a,(hl)
 or a
 jp z,collision_special_next
 push hl
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 call player_overlap
 pop hl
 or a
 jp z,collision_special_next
 ld (hl),0
 call damage_player
 pop bc
 ret
collision_special_next:
 ld de,5
 add hl,de
 pop bc
 djnz collision_special_loop
 ld ix,enemies
 ld b,3
collision_loop:
 push bc
 ld a,(ix+3)
 or a
 jp z,collision_no_bullet
 ld a,(ix+4)
 ld e,a
 ld a,(ix+5)
 ld d,a
 call player_overlap
 or a
 jp z,collision_no_bullet
 xor a
 ld (ix+3),a
 call damage_player
 jp collision_done
collision_no_bullet:
 ld a,(ix+0)
 or a
 jp z,collision_done
 ld a,(ix+1)
 ld e,a
 ld a,(ix+2)
 ld d,a
 ld a,(phase)
 cp 3
 jp nz,coll_regular_actor
 call actor_overlap_nine
 jp coll_actor_result
coll_regular_actor:
 call actor_overlap
coll_actor_result:
 or a
 jp z,collision_done
 ld a,(tank_mode)
 or a
 jp nz,collision_done
 ; A soldier/mecha contact hurts Grit on foot only.
 call damage_player
collision_done:
 pop bc
 ld a,(invuln)
 or a
 ret nz
 ld de,12
 add ix,de
 djnz collision_loop
 ret

; Tank's heavy collision box kills ALL nearby infantry every tick.
; Projectile damage to the tank continues using the normal hit routine.
tank_ram_enemies:
 ld a,(phase)
 cp 3
 ret z
 ld ix,enemies
 ld b,3
tram_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,tram_next
 ld d,(ix+2)
 ld e,(ix+1)
 call actor_overlap
 or a
 jp z,tram_next
 xor a
 ld (ix+0),a
 ld (ix+3),a
 ld a,(kills)
 inc a
 ld (kills),a
 call draw_hud
 call sound_hit
tram_next:
 ld de,12
 add ix,de
 pop bc
 djnz tram_loop
 ret

; Input D=y E=x, returns A=1 if overlaps 2x2 player/tank.
actor_overlap:
 ; D/E top-left of 2x2 actor: four possible overlapping cells.
 call player_overlap
 or a
 ret nz
 inc e
 call player_overlap
 or a
 ret nz
 dec e
 inc d
 call player_overlap
 or a
 ret nz
 inc e
 jp player_overlap

; Physical 3x3 hitbox for the larger mecha rather than the 2x2 soldier.
actor_overlap_nine:
 ld b,3
acn_row:
 push bc
 ld c,3
acn_col:
 push bc
 call player_overlap
 pop bc
 or a
 jp nz,acn_found
 inc e
 dec c
 jp nz,acn_col
 dec e
 dec e
 dec e
 inc d
 pop bc
 djnz acn_row
 xor a
 ret
acn_found:
 pop bc
 ld a,1
 ret

player_overlap:
 ld a,(player_x)
 ld c,a
 ld a,e
 cp c
 jp z,overlap_x_yes
 inc c
 ld a,e
 cp c
 jp nz,overlap_no
overlap_x_yes:
 ld a,(player_y)
 ld c,a
 ld a,d
 cp c
 jp z,overlap_yes
 inc c
 ld a,d
 cp c
 jp nz,overlap_no
overlap_yes:
 ld a,1
 ret
overlap_no:
 xor a
 ret

damage_player:
 ld a,(tank_mode)
 or a
 jp z,hurt_foot
 ld a,(armor)
 dec a
 ld (armor),a
 jp nz,hurt_grace
 xor a
 ld (tank_mode),a
hurt_grace:
 call draw_hud
 ld a,25
 ld (invuln),a
 call sound_hurt
 ret
hurt_foot:
 ld a,(health)
 dec a
 ld (health),a
 jp nz,hurt_survive
 ld a,(lives)
 dec a
 ld (lives),a
 jp nz,hurt_new_life
 ld a,2
 ld (state),a
 call sound_hurt
 ret
hurt_new_life:
 ld a,4
 ld (health),a
 ld a,50
 ld (invuln),a
 jp hurt_show
hurt_survive:
 ld a,28
 ld (invuln),a
hurt_show:
 call sound_hurt
 call draw_hud
 ret

; --- render / erase only dynamic cells -------------------------------------
erase_dynamic:
 ld a,(ration_available)
 or a
 jp z,erase_ration_done
 ld a,(ration_y)
 ld d,a
 ld e,11
 call restore_tile
erase_ration_done:
 ld a,(fx_ttl)
 or a
 jp z,erase_fx_done
 ld a,(fx_y)
 ld d,a
 ld a,(fx_x)
 ld e,a
 call restore_quad
erase_fx_done:
 ld a,(player_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 call restore_quad
 ld a,(bullet_on)
 or a
 jp z,erase_no_player_bullet
 ld a,(bullet_y)
 ld d,a
 ld a,(bullet_x)
 ld e,a
 call restore_tile
erase_no_player_bullet:
 ld hl,special_shots
 ld b,6
erase_special_loop:
 push bc
 ld a,(hl)
 or a
 jp z,erase_special_next
 push hl
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 call restore_tile
 pop hl
erase_special_next:
 ld de,5
 add hl,de
 pop bc
 djnz erase_special_loop
 ld ix,enemies
 ld b,3
erase_actor_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,erase_no_actor
 ld a,(ix+2)
 ld d,a
 ld a,(ix+1)
 ld e,a
 ld a,(phase)
 cp 3
 jp nz,erase_regular_actor
 call restore_nine
 jp erase_no_actor
erase_regular_actor:
 call restore_quad
erase_no_actor:
 ld a,(ix+3)
 or a
 jp z,erase_no_hostile
 ld a,(ix+5)
 ld d,a
 ld a,(ix+4)
 ld e,a
 call restore_tile
erase_no_hostile:
 ld de,12
 add ix,de
 pop bc
 djnz erase_actor_loop
 ld a,(tank_available)
 or a
 jp z,erase_no_tank
 ld a,(tank_y)
 ld d,a
 ld e,14
 call restore_quad
erase_no_tank:
 ld a,(boss_hp)
 or a
 ret z
 ld a,(boss_x)
 ld e,a
 ld d,4
 jp restore_hind

draw_dynamic:
 ld a,(ration_available)
 or a
 jp z,draw_no_ration
 ld a,(ration_y)
 ld d,a
 ld e,11
 ld a,27
 call paint_tile
draw_no_ration:
 ld a,(tank_available)
 or a
 jp z,draw_no_pickup
 ld a,(tank_y)
 ld d,a
 ld e,14
 ld a,(frame)
 and 4
 add a,128
 call paint_quad
draw_no_pickup:
 ld a,(boss_hp)
 or a
 jp z,draw_no_boss
 ld a,(boss_x)
 ld e,a
 ld d,4
 call paint_hind
draw_no_boss:
 ld ix,enemies
 ld b,3
draw_actor_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,draw_skip_actor
 ld a,(ix+2)
 ld d,a
 ld a,(ix+1)
 ld e,a
 ld a,(phase)
 cp 3
 jp z,draw_mecha_actor
 ; Soldado: 4 vistas x 2 fotogramas; (ix+6) stores facing on foot.
 ld a,(ix+6)
 add a,a
 add a,a
 add a,a
 ld c,a
 ld a,(ix+8)
 or a
 jp z,draw_guard_still
 ld a,(frame)
 and 4
 jp draw_guard_anim
draw_guard_still:
 xor a
draw_guard_anim:
 add a,c
 add a,96
 call paint_quad
 jp draw_skip_actor
draw_mecha_actor:
 ld a,(frame)
 and 4
 jp z,mech_anim_zero
 ld a,145
 jp mech_draw
mech_anim_zero:
 ld a,136
mech_draw:
 call paint_nine
draw_skip_actor:
 ld a,(ix+3)
 or a
 jp z,draw_skip_hostile
 ld a,(ix+5)
 ld d,a
 ld a,(ix+4)
 ld e,a
 ld a,186
 call paint_tile
draw_skip_hostile:
 ld de,12
 add ix,de
 pop bc
 djnz draw_actor_loop
 ld a,(bullet_on)
 or a
 jp z,draw_no_player_bullet
 ld a,(bullet_y)
 ld d,a
 ld a,(bullet_x)
 ld e,a
 ld a,(bullet_power)
 or a
 jp z,draw_rifle_bullet
 ld hl,tank_shell_mask
 ld (mask_src),hl
 ld hl,tank_shell_sprite
 ld a,0x46              ; yellow shell, fixed legal ZX attribute
 call blit_masked_cell
 jp draw_no_player_bullet
draw_rifle_bullet:
 ld a,(bullet_dir)
 add a,178
 call paint_tile
draw_no_player_bullet:
 ld hl,special_shots
 ld b,6
draw_special_loop:
 push bc
 ld a,(hl)
 or a
 jp z,draw_special_next
 push hl
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,186
 call paint_tile
 pop hl
draw_special_next:
 ld de,5
 add hl,de
 pop bc
 djnz draw_special_loop
 call draw_fx
 ld a,(invuln)
 and 2
 ret nz
 ld a,(player_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 ld a,(tank_mode)
 or a
 jp z,draw_player_one
 ld a,(player_moving)
 or a
 jp z,tank_draw_idle
 ld a,(frame)
 and 4
 jp tank_draw_body
tank_draw_idle:
 xor a
tank_draw_body:
 add a,128
 call paint_quad
 ; Four cardinal gun directions painted as masked overlays on animated hull.
 ld a,(face)
 add a,28
 ld (turret_glyph),a
 ld a,(player_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 ld a,(face)
 cp 1
 jp z,tank_turret_down
 cp 2
 jp z,tank_turret_left
 cp 3
 jp z,tank_turret_right
 jp tank_turret_draw
tank_turret_down:
 inc d
 inc e
 jp tank_turret_draw
tank_turret_left:
 inc d
 jp tank_turret_draw
tank_turret_right:
 inc e
tank_turret_draw:
 ld a,(turret_glyph)
 jp paint_tile
draw_player_one:
 ld a,(face)
 add a,a
 add a,a
 add a,a
 ld c,a
 ld a,(player_moving)
 or a
 jp z,player_idle_frame
 ld a,(frame)
 and 4
 jp player_select_frame
player_idle_frame:
 xor a
player_select_frame:
 add a,c
 add a,32
 jp paint_quad

; 24x24 mecha is visually and logically larger than the 16x16 soldier.
paint_nine:
 ld (quad_id),a
 ld b,3
pn_row:
 push bc
 ld c,3
pn_col:
 ld a,(quad_id)
 call paint_tile
 ld a,(quad_id)
 inc a
 ld (quad_id),a
 inc e
 dec c
 jp nz,pn_col
 dec e
 dec e
 dec e
 inc d
 pop bc
 djnz pn_row
 ret
restore_nine:
 ld b,3
rn_row:
 push bc
 ld c,3
rn_col:
 call restore_tile
 inc e
 dec c
 jp nz,rn_col
 dec e
 dec e
 dec e
 inc d
 pop bc
 djnz rn_row
 ret


; Input D/E=top-left of 2x2, A=tile id base.
paint_quad:
 ld (quad_id),a
 ld a,(quad_id)
 call paint_tile
 inc e
 ld a,(quad_id)
 inc a
 call paint_tile
 dec e
 inc d
 ld a,(quad_id)
 add a,2
 call paint_tile
 inc e
 ld a,(quad_id)
 add a,3
 call paint_tile
 ret
restore_quad:
 call restore_tile
 inc e
 call restore_tile
 dec e
 inc d
 call restore_tile
 inc e
 call restore_tile
 ret
paint_hind:
 ld a,(frame)
 and 4
 jp z,ph_first_frame
 ld a,166
 jp ph_set_tile
ph_first_frame:
 ld a,154
ph_set_tile:
 ld (sequence_tile),a
 ld b,3
ph_row:
 push bc
 ld c,4
ph_col:
 ld a,(sequence_tile)
 call paint_tile
 ld a,(sequence_tile)
 inc a
 ld (sequence_tile),a
 inc e
 dec c
 jp nz,ph_col
 ld a,(boss_x)
 ld e,a
 inc d
 pop bc
 djnz ph_row
 ret
restore_hind:
 ld b,3
rh_row:
 push bc
 ld c,4
rh_col:
 call restore_tile
 inc e
 dec c
 jp nz,rh_col
 ld a,(boss_x)
 ld e,a
 inc d
 pop bc
 djnz rh_row
 ret

update_fx:
 ld a,(fx_ttl)
 or a
 ret z
 dec a
 ld (fx_ttl),a
 ret
spawn_fx:
 ld a,(ix+1)
 ld (fx_x),a
 ld a,(ix+2)
 ld (fx_y),a
 ld a,8
 ld (fx_ttl),a
 ret
draw_fx:
 ld a,(fx_ttl)
 or a
 ret z
 ld b,a
 ld a,(fx_y)
 ld d,a
 ld a,(fx_x)
 ld e,a
 ld a,b
 cp 4
 jp c,fx_second
 ld a,187
 jp paint_quad
fx_second:
 ld a,191
 jp paint_quad

; --- renderer: individual 8x8 font/tile + attribute, 256x192 Spectrum layout
; BLIT input HL -> eight bytes, D=character row, E=column, A=INK attribute.
paint_tile:
 push af
 push bc
 push de
 push hl
 ld (quad_save),a
 ld c,a
 ld b,0
 ld hl,glyph_colors
 add hl,bc
 ld a,(hl)
 ld (paint_attr),a
 ld a,(quad_save)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,glyphs
 add hl,bc
 ld a,(quad_save)
 cp 27
 jp c,paint_static
 cp 32
 jp c,paint_dynamic
 cp 195
 jp nc,paint_static
 jp paint_dynamic
paint_dynamic:
 cp 195
 jp nc,paint_static
 push hl
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,glyph_masks
 add hl,bc
 ld (mask_src),hl
 pop hl
 ld a,(paint_attr)
 call blit_masked_cell
 jp paint_done
paint_static:
 ld a,(paint_attr)
 call blit_cell
paint_done:
 pop hl
 pop de
 pop bc
 pop af
 ret
restore_tile:
 push bc
 push hl
 call map_address
 ld a,(hl)
 pop hl
 pop bc
 jp paint_tile
; input D=row E=column, output HL -> map_data + row*32 + column
map_address:
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,map_data
 add hl,bc
 ld c,e
 ld b,0
 add hl,bc
 ret
; output A=1 if solid map cell, 0 if passable; D/E preserved.
tile_solid:
 push bc
 push hl
 call map_address
 ld a,(hl)
 ld l,a
 ld h,0
 ld bc,solid_flags
 add hl,bc
 ld a,(hl)
 pop hl
 pop bc
 ret


print_text:
 ld a,(hl)
 or a
 ret z
 push hl
 call paint_ascii
 pop hl
 inc hl
 inc e
 ld a,e
 cp 32
 ret nc
 jp print_text
paint_ascii:
 push af
 push bc
 push de
 push hl
 sub 32
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,font_grit      ; proprietary original 5x7 pixel type; no ROM font
 add hl,bc
 ld a,e
 cp 24
 ld a,0x47
 jp c,paint_ascii_ready
 ld a,(hud_color)
paint_ascii_ready:
 call blit_cell
 pop hl
 pop de
 pop bc
 pop af
 ret

blit_cell:
 call mark_dirty
 push af
 push bc
 push de
 push hl
 ld (blit_src),hl
 ld (blit_attr),a
 ld a,d
 ld (blit_y),a
 ld a,e
 ld (blit_x),a
 ; bitmap start at 0x4000 | ((row AND 24)<<8), low=((row AND 7)*32)+x
 ld a,d
 and 24
 add a,0x60
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ld de,(blit_src)
 ld b,8
blit_pixels:
 ld a,(de)
 ld (hl),a
 inc de
 inc h
 djnz blit_pixels
 ; attribute address 0x5800+row*32+column
 ld a,(blit_y)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,0x7800
 add hl,de
 ld a,(blit_x)
 ld e,a
 ld d,0
 add hl,de
 ld a,(blit_attr)
 ld (hl),a
 pop hl
 pop de
 pop bc
 pop af
 ret

; Sprite con mascara expandida (1 px negro alrededor): preserva fondo.
; (bitmap_fondo AND mascara) OR sprite. La mascara elimina el fondo bajo
; la silueta, pero el atributo sigue siendo por celda 8x8 en Spectrum.
blit_masked_cell:
 call mark_dirty
 push af
 push bc
 push de
 push hl
 push ix                    ; IX is the actor pointer in gameplay loops
 ld (blit_src),hl
 ld (blit_attr),a
 ld a,d
 ld (blit_y),a
 ld a,e
 ld (blit_x),a
 ld a,d
 and 24
 add a,0x60               ; shadow screen, never visible mid-frame
 ld h,a
 ld a,d
 and 7
 add a,a
 add a,a
 add a,a
 add a,a
 add a,a
 add a,e
 ld l,a
 ld de,(blit_src)        ; sprite byte pointer
 push hl
 ld hl,(mask_src)
 push hl
 pop ix                   ; independent mask byte pointer
 pop hl                   ; screen byte pointer
 ld b,8
bm_pixels:
 ld c,(ix+0)
 ld a,(hl)
 and c
 ld c,a
 ld a,(de)
 or c
 ld (hl),a
 inc de
 inc ix
 inc h
 djnz bm_pixels
 ; Each cell has a legal Spectrum attribute; return to static attr on erase.
 ld a,(blit_y)
 ld l,a
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld de,0x7800
 add hl,de
 ld a,(blit_x)
 ld e,a
 ld d,0
 add hl,de
 ld a,(blit_attr)
 ld (hl),a
 pop ix
 pop hl
 pop de
 pop bc
 pop af
 ret

; --- short beeper SFX: OUT 0xFE bit 4, finite wave periods ----------
; Tone: B=half-wave pairs, C=half-wave delay loops. Short blocking effect.
tone:
 push af
 push bc
 push de
tone_cycle:
 ld a,0x10
 out (0xfe),a
 ld d,c
tone_high:
 dec d
 jp nz,tone_high
 xor a
 out (0xfe),a
 ld d,c
tone_low:
 dec d
 jp nz,tone_low
 djnz tone_cycle
 pop de
 pop bc
 pop af
 ret
sound_fire:
 ld b,28
 ld c,28
 jp tone
sound_pickup:
 ld b,38
 ld c,45
 jp tone
sound_hit:
 ld b,25
 ld c,40
 jp tone
sound_hurt:
 ld b,50
 ld c,55
 jp tone
sound_mecha_down:
 ld b,65
 ld c,65
 jp tone

; --- strings ----------------------------------------------------------------
; Fullscreen title and Game Over are native Spectrum bitmaps, not ROM text.
hud_smiley_left: db 0x03,0x04,0x0a,0x08,0x0a,0x09,0x04,0x03
hud_smiley_right: db 0xc0,0x20,0x50,0x10,0x50,0x90,0x20,0xc0
hud_smiley_empty: db 0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00
hud_bar_full: db 0x7e,0xff,0xff,0xff,0xff,0xff,0xff,0x7e
hud_bar_empty: db 0x7e,0x81,0x81,0x81,0x81,0x81,0x81,0x7e

spc_1a: db "FASE 1:",0
spc_1b: db "LA JUNGLA",0
spc_2a: db "FASE 2:",0
spc_2b: db "EL LABORATORIO",0
spc_3a: db "FASE 3:",0
spc_3b: db "COMPLEJO",0
win_1: db "MISION CUMPLIDA",0
win_2: db "GRIT HA VENCIDO",0
win_3: db "SPACE PARA REPETIR",0
;%%GENERATED_ASSETS%%

; --- mutable state ----------------------------------------------------------
phase: db 1
sector: db 1
lives: db 3
health: db 4
kills: db 0
state: db 0                 ; 0 playing, 1 won, 2 lost
frame: db 0
anim_stop_row: db 24
full_redraw: db 0
dirty_count: db 0
rng: db 0x9b
player_x: db 15
player_y: db 20
axis_x: db 0
axis_y: db 0
camera_top: db 24
level_ptr: dw 0
tank_y: db 13
scroll_row: db 0
scroll_src: dw 0
scroll_dst: dw 0
face: db 0
player_moving: db 0
turret_glyph: db 28
ration_available: db 0
ration_y: db 13
move_cool: db 0
cool: db 0
invuln: db 0
tank_mode: db 0
armor: db 0
tank_available: db 0
fx_ttl: db 0
fx_x: db 0
fx_y: db 0
target_x: db 0
target_y: db 0
bullet_on: db 0
bullet_x: db 0
bullet_y: db 0
bullet_dir: db 0
bullet_power: db 0       ; 0=rifle/solid collision, 1=tank/piercing
boss_x: db 0
boss_dir: db 0
boss_hp: db 0
mecha_remaining: db 0
mecha_spawn_x: db 0
mecha_spawn_y: db 0
shot_variant: db 0
shot_origin_x: db 0
shot_origin_y: db 0
special_shots: ds 30           ; 6 x (alive,x,y,direction,reserved)
enemies: ds 36              ; 3 structs x 12: active,x,y,shot,bx,by,face/hp,shot_dir/anchor,role,reload,warning,patrol_x
; Deliberately broad tank-shell silhouette: 4x4 hot center, dark ring.
tank_shell_sprite:
 db 0,24,60,126,126,60,24,0
tank_shell_mask:
 db 255,231,195,129,129,195,231,255
quad_id: db 0
quad_save: db 0
sequence_tile: db 0
hud_color: db 0x47
paint_attr: db 0
blit_attr: db 0
blit_src: dw 0
mask_src: dw 0
blit_x: db 0
blit_y: db 0
map_data: ds 768
dirty_flags: ds 768
dirty_pairs: ds 480      ; at most 240 dirty 8x8 coordinates
code_end:
