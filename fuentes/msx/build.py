import sys, importlib
from PIL import Image
import art
from rooms import Mem
from render import render
import sim
B = 0x8500
REGS = [0, 0xe2, 6, 0x80, 0, 0x36, 7, 0]

def patch_margins(d):
    remove_static_scarabs(d)
    for base in (0xc500,0xc5c0,0xc680,0xc740,0xc800,0xc8c0,0xc980):
        for r in range(6):
            for c in (0,1,31):
                d[base-B+r*32+c]=art.BLANK
    for i in range(0xa0):
        r, c = divmod(i, 32)
        v = d[0xcd00-B+i]
        if v == 0x20: v = art.BLANK
        elif v == 0xdb:
            if r in (0, 4) or c in (2, 30): v = art.STATUS_BORDER
            else: v = art.ANKH_SMALL
        d[0xcd00-B+i] = v
    for k, ch in enumerate('PUNTOS'):
        assert d[0xcd44-B+k] == ord(ch)
        d[0xcd44-B+k] = art.PINK[ch]
    for k, ch in enumerate('VIDAS'):
        assert d[0xcd50-B+k] == ord(ch)
        d[0xcd50-B+k] = art.GREEN[ch]

def remove_static_scarabs(d):
    """the green scarab (E652 drawer) is now the points pickup: drop its fixed copies from the room routines"""
    for r in range(256):
        for k in range(0, 15, 3):
            a = 0xD5C0 - B + 16 * r + k
            if d[a] == 0xCD and (d[a + 1] | d[a + 2] << 8) in (0xE652, 0xE6D4, 0xE6C7):   # scarab; lone char E0 (mirrored cat now); room 50 cornice fill
                d[a:a + 3] = b'\0\0\0'

def apply_art(d):
    for code, rows in art.T.items():
        for y, r in enumerate(rows):
            v = 0
            for x, ch in enumerate(r):
                if ch == '#': v |= 0x80 >> x
            d[0xcda0 - B + code * 8 + y] = v
    for g, (fg, bg) in art.GROUP_COLORS.items():
        d[0xd5a0 - B + g] = (fg << 4) | bg

def sheet(m, rooms, out, entries_for=None, objdefs=None, scale=1):
    imgs = []
    for r in rooms:
        ent = entries_for(r) if entries_for else None
        v = sim.compose(m, r, entries=ent, objdefs=objdefs)
        render(v, REGS, '_tmp_render.png', sprites=False, scale=scale)
        imgs.append(Image.open('_tmp_render.png').copy())
    cols = min(4, len(imgs)); rows = (len(imgs) + cols - 1) // cols
    W, H = imgs[0].size
    sh = Image.new('RGB', (cols * (W + 4), rows * (H + 4)), (80, 80, 80))
    for i, im in enumerate(imgs):
        sh.paste(im, ((i % cols) * (W + 4) + 2, (i // cols) * (H + 4) + 2))
    sh.save(out)

if __name__ == '__main__':
    d = bytearray(open('game.bin', 'rb').read())
    apply_art(d)
    patch_margins(d)
    m = Mem(d)
    rooms = [int(x) for x in sys.argv[2:]] or [0, 1, 2, 3, 16, 17, 21, 50]
    sheet(m, rooms, sys.argv[1], scale=int(__import__('os').environ.get('SCALE','1')))
