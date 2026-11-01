# Python model of the room drawing + the new decoration pass (mirrors the Z80 code)
import art
from rooms import Mem, run
B = 0x8500
NT = 0x1800
CHECK_CELLS = [11 * 32 + 13, 11 * 32 + 18, 6 * 32 + 16, 16 * 32 + 16]
MASONRY = set(range(0x60, 0x68))
OPEN = 0x20

import random as _r
def room_style(room):
    """0 normal, 1 lapis tile floor (0x94), 2 gilded cornice floor (0xD8), 3 gilded cornice ceiling"""
    if room in (0, 240): return 0
    if room == 50: return 1          # lapis room: pink-and-blue tile floor
    v = _r.Random(555 + room * 17).random()
    return 0 if v < 0.52 else 1 if v < 0.68 else 2 if v < 0.84 else 3
STYLE_CHARS = None
def style_chars(style):
    fb, fr, ca, cb = art.FLOOR_B, art.FLOOR_R, art.CEIL_A, art.CEIL_B
    return [(fb, fr, ca, cb), (0x94, 0x94, ca, cb), (0xD8, 0xD8, ca, cb), (fb, fr, 0xD8, 0xD8)][style]
def band_pass(nt, style=0):
    FB, FR, CA, CB = style_chars(style)
    """nt: bytearray(768) name table. Same algorithm as Z80 DECOR pass."""
    orig = bytes(nt)
    # pass 1: wall cells (rows 1..18, cols 2..30)
    for r in range(1, 19):
        for c in range(2, 31):
            i = r * 32 + c
            if nt[i] not in MASONRY:
                continue
            if nt[i - 32] == OPEN:
                nt[i] = FB if (c & 1) == 0 else FR
            elif nt[i + 32] == OPEN:
                nt[i] = CA if (c & 1) == 0 else CB
            elif nt[i - 1] == OPEN or nt[i + 1] == OPEN:
                nt[i] = art.SIDE_B if (r & 1) == 0 else art.SIDE_R
    # pass 2: lotus frieze under ceilings
    for r in range(2, 19):
        for c in range(2, 31):
            i = r * 32 + c
            if nt[i] == OPEN and nt[i - 32] in (art.CEIL_A, art.CEIL_B):
                nt[i] = art.LOTUS if (c & 1) == 0 else art.BUD
    # keep collision cells exactly as they were
    for i in CHECK_CELLS:
        if orig[i] == OPEN:
            nt[i] = OPEN

def place_objects(nt, entries, objdefs):
    for oid, pos in entries:
        w, h, chars = objdefs[oid]
        k = 0
        for y in range(h):
            for x in range(w):
                ch = chars[k]; k += 1
                if ch != 0xFF:
                    nt[pos + y * 32 + x] = ch

def compose(m, room, decor=True, entries=None, objdefs=None, objects=True):
    vram = bytearray(16384)
    for i in range(0x800): vram[i] = m[0xcda0 + i]
    for i in range(32): vram[0x2000 + i] = m[0xd5a0 + i]
    for i in range(0x300): vram[NT + i] = 0x20
    vram[0x1b00] = 208
    run(m, vram, 0xb18f)
    t = m[0xcb00 + room]
    run(m, vram, 0xb000 + 13 * t)
    if decor:
        nt = bytearray(vram[NT:NT + 768])
        for i in range(32): nt[i] = art.BLANK
        band_pass(nt, room_style(room))
        if entries:
            place_objects(nt, entries, objdefs)
        vram[NT:NT + 768] = nt
    if objects:
        run(m, vram, 0xd5c0 + 16 * room)
    return vram
