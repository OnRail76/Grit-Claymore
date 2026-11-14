; GRIT CLAYMORE - motor V1.1 - scroll rapido / sombra en RAM alta / SFX por tick / joystick
; ZX Spectrum 48K, Z80A. Plain code at 0x8000. BASIC is only a tape loader.
; Scrolling top-down game. Q/A/O/P incl diagonals, SPACE fires in last direction.
; MIT licence, (c) 2026 Tony C. Ware. See README and LIMITATIONS.
org 0x8000
; V1.8: variables nuevas en el hueco libre que queda tras las pantallas RLE
; bajadas a 0x5E00 (acaban en ~0x7F24; tests/test_v18.py lo comprueba).
rng16: equ 0x7ff0           ; generador xorshift de 16 bits (nunca 0)
run_meter: equ 0x7ff2       ; cuanto lleva Grit avanzando sin parar
ss_side: equ 0x7ff3         ; aparicion lateral: 0 izquierda, 1 derecha
force_attr: equ 0x7ff4      ; V1.9: si no es 0, color de todo lo que se pinta
boss_half: equ 0x7ff5       ; V1.9: vida del jefe a la que entra en rabia
boss_rage: equ 0x7ff6       ; V1.9: 1 = jefe en rabia
rage_flash: equ 0x7ff7      ; V1.9: ticks de parpadeo rojo al entrar en rabia
boss_mask: equ 0x7ff8       ; V1.9: cadencia de disparo del jefe (2^n-1)
tank_flash: equ 0x7ff9      ; V1.9: ticks de parpadeo rojo del tanque tocado
entry:
 di
 xor a
 out (0xfe),a
 ld sp,0                 ; pila en lo alto de la RAM (0xFB00..0xFFFF)
 ; V1.1: las tres pantallas RLE viajan al final del bloque de cinta y se
 ; bajan a 0x5E00 (RAM contendida, solo se leen en titulo/final). Su hueco
 ; lo ocupan despues los buffers y la pantalla sombra en RAM rapida.
 ld hl,rle_block
 ld de,0x5e00
 ld bc,rle_block_end-rle_block
 ldir
 ld hl,solid_flags_load    ; V1.8: tabla de colisiones -> 0x5B00
 ld de,solid_flags
 ld bc,256
 ldir
 ld hl,glyph_colors_load   ; V1.9: colores de los graficos -> 0x5D00
 ld de,glyph_colors
 ld bc,256
 ldir
 ld hl,0x9b37              ; V1.8: semilla del generador (no puede ser 0)
 ld (rng16),hl
 xor a
 ld (run_meter),a
 ld (force_attr),a
 ei
 call detect_kempston
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
 ld (bonus_life),a
 ld hl,score
 ld b,6
mng_score:
 ld (hl),a
 inc hl
 djnz mng_score
 ld hl,sfx_none
 ld (sfx_ptr),hl
 call show_phase_card
 call scene_init
main_loop:
 xor a
 out (0xfe),a
 call frame_sync        ; 25 ticks/s medidos con FRAMES, no con HALT fijos
 call check_pause
 ld a,(state)
 or a
 jp nz,handle_end
 call erase_dynamic
 call animate_tiles
 call update_fx
 call read_controls
 call update_player_bullets
 call update_soldiers
 call update_special
 call update_special_shots
 call handle_collisions
 ld a,(state)
 or a
 jp nz,handle_end
 call draw_dynamic
 call present_frame
 call sfx_step
 call engine_sound
 ld a,(frame)
 inc a
 ld (frame),a
 jp main_loop
handle_end:
 push af
 call update_hiscore
 pop af
 cp 1
 jp z,win_screen
 jp lose_screen

; Espera a que hayan pasado 2 interrupciones desde el tick anterior. Si la
; logica tardo mas, no espera: un tick caro ya no cuesta fotogramas de mas.
frame_sync:
 ld hl,0x5c78            ; FRAMES (lo incrementa la interrupcion IM1 de la ROM)
fs_wait:
 ld a,(last_frames)
 ld b,a
 ld a,(sync_need)
 ld c,a
 ld a,(hl)
 sub b
 cp c
 jp nc,fs_done
 halt
 jp fs_wait
fs_done:
 ld a,(hl)
 ld (last_frames),a
 ld a,2
 ld (sync_need),a
 ret

; H = pausa. Borde azul mientras dura; otra pulsacion de H reanuda.
check_pause:
 ld bc,0xbffe
 in a,(c)
 bit 4,a
 ret nz
 ld a,1
 out (0xfe),a
cp_release:
 halt
 in a,(c)
 bit 4,a
 jp z,cp_release
cp_press:
 halt
 in a,(c)
 bit 4,a
 jp nz,cp_press
cp_release2:
 halt
 in a,(c)
 bit 4,a
 jp z,cp_release2
 xor a
 out (0xfe),a
 ret

; Presentacion del tick: 0 = solo celdas sucias, 1 = scroll (24 columnas de
; juego + celdas sucias del HUD), 2 = desbordamiento de la cola (todo).
present_frame:
 ld a,(full_redraw)
 or a
 jp z,present_dirty
 cp 2
 jp z,present_full
 call present_playfield
 call present_dirty
 xor a
 ld (full_redraw),a
 ret

; V1.1: la zona de juego de la sombra es un anillo de 24 filas. La fila
; logica d vive en la fila fisica (d+shadow_top) mod 24, asi que el scroll
; ya no mueve ni un byte de bitmap: gira el anillo y pinta la fila nueva.
; Aqui se copia fila a fila a su sitio real en pantalla, solo columnas
; 0..23 (24 LDI por linea). El HUD no gira ni se copia.
present_playfield:
 ld a,(shadow_top)
 ld (pp_phys),a
 xor a
pp_row:
 ld (pp_log),a
 ld d,a
 rrca
 rrca
 rrca
 and 0xe0
 ld e,a
 ld a,d
 and 24
 add a,0x40
 ld d,a                   ; DE = fila logica en pantalla
 ld a,(pp_phys)
 ld h,a
 rrca
 rrca
 rrca
 and 0xe0
 ld l,a
 ld a,h
 and 24
 add a,0xe0
 ld h,a                   ; HL = fila fisica en la sombra
 ld b,8
 ld c,255
pp_line:
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ldi
 ld a,l
 sub 24
 ld l,a
 inc h
 ld a,e
 sub 24
 ld e,a
 inc d
 djnz pp_line
 ld a,(pp_phys)
 rrca
 rrca
 rrca
 and 3
 add a,0xf8
 ld h,a
 ld a,(pp_log)
 rrca
 rrca
 rrca
 and 3
 add a,0x58
 ld d,a
 ld bc,24
 ldir                     ; atributos de la fila
 ld a,(pp_phys)
 inc a
 cp 24
 jp c,pp_phys_ok
 xor a
pp_phys_ok:
 ld (pp_phys),a
 ld a,(pp_log)
 inc a
 cp 24
 jp nz,pp_row
 ret

; D=fila logica, E=columna -> A=fila fisica en la sombra. Solo usa A.
phys_row:
 ld a,e
 cp 24
 ld a,d
 ret nc                   ; el HUD (columnas 24..31) no gira
 ld a,(shadow_top)
 add a,d
 cp 24
 ret c
 sub 24
 ret

; Bits de control (formato Kempston): 0 dcha, 1 izda, 2 abajo, 3 arriba, 4 fuego.
; Suma teclado Q/A/O/P/SPACE, Sinclair (6/7/8/9/0) y Kempston si se detecto.
read_input:
 ld d,0
 ld bc,0xfbfe
 in a,(c)
 bit 0,a
 jp nz,ri_a
 ld d,8
ri_a:
 ld bc,0xfdfe
 in a,(c)
 bit 0,a
 jp nz,ri_op
 ld a,d
 or 4
 ld d,a
ri_op:
 ld bc,0xdffe
 in a,(c)
 ld e,a
 bit 1,e
 jp nz,ri_p
 ld a,d
 or 2
 ld d,a
ri_p:
 bit 0,e
 jp nz,ri_space
 ld a,d
 or 1
 ld d,a
ri_space:
 ld bc,0x7ffe
 in a,(c)
 bit 0,a
 jp nz,ri_sinclair
 ld a,d
 or 16
 ld d,a
ri_sinclair:
 ld bc,0xeffe            ; fila 6 7 8 9 0 = joystick Sinclair / Interface 2
 in a,(c)
 ld e,a
 bit 4,e
 jp nz,ri_s7
 ld a,d
 or 2
 ld d,a
ri_s7:
 bit 3,e
 jp nz,ri_s8
 ld a,d
 or 1
 ld d,a
ri_s8:
 bit 2,e
 jp nz,ri_s9
 ld a,d
 or 4
 ld d,a
ri_s9:
 bit 1,e
 jp nz,ri_s0
 ld a,d
 or 8
 ld d,a
ri_s0:
 bit 0,e
 jp nz,ri_kempston
 ld a,d
 or 16
 ld d,a
ri_kempston:
 ld a,(kempston_ok)
 or a
 jp z,ri_store
 in a,(0x1f)
 and 0x1f
 or d
 ld d,a
ri_store:
 ld a,d
 ld (input_bits),a
 ret

; Solo se acepta Kempston si 256 lecturas seguidas, tomadas en el borde
; superior (bus flotante = 0xFF sin interfaz), tienen los bits 5..7 a cero
; y nunca izquierda+derecha a la vez.
detect_kempston:
 xor a
 ld (kempston_ok),a
 halt
 ld b,0
dk_loop:
 in a,(0x1f)
 ld c,a
 and 0xe0
 ret nz
 ld a,c
 and 3
 cp 3
 ret z
 djnz dk_loop
 ld a,1
 ld (kempston_ok),a
 ret

; --- title & screens --------------------------------------------------------
title_screen:
 xor a
 out (0xfe),a
 ld hl,title_rle
 ld de,0x4000
 call unpack_title
 call detect_kempston    ; V1.3: hay interfaz? (bus flotante = no)
 call space_release
 ld hl,title_tune
 ld (music_ptr),hl
 ld a,1
 ld (music_on),a
 call space_press
 xor a
 ld (music_on),a
 ; V1.3: si se empezo con el FUEGO del Kempston se juega con joystick;
 ; con SPACE (o el 0 de Sinclair) se juega con teclado y el puerto del
 ; Kempston ya no se lee.
 ld a,(kempston_ok)
 or a
 jp z,ts_mode_done
 in a,(0x1f)
 and 0x10
 jp nz,ts_mode_done
 xor a
 ld (kempston_ok),a
ts_mode_done:
 ; El instante de la pulsacion siembra el generador aleatorio.
 ld a,(0x5c78)
 ld hl,rng16
 xor (hl)
 jp nz,ts_seed_ok
 inc a                    ; V1.8: el xorshift no puede quedarse en 0
ts_seed_ok:
 ld (hl),a
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
; "SPACE" = cualquier boton de fuego (SPACE, 0 de Sinclair o Kempston).
space_release:
sr_wait:
 halt
 call read_input
 ld a,(input_bits)
 bit 4,a
 jp nz,sr_wait
 ret
space_press:
sp_wait:
 call read_input
 ld a,(input_bits)
 bit 4,a
 ret nz
 ld a,(music_on)
 or a
 jp nz,sp_music
 halt
 jp sp_wait
sp_music:
 call music_step
 jp sp_wait

; Melodia del titulo: pares (ciclos, retardo); retardo 0 = silencio de
; "ciclos" fotogramas; ciclos 0 = fin. Se consulta el fuego entre nota y nota.
; V1.7: suena UNA vez cada vez que se llega al titulo; al acabar, silencio.
music_step:
 ld hl,(music_ptr)
 ld a,(hl)
 or a
 jp nz,ms_play
 ld (music_on),a
 ret
ms_play:
 ld b,a
 inc hl
 ld c,(hl)
 inc hl
 ld (music_ptr),hl
 ld a,c
 or a
 jp z,ms_rest
 call tone
 halt
 ret
ms_rest:
 halt
 djnz ms_rest
 ret

; --- 2-second pre-stage title cards, text rendered from the 8x8 arcade font ---
; Runs ONCE per phase, not every individual scrolling sector.
show_phase_card:
 ; V1.2: tarjeta enmarcada con retrato del jefe de la fase y el objetivo.
 xor a
 out (0xfe),a
 call screen_clear
 ld a,(phase)
 dec a
 ld l,a
 add a,a
 add a,l                  ; A = (fase-1)*3
 ld l,a
 ld h,0
 add hl,hl                ; *2: tres punteros de 16 bits por fase
 ld bc,card_texts
 add hl,bc
 ld (card_ptr),hl
 ; color de la fase en todos los atributos (el retrato pone los suyos)
 ld a,(phase)
 ld l,a
 ld h,0
 ld bc,card_colors-1
 add hl,bc
 ld a,(hl)
 ld (card_color),a
 ld hl,0xf800
 ld de,0xf801
 ld bc,767
 ld (hl),a
 ldir
 call draw_card_frame
 ; textos: FASE n / nombre / ENEMIGO FINAL / jefe, centrados
 ld hl,(card_ptr)
 ld d,4
 call print_card_line
 ld d,6
 call print_card_line
 push hl
 ld hl,txt_jefe
 ld d,15
 ld e,9
 call print_text
 pop hl
 ld d,17
 call print_card_line
 ; retrato del jefe en el centro (columnas 14..17, filas 9..11)
 call load_boss_gfx
 ld a,14
 ld (boss_x),a
 ld e,a
 ld d,9
 call paint_hind
 ld hl,txt_record
 ld d,20
 ld e,10
 call print_text
 ld hl,hiscore
 ld b,6
spc_record:
 ld a,(hl)
 call put_digit
 inc hl
 inc e
 djnz spc_record
 ; color por linea: titulo y jefe en blanco, resto en el color de la fase
 ld a,(card_color)
 ld c,a
 ld d,6
 call card_row
 ld d,15
 call card_row
 ld d,20
 call card_row
 ld c,0x47
 ld d,4
 call card_row
 ld d,17
 call card_row
 call present_full
 ld b,100            ; 100 PAL 50Hz interrupts = 2 seconds.
spc_hold:
 halt
 djnz spc_hold
 ret

; HL -> puntero a texto en la tabla; D = fila. Centra en 32 columnas.
print_card_line:
 ld e,(hl)
 inc hl
 ld a,(hl)
 inc hl
 push hl
 ld h,a
 ld l,e
 push hl
 ld b,0
pcl_len:
 ld a,(hl)
 or a
 jp z,pcl_go
 inc b
 inc hl
 jp pcl_len
pcl_go:
 ld a,32
 sub b
 rrca
 and 127
 ld e,a
 pop hl
 call print_text
 pop hl
 ret

card_row:
 ; D = fila, C = atributo; columnas 4..27. La sombra esta en fila 0 (screen_clear).
 ld l,d
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 add hl,hl
 ld a,h
 add a,0xf8
 ld h,a
 ld a,l
 add a,4
 ld l,a
 ld b,24
crw_loop:
 ld (hl),c
 inc hl
 djnz crw_loop
 ret

; Marco doble de 26x20 celdas (columnas 3..28, filas 1..22) con 3 glifos.
draw_card_frame:
 ld d,1
 ld e,3
 ld hl,card_frame_glyphs
 call card_glyph
 ld d,1
 ld e,28
 ld hl,card_glyph_tr
 call card_glyph
 ld d,22
 ld e,3
 ld hl,card_glyph_bl
 call card_glyph
 ld d,22
 ld e,28
 ld hl,card_glyph_br
 call card_glyph
 ld e,4
dcf_h:
 ld d,1
 ld hl,card_frame_glyphs+8
 call card_glyph
 ld d,22
 ld hl,card_glyph_hb
 call card_glyph
 inc e
 ld a,e
 cp 28
 jp nz,dcf_h
 ld d,2
dcf_v:
 ld e,3
 ld hl,card_frame_glyphs+16
 call card_glyph
 ld e,28
 ld hl,card_glyph_vr
 call card_glyph
 inc d
 ld a,d
 cp 22
 jp nz,dcf_v
 ret
card_glyph:
 ld a,(card_color)
 jp blit_cell

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
 ld (boss_rage),a          ; V1.9
 ld (rage_flash),a
 ld (tank_flash),a
 ld (tank_available),a
 ld (mecha_remaining),a
 ld (boss_hp),a
 ld (fx_ttl),a
 ld (ration_available),a
 ld (player_moving),a
 ld (full_redraw),a
 ld hl,bullets
 ld b,10                 ; las dos balas propias
si_bullets:
 ld (hl),a
 inc hl
 djnz si_bullets
 ld hl,special_shots
 ld de,special_shots+1
 ld bc,29
 ld (hl),a
 ldir
 ld hl,enemies
 ld de,enemies+1
 ld bc,47
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
 ld a,16
 jp boss_init_hp
boss_init2:
 cp 2
 jp nz,boss_init3
 ld a,24
 jp boss_init_hp
boss_init3:
 ld a,32
boss_init_hp:
 ld (boss_hp),a
 rrca                      ; V1.9: rabia a mitad de vida (16/24/32 -> 8/12/16)
 ld (boss_half),a
 ld a,(boss_hp)
 ld a,14
 ld (boss_x),a
 call load_boss_gfx
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
 call setup_plasma
 ld a,(phase)
 cp 3
 jp nz,scene_no_mechas
 ld a,(sector)
 cp 4
 jp z,scene_no_mechas
 call spawn_mecha_group
scene_no_mechas:
 ld a,2                  ; V1.3: dos oleadas mas de tres mechas por sector
 ld (mecha_waves),a
 ld a,16
 ld (wave_camera),a
 ; V1.4: una racion en cada sector, arena del jefe incluida; en la fase 3
 ; otra de refuerzo a mitad de sector (ration_mid).
 ld a,1
 ld (ration_available),a
 ld a,13
 ld (ration_y),a
 call place_ration
 xor a
 ld (ration_mid),a
 ld a,(phase)
 cp 3
 jp nz,scene_ration_done
 ld a,(sector)
 cp 4
 jp z,scene_ration_done
 ld a,1
 ld (ration_mid),a
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
 ; V1.1: pantalla sombra completa (6912 bytes) en 0xE000..0xFAFF, fuera de
 ; la memoria contendida por la ULA. Pila en 0xFB00..0xFFFF.
 xor a
 ld (shadow_top),a
 ld hl,0xe000
 ld de,0xe001
 ld bc,6143
 ld (hl),a
 ldir
 ld a,7
 ld hl,0xf800
 ld de,0xf801
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
 ; AF se guarda ANTES de tocar A, tambien en la salida rapida.
 push af
 ld a,(full_redraw)
 or a
 jp z,md_continue
 cp 2
 jp z,md_skip
 ld a,e
 cp 24
 jp nc,md_continue      ; con scroll pendiente, el HUD si se encola
md_skip:
 pop af
 ret
md_continue:
 push hl
 ld a,d
 rrca
 rrca
 rrca
 ld h,a
 and 0xe0
 or e
 ld l,a
 ld a,h
 and 3
 add a,dirty_flags>>8
 ld h,a
 ld a,(hl)
 or a
 jp nz,md_done
 ld (hl),1
 ld a,(dirty_count)
 cp 240
 jp nc,md_overflow
 inc a
 ld (dirty_count),a
 dec a
 ld l,a
 ld h,0
 add hl,hl
 ld a,h
 add a,dirty_pairs>>8
 ld h,a
 ld (hl),d
 inc hl
 ld (hl),e
 jp md_done
md_overflow:
 ld (hl),0
 ld a,2
 ld (full_redraw),a
md_done:
 pop hl
 pop af
 ret

; D=fila E=columna. Usa A y HL.
clear_dirty_one:
 ld a,d
 rrca
 rrca
 rrca
 ld h,a
 and 0xe0
 or e
 ld l,a
 ld a,h
 and 3
 add a,dirty_flags>>8
 ld h,a
 ld (hl),0
 ret

; Called ONCE when an arena enters or the 8px viewport strip scrolls.
; Full screen copy is necessarily costlier, but ordinary animation uses only
; dirty 8x8 cells instead of showing the blanked background to the ULA.
present_full:
 call present_playfield
 ld hl,0xe018
 ld de,0x4018
 ld a,216                 ; 192 lineas de bitmap + 24 de atributos, columnas 24..31
pf_hud:
 ld bc,8
 ldir
 ld bc,24
 add hl,bc
 ex de,hl
 add hl,bc
 ex de,hl
 dec a
 jp nz,pf_hud
 xor a
 ld (full_redraw),a
 jp clear_dirty

; Sparse presentation, ONLY the tiles changed by actor movement or the HUD.
; Tras un scroll (full_redraw=1) las celdas de juego ya se copiaron en
; bloque: aqui solo se liberan sus marcas y se presentan las del HUD.
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
 ld a,(full_redraw)
 or a
 jp z,pd_show
 ld a,e
 cp 24
 jp c,pd_skip
pd_show:
 call present_cell
pd_skip:
 pop hl
 pop bc
 djnz pd_next
 xor a
 ld (dirty_count),a
 ret

; D = tile row E = column. Copia 8 bytes de pixeles y el atributo de la
; sombra (0xE000) a la pantalla (0x4000): mismo byte bajo, alto XOR 0xA0.
present_cell:
 push de
 call phys_row
 ld b,a
 rrca
 rrca
 rrca
 and 0xe0
 or e
 ld l,a
 ld a,b
 and 24
 add a,0xe0
 ld h,a                   ; HL = celda en la sombra (fila fisica)
 ld a,d
 rrca
 rrca
 rrca
 and 0xe0
 or e
 ld e,a
 ld a,d
 ld c,a
 and 24
 add a,0x40
 ld d,a                   ; DE = celda en pantalla (fila logica)
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,(hl)
 ld (de),a
 inc h
 inc d
 ld a,b
 rrca
 rrca
 rrca
 and 3
 add a,0xf8
 ld h,a
 ld a,c
 rrca
 rrca
 rrca
 and 3
 add a,0x58
 ld d,a
 ld a,(hl)
 ld (de),a
 pop de
 ret

; --- V074 environmental tile animation (two frames, 1-2-1-2) ---
; Only 8-pixel tiles in the *current* 24x24 playfield are repainted.
; The HUD never enters this loop. Sprites were erased in SHADOW RAM first.
; XOR masks toggle the same 8-byte glyph between two frames: very low RAM.
animate_tiles:
 ; V1.1: cuatro bandas de 6 filas en los ticks 0..3 de cada 8, recorriendo
 ; el mapa con un puntero lineal. Reparte el coste y elimina el tiron.
 ; V1.3: ocho bandas de 3 filas, una por tick: mismo ritmo, mitad de coste.
 ld a,(frame)
 and 7
 or a
 jp nz,anim_band
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
 xor a
anim_band:
 ld d,a
 add a,a
 add a,d                  ; primera fila = banda*3
 ld d,a
 add a,3
 ld (anim_stop_row),a
 ld e,0
 call map_address
anim_row:
 ld e,0
anim_col:
 ld a,(hl)
 cp 4
 jr z,anim_repaint
 cp 16
 jr c,anim_skip
 jr z,anim_repaint
 cp 24
 jr z,anim_repaint
 cp 26
 jr nz,anim_skip
anim_repaint:
 call paint_tile
anim_skip:
 inc hl
 inc e
 ld a,e
 cp 24
 jr nz,anim_col
 ld bc,8
 add hl,bc
 inc d
 ld a,(anim_stop_row)
 cp d
 jr nz,anim_row
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
 ; V1.2: cada fase tiene su propio diccionario de filas de 24 tiles.
 ld a,(phase)
 dec a
 add a,a
 ld l,a
 ld h,0
 ld bc,map_rows_bases
 add hl,bc
 ld a,(hl)
 inc hl
 ld h,(hl)
 ld l,a
 ld (rows_base),hl
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
 ld bc,(rows_base)
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
 ld a,(full_redraw)
 cp 2
 jp z,scroll_keep_full
 ld a,1
 ld (full_redraw),a
scroll_keep_full:
 ld a,(camera_top)
 or a
 ret z
 dec a
 ld (camera_top),a
 ld a,(run_meter)          ; V1.8: avanzar sin parar llena el medidor
 add a,4
 jp nc,scroll_meter_ok
 ld a,255
scroll_meter_ok:
 ld (run_meter),a
 ld a,4
 ld (sync_need),a         ; todo paso de scroll dura 4 fotogramas: 12,5 pasos/s
 ld a,(shadow_top)        ; gira el anillo: la fila que sale por abajo
 or a                     ; pasa a ser la fila logica 0
 jp nz,scroll_ring_ok
 ld a,24
scroll_ring_ok:
 dec a
 ld (shadow_top),a
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
 ; Shift actors to match scrolled terrain. V1.2: las balas de Grit NO se
 ; desplazan con el scroll: siguen subiendo a dos celdas por tick por la
 ; pantalla, el doble que el terreno, en vez de quedarse quietas al avanzar.
scroll_bullet_done:
 ld ix,enemies
 ld b,4
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
 ld a,(pickup_on)
 or a
 jp z,scroll_no_pickup
 ld a,(pickup_y)
 inc a
 ld (pickup_y),a
 cp 21
 jp c,scroll_no_pickup
 xor a
 ld (pickup_on),a
scroll_no_pickup:
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
; V1.3: en cada baja solo cambian las cifras; el resto del panel no se toca.
draw_score:
 ld a,0x47
 ld (hud_color),a
 ld hl,score
 ld b,6
 ld d,5
 ld e,25
ds_loop:
 ld a,(hl)
 call put_digit
 inc hl
 inc e
 djnz ds_loop
 ret

draw_hud:
 ld a,0x47                   ; white numbers for PUNTOS
 ld (hud_color),a
 ; PUNTOS: seis cifras decimales reales (score), 100 por soldado.
 ld hl,score
 ld b,6
 ld d,5
 ld e,25
hud_score_loop:
 ld a,(hl)
 call put_digit
 inc hl
 inc e
 djnz hud_score_loop
 call draw_lives
 jp draw_bars
draw_lives:
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
 ld a,0x44
 jp hud_life_draw
hud_life_empty:
 ld hl,hud_smiley_empty
 ld a,0x05
hud_life_draw:
 call blit_cell
 inc e
 ld a,c
 or a
 jp z,hud_life_right_empty
 ld hl,hud_smiley_right
 ld a,0x44
 jp hud_life_right_draw
hud_life_right_empty:
 ld hl,hud_smiley_empty_r
 ld a,0x05
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
 ret
draw_bars:
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
 ; TANQUE: cuatro celdas. En la fase 3 (sin tanque) es el marcador ARMA.
 ld a,0x46
 ld (bar2_attr),a
 ld a,(phase)
 cp 3
 jp nz,hud_tank_mode
 ld a,0x43                ; plasma en magenta
 ld (bar2_attr),a
 ld a,(plasma_ammo)
 add a,2
 ld c,0
hud_ammo_div:
 sub 3
 jp c,hud_tank_setup
 inc c
 jp hud_ammo_div
hud_tank_mode:
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
 ld b,4                   ; V1.4: cuatro celdas, mismas que PODER
 ld d,22
 ld e,26
hud_tank_loop:
 push bc
 ld a,c
 or a
 jp z,hud_tank_empty
 ld hl,hud_bar_full
 ld a,(bar2_attr)
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
 call read_input
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
 ld a,(input_bits)
 bit 3,a
 jp z,controls_a
 ld a,1
 ld (axis_y),a
 ld a,(target_y)
 dec a
 ld (target_y),a
 jp controls_horizontal
controls_a:
 ld a,(input_bits)
 bit 2,a
 jp z,controls_horizontal
 ld a,2
 ld (axis_y),a
 ld a,(target_y)
 inc a
 ld (target_y),a
controls_horizontal:
 ld a,(input_bits)
 bit 1,a
 jp z,controls_p
 ld a,1
 ld (axis_x),a
 ld a,(target_x)
 dec a
 ld (target_x),a
 jp controls_direction
controls_p:
 ld a,(input_bits)
 bit 0,a
 jp z,controls_direction
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
 ; V1.6: avanzar con scroll respeta el terreno igual que un paso normal:
 ; si la fila que bajaria sobre Grit es solida, no se avanza (antes el
 ; scroll metia arbustos y muros encima de el y lo dejaba atrapado).
 ld a,(target_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 call quad_free
 jp nz,controls_fire
 ld a,1
 ld (player_moving),a
 call scroll_scene
 jp controls_fire
controls_y_ok:
 ; V1.1: en la arena del jefe no se sube de la fila 9. El Hind ocupa las
 ; filas 4..6 y dispara desde la 7: ya no hay hueco seguro encima.
 ld a,(sector)
 cp 4
 jp nz,controls_y_free
 ld a,(target_y)
 cp 9
 jp c,controls_fire
controls_y_free:
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
 ld a,3                    ; V1.9: el tanque, una casilla cada 4 ticks
 ld (move_cool),a
 jp controls_check_pickup
ctrl_speed_foot:
 ld a,1
 ld (move_cool),a
controls_check_pickup:
 call check_ration
 call check_pickup
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
 ld a,4                   ; V1.4: el tanque aguanta cuatro impactos
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
 ld a,(input_bits)
 bit 4,a
 ret z
 ld a,(cool)
 or a
 ret nz
 ; V1.1: dos balas propias en pantalla.
 ld hl,bullets
 ld a,(hl)
 or a
 jp z,fire_slot
 ld hl,bullets+5
 ld a,(hl)
 or a
 ret nz
fire_slot:
 ld a,(tank_mode)
 or a
 jp z,fire_foot
 ld a,5
 jp fire_set_cool
fire_foot:
 ld a,3
fire_set_cool:
 ld (cool),a
 ld (hl),1
 inc hl
 ld a,(player_x)
 inc a
 ld (hl),a
 inc hl
 ld a,(player_y)
 inc a
 ld (hl),a
 inc hl
 ld a,(face)
 ld (hl),a
 inc hl
 ld a,(tank_mode)
 or a
 jp nz,fs_power
 ld a,(plasma_ammo)       ; V1.5: canon de plasma de la fase 3
 or a
 jp z,fs_power
 dec a
 ld (plasma_ammo),a
 ld (hl),2
 call draw_bars
 jp sound_plasma
fs_power:
 ld (hl),a
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
 ld a,(ration_y)
 ld d,a
 ld a,(ration_x)
 ld e,a
 call player_overlap     ; basta con tocar la lata con cualquier celda de Grit
 or a
 ret z
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

; La racion ya no sale siempre en la columna 11: se prueba una columna al
; azar que sea transitable (8 intentos; si no, la 11 de siempre).
place_ration:
 ld a,(ration_y)          ; V1.4: fila variable (13 al empezar, 3 a mitad)
 ld d,a
 ld b,8
pr_try:
 call rand
 and 15
 add a,4
 ld e,a
 call tile_solid
 or a
 jp z,pr_ok
 djnz pr_try
 ld e,11
pr_ok:
 ld a,e
 ld (ration_x),a
 ret
; V1.8: xorshift de 16 bits (periodo 65535). El de antes (sumar 37 y rotar)
; repetia la misma columna varias veces seguidas. Devuelve A; usa HL.
rand:
 ld hl,(rng16)
 ld a,h
 rra
 ld a,l
 rra
 xor h
 ld h,a
 ld a,l
 rra
 ld a,h
 rra
 xor l
 ld l,a
 xor h
 ld h,a
 ld (rng16),hl
 ret

next_sector:
 ld a,(sector)
 inc a
 ld (sector),a
 call scene_init
 ret

; --- bullets and soldiers --------------------------------------------------
; Cada bala se copia a las variables de trabajo bullet_*, se actualiza con
; la rutina de siempre y se devuelve a su hueco.
update_player_bullets:
 ld hl,bullets
 call upb_one
 ld hl,bullets+5
upb_one:
 ld a,(hl)
 or a
 ret z
 push hl
 ld de,bullet_on
 ld bc,5
 ldir
 ; V1.2: dos celdas por tick, con colision en cada celda. Asi la bala
 ; deja atras al scroll (que la baja una celda por paso) y nunca atraviesa
 ; a un enemigo sin comprobarlo.
 call update_player_bullet
 ld a,(bullet_on)
 or a
 call nz,update_player_bullet
 pop de
 ld hl,bullet_on
 ld bc,5
 ldir
 ret
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
 call shot_blocked       ; V1.1: el agua no para las balas, los muros si
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
 ld c,a
 ld a,(bullet_power)      ; V1.5: el plasma quita dos al jefe
 cp 2
 ld a,c
 jp nz,boss_hp_store
 or a
 jp z,boss_hp_store
 dec a
boss_hp_store:
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
 ld a,(sector)
 cp 4
 jp z,pb_soldiers
 ld ix,enemies
 ld b,4
pb_mecha_loop:
 push bc
 ld a,(ix+0)
 cp 2
 jp nz,pb_mecha_next
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
 ld c,1
 ld a,(bullet_power)      ; V1.5: el plasma quita tres impactos
 cp 2
 jp nz,pmh_damage
 ld c,3
pmh_damage:
 xor a
 ld (bullet_on),a
 ld a,(ix+6)
 sub c
 jp c,pmh_dead
 ld (ix+6),a
 jp nz,pb_mecha_damaged
pmh_dead:
 xor a
 ld (ix+6),a
 ld d,(ix+2)
 ld e,(ix+1)
 call restore_nine        ; el mecha destruido deja el suelo limpio
 xor a
 ld (ix+0),a
 call spawn_fx
 ld a,(mecha_remaining)
 dec a
 ld (mecha_remaining),a
 ld hl,kills
 inc (hl)
 ld a,3                  ; 300 puntos por mecha
 call add_score
pb_mecha_score_ok:
 call draw_score
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
 dec b                    ; djnz no llega: el bucle crecio con el plasma
 jp nz,pb_mecha_loop
pb_soldiers:
 ld ix,enemies
 ld b,4
pbs_loop:
 ld a,(ix+0)
 cp 1
 jp nz,pbs_next
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
 ld hl,kills
 inc (hl)
 ld a,1
 call add_score
pbs_score_ok:
 call sound_hit
 call draw_score
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
 ld a,(run_meter)          ; V1.8: y se vacia solo, un punto por tick
 or a
 jp z,us_meter_done
 dec a
 ld (run_meter),a
us_meter_done:
 call update_mechas
 call mecha_wave_check
 call ration_mid_check
 ld ix,enemies
 ld b,4
us_loop:
 push bc
 call move_hostile_bullet
 ld a,(ix+0)
 cp 1
 jp nz,us_next
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
 ld d,(ix+2)
 ld e,(ix+1)
 dec e
 call quad_free
 jp nz,us_assault_advance
 dec (ix+1)
 ld a,2
 ld (ix+6),a
 jp us_assault_advance
us_assault_right:
 cp 19
 jp nc,us_assault_advance
 ld d,(ix+2)
 ld e,(ix+1)
 inc e
 call quad_free
 jp nz,us_assault_advance
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
 ld d,(ix+2)
 inc d
 ld e,(ix+1)
 call quad_free
 jp nz,us_detect
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
 ld d,(ix+2)
 ld e,(ix+1)
 inc e
 call quad_free
 jp nz,us_detect
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
 ld d,(ix+2)
 ld e,(ix+1)
 dec e
 call quad_free
 jp nz,us_detect
 dec (ix+1)
 ld a,2
 ld (ix+6),a
us_detect:
 ; V1.3: Grit por debajo -> disparo hacia abajo; Grit ya les ha adelantado
 ; (por encima, a menos de 11 filas) -> se dan la vuelta y disparan arriba.
 xor a
 ld (shoot_up),a
 ld a,(player_y)
 ld c,a
 ld a,(ix+2)
 add a,2
 cp c
 jp nc,us_check_above
 ld a,(ix+2)
 add a,12
 cp c
 jp c,us_not_visible
 jp us_check_dx
us_check_above:
 ld a,(player_y)
 add a,2
 ld c,a
 ld a,(ix+2)
 cp c
 jp c,us_not_visible
 ld c,a
 ld a,(player_y)
 add a,11
 cp c
 jp c,us_not_visible
 ld a,1
 ld (shoot_up),a
us_check_dx:
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
 ld c,a
 ld a,(ix+8)               ; V1.8: el rojo (fijo) es tirador: ve a 12
 or a                      ; columnas; los demas a 8
 ld a,8
 jp nz,us_range_ok
 ld a,12
us_range_ok:
 cp c
 jp c,us_not_visible
 jp z,us_not_visible
 ld a,(ix+9)
 or a
 jp nz,us_not_visible
 ld a,(ix+3)
 or a
 jp nz,us_not_visible
 ld a,(ix+10)
 or a
 jp nz,us_countdown
 ld a,(run_meter)         ; V1.8: a quien llega corriendo le disparan
 cp 40                    ; casi sin aviso
 ld a,2
 jp nc,us_set_warn
 ld a,(phase)             ; V1.3: reaccion mas rapida en fases 2 y 3
 cp 1
 ld a,8
 jp z,us_set_warn
 ld a,5
us_set_warn:
 ld (ix+10),a
 jp us_next
us_countdown:
 dec a
 ld (ix+10),a
 jp nz,us_next
 ; Tope de balas enemigas visibles: 2 en la fase 1, 3 despues (V1.3).
 ld a,(enemies+3)
 ld c,a
 ld a,(enemies+15)
 add a,c
 ld c,a
 ld a,(enemies+27)
 add a,c
 ld c,a
 ld a,(enemies+39)
 add a,c
 ld c,a
 ld a,(phase)
 cp 1
 ld a,2
 jp z,us_cap_ready
 ld a,3
us_cap_ready:
 cp c
 jp z,us_next
 jp c,us_next
 ld a,(shoot_up)
 or a
 jp z,us_aim_down
 ; hacia arriba: de espaldas a la camara, bala desde encima del soldado.
 ; V1.8: recta si Grit esta en su columna; si no (4), la bala corrige su
 ; columna hacia Grit una vez cada dos filas: a quien huye le alcanza.
 ld (ix+6),0
 ld a,(player_x)
 ld c,a
 ld a,(ix+1)
 cp c
 ld a,3
 jp z,us_up_dir
 inc a
us_up_dir:
 ld (ix+7),a
 ld a,(ix+1)
 ld (ix+4),a
 ld a,(ix+2)
 dec a
 ld (ix+5),a
 jp us_shot_armed
us_aim_down:
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
us_shot_armed:
 ld a,1
 ld (ix+3),a
 ld a,(phase)
 cp 1
 jp z,us_set_easy_cool
 ld a,20
 jp us_set_cool
us_set_easy_cool:
 ld a,28
us_set_cool:
 ld c,a
 ld a,(ix+8)               ; V1.8: el tirador recarga 10 ticks antes
 or a
 ld a,c
 jp nz,us_cool_store
 sub 10
us_cool_store:
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
 ld a,(run_meter)          ; V1.8: corriendo, refuerzos el doble de rapido
 cp 40
 jp nc,us_spawn_fast
 ld a,(phase)
 cp 2
 jp z,us_spawn_fast
 ld a,b
 and 15
 ret nz
 jp spawn_soldier
us_spawn_fast:
 ld a,b
 and 7
 ret nz
 jp spawn_soldier

move_hostile_bullet:
 ld a,(ix+3)
 or a
 ret z
 ld a,(ix+7)              ; V1.8: la bala hacia arriba (Grit ya paso de
 cp 3                     ; largo) va a una casilla por tick, el doble que
 jp nc,mb_up              ; Grit: huir ya no basta, hay que apartarse
 ld a,(frame)
 and 1
 ret nz                  ; one tile per two frames: visibly dodgeable
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
 jp nc,mb_remove
 ld d,a
 ld e,(ix+4)
 call shot_blocked       ; V1.1: los muros tambien paran las balas enemigas
 or a
 ret z
mb_remove:
 xor a
 ld (ix+3),a
 ret
mb_up:
 jp z,mb_up_y              ; 3: recta
 ld a,(frame)              ; 4: una columna hacia Grit cada dos filas
 and 1
 jp nz,mb_up_y
 ld a,(player_x)
 cp (ix+4)
 jp z,mb_up_y
 jp c,mb_up_left
 inc (ix+4)
 jp mb_up_y
mb_up_left:
 dec (ix+4)
mb_up_y:
 ld a,(ix+5)
 dec a
 ld (ix+5),a
 cp 2
 jp c,mb_remove
 ld d,a
 ld e,(ix+4)
 call shot_blocked
 or a
 ret z
 jp mb_remove

spawn_soldier:
 ld ix,enemies
 ld b,4
 ld a,(phase)
 cp 3
 jp nz,ss_find
 ld ix,enemies+36         ; fase 3: los huecos 1-3 son de los mechas
 ld b,1
ss_find:
 ld a,(ix+0)
 or a
 jp z,ss_found
 ld de,12
 add ix,de
 djnz ss_find
 ret
ss_found:
 ; V1.8: tres entradas. Arriba (como siempre), por un lado a media pantalla
 ; o, si Grit lleva un rato avanzando sin parar, emboscada por un lado a
 ; su altura. Despues el rol; el rojo (fijo) solo se queda donde ve campo.
 ld a,(run_meter)
 cp 40
 jp nc,ss_ambush
 call rand
 and 3
 jp nz,ss_top               ; 3 de cada 4: arriba
 call rand
 and 7
 add a,5                    ; filas 5..12
 jp ss_side_row
ss_ambush:
 ; Emboscada por detras: 3..6 filas por debajo de Grit, cerca de el (busca
 ; suelo libre desde 4 columnas a su lado hacia fuera). Dispara hacia arriba.
 call rand
 and 3
 add a,3
 ld c,a
 ld a,(player_y)
 add a,c
 cp 20
 jp nc,ss_top
 ld (ix+2),a
 call rand
 and 1
 ld (ss_side),a
 jp ss_amb_scan
ss_side_row:
 ld (ix+2),a
 call rand
 and 1
 ld (ss_side),a
 ld b,7                     ; busca suelo libre desde el borde hacia dentro
 ld e,1
 ld c,1
 jp z,ss_scan_go
 ld e,21
 ld c,255
 jp ss_scan_go
; Emboscada: desde 4 columnas al lado de Grit hacia fuera.
ss_amb_scan:
 ld b,6
 ld a,(ss_side)
 or a
 ld a,(player_x)
 ld c,1
 jp nz,ss_amb_right
 ld c,255
 sub 4
 jp c,ss_top
 jp ss_amb_go
ss_amb_right:
 add a,4
ss_amb_go:
 ld e,a
ss_scan_go:
 ld d,(ix+2)
ss_scan:
 ld a,e                     ; fuera del campo (0 o 22..): se rinde
 or a
 jp z,ss_top
 cp 22
 jp nc,ss_top
 push de
 push bc
 call quad_free
 pop bc
 pop de
 jp z,ss_side_found
 ld a,e
 add a,c
 ld e,a
 djnz ss_scan
 jp ss_top
ss_side_found:
 push de                    ; nunca encima de Grit
 call actor_overlap
 pop de
 or a
 jp nz,ss_top
 ld (ix+1),e
 ld a,(ss_side)             ; mira hacia dentro
 or a
 ld a,3
 jp z,ss_face_in
 ld a,2
ss_face_in:
 ld (ix+6),a
 jp ss_place_row
ss_top:
 ld a,4
 ld (ss_tries),a
ss_try:
 call rand
 and 15                 ; keep both 8px columns inside the 24-column playfield
 add a,4                ; spawn at x=4..19
 ld (ix+1),a
 ld e,a
 ld a,1
 ld (ix+6),a
 ld d,4
 call quad_free          ; las cuatro celdas del soldado deben ser suelo
 jp z,ss_place
 ld a,(ss_tries)
 dec a
 ld (ss_tries),a
 jp nz,ss_try
 ret
ss_place:
 ld a,4
 ld (ix+2),a
ss_place_row:
 ld a,1
 ld (ix+0),a
 xor a
 ld (ix+3),a
 ld (ix+9),a
 ld (ix+10),a
 ld a,(ix+1)
 ld (ix+11),a
 call rand
 and 3
 jp z,ss_stationary
 cp 1
 jp z,ss_patrol
 ld a,2
 jp ss_role_store
ss_stationary:
 ; El tirador necesita ver: las 4 filas bajo el no pueden ser muro.
 ld d,(ix+2)
 inc d
 inc d
 ld e,(ix+1)
 ld b,4
ss_view:
 push bc
 push de
 call tile_solid
 pop de
 pop bc
 or a
 ld a,2                     ; tapado: mejor que vaya al asalto
 jp nz,ss_role_store
 inc d
 djnz ss_view
 ld a,1                     ; quieto y mirando hacia abajo
 ld (ix+6),a
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
 ld (ix+0),2
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
 ld b,4
um_loop:
 push bc
 ld a,(ix+0)
 cp 2
 jp nz,um_next
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
 ld d,(ix+2)
 ld e,(ix+1)
 call restore_column      ; libera la columna que abandona
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
 ld d,(ix+2)
 ld e,(ix+1)
 inc e
 inc e
 call restore_column
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
 ; V1.9: rabia a mitad de vida: parpadea en rojo, va el doble de rapido,
 ; dispara mas a menudo y siempre en abanico.
 ld a,(rage_flash)
 or a
 jp z,uh_no_flash
 dec a
 ld (rage_flash),a
uh_no_flash:
 ld a,(boss_rage)
 or a
 jp nz,uh_rage_ok
 ld a,(boss_half)
 ld b,a
 ld a,(boss_hp)
 cp b
 jp z,uh_enrage
 jp nc,uh_rage_ok
uh_enrage:
 ld a,1
 ld (boss_rage),a
 ld a,16
 ld (rage_flash),a
uh_rage_ok:
 ; cadencias: moverse cada 4 ticks (fase 3: cada 2); en rabia, la mitad
 ld a,(phase)
 cp 3
 ld c,3
 jp nz,uh_mmask
 ld c,1
uh_mmask:
 ld a,(boss_rage)
 or a
 jp z,uh_mmask_ok
 ld a,c                    ; C/2 (srl no esta en el ensamblador)
 rrca
 and 0x7f
 ld c,a
uh_mmask_ok:
 ld a,(frame)
 and c
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
 ; cadencia de disparo: fases 1 y 2 cada 16 ticks (antes 32 y 16), 3 cada 8;
 ; en rabia la mitad (la fase 3 sigue en 8: ya dispara en abanico).
 ld a,(phase)
 ld c,15
 cp 3
 jp nz,hs_mask
 ld c,7
 jp hs_mask_set
hs_mask:
 ld a,(boss_rage)
 or a
 jp z,hs_mask_set
 ld a,c                    ; C/2 (srl no esta en el ensamblador)
 rrca
 and 0x7f
 ld c,a
hs_mask_set:
 ld a,c
 ld (boss_mask),a
 ld a,(frame)
 and c
 ret nz
hind_fire_now:
 ld a,(boss_x)
 add a,2
 ld (shot_origin_x),a
 ld a,7
 ld (shot_origin_y),a
 ld a,(boss_rage)
 or a
 jp nz,hind_fan
 ld a,(phase)
 cp 3
 jp z,hind_fan
 ; V1.9: disparo apuntado. Si Grit esta bajo el jefe, recto desde la
 ; columna que tiene encima; si no, en diagonal hacia el desde el borde
 ; mas cercano (1 abajo-izquierda, 2 abajo-derecha).
 ld a,(boss_x)
 ld c,a
 ld a,(player_x)
 cp c
 jp c,hind_aim_left
 ld a,c
 add a,3
 ld c,a
 ld a,(player_x)
 cp c
 jp z,hind_aim_down
 jp c,hind_aim_down
 ld a,c                    ; a la derecha del jefe
 ld (shot_origin_x),a
 ld a,2
 jp hind_aim
hind_aim_left:
 ld a,c
 ld (shot_origin_x),a
 ld a,1
 jp hind_aim
hind_aim_down:
 ld a,(player_x)
 ld (shot_origin_x),a
 xor a
hind_aim:
 ld (shot_variant),a
 push af
 call emit_special_shot
 pop af
 or a
 ret z                     ; ya era recto
 ld a,(phase)
 cp 1
 ret z
 xor a                     ; fase 2: ademas uno recto
 ld (shot_variant),a
 jp emit_special_shot
hind_fan:
 xor a
 ld (shot_variant),a
 call emit_special_shot
 ld a,1
 ld (shot_variant),a
 call emit_special_shot
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
 push hl
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 ld a,(sector)
 cp 4
 jp z,uss_keep
 call shot_blocked
 or a
 jp nz,uss_kill
uss_keep:
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
 ; V1.1: derribar al jefe puntua: 2000 / 3000 / 4000.
 ld a,(phase)
 ld b,a
 add a,a
 add a,a
 add a,b
 add a,a
 add a,10
 call add_score
 call draw_hud
 ld a,(boss_x)            ; explosion sobre el jefe mientras suena la fanfarria
 inc a
 ld (fx_x),a
 ld a,5
 ld (fx_y),a
 ld a,8
 ld (fx_ttl),a
 call draw_dynamic
 call present_frame
 call boss_jingle
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
 ld b,4
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
 ld a,(ix+0)
 cp 2
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
 ld b,4
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
 ld hl,kills
 inc (hl)
 ld a,1
 call add_score
 call draw_score
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
 ld a,12                   ; V1.9: el tanque tocado parpadea en rojo
 ld (tank_flash),a
 ld a,(armor)
 dec a
 ld (armor),a
 jp nz,hurt_grace
 xor a
 ld (tank_mode),a
 ld a,(player_x)          ; el tanque revienta con la explosion estandar
 ld (fx_x),a
 ld a,(player_y)
 ld (fx_y),a
 ld a,8
 ld (fx_ttl),a
hurt_grace:
 call draw_bars           ; V1.3: solo cambian las barras
 ld a,25
 ld (invuln),a
 call sound_hurt
 ret
hurt_foot:
 ld a,(health)
 dec a
 ld (health),a
 jp nz,hurt_survive
 call death_sequence
 ld a,(lives)
 dec a
 ld (lives),a
 jp nz,hurt_new_life
 ld a,2
 ld (state),a
 ret
hurt_new_life:
 xor a
 ld (plasma_ammo),a       ; V1.5: el canon se pierde con la vida
 ld a,4
 ld (health),a
 ld a,50
 ld (invuln),a
 call draw_lives
 jp hurt_show
hurt_survive:
 ld a,28
 ld (invuln),a
hurt_show:
 call sound_hurt
 jp draw_bars             ; V1.3: las vidas ya se repintaron si cambiaron

; Muerte de Grit: el mundo se congela, explosion de dos fotogramas sobre el
; personaje con dos tonos graves, y se limpia antes de seguir.
death_sequence:
 push ix
 call draw_hud
 call draw_dynamic
 ld a,187
 call death_paint
 ld b,70
 ld c,110
 call tone
 ld b,6
ds_hold1:
 halt
 djnz ds_hold1
 ld a,191
 call death_paint
 ld b,60
 ld c,180
 call tone
 ld b,14
ds_hold2:
 halt
 djnz ds_hold2
 ld a,(player_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 call restore_quad
 pop ix
 ret
death_paint:
 ld (death_glyph),a
 ld a,(player_y)
 ld d,a
 ld a,(player_x)
 ld e,a
 ld a,(death_glyph)
 call paint_quad
 jp present_frame

; A=centenas a sumar. Marcador de seis cifras; cada 10.000 puntos, una vida
; (hasta las tres del HUD). Conserva BC y HL.
add_score:
 push bc
 push hl
 ld b,a
as_loop:
 ld hl,score+3
as_digit:
 inc (hl)
 ld a,(hl)
 cp 10
 jp c,as_next
 ld (hl),0
 dec hl
 ld a,l
 cp (score+1)&255
 jp nz,as_digit
 ld a,1
 ld (bonus_life),a
 jp as_digit
as_next:
 djnz as_loop
 ld a,(bonus_life)
 or a
 jp z,as_done
 xor a
 ld (bonus_life),a
 ld a,(lives)
 cp 3
 jp nc,as_done
 inc a
 ld (lives),a
 call sound_pickup
 call draw_hud            ; vida extra: se repinta el panel entero
as_done:
 pop hl
 pop bc
 ret

; Guarda el record de la sesion si la puntuacion lo supera.
update_hiscore:
 ld hl,score
 ld de,hiscore
 ld b,6
uh_compare:
 ld a,(de)
 cp (hl)
 jp c,uh_copy
 ret nz
 inc hl
 inc de
 djnz uh_compare
 ret
uh_copy:
 ld hl,score
 ld de,hiscore
 ld bc,6
 ldir
 ret

; D=fila E=columna de la esquina de un actor 2x2. Z (A=0) si las cuatro
; celdas son transitables. Conserva BC, DE, HL.
quad_free:
 call tile_solid
 or a
 ret nz
 inc e
 call tile_solid
 dec e
 or a
 ret nz
 inc d
 call tile_solid
 dec d
 or a
 ret nz
 inc d
 inc e
 call tile_solid
 dec d
 dec e
 or a
 ret

; A<>0 si la celda D,E detiene un proyectil: cualquier solido salvo el agua
; (tile 4), que impide andar pero no disparar por encima.
shot_blocked:
 push bc
 push hl
 call map_address
 ld a,(hl)
 cp 4
 jp z,sb_free
 ld l,a
 ld h,0
 ld bc,solid_flags
 add hl,bc
 ld a,(hl)
 pop hl
 pop bc
 ret
sb_free:
 xor a
 pop hl
 pop bc
 ret

; --- render / erase only dynamic cells -------------------------------------
erase_dynamic:
 ld a,(ration_available)
 or a
 jp z,erase_ration_done
 ld a,(ration_y)
 ld d,a
 ld a,(ration_x)
 ld e,a
 call restore_tile
erase_ration_done:
 ld a,(pickup_on)
 or a
 jp z,erase_pickup_done
 ld a,(pickup_y)
 ld d,a
 ld a,(pickup_x)
 ld e,a
 call restore_quad
erase_pickup_done:
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
 ld hl,bullets
 call erase_one_bullet
 ld hl,bullets+5
 call erase_one_bullet
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
 ld b,4
erase_actor_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,erase_no_actor
 ld a,(ix+2)
 ld d,a
 ld a,(ix+1)
 ld e,a
 ld a,(ix+0)
 cp 2
 jp nz,erase_regular_actor
 ; V1.1: los mechas no se borran cada tick: se repintan enteros desde el
 ; tile de fondo (paint_mecha). Solo se restaura lo que dejan al moverse.
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
 ld a,(ration_x)
 ld e,a
 ld a,27
 call paint_tile
draw_no_ration:
 call draw_pickup
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
 ld b,4
draw_actor_loop:
 push bc
 ld a,(ix+0)
 or a
 jp z,draw_skip_actor
 ld a,(ix+2)
 ld d,a
 ld a,(ix+1)
 ld e,a
 ld a,(ix+0)
 cp 2
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
 push af
 ld a,(ix+8)
 ld c,a
 ld b,0
 ld hl,role_colors
 add hl,bc
 ld a,(hl)
 ld (actor_attr),a
 pop af
 call paint_quad
 xor a
 ld (actor_attr),a
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
 call paint_mecha
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
 ld hl,bullets
 call draw_one_bullet
 ld hl,bullets+5
 call draw_one_bullet
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
 ; V1.9: casco verde militar y canon blanco; tocado, parpadea en rojo.
 push af
 ld a,(tank_flash)
 or a
 jp z,tdb_green
 dec a
 ld (tank_flash),a
 and 2
 jp z,tdb_green
 ld a,0x42
 jp tdb_set
tdb_green:
 ld a,0x44
tdb_set:
 ld (force_attr),a
 pop af
 add a,128
 call paint_quad
 ld a,(force_attr)
 cp 0x42
 jp z,tdb_turret
 ld a,0x47
 ld (force_attr),a
tdb_turret: ; Four cardinal gun directions painted as masked overlays on animated hull.
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
 call paint_tile
 xor a
 ld (force_attr),a
 ret
erase_one_bullet:
 ld a,(hl)
 or a
 ret z
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 jp restore_tile
draw_one_bullet:
 ld a,(hl)
 or a
 ret z
 inc hl
 ld e,(hl)
 inc hl
 ld d,(hl)
 inc hl
 ld b,(hl)
 inc hl
 ld a,(hl)
 or a
 jp z,dob_rifle
 ld hl,tank_shell_mask
 ld (mask_src),hl
 ld hl,tank_shell_sprite
 cp 2
 ld a,0x46              ; yellow shell, fixed legal ZX attribute
 jp nz,blit_masked_cell
 ld a,0x43              ; V1.5: bola de plasma magenta
 jp blit_masked_cell
dob_rifle:
 ld a,b
 add a,178
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
; V1.1: mecha de 3x3 celdas sin fase de borrado. Cada celda se compone de
; una vez: (tile del mapa AND mascara) OR sprite -> sombra, y de ahi a la
; pantalla. Es mas barato que restaurar + pintar con mascara + encolar.
paint_mecha:
 ld (quad_id),a
 ld b,3
pm_row:
 push bc
 ld c,3
pm_col:
 push bc
 call mecha_cell
 pop bc
 ld a,(quad_id)
 inc a
 ld (quad_id),a
 inc e
 dec c
 jp nz,pm_col
 dec e
 dec e
 dec e
 inc d
 pop bc
 djnz pm_row
 ret
mecha_cell:
 push de
 push ix
 call map_address
 ld l,(hl)
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,glyphs
 add hl,bc
 push hl                  ; tile de fondo
 ld a,(quad_id)
 ld c,a
 ld b,0
 ld hl,glyph_colors
 add hl,bc
 ld a,(hl)
 ld (blit_attr),a
 ld l,c
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld bc,glyphs
 add hl,bc                ; HL = sprite
 push hl
 ld bc,glyph_masks-glyphs
 add hl,bc
 push hl
 pop ix                   ; IX = mascara
 pop hl
 call phys_row
 ld (blit_y),a
 ld b,a
 rrca
 rrca
 rrca
 and 0xe0
 or e
 ld c,a
 ld a,b
 and 24
 add a,0xe0
 ld b,a                   ; BC = celda en la sombra
 pop de                   ; DE = tile de fondo
 ld a,(de)
 and (ix+0)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+1)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+2)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+3)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+4)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+5)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+6)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(de)
 and (ix+7)
 or (hl)
 ld (bc),a
 inc de
 inc hl
 inc b
 ld a,(blit_y)
 rrca
 rrca
 rrca
 and 3
 add a,0xf8
 ld b,a
 ld a,(blit_attr)
 ld (bc),a
 pop ix
 pop de
 jp present_cell
restore_column:
 call restore_tile
 inc d
 call restore_tile
 inc d
 jp restore_tile
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
 call boss_tint            ; V1.9: aviso de disparo / rabia
 call ph_body
 xor a
 ld (force_attr),a
 ret
; Aviso: los 4 ticks antes de disparar el jefe destella en blanco; al entrar
; en rabia parpadea en rojo.
boss_tint:
 ld a,(rage_flash)
 or a
 jp z,bt_warn
 ld a,(frame)
 and 2
 ret z
 ld a,0x42
 ld (force_attr),a
 ret
bt_warn:
 ld a,(boss_mask)
 ld b,a
 ld a,(frame)
 add a,4
 and b
 cp 4
 ret nc
 ld a,(frame)
 and 1
 ret z
 ld a,0x47
 ld (force_attr),a
 ret
ph_body:
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
 ld c,a
 ld b,0
 ld hl,glyph_colors
 add hl,bc
 ld a,(hl)
 cp 0x42                 ; V1.3: el casco rojo del soldado cambia segun su rol
 jp nz,pt_attr_ok
 ld a,(actor_attr)
 or a
 jp nz,pt_attr_ok
 ld a,0x42
pt_attr_ok:
 ld b,a                    ; V1.9: color forzado (tanque, jefe que avisa)
 ld a,(force_attr)
 or a
 jp nz,pt_forced
 ld a,b
pt_forced:
 ld (paint_attr),a
 ld l,c
 ld h,0
 add hl,hl
 add hl,hl
 add hl,hl
 ld a,c
 ld bc,glyphs
 add hl,bc
 cp 27
 jp c,paint_static
 cp 32
 jp c,paint_dynamic
 cp 195
 jp nc,paint_static
paint_dynamic:
 push hl
 ld bc,glyph_masks-glyphs
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
; input D=row E=column, output HL -> map_data + row*32 + column.
; map_data empieza en limite de pagina: sin sumas de 16 bits. Usa A y HL.
map_address:
 ld a,d
 rrca
 rrca
 rrca
 ld h,a
 and 0xe0
 or e
 ld l,a
 ld a,h
 and 3
 add a,map_data>>8
 ld h,a
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
 ld c,a
 call phys_row
 ld b,a                   ; fila fisica en el anillo
 rrca
 rrca
 rrca
 and 0xe0
 or e
 ld e,a                   ; byte bajo comun a bitmap y atributo
 ld a,b
 and 24
 add a,0xe0
 ld d,a
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,(hl)
 ld (de),a
 inc hl
 inc d
 ld a,b
 rrca
 rrca
 rrca
 and 3
 add a,0xf8
 ld d,a
 ld a,c
 ld (de),a
 pop hl
 pop de
 pop bc
 pop af
 ret

; Sprite con mascara expandida (1 px negro alrededor): preserva fondo.
; (bitmap_fondo AND mascara) OR sprite, en la pantalla sombra.
; HL=sprite, (mask_src)=mascara, D=fila, E=columna, A=atributo.
blit_masked_cell:
 call mark_dirty
 push af
 push bc
 push de
 push hl
 ld (blit_attr),a
 call phys_row
 ld (blit_y),a
 ld d,a
 rrca
 rrca
 rrca
 and 0xe0
 or e
 ld e,a
 ld a,d
 and 24
 add a,0xe0
 ld d,a
 ex de,hl                 ; HL=sombra, DE=sprite
 ld bc,(mask_src)
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(bc)
 and (hl)
 ex de,hl
 or (hl)
 ex de,hl
 ld (hl),a
 inc bc
 inc de
 inc h
 ld a,(blit_y)
 rrca
 rrca
 rrca
 and 3
 add a,0xf8
 ld h,a
 ld a,(blit_attr)
 ld (hl),a
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
; V1.1: los efectos ya no congelan el juego. Cada efecto es una lista de
; rafagas (ciclos, retardo) y se toca UNA rafaga corta por tick.
sfx_step:
 ld hl,(sfx_ptr)
 ld a,(hl)
 or a
 ret z
 ld b,a
 inc hl
 ld c,(hl)
 inc hl
 ld (sfx_ptr),hl
 jp tone
sfx_set:
 ld (sfx_ptr),hl
 pop hl
 ret
sound_fire:
 push hl
 ld hl,sfx_fire
 jp sfx_set
sound_pickup:
 push hl
 ld hl,sfx_pickup
 jp sfx_set
sound_hit:
 push hl
 ld hl,sfx_hit
 jp sfx_set
sound_hurt:
 push hl
 ld hl,sfx_hurt
 jp sfx_set
sound_mecha_down:
 push hl
 ld hl,sfx_mecha
 jp sfx_set
; Fanfarria corta (bloqueante: el juego esta parado entre fases).
boss_jingle:
 ld hl,jingle_boss
bj_loop:
 ld a,(hl)
 or a
 ret z
 ld b,a
 inc hl
 ld c,(hl)
 inc hl
 call tone
 halt
 jp bj_loop
sfx_none: db 0
sfx_fire: db 10,24,9,30,7,38,6,48,0
sfx_hit: db 4,70,8,30,3,90,5,55,2,120,0
sfx_hurt: db 3,90,3,100,2,115,2,130,2,150,2,170,0
sfx_pickup: db 5,56,6,44,8,35,10,28,11,22,0
sfx_mecha: db 2,140,6,40,2,160,5,50,2,180,4,65,2,200,2,230,0
jingle_boss: db 86,158,115,118,145,94,230,118,0
; Melodia original del titulo (La menor). Corchea ~110 ms.
title_tune:
 db 97,141,97,141,115,118,129,105,230,118,194,141
 db 86,158,86,158,97,141,115,118,194,141,11,0
 db 97,141,97,141,115,118,129,105,145,94,129,105,230,118
 db 97,141,86,158,72,188,86,158,194,141,30,0
 db 0

; --- strings ----------------------------------------------------------------
; Fullscreen title and Game Over are native Spectrum bitmaps, not ROM text.
; V1.2: icono de vida = cabeza de Grit con boina (8 px centrados en dos celdas)
hud_smiley_left: db 0x01,0x07,0x0f,0x05,0x07,0x06,0x03,0x00
hud_smiley_right: db 0xc0,0xe0,0xf0,0xa0,0xe0,0x60,0xc0,0x00
hud_smiley_empty: db 0x00,0x03,0x04,0x04,0x04,0x04,0x03,0x00
hud_smiley_empty_r: db 0x00,0xc0,0x20,0x20,0x20,0x20,0xc0,0x00
hud_bar_full: db 0x7e,0xbf,0xbf,0xff,0xff,0xff,0xff,0x7e
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
txt_record: db "RECORD ",0

; V1.2: copia el jefe de la fase (24 glifos, mascaras y atributos) sobre
; los indices 154..177 del banco grafico. Lancha, camion blindado o Hind.
load_boss_gfx:
 ld a,(phase)
 dec a
 ld hl,boss_bank
 ld bc,408
 or a
 jp z,lbg_copy
lbg_next:
 add hl,bc
 dec a
 jp nz,lbg_next
lbg_copy:
 ld de,glyphs+1232
 ld bc,192
 ldir
 ld de,glyph_masks+1232
 ld bc,192
 ldir
 ld de,glyph_colors+154
 ld bc,24
 ldir
 ret

card_texts:
 dw spc_1a,spc_1b,boss_1
 dw spc_2a,spc_2b,boss_2
 dw spc_3a,spc_3b,boss_3
card_colors: db 0x44,0x46,0x45
boss_1: db "LANCHA PATRULLERA",0
boss_2: db "CAMION BLINDADO",0
boss_3: db "HIND DEL COMISARIO",0
txt_jefe: db "ENEMIGO FINAL:",0
; esquinas y lado derecho: el mismo glifo reflejado
card_glyph_tr: db 0,0,248,8,232,40,40,40
card_glyph_bl: db 20,20,20,23,16,31,0,0
card_glyph_hb: db 0,0,0,255,0,255,0,0
card_glyph_br: db 40,40,40,232,8,248,0,0
card_glyph_vr: db 40,40,40,40,40,40,40,40
card_ptr: dw 0
card_color: db 0
rows_base: dw 0

; V1.3: oleadas de mechas en la fase 3. Al limpiar un grupo y avanzar ocho
; filas aparece otro de tres en lo alto (filas 2-4), lejos de Grit.
mecha_wave_check:
 ld a,(phase)
 cp 3
 ret nz
 ld a,(sector)
 cp 4
 ret z
 ld a,(mecha_remaining)
 or a
 ret nz
 ld a,(mecha_waves)
 or a
 ret z
 ld a,(camera_top)
 ld c,a
 ld a,(wave_camera)
 cp c
 ret c
 ld a,(mecha_waves)
 dec a
 ld (mecha_waves),a
 ld a,(wave_camera)
 sub 8
 ld (wave_camera),a
 ld a,3
 ld (mecha_remaining),a
 ld ix,enemies
 ld hl,wave_layout        ; en V: laterales arriba, central tres filas mas abajo
 ld b,3
mw_loop:
 ld c,(hl)
 inc hl
 ld (ix+0),2
 ld (ix+1),c
 ld (ix+7),c
 ld a,(hl)
 inc hl
 ld (ix+2),a
 ld (ix+6),6
 ld (ix+3),0
 ld (ix+10),0
 ld a,b
 and 1
 ld (ix+8),a
 ld a,b
 add a,a
 add a,a
 add a,8
 ld (ix+9),a
 ld de,12
 add ix,de
 djnz mw_loop
 jp sound_pickup

; V1.3: motor del tanque. Un "brum" grave cada vez que el tanque avanza,
; solo si no suena otro efecto. Dos tonos alternos para el traqueteo.
engine_sound:
 ld a,(tank_mode)
 or a
 ret z
 ld a,(player_moving)
 or a
 ret z
 ld hl,(sfx_ptr)
 ld a,(hl)
 or a
 ret nz
 ld b,3
 ld c,150
 ld a,(frame)
 and 2
 jp z,tone
 ld c,185
 jp tone

wave_layout: db 6,2,11,5,16,2   ; x,y: recorridos de +-3 sin cruzarse
role_colors: db 0,0x43,0x45      ; fijo (rojo), patrulla (magenta), asalto (cian)
actor_attr: db 0
shoot_up: db 0
ss_tries: db 0
mecha_waves: db 0
wave_camera: db 0

; V1.4: racion de refuerzo de la fase 3. Cuando la camara pasa la fila 12
; y no hay otra racion en pantalla, aparece una en lo alto (fila 3).
ration_mid_check:
 ld a,(ration_mid)
 or a
 ret z
 ld a,(ration_available)
 or a
 ret nz
 ld a,(camera_top)
 cp 13
 ret nc
 xor a
 ld (ration_mid),a
 ld a,3
 ld (ration_y),a
 call place_ration
 ld a,1
 ld (ration_available),a
 ret
ration_mid: db 0

; V1.5: canon de plasma. Dos cajas en la fase 3 (sectores 1 y 3), en una
; posicion 2x2 transitable al azar en la fila 15. Recogerla da 12 disparos
; que atraviesan muros y soldados y quitan 3 impactos a un mecha (2 al Hind).
setup_plasma:
 xor a
 ld (pickup_on),a
 ld a,(phase)
 cp 3
 ret nz
 ; rotulo ARMA sobre la franja magenta del modulo TANQUE (misma tipografia)
 ld hl,hud_arma_label
 ld d,20
 ld e,25
 ld b,6
sp_label:
 ld a,0x58
 call blit_cell
 push bc
 ld bc,8
 add hl,bc
 pop bc
 inc e
 djnz sp_label
 ld a,(sector)
 cp 2
 ret z
 cp 4
 ret z
 ld b,8
sp_try:
 push bc
 call rand
 and 15
 add a,4
 ld e,a
 ld (pickup_x),a
 ld d,15
 call quad_free
 pop bc
 jp z,sp_found
 djnz sp_try
 ret
sp_found:
 ld a,15
 ld (pickup_y),a
 ld a,1
 ld (pickup_on),a
 ret

check_pickup:
 ld a,(pickup_on)
 or a
 ret z
 ld a,(pickup_y)
 ld d,a
 ld a,(pickup_x)
 ld e,a
 call actor_overlap
 or a
 ret z
 xor a
 ld (pickup_on),a
 ld a,12
 ld (plasma_ammo),a
 call draw_bars
 jp sound_pickup

draw_pickup:
 ld a,(pickup_on)
 or a
 ret z
 ld a,(pickup_y)
 ld d,a
 ld a,(pickup_x)
 ld e,a
 ld hl,plasma_crate
 ld b,4
dp_cell:
 push bc
 push hl
 ld bc,32
 add hl,bc
 ld (mask_src),hl
 pop hl
 ld a,0xc3                ; FLASH + BRIGHT, tinta magenta: parpadea solo
 call blit_masked_cell
 ld bc,8
 add hl,bc
 inc e
 pop bc
 ld a,b
 cp 3
 jp nz,dp_next
 dec e
 dec e
 inc d
dp_next:
 djnz dp_cell
 ret

; V1.5: caja de armas con rayo (16x16), cuatro celdas y su mascara
plasma_crate:
 db 255,128,191,160,160,161,163,160
 db 255,1,241,113,225,193,241,225
 db 161,163,167,166,191,128,255,96
 db 193,129,1,1,241,1,255,6
 db 0,0,0,0,12,8,8,8
 db 0,0,4,4,4,4,4,4
 db 8,0,0,0,0,0,0,0
 db 12,28,60,4,4,0,0,0
sound_plasma:
 push hl
 ld hl,sfx_plasma
 jp sfx_set
sfx_plasma: db 6,18,6,26,5,36,5,50,4,70,0
plasma_ammo: db 0
pickup_on: db 0
pickup_x: db 0
pickup_y: db 0
bar2_attr: db 0x46
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
bullets: ds 10              ; V1.1: 2 x (on,x,y,dir,power)
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
enemies: ds 48              ; V1.3: 4 structs x 12 (active: 1 soldado, 2 mecha): active,x,y,shot,bx,by,face/hp,shot_dir/anchor,role,reload,warning,patrol_x
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
; --- V1.1 ---
score_guard: db 0
score: ds 6                 ; seis cifras decimales, la mas alta primero
hiscore: ds 6
bonus_life: db 0
ration_x: db 11
input_bits: db 0
kempston_ok: db 0
last_frames: db 0
music_on: db 0
music_ptr: dw 0
sfx_ptr: dw sfx_none
death_glyph: db 0
shadow_top: db 0            ; fila fisica de la sombra que contiene la fila logica 0
pp_phys: db 0
pp_log: db 0
sync_need: db 2
;%%RLE_ASSETS%%
code_end:
