# Ending screen: composed image -> SCREEN 1 tiles + text
from PIL import Image, ImageDraw
from render import PAL
import ending_art, art
B = 0x8500
RESERVED_GROUPS = {4, 6, 7, 8, 9, 10, 11}
TEXT = [
    (3, 16, 'HAS COMPLETADO'),
    (4, 16, 'TU MISI\x01N,'),
    (6, 16, 'LLEGASTE AL'),
    (7, 16, 'REINO DE'),
    (8, 16, 'ANUBIS.'),
    (10, 16, 'PERO NO TE'),
    (11, 16, 'LLEVAR\x02S TUS'),
    (12, 16, 'RIQUEZAS AL'),
    (13, 16, 'OTRO MUNDO.'),
    (17, 16, 'PUNTOS:'),
    (20, 16, 'PULSA ESPACIO'),
]
SCORE_POS = (17, 23)
# game-over screen: same Anubis artwork, different words (\x03 = I with acute)
GO_TEXT = [
    (4, 16, 'HASTA AQU\x03'),
    (5, 16, 'HAS LLEGADO.'),
    (8, 16, 'ANUBIS TE'),
    (9, 16, 'ACOGE EN'),
    (10, 16, 'SU SENO.'),
    (17, 16, 'PUNTOS:'),
    (20, 16, 'PULSA ESPACIO'),
]
ART_NT = None
TR = None

def compose():
    im = Image.new('P', (256, 192), 1)
    im.putpalette([c for p in PAL for c in p] + [0] * (768 - 48))
    d = ImageDraw.Draw(im)
    # top & bottom friezes: coloured rectangles on sandstone
    for row in (0, 23):
        y = row * 8
        d.rectangle([0, y, 255, y + 7], fill=10)
        for c in range(32):
            d.rectangle([c * 8 + 1, y + 2, c * 8 + 6, y + 5], fill=4 if c % 2 == 0 else 6)
    # starry band under the top frieze (row 1) and lotus row (row 2)
    d.rectangle([0, 8, 255, 15], fill=4)
    for c in range(0, 32, 2):
        d.point((c * 8 + 3, 10), fill=11); d.line([(c * 8 + 2, 11), (c * 8 + 4, 11)], fill=11); d.point((c * 8 + 3, 12), fill=11)
    for c in range(32):
        x = c * 8
        col = 7 if c % 2 == 0 else 8
        d.line([(x + 3, 16), (x + 3, 19)], fill=col)
        d.polygon([(x + 1, 19), (x + 5, 19), (x + 3, 22)], fill=col)
    # anubis
    a = ending_art.draw(); ending_art.fix_cells(a)
    im.paste(a, (8, 40))
    # vertical side bands rows 3..22
    for row in range(3, 23):
        for cx in (0, 31):
            x, y = cx * 8, row * 8
            d.rectangle([x, y, x + 7, y + 7], fill=10)
            d.rectangle([x + 2, y + 1, x + 5, y + 6], fill=4 if row % 2 == 0 else 6)
    return im

def tileize(im):
    px = im.load()
    cells = {}
    for cy in range(24):
        for cx in range(32):
            cols = {}
            for y in range(8):
                for x in range(8):
                    c = px[cx * 8 + x, cy * 8 + y]; cols[c] = cols.get(c, 0) + 1
            assert len(cols) <= 2, (cx, cy, cols)
            if list(cols) == [1]:
                continue
            ks = sorted(cols, key=lambda c: -cols[c])
            if 1 in cols: bg = 1; fg = [c for c in cols if c != 1][0]
            elif len(ks) == 1: bg = 1; fg = ks[0]
            else: bg, fg = ks[0], ks[1]
            pat = tuple(sum(0x80 >> x for x in range(8) if px[cx * 8 + x, cy * 8 + y] == fg) for y in range(8))
            cells[(cy, cx)] = ((fg, bg), pat)
    return cells

def build():
    cells = tileize(compose())
    # accent letters + period, gold on black
    extra = {}
    g = open('game.bin', 'rb').read()
    def glyph(ch): return [g[0xCDA0 - B + ord(ch) * 8 + y] for y in range(8)]
    O = glyph('O'); A = glyph('A'); I = glyph('I')
    extra['\x03'] = ((10, 1), (0x06, 0x0C, 0x3E, 0x1C, 0x1C, 0x1C, 0x3E, 0))   # I with acute
    extra['\x01'] = ((10, 1), tuple([0x0C, 0x18] + O[2:]))   # O with acute
    extra['\x02'] = ((10, 1), tuple([0x0C, 0x18] + A[2:]))   # A with acute
    extra['Y'] = ((10, 1), tuple(glyph('Y')))
    extra['Z'] = ((10, 1), tuple(glyph('Z')))
    extra[','] = ((10, 1), (0, 0, 0, 0, 0, 0x30, 0x30, 0x60))
    extra['.'] = ((10, 1), (0, 0, 0, 0, 0, 0, 0x30, 0x30))
    # allocate codes
    bypair = {}
    for key, (pair, pat) in list(cells.items()) + [(k, v) for k, v in extra.items()]:
        bypair.setdefault(pair, [])
        if pat not in bypair[pair]: bypair[pair].append(pat)
    groups = [gid for gid in range(32) if gid not in RESERVED_GROUPS]
    code_of = {}; colors = {}; pats = {}
    gi = 0
    for pair, plist in sorted(bypair.items(), key=lambda kv: -len(kv[1])):
        for k in range(0, len(plist), 8):
            gid = groups[gi]; gi += 1
            colors[gid] = pair
            for j, p in enumerate(plist[k:k + 8]):
                code = gid * 8 + j; code_of[(pair, p)] = code; pats[code] = p
    nt = [0x20] * 768
    for (cy, cx), (pair, pat) in cells.items():
        nt[cy * 32 + cx] = code_of[(pair, pat)]
    tr = {k: code_of[v] for k, v in extra.items()}
    global ART_NT, TR
    ART_NT = list(nt); TR = tr
    for row, col, s in TEXT:
        for i, ch in enumerate(s):
            nt[row * 32 + col + i] = tr.get(ch, ord(ch))
    colors.update({4: (10, 1), 6: (11, 1), 7: (11, 1), 8: (10, 1), 9: (10, 1), 10: (10, 1), 11: (10, 1)})
    print('ending: %d unique tiles in %d groups' % (len(pats), gi))
    return nt, pats, colors

if __name__ == '__main__':
    nt, pats, colors = build()
    import sys
    if 'go' in sys.argv:
        nt = list(ART_NT)
        for row, col, t in GO_TEXT:
            for i, ch in enumerate(t): nt[row * 32 + col + i] = TR.get(ch, ord(ch))
    vram = bytearray(16384)
    g = open('game.bin', 'rb').read()
    for i in range(2048): vram[i] = g[0xCDA0 - B + i]
    for c, p in pats.items(): vram[c * 8:c * 8 + 8] = bytes(p)
    for gid in range(32):
        fg, bg = colors.get(gid, (15, 1)); vram[0x2000 + gid] = fg << 4 | bg
    for i, ch in enumerate(nt): vram[0x1800 + i] = ch
    for i, ch in enumerate('0450'): vram[0x1800 + SCORE_POS[0] * 32 + SCORE_POS[1] + i] = ord(ch)
    from render import render
    render(vram, [0, 0xe2, 6, 0x80, 0, 0x36, 7, 0], 'end/gameover.png' if 'go' in sys.argv else 'end/ending.png', sprites=False, scale=2)
