# Adds moving monsters + lives system on top of the decorated build
import subprocess, sys
import make, monsters, art
from rooms import Mem
B = 0x8500
DATA, DATA_END = 0x87D0, 0x8B40     # unused tail of the title font block
CODE, CODE_END = 0xB898, 0xBB34     # unused padding/leftovers inside the game code area
CODE2, CODE2_END = 0xA10F, 0xA224   # unreachable NOP padding after the main loop
CODE3, CODE3_END = 0xBBDD, 0xBDDC   # zero padding
CODE4, CODE4_END = 0xE000, 0xE5C0   # empty per-room routine slots (rooms 164-255)
CODE5, CODE5_END = 0xDC10, 0xDE40   # empty per-room routine slots (rooms 101-135)
VARS, VARS_END = 0xDE50, 0xDED0     # empty room slots 137-144
CODE6, CODE6_END = 0xDEE0, 0xDFF0   # empty room slots 146-162
CODE7, CODE7_END = 0xD900, 0xDAC0   # empty room slots 52-79
CODE8, CODE8_END = 0xDAD0, 0xDC00   # empty room slots 81-99
CODE9, CODE9_END = 0xD720, 0xD790   # empty room slots 22-28 (sounds)
CODE10, CODE10_END = 0xD7E0, 0xD8A0 # empty room slots 34-45 (death sequence)
DATA2, DATA2_END = 0xD610, 0xD6C0   # empty room slots 5-15 (game-over text)

ASM = r'''
JIFFY   equ 0FC9Eh
ROOM    equ 0F304h
BLANK   equ {BLANK}
        org {DATA}h
PATS:
{PATS}
ROOMTAB:
{ROOMTAB}
TYPETAB:
{TYPETAB}
COLTAB: db 0,3,9,15,13,14,7
LIVES:  db 10
INV:    db 0
BLINK:  db 0
LASTJ:  db 0
LASTR:  db 0FFh
TICK:   db 0
RCODE:  db 0
RPAR:   db 0
TPTR:   dw 0
SAVESP: dw 0
MON0:   ds 8
MON1:   ds 8
SATB:   ds 8
DATAEND:

        org {CODE2}h
COLLIDE:
        ld a,(MODE)
        cp 1
        ret z
        ld a,(INV)
        or a
        ret nz
        ld hl,1B00h
        call 004Ah
        ld d,a
        ld hl,1B01h
        call 004Ah
        ld e,a
        ld ix,MON0
        call MCHK
        jr c,HIT
        ld ix,MON1
        call MCHK
        ret nc
HIT:    ld a,100
        ld (INV),a
        ld a,1
        ld (BLINK),a
        call HURTSND
        ld hl,LIVES
        dec (hl)
        call LIVESRAM
        ld hl,0CD56h
        ld de,1AB6h
        ld bc,2
        call 005Ch
        ld a,(LIVES)
        or a
        ret nz
GAMEOVER:
        jp DEATH
MCHK:   ld a,(ix+0)
        or a
        ret z
        cp 4
        jr z,MCS
        cp 6
        jr z,MCS
        ld b,(ix+2)
        ld c,(ix+1)
        jr MC1
MCS:    ld b,(ix+1)
        ld c,(ix+2)
MC1:    ld a,d
        sub b
        jr nc,MC2
        neg
MC2:    cp 12
        ret nc
        ld a,e
        sub c
        jr nc,MC3
        neg
MC3:    cp 11
        ret
LIVESRAM:
        ld a,(LIVES)
        ld b,'0'-1
LR0:    inc b
        sub 10
        jr nc,LR0
        add a,10+'0'
        ld c,a
        ld a,b
        cp '0'
        jr z,LR1
        ld (0CD56h),a
        ld a,c
        ld (0CD57h),a
        ret
LR1:    ld a,c
        ld (0CD56h),a
        ld a,BLANK
        ld (0CD57h),a
        ret
ADDD:   ld a,(hl)
        add a,c
        cp '9'+1
        jr c,AD1
        sub 10
        ld (hl),a
        dec hl
        ld c,1
        ld a,l
        cp 4Ah
        ret z
        jr ADDD
AD1:    ld (hl),a
        ret
FLAGADDR:
        ld c,a
        rrca
        rrca
        rrca
        and 31
        ld e,a
        ld d,0
        ld hl,FLAGS
        add hl,de
        ld a,c
        and 7
        ld b,a
        ld a,1
        ret z
FA1:    add a,a
        djnz FA1
        ret
CODE2END:
        org {CODE}h
GAMESTART:
        ld (SAVESP),sp
        ld a,10
        ld (LIVES),a
        call LIVESRAM
        ld a,0FFh
        ld (LASTR),a
        xor a
        ld (INV),a
        ld (BLINK),a
        ld (MON0),a
        ld (MON1),a
        ld (PKACT),a
        ld hl,FLAGS
        ld b,33
GS1:    ld (hl),a
        inc hl
        djnz GS1
        ld hl,0CD4Bh
        ld b,4
GS2:    ld (hl),'0'
        inc hl
        djnz GS2
        ld a,(JIFFY)
        ld (LASTJ),a
        jp 0A000h

DELAY1: push bc
        push de
        push ix
        call MONSTERS
        pop ix
        pop de
        pop bc
        ld hl,300h
D1:     dec hl
        ld a,h
        or l
        jr nz,D1
        ret
DELAY2: push bc
        push de
        push ix
        call MONSTERS
        pop ix
        pop de
        pop bc
        ld hl,500h
D2:     dec hl
        ld a,h
        or l
        jr nz,D2
        ret

MONSTERS:
        ld a,(ROOM)
        ld b,a
        ld a,(LASTR)
        cp b
        jr z,MS0
        call NEWROOM
        call MODEFIX
        call PKSETUP
MS0:    call PKCHK
        call ENDCHK
        ld a,(JIFFY)
        ld b,a
        ld a,(LASTJ)
        ld c,a
        ld a,b
        ld (LASTJ),a
        sub c
        ret z
        cp 5
        jr c,MS1
        ld a,4
MS1:    ld b,a
MS2:    push bc
        call STEP
        pop bc
        djnz MS2
        call DRAW
        jp COLLIDE

STEP:   ld hl,TICK
        inc (hl)
        ld a,(INV)
        or a
        jr z,ST0
        dec a
        ld (INV),a
        jr nz,ST0
        ld (BLINK),a
ST0:    ld ix,MON0
        call MSTEP
        ld ix,MON1
MSTEP:  ld a,(ix+0)
        or a
        ret z
        ld a,(TICK)
        and (ix+6)
        ret nz
        ld a,(ix+1)
        add a,(ix+5)
        ld (ix+1),a
        cp (ix+3)
        jr z,MSL
        jr c,MSL
        cp (ix+4)
        ret c
        ld a,(ix+0)
        cp 6
        jr z,MSW
        ld (ix+5),0FFh
        ret
MSW:    ld a,(ix+3)
        ld (ix+1),a
        ret
MSL:    ld (ix+5),1
        ret

DRAW:   ld a,(TICK)
        rrca
        rrca
        rrca
        and 1
        add a,a
        add a,a
        ld c,a
        ld hl,SATB
        ld ix,MON0
        call MDRAW
        ld ix,MON1
        call MDRAW
        ld hl,SATB
        ld de,1B04h
        ld bc,8
        call 005Ch
        ld a,(BLINK)
        or a
        ld a,0Bh
        jr z,DR1
        ld a,(TICK)
        and 4
        ld a,0Bh
        jr z,DR1
        xor a
DR1:    ld hl,1B03h
        jp 004Dh
MDRAW:  ld a,(ix+0)
        or a
        jr nz,MD1
        ld (hl),0D1h
        inc hl
        inc hl
        inc hl
        inc hl
        ret
MD1:    push hl
        ld e,a
        ld d,0
        ld hl,AXTAB
        add hl,de
        ld b,(hl)
        ld hl,PBTAB
        add hl,de
        ld a,(hl)
        add a,c
        ld e,a
        pop hl
        ld a,(ix+0)
        cp 4
        jr nc,MD2
        bit 7,(ix+5)
        jr nz,MD2
        ld a,e
        add a,8
        ld e,a
MD2:    ld a,b
        or a
        jr nz,MDV
        ld a,(ix+2)
        ld (hl),a
        inc hl
        ld a,(ix+1)
        jr MD3
MDV:    ld a,(ix+1)
        ld (hl),a
        inc hl
        ld a,(ix+2)
MD3:    ld (hl),a
        inc hl
        ld (hl),e
        inc hl
MDC:    push hl
        ld e,(ix+0)
        ld d,0
        ld hl,COLTAB
        add hl,de
        ld a,(hl)
        pop hl
        ld (hl),a
        inc hl
        ret

; ---- secret modes: menu key 3 = monsters harmless, key 4 = no monsters
MENUX:  bit 3,a
        jr z,MX3
        bit 4,a
        jp nz,8587h
MX4:    ld a,2
        jr MXS
MX3:    ld a,1
        jr MXS
GSNORM: xor a
MXS:    ld (MODE),a
        jp GAMESTART
MODEFIX:
        ld a,(MODE)
        cp 2
        ret nz
        xor a
        ld (MON0),a
        ld (MON1),a
        ret
PATS2:
{PATS2}
ECOL:
{ECOL}
CODEEND:
        org {CODE3}h
PKTAB:
{PKTAB}
PKGAIN:
        ld a,(PKCODE)
        and 40h
        jr nz,PANKH
        ld hl,0CD4Eh
        ld c,5
        call ADDD
        ld hl,0CD4Dh
        ld c,2
        call ADDD
        ld hl,0CD4Bh
        ld de,1AABh
        ld bc,4
        jp 005Ch
PANKH:  ld a,(LIVES)
        cp 99
        ret nc
        inc a
        ld (LIVES),a
        call LIVESRAM
        ld hl,0CD56h
        ld de,1AB6h
        ld bc,2
        jp 005Ch
LOADS:  ld a,(ix+1)
        ld (PKCODE),a
        ld a,(ix+2)
        ld (PKX),a
        ld a,(ix+3)
        ld (PKY),a
        ld l,(ix+4)
        ld h,(ix+5)
        ld (PKADDR),hl
        ret
PKX2:
{PKX2}
        db 0FFh
CODE3END:
        org {VARS}h
PKACT:  db 0
MODE:   db 0
STROOM: db 0
PKCODE: db 0
PKX:    db 0
PKY:    db 0
PKADDR: dw 0
FLAGS:  ds 32
EXFL:   db 0
SLOTS:  ds 27
VARSEND:
        org {CODE4}h
ENDING: ld hl,ETXT
        call ENDSCR
        call SCORE
        call 8C00h
EW:     xor a
        call 00D8h
        or a
        jr z,EW
        ld sp,(SAVESP)
        jp 8500h
SCORE:  ld hl,0CD4Bh
        ld de,{SCOREADDR}
        ld bc,4
        jp 005Ch
ENDSCR: push hl
        ld hl,1B00h
        ld a,0D1h
        call 004Dh
        ld hl,1B04h
        ld a,0D1h
        call 004Dh
        ld hl,1B08h
        ld a,0D1h
        call 004Dh
        ld hl,1800h
        ld bc,768
        ld a,20h
        call 0056h
        ld hl,EPAT
        ld b,{NPAT}
EP1:    push bc
        ld a,(hl)
        inc hl
        push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ex de,hl
        pop hl
        push hl
        ld bc,8
        call 005Ch
        pop hl
        ld bc,8
        add hl,bc
        pop bc
        djnz EP1
        ld hl,ECOL
        ld de,2000h
        ld bc,32
        call 005Ch
        ld hl,ESEG
        call SEGS
        pop hl
SEGS:   ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,d
        or a
        ret z
        ld c,(hl)
        ld b,0
        inc hl
        push hl
        push bc
        call 005Ch
        pop bc
        pop hl
        add hl,bc
        jr SEGS
EPAT:
{EPAT}
ESEG:
{ESEG}
        dw 0
ETXT:
{ETXT}
        dw 0
CODE4END:
        org {DATA2}h
GTXT:
{GTXT}
        dw 0
HURTSND: ld a,7                 ; two low tones a semitone apart, bending down
        ld e,0BCh
        call PSGW
        ld a,8
        ld e,0Fh
        call PSGW
        ld a,9
        call PSGW
        ld hl,0380h
        ld b,14
HS1:    push bc
        xor a
        ld e,l
        call PSGW
        ld a,1
        ld e,h
        call PSGW
        push hl
        ld de,-58
        add hl,de
        ld a,2
        ld e,l
        call PSGW
        ld a,3
        ld e,h
        call PSGW
        pop hl
        ld de,12
        add hl,de
        ld b,1
        call WAITJ
        pop bc
        djnz HS1
        jp SNDOFF
DATA2END:
        org {CODE9}h
; ---- PSG sounds
PSGW:   out (0A0h),a
        ld a,e
        out (0A1h),a
        ret
WAITJ:  ld a,(JIFFY)
        add a,b
        ld c,a
WJ1:    ld a,(JIFFY)
        cp c
        jr nz,WJ1
        ret
PSGDLY: ld hl,500h              ; ~9 ms busy wait while a PSG tone sounds
PDL:    dec hl
        ld a,h
        or l
        jr nz,PDL
        ret
JOYSND: ld a,7                  ; quick rising C major arpeggio
        ld e,0BEh
        call PSGW
        ld a,8
        ld e,0Dh
        call PSGW
        ld hl,JOYT
JS1:    ld a,(hl)
        or a
        jr z,SNDOFF
        ld e,a
        xor a
        call PSGW
        ld a,1
        ld e,0
        call PSGW
        inc hl
        ld b,3
        call WAITJ
        jr JS1
SNDOFF: ld a,8
        ld e,0
        call PSGW
        ld a,9
        call PSGW
        ld a,7
        ld e,0B8h
        jp PSGW
JOYT:   db 0D6h,0AAh,08Fh,06Bh,0
CODE9END:
        org {CODE10}h
; ---- death: colour-cycling player + falling tone, then the game-over screen
DEATH:  ld hl,1B04h
        ld a,0D1h
        call 004Dh
        ld hl,1B08h
        ld a,0D1h
        call 004Dh
        ld a,7
        ld e,0BEh
        call PSGW
        ld hl,30h
        ld b,120
DT1:    push bc
        push hl
        xor a
        ld e,l
        call PSGW
        ld a,1
        ld e,h
        call PSGW
        ld a,b
        srl a
        srl a
        cp 16
        jr c,DT2
        ld a,15
DT2:    ld e,a
        ld a,8
        call PSGW
        ld a,b
        rra
        and 7
        ld e,a
        ld d,0
        ld hl,DCOL
        add hl,de
        ld a,(hl)
        ld hl,1B03h
        call 004Dh
        ld b,1
        call WAITJ
        pop hl
        ld d,h
        ld e,l
        ld b,5
DT3:    srl d
        rr e
        djnz DT3
        add hl,de
        inc hl
        pop bc
        djnz DT1
        call SNDOFF
        ld hl,1B00h
        ld a,0D1h
        call 004Dh
        ld b,40
        call WAITJ
        ld hl,GTXT
        call ENDSCR
        call SCORE
        jp EW
DCOL:   db 15,11,10,9,8,13,7,3
CODE10END:
        org {CODE5}h
; ---- menu dispatcher: 3 harmless monsters, 4 no monsters, 5 choose the starting screen
GS0:    xor a
        ld (STROOM),a
        jp GSNORM
MENU2:  ld b,a
        xor a
        ld (STROOM),a
        ld a,b
        bit 3,a
        jp z,MX3
        bit 4,a
        jp z,MX4
        bit 5,a
        jp nz,8587h
MODE5:  ld hl,M5TAB
        ld b,M5N
M5L:    push bc
        ld e,(hl)
        ld d,0
        ex de,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ex de,hl                ; DE = VRAM dest
        inc hl
        ld a,(hl)
        inc hl
        push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld bc,0CDA0h
        add hl,bc
        ld bc,8
        call 005Ch
        pop hl
        pop bc
        djnz M5L
        ld hl,M5CUR
        ld de,0B2h*8
        ld bc,8
        call 005Ch
        ld hl,2014h             ; colour groups 20-22 : light yellow
        ld b,3
M5C:    ld a,0B1h
        call 004Dh
        inc hl
        djnz M5C
        ld hl,M5TXT
        ld de,{PROMPT}
        ld bc,10
        call 005Ch
M5W:    ld a,0F0h               ; wait until key 5 is released
        out (0AAh),a
        in a,(0A9h)
        bit 5,a
        jr z,M5W
        call 0156h              ; KILBUF
        xor a
        ld (M5N_),a
M5D:    ld hl,M5DIG             ; show digits + cursor
        ld de,{PROMPT}+10
        ld bc,4
        call 005Ch
        call 009Fh              ; CHGET
        cp 0Dh
        jr z,M5OK
        cp 08h
        jr z,M5BS
        cp '0'
        jr c,M5D
        cp '9'+1
        jr nc,M5D
        ld c,a
        ld a,(M5N_)
        cp 3
        jr nc,M5D
        ld e,a
        ld d,0
        inc a
        ld (M5N_),a
        ld hl,M5DIG
        add hl,de
        ld a,c
        sub '0'
        add a,{D0}
        ld (hl),a
        inc hl
        ld (hl),{CUR}
        jr M5D
M5BS:   ld a,(M5N_)
        or a
        jr z,M5D
        dec a
        ld (M5N_),a
        ld e,a
        ld d,0
        ld hl,M5DIG
        add hl,de
        ld (hl),{CUR}
        inc hl
        ld (hl),20h
        jr M5D
M5OK:   ld hl,M5DIG             ; value = digits (clamped to 255)
        ld a,(M5N_)
        ld b,a
        ld de,0
        or a
        jr z,M5V
M5P:    ld a,(hl)
        sub {D0}
        push hl
        ld h,d
        ld l,e
        add hl,hl
        add hl,hl
        add hl,de
        add hl,hl               ; *10
        ld e,a
        ld d,0
        add hl,de
        ex de,hl
        pop hl
        inc hl
        djnz M5P
M5V:    ld a,d
        or a
        ld a,e
        jr z,M5S
        ld a,255
M5S:    ld (STROOM),a
        xor a
        jp MXS
M5N_:   db 0
M5CUR:  db 0,0,0,0,0,0,7Eh,7Eh
M5DIG:  db {CUR},20h,20h,20h
M5TXT:  db {TXT}
M5TAB:
{M5TAB}
M5N     equ {M5COUNT}
ENDCHK: ld a,(LASTR)
        cp {LROOM}
        ret nz
        ld hl,1B00h
        call 004Ah
        add a,9
        ld d,a
        ld hl,1B01h
        call 004Ah
        add a,8
        ld e,a
        ld a,d
        sub {LCY}
        jr nc,EC1
        neg
EC1:    cp 16
        ret nc
        ld a,e
        sub {LCX}
        jr nc,EC2
        neg
EC2:    cp 18
        ret nc
        jp CNTDOWN
CODE5END:
        org {CODE6}h
; ---- touching the lotus: the riches drain away while the explorer flashes in colours
CNTDOWN:
        ld b,0
CD1:    ld hl,0CD4Bh
        ld c,4
CDZ:    ld a,(hl)
        cp '0'
        jr nz,CDGO
        inc hl
        dec c
        jr nz,CDZ
        jr CDEND
CDGO:   push bc
        ld hl,0CD4Eh
        ld c,5
        call SUBD
        ld hl,0CD4Bh
        ld de,1AABh
        ld bc,4
        call 005Ch
        pop bc
        inc b
        ld a,b
        and 0Fh
        cp 2
        jr nc,CDC
        add a,2
CDC:    ld hl,1B03h
        call 004Dh
        ld a,b                  ; PSG tone A: falling-coins blip
        add a,a
        add a,a
        and 7Fh
        add a,40h
        ld e,a
        xor a
        call PSGW
        ld a,1
        ld e,0
        call PSGW
        ld a,7
        ld e,0BEh
        call PSGW
        ld a,8
        ld e,0Ch
        call PSGW
        call PSGDLY
        jr CD1
CDEND:  call SNDOFF
        ld hl,1B03h
        ld a,0Fh
        call 004Dh
        ld a,(JIFFY)
        add a,60
        ld e,a
CDW:    ld a,(JIFFY)
        cp e
        jr nz,CDW
        jp ENDING
SUBD:   ld a,(hl)               ; subtract C from the digit at (HL), borrowing leftwards
        sub c
        cp '0'
        jr nc,SB2
        add a,10
        ld (hl),a
        dec hl
        ld c,1
        ld a,l
        cp 4Ah
        ret z
        jr SUBD
SB2:    ld (hl),a
        ret
; ---- pickups: ankh 1x2 (2C/2D) or green scarab 2x2 (C0-C3)
PKDRAW: ld a,(PKCODE)
        and 40h
        jr z,PD2
        ld a,2Ch
        call 004Dh
        ld de,32
        add hl,de
        ld a,2Dh
        jp 004Dh
PD2:    ld a,(PKX)
        add a,4
        ld (PKX),a
        ld a,0C0h
        call 004Dh
        inc hl
        ld a,0C1h
        call 004Dh
        ld de,31
        add hl,de
        ld a,0C2h
        call 004Dh
        inc hl
        ld a,0C3h
        jp 004Dh
PKERASE:
        ld hl,(PKADDR)
        ld a,(PKCODE)
        and 40h
        ld a,20h
        call 004Dh
        jr nz,PE2
        inc hl
        call 004Dh
        dec hl
PE2:    ld de,32
        add hl,de
        call 004Dh
        ret nz
        inc hl
        jp 004Dh
CODE6END:
        org {CODE7}h
NEWROOM:
        ld a,b
        ld (LASTR),a
        ld (RPAR),a
        push bc
        ld hl,PATS
        ld de,38C0h
        ld bc,448
        call 005Ch
        ld hl,PATS2
        ld de,3A80h
        ld bc,128
        call 005Ch
        pop bc
        ld a,(INV)
        cp 75
        jr nc,NR1
        ld a,75
        ld (INV),a
NR1:    ld e,b
        ld d,0
        ld hl,0CB00h
        add hl,de
        ld a,(hl)
        ld l,a
        ld h,0
        add hl,hl
        push hl
        add hl,hl
        pop de
        add hl,de
        ld de,TYPETAB
        add hl,de
        ld (TPTR),hl
        ld e,b
        ld d,0
        ld hl,ROOMTAB
        add hl,de
        ld a,(hl)
        ld (RCODE),a
        ld ix,MON0
        and 3
        ld (ix+0),a
        jr z,NRB
        ld a,(RCODE)
        rrca
        rrca
        and 1
        call SETWALK
        ld a,(RCODE)
        and 40h
        call SETSPD
NRB:    ld ix,MON1
        ld (ix+0),0
        ld a,(RCODE)
        rrca
        rrca
        rrca
        and 7
        ret z
        cp 3
        jr z,NRB3
        cp 4
        jr nc,NRB4
        dec a                   ; 1,2: spider
        call SPCOL
        ld (ix+0),4
        ld (ix+3),37h
        ld (ix+4),50h
        ld a,(RPAR)
        and 15
        add a,38h
        ld (ix+1),a
        ld (ix+5),1
        jr NRSPD
NRB4:   cp 6
        jr nc,NRB6
        sub 4                   ; 4,5: bat over a segment, at head height
        call SETWALK
        ld (ix+2),46h
        ld (ix+0),5
        jr NRSPD
NRB6:   sub 6                   ; 6,7: drop falling from the ceiling
        call SPCOL
        ld (ix+0),6
        ld (ix+3),38h
        ld (ix+4),56h
        ld a,(RPAR)
        and 1Fh
        add a,38h
        ld (ix+1),a
        ld (ix+5),2
        ld (ix+6),0
        ret
NRB3:   ld a,(MON0)
        inc a
        cp 4
        jr c,NB4
        ld a,1
NB4:    ld (ix+0),a
        ld a,(RCODE)
        rrca
        rrca
        and 1
        xor 1
        call SETWALK
NRSPD:  ld a,(RCODE)
        and 80h
SETSPD: or a
        ld a,1
        jr z,SS1
        xor a
SS1:    ld (ix+6),a
        ret
SPCOL:  ld hl,(TPTR)
        ld de,4
        add hl,de
        ld e,a
        ld d,0
        add hl,de
        ld a,(hl)
        ld (ix+2),a
        ret
SETWALK:
        add a,a
        ld e,a
        ld d,0
        ld hl,(TPTR)
        add hl,de
        ld a,(hl)
        ld (ix+3),a
        inc hl
        ld a,(hl)
        ld (ix+4),a
        ld (ix+2),57h
        ld a,(RPAR)
        and 1
        jr z,SW1
        ld a,(ix+4)
        ld (ix+1),a
        ld (ix+5),0FFh
        ret
SW1:    ld a,(ix+3)
        ld (ix+1),a
        ld (ix+5),1
        ret
AXTAB:  db 0,0,0,0,1,0,1
PBTAB:  db 0,24,40,56,72,80,88
CODE7END:
        org {CODE8}h
; ---- up to three pickups per room (slot: act, code, x, y, addr(2), flagptr(2), mask)
PKSETUP:
        xor a
        ld (SLOTS),a
        ld (SLOTS+9),a
        ld (SLOTS+18),a
        ld a,(LASTR)
        ld e,a
        ld d,0
        ld hl,PKTAB
        add hl,de
        ld a,(hl)
        or a
        jr z,PSX
        push af
        ld a,(LASTR)
        call FLAGADDR
        ld c,a
        pop af
        ld ix,SLOTS
        call PSLOT
PSX:    ld hl,PKX2
        ld b,0
PX1:    ld a,(hl)
        cp 0FFh
        ret z
        ld c,a
        ld a,(LASTR)
        cp c
        jr z,PX2
        inc hl
        inc hl
        inc hl
        inc b
        jr PX1
PX2:    inc hl
        ld ix,SLOTS+9
        ld e,0
        call PXS
        inc hl
        ld ix,SLOTS+18
        ld e,1
PXS:    push hl
        push bc
        ld a,b                  ; flag bit = 2*entry + e
        add a,a
        add a,e
        ld e,a
        ld a,1
        inc e
PXM:    dec e
        jr z,PXN
        add a,a
        jr PXM
PXN:    ld c,a
        ld a,(hl)
        ld hl,EXFL
        call PSLOT
        pop bc
        pop hl
        ret
PSLOT:  ld (ix+1),a             ; A = code, HL = flag byte, C = mask
        ld (ix+6),l
        ld (ix+7),h
        ld (ix+8),c
        ld a,(hl)
        and c
        ret nz
        ld (ix+0),1
        ld a,(ix+1)
        and 31
        ld c,a
        add a,a
        add a,a
        add a,a
        ld (ix+2),a
        ld a,(ix+1)
        and 80h
        ld a,11
        jr z,PSL1
        ld a,8
PSL1:   ld b,a
        add a,a
        add a,a
        add a,a
        ld (ix+3),a
        ld l,b
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        add hl,hl
        ld b,0
        add hl,bc
        ld de,1800h
        add hl,de
        ld (ix+4),l
        ld (ix+5),h
        call LOADS
        call PKDRAW
        ld a,(PKX)
        ld (ix+2),a
        ret
PKCHK:  ld ix,SLOTS
        call PK1
        ld ix,SLOTS+9
        call PK1
        ld ix,SLOTS+18
PK1:    ld a,(ix+0)
        or a
        ret z
        ld hl,1B00h
        call 004Ah
        add a,9
        ld d,a
        ld hl,1B01h
        call 004Ah
        add a,8
        ld e,a
        ld a,(ix+3)
        add a,8
        ld b,a
        ld a,d
        sub b
        jr nc,PQ1
        neg
PQ1:    cp 14
        ret nc
        ld a,(ix+2)
        add a,4
        ld b,a
        ld a,e
        sub b
        jr nc,PQ2
        neg
PQ2:    cp 10
        ret nc
        ld (ix+0),0
        call LOADS
        call PKERASE
        ld l,(ix+6)
        ld h,(ix+7)
        ld a,(ix+8)
        or (hl)
        ld (hl),a
        call JOYSND
        jp PKGAIN
CODE8END:
'''

def db_lines(data, per=16):
    return '\n'.join('        db ' + ','.join(str(b) for b in data[i:i + per]) for i in range(0, len(data), per))

def post_patch(d):
    m = Mem(bytes(d))
    slots = monsters.type_slots(m)
    codes = monsters.room_codes(m, slots)
    tt = []
    for segs, spid in slots:
        s = list(segs) + [(0x28, 0x60)] * (2 - len(segs))
        p = list(spid) + [0x40] * (2 - len(spid))
        tt += [s[0][0], s[0][1], s[1][0], s[1][1], p[0], p[1]]
    import gen
    pk, pst = monsters.pickup_table(m, lambda r: gen.room_entries(m, r), gen.OBJDEFS_BY_ID)
    print('pickups:', pst)
    import ending, title
    ent_nt, ent_pats, ent_cols = ending.build()
    epat = []
    for code, p in sorted(ent_pats.items()): epat += [code] + list(p)
    ecol = [(ent_cols.get(g, (15, 1))[0] << 4) | ent_cols.get(g, (15, 1))[1] for g in range(32)]
    def fmt(segs): return '\n'.join('        dw %d\n        db %d,%s' % (a, len(run), ','.join(map(str, run))) for a, run in segs)
    eseg = fmt(title.segments({i: c for i, c in enumerate(ending.ART_NT) if c != 0x20}))
    etr = ending.TR
    def tseg(lines, tr): return fmt((0x1800 + r * 32 + c, [tr.get(ch, ord(ch)) for ch in t]) for r, c, t in lines)
    lpos = gen.LOTUS_POS[gen.LOTUS_ROOM]
    lr, lc = divmod(lpos, 32)
    # mode-5 prompt glyphs: title chars A0-B7 <- game font
    chars = 'PANTL:'
    m5 = [(0xA0 + i, ord(ch)) for i, ch in enumerate(chars)] + [(0xA8 + k, 0x30 + k) for k in range(10)]
    tcode = {ch: 0xA0 + i for i, ch in enumerate(chars)}
    txt = [tcode[c] if c != ' ' else 0x20 for c in 'PANTALLA: ']
    import gen as _g
    pkx2 = []
    for room, codes_ in sorted(_g.MULTI_PICKUPS.items()):
        pkx2 += [room] + codes_[1:3]
    src = ASM.format(CODE9='0%X' % CODE9, CODE10='0%X' % CODE10, DATA2='0%X' % DATA2, ETXT=tseg(ending.TEXT, etr), GTXT=tseg(ending.GO_TEXT, etr), CODE8='0%X' % CODE8, PKX2=db_lines(pkx2) if pkx2 else '', CODE7='0%X' % CODE7, PATS2=db_lines(monsters.pattern_data2()), CODE6='0%X' % CODE6, CODE5='0%X' % CODE5, PROMPT=0x1800 + 14 * 32 + 9, D0=0xA8, CUR=0xB2,
                     TXT=','.join(map(str, txt)), M5TAB=db_lines([x for p in m5 for x in p]), M5COUNT=len(m5),
                     CODE4='0%X' % CODE4, LROOM=gen.LOTUS_ROOM, LCY=lr * 8 + 12, LCX=lc * 8 + 16,
                     NPAT=len(ent_pats), ECOL=db_lines(ecol), EPAT=db_lines(epat), ESEG=eseg,
                     SCOREADDR=0x1800 + ending.SCORE_POS[0] * 32 + ending.SCORE_POS[1],
                     DATA='0%X' % DATA, CODE='0%X' % CODE, CODE2='0%X' % CODE2, BLANK=art.BLANK,
                     CODE3='0%X' % CODE3, VARS='0%X' % VARS, PKTAB=db_lines(pk),
                     PATS=db_lines(monsters.pattern_data()), ROOMTAB=db_lines(codes), TYPETAB=db_lines(tt))
    open('mons.asm', 'w').write(src)
    r = subprocess.run(['pasmo', '--bin', 'mons.asm', 'mons.bin', 'mons.sym'], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); sys.exit(1)
    sym = {}
    for line in open('mons.sym'):
        p = line.split()
        if len(p) >= 3 and p[1] == 'EQU': sym[p[0]] = int(p[2].rstrip('H'), 16)
    bin_ = open('mons.bin', 'rb').read()
    de, ce, c2 = sym['DATAEND'], sym['CODEEND'], sym['CODE2END']
    print('monster data %04X-%04X  code %04X-%04X, %04X-%04X' % (DATA, de - 1, CODE2, c2 - 1, CODE, ce - 1))
    assert de <= DATA_END and ce <= CODE_END and c2 <= CODE2_END
    assert all(b == 0 for b in d[DATA - B:de - B]) and all(b == 0 for b in d[CODE2 - B:c2 - B])
    c3, ve = sym['CODE3END'], sym['VARSEND']
    print('pickup code %04X-%04X vars %04X-%04X' % (CODE3, c3 - 1, VARS, ve - 1))
    assert c3 <= CODE3_END and ve <= VARS_END
    assert all(b == 0 for b in d[CODE3 - B:c3 - B])
    c4 = sym['CODE4END']
    print('ending %04X-%04X' % (CODE4, c4 - 1))
    assert c4 <= CODE4_END
    c5 = sym['CODE5END']
    print('mode5 %04X-%04X' % (CODE5, c5 - 1))
    assert c5 <= CODE5_END
    c8 = sym['CODE8END']
    print('code8 %04X-%04X' % (CODE8, c8 - 1))
    assert c8 <= CODE8_END
    c7 = sym['CODE7END']
    print('code7 %04X-%04X' % (CODE7, c7 - 1))
    assert c7 <= CODE7_END
    for nm, lo, hi in (('DATA2', DATA2, DATA2_END), ('CODE9', CODE9, CODE9_END), ('CODE10', CODE10, CODE10_END)):
        e = sym[nm + 'END']
        print('%s %04X-%04X (limit %04X)' % (nm, lo, e - 1, hi))
        assert e <= hi
        assert all(b == 0 or (b == 0xC9 and (a & 15) == 15) for a, b in zip(range(lo, e), d[lo - B:e - B]))
        d[lo - B:e - B] = bin_[lo - DATA:e - DATA]
    c6 = sym['CODE6END']
    print('code6 %04X-%04X' % (CODE6, c6 - 1))
    assert c6 <= CODE6_END
    for lo, hi in ((DATA, de), (CODE2, c2), (CODE, ce), (CODE3, c3), (CODE4, c4), (CODE5, c5), (CODE6, c6), (CODE7, c7), (CODE8, c8), (VARS, ve)):
        d[lo - B:hi - B] = bin_[lo - DATA:hi - DATA]
    def jp(at, target):
        d[at - B:at + 3 - B] = bytes([0xC3, target & 255, target >> 8])
    assert d[0x859E - B] == 0xC3 and d[0xA224 - B] == 0x21
    jp(0x859E, sym['GS0'])
    assert d[0x8599 - B:0x859C - B] == bytes([0x18, 0xEC, 0x00])
    jp(0x8599, sym['MENU2'])
    # starting room comes from STROOM (mode 5)
    assert d[0xA0F4 - B:0xA0FA - B] == bytes([0x00, 0x3E, 0x00, 0x32, 0x04, 0xF3])
    st = sym['STROOM']
    d[0xA0F4 - B:0xA0FA - B] = bytes([0x3A, st & 255, st >> 8, 0x32, 0x04, 0xF3])
    jp(0xA224, sym['DELAY1'])
    # status line: "VIDAS:10" and two ankhs
    d[0xCD56 - B] = ord('1'); d[0xCD57 - B] = ord('0'); d[0xCD58 - B] = art.BLANK
    # score "0000" in cols 11-14
    d[0xCD4B - B:0xCD4F - B] = b'0000'; d[0xCD4F - B] = art.BLANK
    n = sum(1 for c in codes if c & 3) + sum(1 for c in codes if (c >> 3) & 3)
    print('monsters in %d rooms, %d total' % (sum(1 for c in codes if c), n))

make.post_patch = post_patch
if __name__ == '__main__':
    make.build('anubis_new.bin', 'ANUBIS_EGIPTO.cas')
