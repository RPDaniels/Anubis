# Build the decorated ANUBIS binary + CAS
import subprocess, struct, sys
import art, gen
from rooms import Mem
from build import apply_art, patch_margins
B = 0x8500
CODE = 0x8D90
BUF = 0x9D00

ASM = r'''
BUF     equ 9D00h
BLANK   equ {BLANK}
FLOORB  equ {FLOOR_B}
FLOORR  equ {FLOOR_R}
CEILA   equ {CEIL_A}
CEILB   equ {CEIL_B}
SIDEB   equ {SIDE_B}
SIDER   equ {SIDE_R}
LOTUS   equ {LOTUS}
BUD     equ {BUD}
        org {CODE}h
DECOR:  ld hl,1800h
        ld de,BUF
        ld bc,768
        call 0059h              ; LDIRMV name table -> buffer
        ld a,(BUF+365)
        ld (SAV0),a
        ld a,(BUF+370)
        ld (SAV1),a
        ld a,(BUF+208)
        ld (SAV2),a
        ld a,(BUF+528)
        ld (SAV3),a
        ld hl,BUF
        ld b,32
ROW0:   ld (hl),BLANK
        inc hl
        djnz ROW0
; ---- room style: floor/ceiling tiles (patched into pass 1)
        ld a,(0F304h)
        ld c,a
        rrca
        rrca
        and 3Fh
        ld e,a
        ld d,0
        ld hl,STYLES
        add hl,de
        ld b,(hl)
        ld a,c
        and 3
        jr z,SY2
SY1:    srl b
        srl b
        dec a
        jr nz,SY1
SY2:    ld a,b
        and 3
        add a,a
        add a,a
        ld e,a
        ld d,0
        ld hl,STAB
        add hl,de
        ld a,(hl)
        ld (P1FA+1),a
        inc hl
        ld a,(hl)
        ld (P1FB+1),a
        inc hl
        ld a,(hl)
        ld (P1CA+1),a
        inc hl
        ld a,(hl)
        ld (P1CB+1),a
; ---- pass 1: dress the masonry edges
        ld hl,BUF+32
P1:     ld a,l
        and 31
        cp 2
        jr c,P1N
        cp 31
        jr nc,P1N
        ld a,(hl)
        sub 60h
        cp 8
        jr nc,P1N
        ld de,-32
        push hl
        add hl,de
        ld a,(hl)
        pop hl
        cp 20h
        jr nz,P1C
        ld a,l
        and 1
P1FA:   ld a,FLOORB
        jr z,P1S
P1FB:   ld a,FLOORR
        jr P1S
P1C:    ld de,32
        push hl
        add hl,de
        ld a,(hl)
        pop hl
        cp 20h
        jr nz,P1L
        ld a,l
        and 1
P1CA:   ld a,CEILA
        jr z,P1S
P1CB:   ld a,CEILB
        jr P1S
P1L:    dec hl
        ld a,(hl)
        inc hl
        cp 20h
        jr z,P1E
        inc hl
        ld a,(hl)
        dec hl
        cp 20h
        jr nz,P1N
P1E:    ld a,l
        and 20h
        ld a,SIDEB
        jr z,P1S
        ld a,SIDER
P1S:    ld (hl),a
P1N:    inc hl
        ld a,l
        cp LOW (BUF+608)
        jr nz,P1
        ld a,h
        cp HIGH (BUF+608)
        jr nz,P1
; ---- pass 2: hanging lotus frieze under the starry ceilings
        ld hl,BUF+64
P2:     ld a,l
        and 31
        cp 2
        jr c,P2N
        cp 31
        jr nc,P2N
        ld a,(hl)
        cp 20h
        jr nz,P2N
        ld de,-32
        push hl
        add hl,de
        ld a,(hl)
        pop hl
        cp CEILA
        jr z,P2Y
        cp CEILB
        jr nz,P2N
P2Y:    ld a,l
        and 1
        ld a,LOTUS
        jr z,P2S
        ld a,BUD
P2S:    ld (hl),a
P2N:    inc hl
        ld a,l
        cp LOW (BUF+608)
        jr nz,P2
        ld a,h
        cp HIGH (BUF+608)
        jr nz,P2
; ---- keep the collision cells exactly as the original
        ld a,(SAV0)
        cp 20h
        jr nz,K1
        ld (BUF+365),a
K1:     ld a,(SAV1)
        cp 20h
        jr nz,K2
        ld (BUF+370),a
K2:     ld a,(SAV2)
        cp 20h
        jr nz,K3
        ld (BUF+208),a
K3:     ld a,(SAV3)
        cp 20h
        jr nz,K4
        ld (BUF+528),a
K4:
; ---- objects of this room
        ld a,(0F304h)
        ld b,a
        ld hl,LISTS
        or a
        jr z,OBJS
SKIP:   ld a,(hl)
        inc hl
        cp 0FFh
        jr z,SKIPE
        inc hl
        jr SKIP
SKIPE:  djnz SKIP
OBJS:   ld a,(hl)
        cp 0FFh
        jr z,DONE
        inc hl
        ld e,(hl)               ; pos low
        inc hl
        push hl
        ld c,a
        rlca
        rlca
        and 3
        add a,HIGH BUF
        ld d,a                  ; DE = BUF + pos
        ld a,c
        and 63
        add a,a
        ld l,a
        ld h,0
        ld bc,OBJTAB
        add hl,bc
        ld a,(hl)
        inc hl
        ld h,(hl)
        ld l,a                  ; HL = object def
        ex de,hl                ; HL = dest, DE = def
        ld a,(de)
        ld c,a                  ; width
        inc de
        ld a,(de)
        ld b,a                  ; height
        inc de
ORow:   push bc
        push hl
        ld b,c
OCol:   ld a,(de)
        cp 0FFh
        jr z,OSk
        ld (hl),a
OSk:    inc hl
        inc de
        djnz OCol
        pop hl
        ld bc,32
        add hl,bc
        pop bc
        djnz ORow
        pop hl
        jr OBJS
DONE:   ld hl,BUF
        ld de,1800h
        ld bc,768
        call 005Ch              ; LDIRVM buffer -> name table
        ld a,(0F304h)           ; only the rooms that really have a routine
        ld hl,RLIST             ; (the empty slots are reused as free memory)
        ld b,{NRL}
RLS:    cp (hl)
        jr z,ROOMJP
        inc hl
        djnz RLS
        ret
ROOMJP: jp 0000h                ; original per-room routine (patched by A3AA)
RLIST:  db {RLIST}
STAB:   db {STAB}
STYLES: db {STYLES}
SAV0:   db 0
SAV1:   db 0
SAV2:   db 0
SAV3:   db 0
OBJTAB:
{OBJTAB}
{OBJDEFS}
LISTS:
{LISTS}
LISTEND:
        org 0A400h              ; dead code of the original (old jump routines)
{TITLE}
ENDALL:
'''

def build(outbin, outcas):
    d = bytearray(open('game.bin', 'rb').read())
    apply_art(d); patch_margins(d)
    m = Mem(bytes(d))
    ids = sorted(gen.OBJDEFS_BY_ID)
    objtab = '\n'.join('        dw OD%d' % i for i in ids)
    defs = []
    for i in ids:
        w, h, ch = gen.OBJDEFS_BY_ID[i]
        defs.append('OD%d:    db %d,%d,%s' % (i, w, h, ','.join(str(c) for c in ch)))
    lists = []
    total = 0
    for r in range(256):
        e = gen.room_entries(m, r)
        total += len(e)
        bs = []
        for oid, pos in e:
            bs += [((pos >> 8) << 6) | oid, pos & 255]
        bs.append(255)
        lists.append('        db ' + ','.join(str(b) for b in bs))
    sym = {k: getattr(art, k) for k in ['BLANK', 'FLOOR_B', 'FLOOR_R', 'CEIL_A', 'CEIL_B', 'SIDE_B',
                                         'SIDE_R', 'LOTUS', 'BUD']}
    import title
    g0 = open('game.bin', 'rb').read()
    rl = [r for r in range(256) if g0[0xD5C0 - B + 16 * r] != 0]
    import sim as _sim
    stab = [c for st in range(4) for c in _sim.style_chars(st)]
    packed = [sum(_sim.room_style(4 * k + j) << (2 * j) for j in range(4)) for k in range(64)]
    src = ASM.format(STAB=','.join(map(str, stab)), STYLES=','.join(map(str, packed)), TITLE=title.asm(), NRL=len(rl), RLIST=','.join(map(str, rl)), CODE='%X' % CODE, OBJTAB=objtab, OBJDEFS='\n'.join(defs), LISTS='\n'.join(lists), **sym)
    open('decor.asm', 'w').write(src)
    r = subprocess.run(['pasmo', '--bin', 'decor.asm', 'decor.bin', 'decor.sym'], capture_output=True, text=True)
    if r.returncode:
        print(r.stdout, r.stderr); sys.exit(1)
    code = open('decor.bin', 'rb').read()
    syms = {}
    for line in open('decor.sym'):
        p = line.split()
        if len(p) >= 3 and p[1] == 'EQU':
            syms[p[0]] = int(p[2].rstrip('H'), 16)
    end = syms['LISTEND']; tend = syms['ENDALL']
    print('decor %04X-%04X, title %04X-%04X, %d objects placed' % (CODE, end - 1, 0xA400, tend - 1, total))
    assert end <= BUF and tend <= 0xA800
    d[CODE - B:end - B] = code[:end - CODE]
    d[0xA400 - B:tend - B] = code[0xA400 - CODE:tend - CODE]
    # hook: A3AA  LD (ROOMJP+1),HL ; A3AD CALL DECOR
    rj = syms['ROOMJP'] + 1
    d[0xA3AA - B:0xA3AD - B] = bytes([0x22, rj & 255, rj >> 8])
    dc = syms['DECOR']
    d[0xA3AD - B:0xA3B0 - B] = bytes([0xCD, dc & 255, dc >> 8])
    tt = syms['TITLE']
    assert d[0x8562-B:0x8565-B] == b'\0\0\0'
    d[0x8562-B:0x8565-B] = bytes([0xCD, tt & 255, tt >> 8])
    extra = getattr(sys.modules[__name__], 'post_patch', None)
    if extra: extra(d)
    open(outbin, 'wb').write(d)
    write_cas(d, outcas)
    return d

def write_cas(d, out):
    orig = open('orig.cas', 'rb').read()
    hdr = orig[:32]          # header block (ANUBIS name) + binary block header
    start, endaddr, ex = 0x8500, 0x8500 + len(d) - 1, 0x8500
    body = struct.pack('<HHH', start, endaddr, ex) + bytes(d)
    open(out, 'wb').write(hdr + body)

if __name__ == '__main__':
    build('anubis_new.bin', 'ANUBIS_EGIPTO.cas')
