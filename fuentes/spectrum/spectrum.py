# Port of the decorated MSX ANUBIS to the ZX Spectrum 48K.
# A small hardware layer (HAL) emulates the MSX VDP (shadow VRAM rendered to the
# Spectrum screen, software sprites), keyboard/joystick, beeper sound and the 50 Hz
# timer.  Every MSX BIOS call / port access of the game is redirected to it.
import struct, subprocess, sys
B = 0x8500
HAL = 0xF400
DELAY_LO, DELAY_HI = 0x40, 0x00
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

T2NOPS = 5
RATE = 223722 * 29 / 256        # TONE2 samples per second (loop padded to match; contended port FE included)
def half(p):
    """AY period -> TONE2 half period (AY clock 1.7897725 MHz)"""
    if not p: return 0
    return max(1, min(255, round(RATE * 16 * p / (2 * 1789772.5))))
def enc_len(n):
    if n & 255 == 0: n += 1
    return ((n >> 8) + 1) << 8 | (n & 255)
def music_table(d):
    """title tune: per note the channel A (arpeggio) and channel B (melody) half periods"""
    x = d[0x8c6e - B:0x8c6e - B + 0x45 * 4]
    out = []
    for i in range(0, len(x), 4):
        out.append((half(x[i] | x[i + 1] << 8), half(x[i + 2] | x[i + 3] << 8)))
    return out

ASM = r'''
SH      equ {SH}h
SHPAT   equ SH
SHNT    equ SH+0800h
SHSAT   equ SH+0B00h
SHCOL   equ SH+0B80h
SHSPR   equ SH+0BA0h
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
        pop hl
        pop af
        ei
        reti
JIF:    dw 0
FULL:   db 1
NREC:   db 0
REC:    ds 4*8

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
        call RENDER
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
        ld de,-1800h
        add hl,de
VP3:    push hl
        push bc
        call RENDER
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
        xor a
        ld (NREC),a
        ld a,1
        ld (FULL),a
        ret

; ------------------------------------------------------------------ rendering
; RENDER: HL = cell index 0..767
RENDER: push hl
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
        ld a,e                  ; giant lotus petals (light blue on MSX): bright cyan
        and 0F0h
        cp 50h
        jr nz,NOLOT
        ld a,c
        cp 0EFh
        jr z,LOT
        sub 21h
        cp 7
        jr nc,NOLOT
LOT:    ld b,45h
NOLOT:  ld l,c
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,SHPAT
        add hl,de
        ex de,hl
        pop hl
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
        ld b,8
RE1:    ld a,(de)
        ld (hl),a
        inc de
        inc h
        djnz RE1
        ret

PRESENT:
        push af
        push bc
        push de
        push hl
        push ix
        ld a,(FULL)
        or a
        jr z,PR1
        xor a
        ld (FULL),a
        ld (NREC),a
        ld hl,0
PR0:    push hl
        call RENDER
        pop hl
        inc hl
        ld a,h
        cp 3
        jr nz,PR0
        jr PR3
PR1:    ld a,(NREC)             ; erase the sprites drawn last time
        or a
        jr z,PR3
        ld b,a
        ld ix,REC
PR2:    push bc
        ld c,(ix+1)             ; cy
PR2y:   ld b,(ix+0)             ; cx
PR2x:   ld a,c
        cp 24
        jr nc,PR2n
        ld a,b
        cp 32
        jr nc,PR2n
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
PR2n:   inc b
        ld a,(ix+2)
        cp b
        jr nc,PR2x
        inc c
        ld a,(ix+3)
        cp c
        jr nc,PR2y
        ld de,4
        add ix,de
        pop bc
        djnz PR2
        xor a
        ld (NREC),a
PR3:    ld ix,SHSAT             ; draw the sprites
        ld b,32
PR4:    ld a,(ix+0)
        cp 0D0h
        jr z,PR9
        cp 0C0h
        jr nc,PR5
        ld a,(ix+3)
        and 0Fh
        jr z,PR5
        push bc
        call DRAWSPR
        pop bc
PR5:    ld de,4
        add ix,de
        djnz PR4
PR9:    pop ix
        pop hl
        pop de
        pop bc
        pop af
        ret

; DRAWSPR: IX -> SAT entry (y, x, pattern, colour)
DRAWSPR:
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
        ld c,0                  ; row k
DS1:    ld a,(SPY)
        add a,c
        cp 192
        jr nc,DS8
        ld (SPROW),a
        ld hl,(SPP)
        ld e,c
        ld d,0
        add hl,de
        ld a,(hl)               ; left byte
        ld de,16
        add hl,de
        ld d,(hl)               ; right byte
        ld e,0
        ld b,a
        ld a,(SPX)
        and 7
        jr z,DS3
        push bc
        ld c,b
        ld b,a
DS2:    srl c
        rr d
        rr e
        djnz DS2
        ld a,c
        pop bc
        ld b,a
DS3:    ; screen address of (SPROW, SPX>>3)
        ld a,(SPROW)
        and 0C0h
        rrca
        rrca
        rrca
        ld h,a
        ld a,(SPROW)
        and 7
        or h
        or 40h
        ld h,a
        ld a,(SPROW)
        and 38h
        add a,a
        add a,a
        ld l,a
        ld a,(SPX)
        rrca
        rrca
        rrca
        and 1Fh
        push af
        or l
        ld l,a
        ld a,(hl)
        or b
        ld (hl),a
        pop af
        cp 31
        jr z,DS8
        inc l
        push af
        ld a,(hl)
        or d
        ld (hl),a
        pop af
        cp 30
        jr z,DS8
        inc l
        ld a,(hl)
        or e
        ld (hl),a
DS8:    inc c
        ld a,c
        cp 16
        jr nz,DS1
        ; colour the empty background cells under the sprite, record the rectangle
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
        ld a,(SPX)
        rrca
        rrca
        rrca
        and 1Fh
        ld (RX0),a
        ld a,(SPX)
        add a,15
        jr nc,DA0
        ld a,0FFh
DA0:    rrca
        rrca
        rrca
        and 1Fh
        ld (RX1),a
        ld a,(SPY)
        rrca
        rrca
        rrca
        and 1Fh
        ld (RY0),a
        ld a,(SPY)
        add a,15
        rrca
        rrca
        rrca
        and 1Fh
        ld (RY1),a
        ld a,(NREC)
        cp 8
        jr nc,DA1
        ld l,a
        inc a
        ld (NREC),a
        ld h,0
        add hl,hl
        add hl,hl
        ld de,REC
        add hl,de
        ld a,(RX0)
        ld (hl),a
        inc hl
        ld a,(RY0)
        ld (hl),a
        inc hl
        ld a,(RX1)
        ld (hl),a
        inc hl
        ld a,(RY1)
        ld (hl),a
DA1:    ld a,(RY0)
        ld c,a
DA2:    ld a,c
        cp 24
        ret nc
        ld a,(RX0)
        ld b,a
DA3:    ld a,b
        cp 32
        jr nc,DA5
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
        push hl
        ld de,SHNT
        add hl,de
        ld a,(hl)
        pop hl
        cp 20h
        jr z,DA4
        cp {BLANK}
        jr nz,DA5
DA4:    ld de,5800h
        add hl,de
        ld a,(SPA)
        ld (hl),a
DA5:    inc b
        ld a,(RX1)
        cp b
        jr nc,DA3
        inc c
        ld a,(RY1)
        cp c
        jr nc,DA2
        ret
SPX:    db 0
SPY:    db 0
SPROW:  db 0
SPA:    db 0
SPP:    dw 0
RX0:    db 0
RX1:    db 0
RY0:    db 0
RY1:    db 0

; ------------------------------------------------------------------ input
; GTSTCK: A = 0 keys / 1 Kempston  ->  A = MSX direction 0..8
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
PRESENTQ:
        ret

GTTRIG: call PRESENT
        ld a,7Fh
        in a,(0FEh)
        bit 0,a
        ld a,0FFh
        ret z
        xor a
        ret

; KROW0: MSX keyboard row 0 (digits 0..7, bit = 0 when pressed)
KROW0:  call PRESENT
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
; ---- two-voice beeper engine: each sample outputs voice A then voice B (pulse interleaving)
; D = half period A (0 = silent), E = half period B (0 = silent), HL = duration (L + 256*(H-1) samples)
TONE2:  di
        ld a,10h
        inc d
        dec d
        jr nz,T2X
        xor a                   ; silent voice: mask 0, slowest counter (keeps the loop timing even)
        dec d
T2X:    ld (SMA+1),a
        ld a,10h
        inc e
        dec e
        jr nz,T2Y
        xor a
        dec e
T2Y:    ld (SMB+1),a
        ld b,d
        ld c,e
        xor a
        ex af,af'
        xor a
T2L:    dec b                   ; voice A
        jr nz,T2A
        ld b,d
SMA:    xor 10h
T2A:    out (0FEh),a
        ex af,af'
        dec c                   ; voice B
        jr nz,T2C
        ld c,e
SMB:    xor 10h
T2C:    ex (sp),hl
        ex (sp),hl
        out (0FEh),a
        ex af,af'
{T2PAD}
        dec l
        jr nz,T2L
        dec h
        jr nz,T2L
        xor a
        out (0FEh),a
        ei
        ret
; ---- AY emulation for the game's sound effects: register writes go to a shadow,
; the waits play the current tones of channels A and B on the beeper
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
        ld ix,PSGR
        ld hl,PSGR+8
        ld c,1
        call CHHALF
        push af
        ld ix,PSGR+2
        ld hl,PSGR+9
        ld c,2
        call CHHALF
        ld e,a
        pop af
        ld d,a
        pop hl
        pop ix
        jp TONE2
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
; ---- title tune: channel A arpeggio + channel B melody, both voices
MUSIC:  call PRESENT
        ld hl,NOTES
        ld b,{NNOTES}
MU1:    push bc
        ld d,(hl)
        inc hl
        ld e,(hl)
        inc hl
        push hl
        ld hl,{NOTELEN}
        call TONE2
        pop hl
        pop bc
        djnz MU1
        ret
NOTES:
{NOTES}

; MONSTERS + screen refresh (patched into the main-loop delay)
HALMON: call {MONSTERS}
        jp PRESENT

ATTRTAB:
{ATTR}
HALEND:
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
    nd = [v for pair in notes for v in pair]
    src = ASM.format(T2PAD='\n'.join(['        nop'] * T2NOPS), JIFLEN='0%Xh' % enc_len(int(RATE * 0.02)), BLIPLEN='0%Xh' % enc_len(int(RATE * 0.005)), NOTELEN='0%Xh' % enc_len(int(RATE * 0.223)), SH='0%X' % SH, HAL='0%X' % HAL, BLANK=art.BLANK, NNOTES=len(notes), NOTES=db_lines(nd),
                     MONSTERS='0%Xh' % sym['MONSTERS'], ATTR=db_lines(attr_table()))
    open('hal.asm', 'w').write(src)
    r = subprocess.run(['pasmo', '--bin', 'hal.asm', 'hal.bin', 'hal.sym'], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); sys.exit(1)
    hs = {}
    for line in open('hal.sym'):
        p = line.split()
        if len(p) >= 3 and p[1] == 'EQU': hs[p[0]] = int(p[2].rstrip('H'), 16)
    hal = open('hal.bin', 'rb').read()
    print('HAL %04X-%04X (%d bytes)' % (HAL, HAL + len(hal) - 1, len(hal)))
    assert HAL + len(hal) <= 0xFDFD
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
    img = bytearray(d) + bytes(HAL - (B + len(d))) + hal
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
    chdr = bytes([3]) + name.ljust(10).encode() + struct.pack('<HHH', len(img), B, 32768)
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
    print('image %04X-%04X, entry %d' % (B, B + len(img) - 1, hs['INIT']))
