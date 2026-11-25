# Title-screen decoration (built as overlay segments + pattern remap)
import art, gen
# title-free slots and their colours
SLOTS = {}   # dest char -> source game char
GROUPS = {}  # group -> (fg,bg)
def group(g, colors, srcs):
    GROUPS[g] = colors
    for k, s in enumerate(srcs):
        SLOTS[g * 8 + k] = s
group(0, (5, 1), list(range(0x60, 0x68)))
group(1, (4, 10), list(range(0x08, 0x10)))
group(2, (6, 10), list(range(0x10, 0x18)))
group(3, (1, 10), list(range(0x18, 0x20)))
group(27, (7, 1), list(range(0x28, 0x30)))
group(28, (10, 1), list(range(0xC8, 0xD0)))
group(29, (11, 1), list(range(0xD0, 0xD6)) + [0x3C, 0x3D])
group(30, (8, 1), [0x74, 0x75, 0x76, 0x77, 0x5F, 0x5E])
group(31, (5, 1), [0xE8, 0xE9, 0xEA, 0xEB])
group(24, (10, 1), [0xE0, 0xE7])   # mirrored cat (faces right)
MAP = {}
for dest, src in SLOTS.items():
    MAP.setdefault(src, dest)
MAP[0xA4] = None  # not available

def overlay():
    nt = {}
    def put(r, c, ch):
        nt[r * 32 + c] = MAP[ch]
    def putobj(name, r, c):
        w, h, chars = gen.OBJDEFS[name]
        for y in range(h):
            for x in range(w):
                ch = chars[y * w + x]
                if ch != 0xFF: put(r + y, c + x, ch)
    for c in range(32):
        put(5, c, art.FLOOR_B if c % 2 == 0 else art.FLOOR_R)
        put(6, c, art.LOTUS if c % 2 == 0 else art.BUD)
        put(18, c, art.FLOOR_B if c % 2 == 0 else art.FLOOR_R)
    for r in range(7, 18):
        put(r, 0, art.SIDE_B if r % 2 == 0 else art.SIDE_R)
        put(r, 31, art.SIDE_B if r % 2 == 0 else art.SIDE_R)
    import random
    rng = random.Random(3)
    for r in range(19, 24):
        for c in range(32):
            put(r, c, (0x61, 0x62, 0x63)[rng.randrange(3)] if r % 2 == 1 else (0x64, 0x65, 0x66)[rng.randrange(3)])
    # inscription band in the masonry
    for c in range(6, 26):
        put(19, c, art.FLOOR_B if c % 2 == 0 else art.FLOOR_R)
        put(23, c, art.FLOOR_B if c % 2 == 0 else art.FLOOR_R)
    gl = art.BLUE_GLYPHS + art.RED_GLYPHS
    for r in range(20, 23):
        for c in range(6, 26):
            put(r, c, (art.BLUE_GLYPHS if c % 2 == 0 else art.RED_GLYPHS)[rng.randrange(6)])
    # winged suns beside the logo
    putobj('wingsun', 2, 5); putobj('wingsun', 2, 24)
    putobj('ankh', 0, 2); putobj('ankh', 0, 29)
    # scene
    putobj('anubis', 15, 2)
    putobj('torch', 8, 3)
    putobj('brazier', 15, 7)
    putobj('cat_r', 15, 11)   # both cats look towards the centre
    putobj('jar', 17, 14)
    putobj('jar', 17, 17)
    putobj('cat', 15, 20)
    putobj('brazier', 15, 23)
    putobj('coffin', 14, 27)
    putobj('torch', 8, 28)
    putobj('eye', 14, 15)
    putobj('scarab', 9, 22) if False else None
    return nt

def segments(nt):
    segs = []
    keys = sorted(nt)
    i = 0
    while i < len(keys):
        s = keys[i]; run = [nt[s]]
        while i + 1 < len(keys) and keys[i + 1] == keys[i] + 1 and len(run) < 255:
            i += 1; run.append(nt[keys[i]])
        segs.append((0x1800 + s, run)); i += 1
    return segs

ASM = r'''
TITLE:  ld hl,TPAT
TP1:    ld a,(hl)          ; dest char (FF = end)
        cp 0FFh
        jr z,TCOL
        inc hl
        push hl
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ex de,hl           ; DE = VRAM dest
        pop hl
        ld a,(hl)          ; src char
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
        jr TP1
TCOL:   ld hl,TCLR
TC1:    ld a,(hl)
        cp 0FFh
        jr z,TSEG
        inc hl
        ld e,a
        ld d,20h
        ld a,(hl)
        inc hl
        push hl
        ex de,hl
        call 004Dh
        pop hl
        jr TC1
TSEG:   ld hl,TSEGS
TS1:    ld e,(hl)
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
        jr TS1
TPAT:
{TPAT}
        db 0FFh
TCLR:
{TCLR}
        db 0FFh
TSEGS:
{TSEGS}
        dw 0
'''
def asm():
    tpat = '\n'.join('        db %d,%d' % (d, s) for d, s in sorted(SLOTS.items()))
    tclr = '\n'.join('        db %d,%d' % (g, (fg << 4) | bg) for g, (fg, bg) in sorted(GROUPS.items()))
    segs = segments(overlay())
    ts = '\n'.join('        dw %d\n        db %d,%s' % (a, len(run), ','.join(map(str, run))) for a, run in segs)
    return ASM.format(TPAT=tpat, TCLR=tclr, TSEGS=ts)
