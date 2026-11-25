# Port of the decorated MSX ANUBIS to the ZX Spectrum 48K.
# A small hardware layer (HAL) emulates the MSX VDP (shadow VRAM rendered to the
# Spectrum screen, software sprites), keyboard/joystick, beeper sound and the 50 Hz
# timer.  Every MSX BIOS call / port access of the game is redirected to it.
import struct, subprocess, sys
B = 0x8500
HAL = 0xF400
IMGBASE = 0x7600              # the loaded image starts with the sound code at 7600
DELAY_LO, DELAY_HI = 0x01, 0x00   # the loop is paced by HALMON (interrupt credits) instead
FRAMECREDIT, LOOPCOST, CREDMAX = 23, 10, 40
SH = 0x6000                # shadow VRAM: pat 0000 / name 0800 / sat 0B00 / col 0B80 / spr 0BA0

# MSX colour -> (spectrum colour, bright)
MSX2ZX = {0: (0, 0), 1: (0, 0), 2: (4, 0), 3: (4, 1), 4: (1, 0), 5: (1, 1), 6: (2, 0), 7: (5, 1),
          8: (2, 1), 9: (2, 1), 10: (6, 0), 11: (6, 1), 12: (4, 0), 13: (3, 1), 14: (7, 0), 15: (7, 1)}

def attr_table():
    t = []
    for v in range(256):
        fg, bg = v >> 4, v & 15
        ink, bi = MSX2ZX[fg]; paper, bp = MSX2ZX[bg]
        bright = bi if fg > 1 else bp
        t.append((bright << 6) | (paper << 3) | ink)
    return t

RATE = 3500000 / 141            # TONE2 samples per second (141 T loop)
def half(p):
    """AY period -> TONE2 half period (AY clock 1.7897725 MHz)"""
    if not p: return 0
    return max(1, min(255, round(RATE * 16 * p / (2 * 1789772.5))))
def enc_len(n):
    if n & 255 == 0: n += 1
    return ((n >> 8) + 1) << 8 | (n & 255)
MRATE = 3500000 / 62.5         # MUSIC loop: 61 T per sample (+ average ULA port contention)
NSEG = 11                       # segments per note (0.223 s / 11 = 20 ms)
def step(p):
    """AY period -> 16-bit phase step for the MUSIC loop (AY clock 1.7897725 MHz)"""
    return round(1789772.5 / (16 * p) * 65536 / MRATE) if p else 0
def music_table(d):
    """title tune: per note the phase steps of channel A (arpeggio) and channel B (melody);
    a silent channel takes the other one's note"""
    x = d[0x8c6e - B:0x8c6e - B + 0x45 * 4]
    out = []
    for i in range(0, len(x), 4):
        a, b = step(x[i] | x[i + 1] << 8), step(x[i + 2] | x[i + 3] << 8)
        m = b or a                  # one clean voice: the melody, or the arpeggio where there is none
        out.append((m, m))
    return out

ASM = r'''
SH      equ {SH}h
SHPAT   equ SH
SHNT    equ SH+0800h
SHSAT   equ SH+0B00h
SHCOL   equ SH+0B80h
SHSPR   equ SH+0BA0h
NRX     equ 7400h           ; sprite slot work area (free RAM below the stack)
SST     equ 7410h
CHG     equ 7420h
ENDF    equ 7424h
SROWS   equ 7430h           ; 4 slots x 30 rows x 3 bytes of shifted sprite
SPYS     equ 75A0h
SPAS     equ 75A4h
TCS     equ 75A8h
CURS    equ 75B8h
SROW    equ 75BAh           ; pointer to the current slot's buffer
CCX     equ 75C0h
CCY     equ 75C1h
CCN     equ 75C2h
CCA     equ 75C3h
CCI     equ 75C4h
TCX0    equ 75C6h
TCX1    equ 75C7h
TCY0    equ 75C8h
TCY1    equ 75C9h
ATTRTAB equ 7800h           ; MSX colour byte -> Spectrum attribute (built by INIT)
        org {HAL}h
; ------------------------------------------------------------------ start-up
INIT:   di
        ld sp,8000h
        ld hl,SH                ; clear the shadow VRAM
        ld de,SH+1
        ld bc,0EFFh
        ld (hl),0
        ldir
        ld hl,4000h             ; clear the screen
        ld de,4001h
        ld bc,1AFFh
        ld (hl),0
        ldir
        xor a
        out (0FEh),a
        ld hl,ATTRTAB           ; attribute table: ink/paper/bright from the MSX colour byte
        ld c,0
AT1:    push hl
        ld a,c
        rrca
        rrca
        rrca
        rrca
        and 0Fh
        ld e,a
        ld d,0
        ld hl,ZXC
        add hl,de
        ld b,(hl)               ; foreground: bit 3 bright, bits 0-2 colour
        ld a,c
        and 0Fh
        ld e,a
        ld hl,ZXC
        add hl,de
        ld d,(hl)               ; background
        pop hl
        ld a,d
        and 7
        rlca
        rlca
        rlca
        ld e,a
        ld a,b
        and 7
        or e
        ld e,a
        ld a,c
        and 0F0h
        cp 20h
        ld a,b
        jr nc,AT2
        ld a,d
AT2:    and 8
        rlca
        rlca
        rlca
        or e
        ld (hl),a
        inc hl
        inc c
        jr nz,AT1
        ld hl,0FE00h            ; IM2 vector table -> FDFDh
        ld de,0FE01h
        ld bc,256
        ld (hl),0FDh
        ldir
        ld a,0C3h
        ld (0FDFDh),a
        ld hl,ISR
        ld (0FDFEh),hl
        ld a,0FEh
        ld i,a
        im 2
        ld a,15
        ld (0F3E9h),a
        ld a,1
        ld (0F3EAh),a
        ei
        jp 8500h
ISR:    push af
        push hl
        ld hl,(JIF)
        inc hl
        ld (JIF),hl
        ld a,(CREDIT)           ; game-loop pacing: each frame earns time for {FRAMECREDIT}/{LOOPCOST} loops
        add a,{FRAMECREDIT}
        cp {CREDMAX}
        jr c,ISR1
        ld a,{CREDMAX}
ISR1:   ld (CREDIT),a
        ld a,(PBUSY)            ; during the game: refresh the sprites right here, at the start of
        or a                    ; the frame, so they are finished before the beam reaches the picture
        jr nz,ISR9
        ld a,(JIF)
        ld hl,LASTH
        sub (hl)
        cp 3
        call c,PRESENT
ISR9:   pop hl
        pop af
        ei
        reti
JIF:    dw 0
CREDIT: db 0
PBUSY:  db 0
FRAMEP: db 0
LASTH:  db 0F0h
FULL:   db 1
NREC:   db 4                    ; 4 sprite slots; an undrawn slot has the empty rectangle FF,FF,0,0
REC:    db 0FFh,0FFh,0,0,0FFh,0FFh,0,0,0FFh,0FFh,0,0,0FFh,0FFh,0,0

; ------------------------------------------------------------------ VRAM address translation
; in: HL = VRAM address   out: HL = shadow address, A = region (1 pat, 2 name, 3 sat, 4 col, 5 spr), Z if ignored
XLAT:   ld a,h
        cp 08h
        jr nc,XL1
        push de
        ld de,SHPAT
        add hl,de
        pop de
        ld a,1
        or a
        ret
XL1:    cp 18h
        jr c,XLN
        cp 1Bh
        jr nc,XL2
        push de
        ld de,SHNT-1800h
        add hl,de
        pop de
        ld a,2
        or a
        ret
XL2:    jr nz,XL3
        ld a,l
        cp 80h
        jr nc,XLN
        ld h,HIGH SHSAT
        ld a,l
        add a,LOW SHSAT
        ld l,a
        ld a,3
        or a
        ret
XL3:    cp 20h
        jr nz,XL4
        ld a,l
        cp 20h
        jr nc,XLN
        add a,LOW SHCOL
        ld l,a
        ld h,HIGH SHCOL
        ld a,4
        or a
        ret
XL4:    cp 38h
        jr c,XLN
        cp 3Bh
        jr nc,XLN
        push de
        ld de,SHSPR-3800h
        add hl,de
        pop de
        ld a,5
        or a
        ret
XLN:    xor a
        ret

; ------------------------------------------------------------------ BIOS replacements
WRTVRM: push hl
        push bc
        push de
        push af
        call XLAT
        jr z,WV9
        ld b,a
        pop af
        push af
        ld (hl),a
        ld a,b
        cp 2
        jr nz,WV2
        ld a,(FULL)
        or a
        jr nz,WV9
        ld de,-SHNT
        add hl,de
        call RENDERQ
        jr WV9
WV2:    cp 3
        jr z,WV9
        cp 5
        jr z,WV9
        ld a,1
        ld (FULL),a
WV9:    pop af
        pop de
        pop bc
        pop hl
        ret

RDVRM:  push hl
        call XLAT
        jr z,RV9
        ld a,(hl)
        pop hl
        ret
RV9:    pop hl
        xor a
        ret

LDIRVM: ex de,hl                ; HL = vram dest, DE = ram src
        push hl
        call XLAT
        pop hl
        ret z
        push af
        push hl                 ; vram start
        push bc
        call XLAT
        ex de,hl                ; HL = src, DE = shadow
        ldir
        pop bc
        pop hl
        pop af
VPOST:  cp 2                    ; A = region, HL = vram start, BC = count
        jr z,VP2
        cp 3
        ret z
        cp 5
        ret z
        ld a,1
        ld (FULL),a
        ret
VP2:    ld a,(FULL)
        or a
        ret nz
        ld a,b                  ; a big block (room drawing): one full redraw later is much faster
        or a
        jr nz,VPF
        ld a,c
        cp 64
        jr c,VP2a
VPF:    ld a,1
        ld (FULL),a
        ret
VP2a:
        ld de,-1800h
        add hl,de
VP3:    push hl
        push bc
        call RENDERQ
        pop bc
        pop hl
        inc hl
        dec bc
        ld a,b
        or c
        jr nz,VP3
        ret

FILVRM: push af
        push hl
        call XLAT
        jr z,FV8
        pop de                  ; DE = vram start
        ld (FVREG),a
        pop af
        push de
        push bc
        ld (hl),a
        dec bc
        ld a,b
        or c
        jr z,FV1
        ld d,h
        ld e,l
        inc de
        ldir
FV1:    pop bc
        pop hl
        ld a,(FVREG)
        jr VPOST
FV8:    pop hl
        pop af
        ret
FVREG:  db 0

LDIRMV: push de
        call XLAT
        pop de
        ret z
        ldir
        ret

INIT32: ld hl,SHNT
        ld de,SHNT+1
        ld bc,767
        ld (hl),20h
        ldir
        ld hl,SHPAT
        ld de,SHPAT+1
        ld bc,07FFh
        ld (hl),0
        ldir
        ld hl,SHSAT
        ld b,32
I32a:   ld (hl),0D1h
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        djnz I32a
        ld a,(0F3E9h)
        add a,a
        add a,a
        add a,a
        add a,a
        ld c,a
        ld a,(0F3EAh)
        and 0Fh
        or c
        ld hl,SHCOL
        ld b,32
I32b:   ld (hl),a
        inc hl
        djnz I32b
        call RECCLR
        ld a,1
        ld (FULL),a
        ret

; ------------------------------------------------------------------ rendering
; RENDER: HL = cell index 0..767
; CELLINFO: HL = cell index -> C = name, B = attribute, DE = pattern address (HL kept)
CELLINFO:
        push hl
        ld de,SHNT
        add hl,de
        ld a,(hl)
        ld c,a
        rrca
        rrca
        rrca
        and 1Fh
        ld e,a
        ld d,0
        ld hl,SHCOL
        add hl,de
        ld e,(hl)
        ld hl,ATTRTAB
        add hl,de
        ld b,(hl)
        ld l,c
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,SHPAT
        add hl,de
        ex de,hl
        pop hl
        ret
; RENDERQ: render a cell now unless a sprite covers it (then the next PRESENT recomposes it)
RENDERQ:
        push bc
        ld a,l
        and 1Fh
        ld b,a
        push hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld c,h
        pop hl
        push hl
        ld a,(NREC)
        ld e,a
        ld iy,REC
        call INRECT
        pop hl
        pop bc
        ret z
RENDER: call CELLINFO
        push hl
        ld a,h
        add a,58h
        ld h,a
        ld (hl),b
        pop hl
        ld a,h
        add a,a
        add a,a
        add a,a
        or 40h
        ld h,a
RE1:
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        ld (hl),a
        ret

PRESENT:
        push af
        push bc
        push de
        push hl
        push ix
        push iy
        ld a,1
        ld (PBUSY),a
        ld a,(FULL)
        or a
        jr z,PR1
        xor a
        ld (FULL),a
        call RECCLR
        ld hl,0
PR0:    push hl
        call RENDER
        pop hl
        inc hl
        ld a,h
        cp 3
        jr nz,PR0
        jr PR3
PR1:
PR3:    call SPRS
PR9:    xor a
        ld (PBUSY),a
        pop iy
        pop ix
        pop hl
        pop de
        pop bc
        pop af
        ret

; ---- sprites: only the slots that changed (or touch one that changed) are erased and redrawn
SPRS:   xor a
        ld (ENDF),a
        ld ix,SHSAT             ; 1: new rectangles and "changed" flags
        ld b,0
SS1:    push bc
        call SLOTP
        ld a,(ix+0)
        cp 0D0h
        jr nz,SS2
        ld a,1
        ld (ENDF),a
SS2:    ld a,(ENDF)
        or a
        jr nz,SSinv
        ld a,(ix+0)
        cp 0C0h
        jr nc,SSinv
        ld a,(ix+3)
        and 0Fh
        jr z,SSinv
        push hl
        push de
        call RECTOF
        pop de
        pop hl
        ld a,(RX0)
        ld (iy+0),a
        ld a,(RY0)
        ld (iy+1),a
        ld a,(RX1)
        ld (iy+2),a
        ld a,(RY1)
        ld (iy+3),a
        ld a,(de)
        cp 0FFh
        jr z,SSch
        ld a,(ix+0)
        cp (hl)
        jr nz,SSch
        inc hl
        ld a,(ix+1)
        cp (hl)
        jr nz,SSch
        inc hl
        ld a,(ix+2)
        cp (hl)
        jr nz,SSch
        inc hl
        ld a,(ix+3)
        cp (hl)
        jr nz,SSch
        xor a
        jr SSst
SSinv:  ld (iy+0),0FFh
        ld (iy+1),0FFh
        ld (iy+2),0
        ld (iy+3),0
        ld a,(de)
        cp 0FFh
        ld a,0
        jr z,SSst
SSch:   ld a,1
SSst:   pop bc
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld (hl),a
        ld de,4
        add ix,de
        inc b
        ld a,b
        cp 4
        jp nz,SS1
        ld a,(FRAMEP)           ; at most half the slots per frame: explorer + first monster,
        xor 1                   ; then the second monster (each sprite moves at 25 Hz)
        ld (FRAMEP),a
        ld hl,CHG
        jr z,PF0
        ld (hl),0
        inc hl
        ld (hl),0
        jr PF1
PF0:    inc hl
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
PF1:
        ld b,0                  ; 2: a sprite under a changed one must be redrawn too
S2a:    push bc
        call SLOTP
        push de
        pop ix                  ; IX = old rectangle of slot b
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jr nz,S2n
        ld a,(ix+0)
        cp 0FFh
        jr z,S2n
        push hl
        ld c,0
S2b:    ld hl,CHG
        ld e,c
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jr z,S2c
        ld a,c
        add a,a
        add a,a
        ld e,a
        ld iy,REC
        add iy,de
        call OVL
        jr z,S2m
        ld iy,NRX
        add iy,de
        call OVL
        jr z,S2m
S2c:    inc c
        ld a,c
        cp 4
        jr nz,S2b
        pop hl
        jr S2n
S2m:    pop hl
        ld (hl),1
S2n:    pop bc
        inc b
        ld a,b
        cp 4
        jr nz,S2a
        ld b,0                  ; 3: erase the old rectangles of the changed slots
S3a:    push bc
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jr z,S3n
        call SLOTP
        push de
        pop ix
        ld a,(ix+0)
        cp 0FFh
        call nz,ERASER
S3n:    pop bc
        inc b
        ld a,b
        cp 4
        jr nz,S3a
        ld b,0                  ; 4: build the changed sprites (shifted rows, rectangles)
S4a:    push bc
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        call nz,DRAWSLOT
        pop bc
        inc b
        ld a,b
        cp 4
        jr nz,S4a
        ld b,0                  ; 5: write their cells (background + every sprite on the cell)
S5a:    push bc
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jr z,S5n
        ld a,b
        add a,a
        add a,a
        ld e,a
        ld hl,NRX
        add hl,de
        ld a,(hl)
        cp 0FFh
        jr z,S5n
        ld a,b
        ld (CURS),a
        call COMPOSE
S5n:    pop bc
        inc b
        ld a,b
        cp 4
        jr nz,S5a
        ret
; DRAWSLOT: B = slot
DRAWSLOT:
        call SLOTP              ; HL = SST slot, DE = REC slot, IY = NRX slot
        push hl
        push de
        ld a,b
        add a,a
        add a,a
        ld e,a
        ld d,0
        ld ix,SHSAT
        add ix,de
        ld a,b
        ld (CURS),a
        ld a,(iy+0)
        cp 0FFh
        call nz,DRAWSPR
        pop de
        pop hl
        push iy                 ; REC slot = new rectangle
        pop bc
        ld a,(bc)
        ld (de),a
        inc bc
        inc de
        ld a,(bc)
        ld (de),a
        inc bc
        inc de
        ld a,(bc)
        ld (de),a
        inc bc
        inc de
        ld a,(bc)
        ld (de),a
        ld a,(ix+0)             ; SST slot = what was drawn
        ld (hl),a
        inc hl
        ld a,(ix+1)
        ld (hl),a
        inc hl
        ld a,(ix+2)
        ld (hl),a
        inc hl
        ld a,(ix+3)
        ld (hl),a
        ret
; OTHERS: OR into cell (CCX, CCY) the other sprites built this frame that cover it
OTHERS: ld b,0
OT1:    ld a,(CURS)
        cp b
        jp z,OT9
        ld hl,CHG
        ld e,b
        ld d,0
        add hl,de
        ld a,(hl)
        or a
        jp z,OT9
        ld a,b
        add a,a
        add a,a
        ld e,a
        ld iy,NRX
        add iy,de
        ld a,(CCX)
        cp (iy+0)
        jp c,OT9
        ld a,(iy+2)
        ld hl,CCX
        cp (hl)
        jp c,OT9
        ld a,(CCY)
        cp (iy+1)
        jp c,OT9
        ld a,(iy+3)
        ld hl,CCY
        cp (hl)
        jp c,OT9
        push bc
        ld a,(CCX)              ; offset = (cell row - its top + 7) * 3 + (column - its x0)
        sub (iy+0)
        ld c,a
        ld e,b
        ld d,0
        ld hl,SPYS
        add hl,de
        ld a,(CCY)
        add a,a
        add a,a
        add a,a
        sub (hl)
        add a,7
        ld l,a
        add a,a
        add a,l
        add a,c
        push af
        ld a,b
        call SRBASE
        pop af
        ld e,a
        ld d,0
        add hl,de
        push hl
        pop iy
        ld hl,(CCI)
        ld a,h
        add a,a
        add a,a
        add a,a
        or 40h
        ld h,a
        ld a,(hl)
        or (iy+0)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+3)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+6)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+9)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+12)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+15)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+18)
        ld (hl),a
        inc h
        ld a,(hl)
        or (iy+21)
        ld (hl),a
        inc h
        pop bc
OT9:    inc b
        ld a,b
        cp 4
        jp nz,OT1
        ret
; DRAWSPR: IX -> SAT entry (y, x, pattern, colour)
DRAWSPR:                        ; composite: each cell = background + sprite, written once
        ld a,(ix+0)
        inc a
        ld (SPY),a
        ld a,(ix+1)
        ld (SPX),a
        ld a,(ix+2)
        and 0FCh
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,SHSPR
        add hl,de
        ld (SPP),hl
        ld a,(ix+3)
        and 0Fh
        add a,a
        add a,a
        add a,a
        add a,a
        or 1
        ld e,a
        ld d,0
        ld hl,ATTRTAB
        add hl,de
        ld a,(hl)
        ld (SPA),a
        call RECTOF
        ld a,(CURS)             ; shifted sprite rows, with 7 empty rows above and below
        call SRBASE
        ld (SROW),hl
        ld b,21
SR0:    ld (hl),0
        inc hl
        djnz SR0
        ld de,48
        add hl,de
        ld b,21
SR1:    ld (hl),0
        inc hl
        djnz SR1
        ld a,(SPX)
        and 7
        ld c,a
        add a,a
        add a,c
        add a,a
        neg
        add a,42
        ld (DSJ+1),a
        xor a
        ld (TCM),a
        dec a
        ld (TFIRST),a
        push ix
        ld ix,(SPP)
        ld hl,(SROW)
        ld de,21
        add hl,de
        ld b,16
DNL:    ld c,(ix+0)
        ld d,(ix+16)
        ld e,0
DSJ:    jr DSH
DSH:
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        srl c
        rr d
        rr e
        ld (hl),c
        inc hl
        ld (hl),d
        inc hl
        ld (hl),e
        inc hl
        ld a,c
        or a
        jr z,DM1
        ld a,(TCM)
        or 1
        ld (TCM),a
DM1:    ld a,d
        or a
        jr z,DM2
        ld a,(TCM)
        or 2
        ld (TCM),a
DM2:    ld a,e
        or a
        jr z,DM3
        ld a,(TCM)
        or 4
        ld (TCM),a
DM3:    ld a,c
        or d
        or e
        jr z,DM4
        ld a,b
        ld (TLAST),a
        ld a,(TFIRST)
        inc a
        jr nz,DM4
        ld a,b
        ld (TFIRST),a
DM4:    inc ix
        dec b
        jp nz,DNL
        pop ix
        ld a,(TCM)              ; the cells that really have pixels
        or a
        jr nz,TK1
        ld a,0FFh
        ld (TCY0),a
        xor a
        ld (TCY1),a
        jr TK9
TK1:    ld b,a
        ld a,(SPX)
        rrca
        rrca
        rrca
        and 1Fh
        ld c,a
        bit 0,b
        jr nz,TK2
        inc a
        bit 1,b
        jr nz,TK2
        inc a
TK2:    ld (TCX0),a
        ld a,c
        bit 2,b
        jr z,TK3
        add a,2
        jr TK4
TK3:    bit 1,b
        jr z,TK4
        inc a
TK4:    ld (TCX1),a
        ld a,(TFIRST)
        ld b,a
        ld a,16
        sub b
        ld b,a
        ld a,(SPY)
        add a,b
        rrca
        rrca
        rrca
        and 1Fh
        ld (TCY0),a
        ld a,(TLAST)
        ld b,a
        ld a,16
        sub b
        ld b,a
        ld a,(SPY)
        add a,b
        rrca
        rrca
        rrca
        and 1Fh
        ld (TCY1),a
TK9:    ld a,(CURS)             ; keep this sprite's data in its slot
        ld e,a
        ld d,0
        ld hl,SPYS
        add hl,de
        ld a,(SPY)
        ld (hl),a
        ld hl,SPAS
        add hl,de
        ld a,(SPA)
        ld (hl),a
        ld a,e
        add a,a
        add a,a
        ld e,a
        ld hl,TCS
        add hl,de
        ld a,(TCX0)
        ld (hl),a
        inc hl
        ld a,(TCX1)
        ld (hl),a
        inc hl
        ld a,(TCY0)
        ld (hl),a
        inc hl
        ld a,(TCY1)
        ld (hl),a
        ret
; SRBASE: A = slot -> HL = its shifted-row buffer
SRBASE: add a,a
        ld e,a
        ld d,0
        ld hl,SRTAB
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        ex de,hl
        ret
SRTAB:  dw SROWS, SROWS+90, SROWS+180, SROWS+270
; COMPOSE: slot (CURS) -> its rectangle's cells written with background + sprites
COMPOSE:
        ld a,(CURS)
        ld e,a
        ld d,0
        ld hl,SPYS
        add hl,de
        ld a,(hl)
        ld (SPY),a
        ld hl,SPAS
        add hl,de
        ld a,(hl)
        ld (SPA),a
        ld a,e
        add a,a
        add a,a
        ld e,a
        ld hl,TCS
        add hl,de
        ld a,(hl)
        ld (TCX0),a
        inc hl
        ld a,(hl)
        ld (TCX1),a
        inc hl
        ld a,(hl)
        ld (TCY0),a
        inc hl
        ld a,(hl)
        ld (TCY1),a
        ld hl,NRX
        add hl,de
        ld a,(hl)
        ld (RX0),a
        inc hl
        ld a,(hl)
        ld (RY0),a
        inc hl
        ld a,(hl)
        ld (RX1),a
        inc hl
        ld a,(hl)
        ld (RY1),a
        ld a,(CURS)
        call SRBASE
        ld (SROW),hl
        ld a,(RY0)
        ld c,a
CC2:    ld a,c
        cp 24
        ret nc
        ld a,(RX0)
        ld b,a
CC3:    ld a,b
        cp 32
        jp nc,CC8
        ld (CCX),a
        ld a,c
        ld (CCY),a
        push bc
        ld l,c
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld e,b
        ld d,0
        add hl,de
        ld (CCI),hl
        call CELLINFO
        ld a,c
        ld (CCN),a
        ld a,b
        ld (CCA),a
        ld a,(CCY)              ; IX = SROW + (cell row - sprite top + 7) * 3 + column
        add a,a
        add a,a
        add a,a
        ld hl,SPY
        sub (hl)
        add a,7
        ld l,a
        add a,a
        add a,l
        ld l,a
        ld a,(RX0)
        ld h,a
        ld a,(CCX)
        sub h
        add a,l
        push de
        ld e,a
        ld d,0
        ld ix,(SROW)
        add ix,de
        pop de
        ld hl,(CCI)
        ld a,h
        add a,a
        add a,a
        add a,a
        or 40h
        ld h,a
        ld a,(de)
        or (ix+0)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+3)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+6)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+9)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+12)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+15)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+18)
        ld (hl),a
        inc de
        inc h
        ld a,(de)
        or (ix+21)
        ld (hl),a
        call OTHERS
        ld a,(CCN)
        cp 20h
        jr z,CA4
        cp {BLANK}
        jr z,CA4
        ld a,(CCA)              ; drawn cell: sprite ink over the cell's paper, if it has pixels
        ld b,a
        ld a,(CCX)
        ld hl,TCX0
        cp (hl)
        jr c,CA3
        ld hl,TCX1
        ld a,(hl)
        ld hl,CCX
        cp (hl)
        jr c,CA3
        ld a,(CCY)
        ld hl,TCY0
        cp (hl)
        jr c,CA3
        ld hl,TCY1
        ld a,(hl)
        ld hl,CCY
        cp (hl)
        jr c,CA3
        ld a,b
        and 38h
        ld b,a
        ld a,(SPA)
        and 47h
        or b
        jr CA5
CA3:    ld a,b
        jr CA5
CA4:    ld a,(SPA)
CA5:    ld hl,(CCI)
        ld de,5800h
        add hl,de
        ld (hl),a
        pop bc
CC8:    inc b
        ld a,(RX1)
        cp b
        jp nc,CC3
        inc c
        ld a,(RY1)
        cp c
        jp nc,CC2
        ret
SPX:    db 0
SPY:    db 0
SPROW:  db 0
DSN:    db 0
TCM:    db 0
TFIRST: db 0
TLAST:  db 0
SPA:    db 0
SPP:    dw 0
RX0:    db 0
RX1:    db 0
RY0:    db 0
RY1:    db 0



; ------------------------------------------------------------------ input
; GTSTCK: A = 0 keys / 1 Kempston  ->  A = MSX direction 0..8
PRESENTQ:
        ret
GTTRIG: call PRESENTX
        ld a,7Fh
        in a,(0FEh)
        bit 0,a
        ld a,0FFh
        ret z
        xor a
        ret

; KROW0: MSX keyboard row 0 (digits 0..7, bit = 0 when pressed)
KROW0:  call PRESENTX
        push bc
        ld a,0F7h
        in a,(0FEh)             ; 1..5 in bits 0..4
        rla
        or 0C1h
        ld b,a                  ; bits1..5 = keys 1..5
        ld a,0EFh
        in a,(0FEh)             ; 0 9 8 7 6
        ld c,a
        bit 0,c
        jr nz,K01
        res 0,b
K01:    bit 4,c
        jr nz,K02
        res 6,b
K02:    bit 3,c
        jr nz,K03
        res 7,b
K03:    ld a,b
        pop bc
        ret

; CHGET: wait for a key: digits, ENTER (0Dh), CAPS+0 = delete (08h)
CHGET:  push bc
        push hl
CG0:    call KEYCODE
        or a
        jr nz,CG0               ; wait for release
CG1:    call PRESENT
        call KEYCODE
        or a
        jr z,CG1
        ld (CGK),a
CG2:    call KEYCODE
        or a
        jr nz,CG2
        ld a,(CGK)
        pop hl
        pop bc
        ret
KEYCODE:
        ld a,0BFh
        in a,(0FEh)
        bit 0,a
        ld a,0Dh
        ret z
        ld a,0FEh
        in a,(0FEh)
        bit 0,a
        jr nz,KC1
        ld a,0EFh
        in a,(0FEh)
        bit 0,a
        ld a,08h
        ret z
KC1:    ld a,0F7h
        in a,(0FEh)
        ld b,a
        ld c,'1'
        ld l,5
KC2:    rr b
        ld a,c
        ret nc
        inc c
        dec l
        jr nz,KC2
        ld a,0EFh
        in a,(0FEh)
        ld b,a
        ld hl,KDIG
KC3:    rr b
        ld a,(hl)
        ret nc
        inc hl
        or a
        jr nz,KC3
        xor a
        ret
KDIG:   db '0','9','8','7','6',0
CGK:    db 0

KILBUF:
ERAFNK: ret

; ------------------------------------------------------------------ sound (beeper)
; TONE: HL = delay units per half period (26 T), DE = half periods
TONE:   di
        xor a
        ex af,af'
TO1:    ex af,af'
        xor 10h
        out (0FEh),a
        ex af,af'
        ld b,h
        ld c,l
TO2:    dec bc
        ld a,b
        or c
        jr nz,TO2
        dec de
        ld a,d
        or e
        jr nz,TO1
        xor a
        out (0FEh),a
        ei
        ret
BEEP:   push af
        push bc
        push de
        push hl
        ld hl,60
        ld de,100
        call TONE
        pop hl
        pop de
        pop bc
        pop af
        ret
; MONSTERS + screen refresh (patched into the main-loop delay)
; once per main loop: monsters, then wait for the loop's share of time (same speed in every room,
; ~115 loops/s like the MSX), and refresh the screen once per frame right after the interrupt,
; while the beam is still in the top border (the sprites no longer flicker)
HALMON: call {MONSTERS}
        ld a,(JIF)
        ld (LASTH),a
HM1:    di
        ld a,(CREDIT)
        sub {LOOPCOST}
        jr nc,HM2
        ei
        halt
        jr HM1
HM2:    ld (CREDIT),a
        ei
        ret

ZXC:
{ZXC}
; PRESENTX: input reads refresh the screen only outside the game loop (menus, waits); in the game
; loop HALMON already refreshes it once per frame, at the right moment
PRESENTX:
        push af
        push hl
        ld a,(JIF)
        ld hl,LASTH
        sub (hl)
        pop hl
        cp 3
        jr c,PX1
        pop af
        jp PRESENT
PX1:    pop af
        ret

; ---- sound loops: in uncontended memory, so their timing (and the pitch) is steady
; ---- beeper tone: D = half period in samples (0: use E; both 0: silence), HL = duration
; (L + 256*(H-1) samples of 137 T, ~25.5 kHz)
TONE2:  di
        ld a,d
        or a
        jr nz,T21
        ld d,e
T21:    ld a,10h
        inc d
        dec d
        jr nz,T22
        xor a                   ; silence
        dec d
T22:    ld (SMA+1),a
        ld b,d
        xor a
T2L:    dec b
        jr nz,T2A
        ld b,d
SMA:    xor 10h
T2A:    out (0FEh),a
        inc ix                  ; padding without memory access (the stack is in contended RAM)
        dec ix
        inc ix
        dec ix
        inc ix
        dec ix
        inc ix
        dec ix
        jp T2B
T2B:    nop
        nop
        dec l
        jr nz,T2L
        dec h
        jr nz,T2L
        xor a
        out (0FEh),a
        ei
        ret
; ---- title tune: one clean square wave (phase accumulator, so the pitch is exact) that alternates
; every ~20 ms between the melody (channel B) and the arpeggio (channel A), like the classic
; two-voice beeper tunes; the shared phase keeps the switches click-free
MUSIC:  call PRESENT
        di
        ld ix,NOTES
        ld hl,0
        ld a,{NNOTES}
        ld (MUN),a
MU1:    ld a,{NSEG}
        ld (MUS),a
MU2:    ld a,(MUS)
        cp 1
        jr nz,MU2a
        ld de,0                 ; last slice of each note: silence, so repeated notes are heard apart
        jr MU4
MU2a:   and 1
        ld a,(ix+0)
        jr nz,MU3               ; odd segments: melody (low nibble)
        rrca                    ; even segments: arpeggio (high nibble)
        rrca
        rrca
        rrca
MU3:    and 0Fh
        add a,a
        ld e,a
        ld d,0
        push hl
        ld hl,STEPS
        add hl,de
        ld e,(hl)
        inc hl
        ld d,(hl)
        pop hl
MU4:    ld bc,{SEGLEN}
MUL:    add hl,de
        ld a,h
        rrca
        rrca
        rrca
        and 10h
        out (0FEh),a
        dec c
        jr nz,MUL
        dec b
        jr nz,MUL
        ld a,0F7h               ; a menu key (1-5 or 0) stops the tune at once
        in a,(0FEh)
        and 1Fh
        cp 1Fh
        jr nz,MUQ
        ld a,0EFh
        in a,(0FEh)
        rra
        jr nc,MUQ
        ld a,(MUS)
        dec a
        ld (MUS),a
        jr nz,MU2
        inc ix
        ld a,(MUN)
        dec a
        ld (MUN),a
        jr nz,MU1
MUQ:    xor a
        out (0FEh),a
        ei
        ret
HALEND:
; ---- above the IM2 table (FE00-FF00, built by INIT)
        org 0FF01h
; SLOTP: B = slot -> HL = SST slot, DE = REC slot, IY = NRX slot
SLOTP:  ld a,b
        add a,a
        add a,a
        ld e,a
        ld d,0
        ld iy,NRX
        add iy,de
        ld hl,REC
        add hl,de
        push hl
        ld hl,SST
        add hl,de
        pop de
        ret
; OVL: rectangles at IX and IY overlap?  Z = yes
OVL:    ld a,(ix+2)
        cp (iy+0)
        jr c,OVN
        ld a,(iy+2)
        cp (ix+0)
        jr c,OVN
        ld a,(ix+3)
        cp (iy+1)
        jr c,OVN
        ld a,(iy+3)
        cp (ix+1)
        jr c,OVN
        xor a
        ret
OVN:    or 1
        ret
; RECCLR: no sprite on screen
RECCLR: push hl
        push bc
        ld hl,REC
        ld b,4
RC1:    ld (hl),0FFh
        inc hl
        ld (hl),0FFh
        inc hl
        ld (hl),0
        inc hl
        ld (hl),0
        inc hl
        djnz RC1
        pop bc
        pop hl
        ret
; ERASER: IX = rectangle (cells) -> background restored
ERASER: ld c,(ix+1)
ER2:    ld b,(ix+0)
ER3:    ld a,c
        cp 24
        jr nc,ER4
        ld a,b
        cp 32
        jr nc,ER4
        ld e,4                  ; a cell under a sprite is composed later, never blanked
        ld iy,NRX
        call INRECT
        jr z,ER4
        ld l,c
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld e,b
        ld d,0
        add hl,de
        push bc
        call RENDER
        pop bc
ER4:    inc b
        ld a,(ix+2)
        cp b
        jr nc,ER3
        inc c
        ld a,(ix+3)
        cp c
        jr nc,ER2
        ret
; RECTOF: SAT entry IX -> cell rectangle RX0, RY0, RX1, RY1
RECTOF: ld a,(ix+1)
        rrca
        rrca
        rrca
        and 1Fh
        ld (RX0),a
        ld a,(ix+1)
        add a,15
        jr nc,RT0
        ld a,0FFh
RT0:    rrca
        rrca
        rrca
        and 1Fh
        ld (RX1),a
        ld a,(ix+0)
        inc a
        ld c,a
        rrca
        rrca
        rrca
        and 1Fh
        ld (RY0),a
        ld a,c
        add a,15
        rrca
        rrca
        rrca
        and 1Fh
        ld (RY1),a
        ret

; INRECT: is cell (B = x, C = y) inside one of E rectangles (x0, y0, x1, y1) at IY?  Z = yes
INRECT: ld a,e
        or a
        jr z,INR0
INR1:   ld a,b
        cp (iy+0)
        jr c,INR2
        ld a,(iy+2)
        cp b
        jr c,INR2
        ld a,c
        cp (iy+1)
        jr c,INR2
        ld a,(iy+3)
        cp c
        jr c,INR2
        xor a
        ret
INR2:   inc iy
        inc iy
        inc iy
        inc iy
        dec e
        jr nz,INR1
INR0:   or 1
        ret
HIEND:
; ---- sound code below the stack (loaded with the game image)
        org 7600h
; ---- AY emulation for the game's sound effects: register writes go to a shadow,
; the waits play the current tones of channels A, B and C on the beeper
PSGR:   ds 16
HPSGW:  push hl
        ld hl,PSGR
        and 0Fh
        add a,l
        ld l,a
        jr nc,HPW1
        inc h
HPW1:   ld (hl),e
        pop hl
        ret
; channel tone -> half period: period * 0.113, 0 if muted
CHHALF: ld a,(PSGR+7)
        and c
        jr nz,CHOFF
        ld a,(hl)
        and 0Fh
        jr z,CHOFF
        ld e,(ix+0)
        ld a,(ix+1)
        and 0Fh
        cp 9
        jr nc,CHHMAX
        ld d,a
        srl d                   ; half period = (period / 2 * 29) >> 7
        rr e
        ld h,d
        ld l,e
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        or a
        sbc hl,de
        sbc hl,de
        sbc hl,de
        add hl,hl
        jr c,CHHMAX
        ld a,h
        jr CHH1
CHHMAX: ld a,0FFh
CHH1:   or a
        ret nz
        inc a
        ret
CHOFF:  xor a
        ret
SFX:    push ix                 ; HL = duration
        push hl
        push bc
        ld ix,PSGR
        ld hl,PSGR+8
        ld c,1
        call CHHALF
        ld (SFXH),a
        ld ix,PSGR+2
        ld hl,PSGR+9
        ld c,2
        call CHHALF
        ld (SFXH+1),a
        ld ix,PSGR+4
        ld hl,PSGR+10
        ld c,4
        call CHHALF
        ld (SFXH+2),a
        ld a,(SFXALT)           ; several channels sounding: take turns call by call (20 ms slices)
        ld b,3
SFX1:   inc a
        cp 3
        jr c,SFX2
        xor a
SFX2:   ld c,a
        ld e,a
        ld d,0
        ld hl,SFXH
        add hl,de
        ld a,(hl)
        or a
        jr nz,SFX3
        ld a,c
        djnz SFX1
        xor a                   ; all silent
SFX3:   ld d,a                  ; D = half period (0: silence)
        ld e,0
        ld a,c
        ld (SFXALT),a
        pop bc
        pop hl
        pop ix
        jp TONE2
SFXALT: db 0
SFXH:   ds 3
HWAITJ: push hl                 ; B jiffies of sound
        push de
HWJ1:   push bc
        ld hl,{JIFLEN}             ; 20 ms of samples
        call SFX
        pop bc
        djnz HWJ1
        pop de
        pop hl
        ret
HWAITP: push bc                 ; refresh the screen, then wait
        call PRESENT
        pop bc
        jr HWAITJ
HPSGDLY: call PRESENT           ; countdown blip (screen + ~5 ms of tone)
        ld hl,{BLIPLEN}
        jp SFX
MUN:    db 0
MUS:    db 0
STEPS:
{STEPS}
NOTES:
{NOTES}

; GTSTCK (joystick/keys) lives here, in the low part of the image
GTSTCK: push bc
        ld c,a
        call PRESENTQ
        ld b,0                  ; bits: 0 up 1 down 2 left 3 right
        ld a,0FBh
        in a,(0FEh)
        bit 0,a                 ; Q
        jr nz,GS1
        set 0,b
GS1:    ld a,0FDh
        in a,(0FEh)
        bit 0,a                 ; A
        jr nz,GS2
        set 1,b
GS2:    ld a,0DFh
        in a,(0FEh)
        bit 1,a                 ; O
        jr nz,GS3
        set 2,b
GS3:    bit 0,a                 ; P
        jr nz,GS4
        set 3,b
GS4:    ld a,0EFh
        in a,(0FEh)
        bit 3,a                 ; 7 up
        jr nz,GS5
        set 0,b
GS5:    bit 4,a                 ; 6 down
        jr nz,GS6
        set 1,b
GS6:    bit 2,a                 ; 8 right
        jr nz,GS7
        set 3,b
GS7:    ld a,0F7h
        in a,(0FEh)
        bit 4,a                 ; 5 left
        jr nz,GS8
        set 2,b
GS8:    ld a,c
        or a
        jr z,GS9
        in a,(1Fh)              ; Kempston: 0 right 1 left 2 down 3 up
        bit 3,a
        jr z,GSa
        set 0,b
GSa:    bit 2,a
        jr z,GSb
        set 1,b
GSb:    bit 1,a
        jr z,GSc
        set 2,b
GSc:    bit 0,a
        jr z,GS9
        set 3,b
GS9:    ld a,b
        and 0Fh
        ld c,a
        ld b,0
        push hl
        ld hl,DIRTAB
        add hl,bc
        ld a,(hl)
        pop hl
        pop bc
        ret
DIRTAB: db 0,1,5,0,7,8,6,7,3,2,4,3,0,1,5,0
LOEND:
'''

def db_lines(data, per=16):
    return '\n'.join('        db ' + ','.join(str(b) for b in data[i:i + per]) for i in range(0, len(data), per))

BIOS = {0x4A: 'RDVRM', 0x4D: 'WRTVRM', 0x5C: 'LDIRVM', 0x56: 'FILVRM', 0x59: 'LDIRMV', 0x6F: 'INIT32',
        0xCC: 'ERAFNK', 0xD5: 'GTSTCK', 0xD8: 'GTTRIG', 0xC0: 'BEEP', 0x9F: 'CHGET', 0x156: 'KILBUF'}

def build(src_bin='anubis_new.bin', mons_sym='mons.sym'):
    import art
    d = bytearray(open(src_bin, 'rb').read())
    sym = {}
    for line in open(mons_sym):
        p = line.split()
        if len(p) >= 3 and p[1] == 'EQU': sym[p[0]] = int(p[2].rstrip('H'), 16)
    notes = music_table(d)
    steps = sorted(set(v for pair in notes for v in pair))
    assert len(steps) <= 16
    nd = [steps.index(a) << 4 | steps.index(b) for a, b in notes]
    sd = [v for st in steps for v in (st & 255, st >> 8)]
    src = ASM.format(FRAMECREDIT=FRAMECREDIT, LOOPCOST=LOOPCOST, CREDMAX=CREDMAX, JIFLEN='0%Xh' % enc_len(int(RATE * 0.02)), BLIPLEN='0%Xh' % enc_len(int(RATE * 0.005)), NSEG=NSEG, SEGLEN='0%Xh' % enc_len(int(MRATE * 0.223 / NSEG)), SH='0%X' % SH, HAL='0%X' % HAL, BLANK=art.BLANK, NNOTES=len(notes), NOTES=db_lines(nd), STEPS=db_lines(sd),
                     MONSTERS='0%Xh' % sym['MONSTERS'], ZXC=db_lines([(MSX2ZX[c][1] << 3) | MSX2ZX[c][0] for c in range(16)]))
    open('hal.asm', 'w').write(src)
    r = subprocess.run(['pasmo', '--bin', 'hal.asm', 'hal.bin', 'hal.sym'], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); sys.exit(1)
    hs = {}
    for line in open('hal.sym'):
        p = line.split()
        if len(p) >= 3 and p[1] == 'EQU': hs[p[0]] = int(p[2].rstrip('H'), 16)
    hal = open('hal.bin', 'rb').read()
    print('HAL %04X-%04X + FF01-%04X' % (HAL, hs['HALEND'] - 1, hs['HIEND'] - 1))
    assert hs['HALEND'] <= 0xFDFD and hs['HIEND'] <= 0x10000
    # ---- patch the game
    n = 0
    for i in range(len(d) - 2):
        if d[i] in (0xCD, 0xC3):
            t = d[i + 1] | d[i + 2] << 8
            if t in BIOS:
                a = hs[BIOS[t]]; d[i + 1] = a & 255; d[i + 2] = a >> 8; n += 1
    print('BIOS calls redirected:', n)
    def patch_seq(old, new):
        cnt = 0; i = 0
        while True:
            j = d.find(old, i)
            if j < 0: break
            d[j:j + len(new)] = new; cnt += 1; i = j + 1
        return cnt
    k = hs['KROW0']
    c1 = patch_seq(bytes([0x3E, 0xF0, 0xD3, 0xAA, 0xDB, 0xA9]), bytes([0xCD, k & 255, k >> 8, 0, 0, 0]))
    j = hs['JIF']
    c2 = patch_seq(bytes([0x3A, 0x9E, 0xFC]), bytes([0x3A, j & 255, j >> 8]))
    mu = hs['MUSIC']
    d[0x8C00 - B:0x8C03 - B] = bytes([0xC3, mu & 255, mu >> 8])
    def jpat(at, target):
        d[at - B:at + 3 - B] = bytes([0xC3, target & 255, target >> 8])
    jpat(sym['PSGW'], hs['HPSGW'])
    jpat(sym['WAITJ'], hs['HWAITJ'])
    jpat(sym['PSGDLY'], hs['HPSGDLY'])
    w = sym['WAITJ']; nw = 0
    for a in range(sym['DEATH'], sym['CODE10END'] - 2):
        if d[a - B] == 0xCD and (d[a - B + 1] | d[a - B + 2] << 8) == w:
            d[a - B + 1] = hs['HWAITP'] & 255; d[a - B + 2] = hs['HWAITP'] >> 8; nw += 1
    assert nw == 2
    left = [a + B for a in range(len(d) - 1) if d[a] == 0xD3 and d[a + 1] in (0xA0, 0xA1) and not 0x8C00 <= a + B < 0x8C6E and not sym['PSGW'] <= a + B < sym['PSGW'] + 6]
    assert not left, [hex(a) for a in left]
    hm = hs['HALMON']
    at = sym['DELAY1'] + 4
    assert d[at - B] == 0xCD and (d[at - B + 1] | d[at - B + 2] << 8) == sym['MONSTERS']
    d[at - B + 1] = hm & 255; d[at - B + 2] = hm >> 8
    # the Spectrum spends ~18k T per main loop refreshing the screen: shorten the delay to keep the MSX speed
    dl = sym['DELAY1'] + 11
    assert d[dl - B:dl - B + 3] == bytes([0x21, 0x00, 0x03])
    d[dl - B + 1] = DELAY_LO; d[dl - B + 2] = DELAY_HI
    print('keyboard reads patched:', c1, ' timer reads patched:', c2)
    # ---- one memory image 8500..HALEND
    assert hal[hs['INIT'] - IMGBASE] == 0xF3, 'hal.bin must start at IMGBASE'
    assert hs['LOEND'] <= 0x7800
    img = bytearray(hal)
    assert not any(img[B - IMGBASE:B - IMGBASE + len(d)]), 'HAL overlaps the game'
    img[B - IMGBASE:B - IMGBASE + len(d)] = d
    return img, hs

# ------------------------------------------------------------------ TAP
def tap_block(flag, data):
    body = bytes([flag]) + bytes(data)
    cs = 0
    for b in body: cs ^= b
    body += bytes([cs])
    return struct.pack('<H', len(body)) + body

def basic_line(num, tokens):
    return struct.pack('>H', num) + struct.pack('<H', len(tokens) + 1) + tokens + b'\r'

def make_tap(img, entry, out, name='ANUBIS'):
    VAL, CLEAR, LOAD, CODE, RAND, USR, BORDER, PAPER, INK, CLS = 0xB0, 0xFD, 0xEF, 0xAF, 0xF9, 0xC0, 0xE7, 0xDA, 0xD9, 0xFB
    def num(v): return bytes([VAL]) + b'"' + str(v).encode() + b'"'
    toks = (bytes([BORDER]) + num(0) + b':' + bytes([PAPER]) + num(0) + b':' + bytes([INK]) + num(7) + b':' +
            bytes([CLS]) + b':' + bytes([CLEAR]) + num(24575) + b':' + bytes([LOAD]) + b'""' + bytes([CODE]) + b':' +
            bytes([RAND, USR]) + num(entry))
    prog = basic_line(10, toks)
    hdr = bytes([0]) + name.ljust(10).encode() + struct.pack('<HHH', len(prog), 10, len(prog))
    chdr = bytes([3]) + name.ljust(10).encode() + struct.pack('<HHH', len(img), IMGBASE, 32768)
    data = tap_block(0, hdr) + tap_block(0xFF, prog) + tap_block(0, chdr) + tap_block(0xFF, img)
    open(out, 'wb').write(data)

# ------------------------------------------------------------------ TAP -> WAV (standard ROM timings)
def tap_to_wav(tapfile, wavfile, rate=44100):
    import wave, array
    data = open(tapfile, 'rb').read()
    T = 3500000
    out = array.array('h'); level = [20000]; acc = [0.0]
    def pulse(t):
        acc[0] += t * rate / T
        n = int(acc[0]); acc[0] -= n
        out.extend([level[0]] * n); level[0] = -level[0]
    def pause(sec):
        out.extend([0] * int(rate * sec))
    i = 0
    pause(0.5)
    while i < len(data):
        ln = data[i] | data[i + 1] << 8; blk = data[i + 2:i + 2 + ln]; i += 2 + ln
        for _ in range(8063 if blk[0] < 128 else 3223): pulse(2168)
        pulse(667); pulse(735)
        for b in blk:
            for k in range(7, -1, -1):
                t = 1710 if (b >> k) & 1 else 855
                pulse(t); pulse(t)
        pause(1.0)
    w = wave.open(wavfile, 'wb'); w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    w.writeframes(out.tobytes()); w.close()
    return len(out) / rate

if __name__ == '__main__':
    img, hs = build()
    open('anubis_zx.bin', 'wb').write(img)
    make_tap(img, hs['INIT'], 'ANUBIS_ZX.tap')
    print('image %04X-%04X, entry %d' % (IMGBASE, IMGBASE + len(img) - 1, hs['INIT']))
