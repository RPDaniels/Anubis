# -*- coding: utf-8 -*-
# Egyptian tile art for ANUBIS (MSX1, SCREEN 1)
# Each tile: 8 strings of 8 chars, '#' = foreground pixel, '.' = background pixel.

# ---- colour groups (char>>3) : (fg, bg) ----------------------------------
# MSX colours: 1 black 2 mgreen 3 lgreen 4 dblue 5 lblue 6 dred 7 cyan
#              8 mred 9 lred 10 dyellow 11 lyellow 12 dgreen 13 magenta 14 grey 15 white
GROUP_COLORS = {
    0x00 >> 3: (15, 1),   # original white objects (+ 0x07 blank)
    0x08 >> 3: (4, 10),   # blue on sandstone : blue band + blue glyphs
    0x10 >> 3: (6, 10),   # red on sandstone  : red band + red glyphs
    0x18 >> 3: (1, 10),   # black ink on gold : sarcophagus / shrine details
    0x20 >> 3: (4, 1),    # background (space) group
    0x28 >> 3: (7, 1),    # turquoise on black: lotus, eye of Horus, ankh, scarab
    0x58 >> 3: (8, 1),    # terracotta        : amphorae, jars
    0x60 >> 3: (5, 1),   # masonry
    0xC8 >> 3: (10, 1),   # gold              : jackal, cat
    0xD0 >> 3: (11, 1),   # bright gold       : brazier, torch, flame core
    0xE8 >> 3: (5, 1),    # light blue        : winged sun, faience vase
    0xF0 >> 3: (12, 1),   # dark green        : papyrus stems
    0xF8 >> 3: (14, 1),   # grey stone        : stone pieces
}

T = {}   # char code -> tile rows

def tile(code, *rows):
    rows = [r.replace(' ', '') for r in rows]
    if len(rows) == 1:
        rows = rows[0].split('|')
    assert len(rows) == 8, (hex(code), rows)
    for r in rows:
        assert len(r) == 8, (hex(code), r)
    T[code] = rows

def big(codes_grid, art):
    """art: list of strings W*8 wide, H*8 tall; codes_grid: rows of char codes (None = skip)"""
    art = [a.replace(' ', '') for a in art]
    H = len(codes_grid); W = len(codes_grid[0])
    assert len(art) == H * 8, (codes_grid, len(art))
    for a in art:
        assert len(a) == W * 8, (codes_grid, a, len(a))
    for cy, row in enumerate(codes_grid):
        for cx, code in enumerate(row):
            if code is None:
                continue
            tile(code, *[art[cy * 8 + y][cx * 8:cx * 8 + 8] for y in range(8)])

BLANK = 0x07
tile(BLANK, *['........'] * 8)

# ---------------------------------------------------------------- masonry
# original ANUBIS stone patterns (0x60-0x67) are kept; only recoloured to sandstone.
_g = open(__file__.replace('art.py', 'game.bin'), 'rb').read()
for _c in range(0x60, 0x68):
    T[_c] = [''.join('#' if _g[0xCDA0 - 0x8500 + _c * 8 + y] & (0x80 >> x) else '.' for x in range(8)) for y in range(8)]

# original braided status-bar border (0xDB) copied to 0xEC, blue on black
STATUS_BORDER = 0x3B   # light-yellow group of the digits
T[STATUS_BORDER] = [''.join('#' if _g[0xCDA0 - 0x8500 + 0xDB * 8 + y] & (0x80 >> x) else '.' for x in range(8)) for y in range(8)]

# ---------------------------------------------------------------- bands
# floor band (wall cell with open space above) : coloured rectangles
FLOOR_B, FLOOR_R = 0x08, 0x10
tile(FLOOR_B, '########','........','.######.','.######.','.######.','.######.','........','########')
tile(FLOOR_R, '########','........','.######.','.######.','.######.','.######.','........','########')
# side band (wall cell with open space left/right)
SIDE_B, SIDE_R = 0x09, 0x11
tile(SIDE_B, '#......#','#.####.#','#.####.#','#.####.#','#.####.#','#.####.#','#.####.#','#......#')
tile(SIDE_R, '#......#','#.####.#','#.####.#','#.####.#','#.####.#','#.####.#','#.####.#','#......#')

# ceiling (wall cell with open space below): starry night sky, gold on blue
CEIL_A, CEIL_B = 0x8C, 0x8D
tile(CEIL_A, '........','...#....','..###...','...#....','........','......#.','........','########')
tile(CEIL_B, '........','........','.....#..','....###.','.....#..','.#......','........','########')

# hanging lotus frieze under the ceiling (background)
LOTUS, BUD = 0x28, 0x74
tile(LOTUS, '...#....','...#....','..###...','.#####..','##.#.##.','#..#..#.','...#....','........')
tile(BUD,   '...#....','...#....','...#....','..###...','..###...','..###...','...#....','........')

# ---------------------------------------------------------------- glyphs
# blue glyphs (0x0A-0x0F) and red glyphs (0x12-0x17) carved on sandstone,
# each with column rule at x=0 (text columns).
GLYPHS = {
 'ankh':   ['#..##...','#.#..#..','#.#..#..','#..##...','#######.','#..##...','#..##...','#..##...'],
 'eye':    ['#.......','#.####..','##....#.','#..##..#','#.####..','#...#...','#..#.#..','#.#...#.'],
 'owl':    ['#.##....','#####...','#.###...','#.####..','#.####..','#..###..','#..#.#..','#.##.##.'],
 'water':  ['#.......','#.......','#.#.#.#.','##.#.#.#','#.......','#.#.#.#.','##.#.#.#','#.......'],
 'sun':    ['#.......','#..###..','#.#...#.','#.#.#.#.','#.#...#.','#..###..','#.......','#.......'],
 'reed':   ['#...#...','#..##...','#..##...','#.###...','#.###...','#..##...','#...#...','#..###..'],
 'bird':   ['#...##..','#..###..','#..##...','#.####..','#######.','#..####.','#...#...','#..##...'],
 'snake':  ['#.....#.','#....###','#.....#.','#.....#.','#....#..','#...#...','#.##.#.#','##....#.'],
 'bread':  ['#.......','#.......','#.......','#..##...','#.####..','#######.','#######.','#.......'],
 'hand':   ['#.......','#.......','#....###','#.######','########','#.####..','#.......','#.......'],
 'djed':   ['#.####..','#..##...','#.####..','#..##...','#.####..','#..##...','#..##...','#.####..'],
 'scarab': ['#..#.#..','#...#...','#.#####.','##.###.#','#.#####.','##.###.#','#.#.#.#.','#.......'],
 'feather':['#...#...','#..##...','#..###..','#..###..','#..###..','#..###..','#...#...','#...#...'],
 'mouth':  ['#.......','#.......','#.......','#.#####.','#######.','#.#####.','#.......','#.......'],
 'vulture':['#.###...','#####...','#.####..','#.#####.','#.######','#.####.#','#..#.#..','#.##.##.'],
 'basket': ['#.......','#.......','#.......','#.......','#######.','#.#####.','#..###..','#.......'],
}
BLUE_GLYPHS = [0x0A, 0x0B, 0x0C, 0x0D, 0x0E, 0x0F]
RED_GLYPHS = [0x12, 0x13, 0x14, 0x15, 0x16, 0x17]
for code, name in zip(BLUE_GLYPHS, ['ankh', 'eye', 'owl', 'water', 'djed', 'vulture']):
    tile(code, *GLYPHS[name])
for code, name in zip(RED_GLYPHS, ['sun', 'reed', 'bird', 'snake', 'scarab', 'feather']):
    tile(code, *GLYPHS[name])

GROUP_COLORS.update({
    0x30 >> 3: (11, 1), 0x38 >> 3: (11, 1),          # digits: light yellow
    0x40 >> 3: (10, 1), 0x48 >> 3: (10, 1), 0x50 >> 3: (10, 1), 0x58 >> 3: (8, 1),
})
RULE = 0xA4          # sandstone with column rule (closes inscription panels)
tile(RULE, '#.......','#.......','#.......','#.......','#.......','#.......','#.......','#.......')
for code, name in zip([0xA5, 0xA6, 0xA7], ['bread', 'hand', 'mouth']):
    tile(code, *GLYPHS[name])

# ---------------------------------------------------------------- objects
OBJ = {}   # name -> (w, h, [codes row-major]) ; 0xFF = transparent

def obj(name, grid, artrows=None):
    if artrows:
        big(grid, artrows)
    flat = [c if c is not None else 0xFF for row in grid for c in row]
    OBJ[name] = (len(grid[0]), len(grid), flat)

# amphora (terracotta) 2x2
obj('amphora', [[0x58, 0x59], [0x5A, 0x5B]], [
    '................',
    '.....######.....',
    '......####......',
    '...##.####.##...',
    '..#..######..#..',
    '..#.########.#..',
    '...##########...',
    '..############..',
    '..############..',
    '..#.##.##.##.#..',
    '..############..',
    '...##########...',
    '....########....',
    '.....######.....',
    '......####......',
    '.....######.....'])

# small jar 1x1 and sun disk (terracotta)
obj('jar', [[0x5E]], ['..####..', '...##...', '..####..', '.######.', '.#.#.##.', '.######.', '..####..', '.######.'])
tile(0x5F, '........', '..####..', '.######.', '########', '########', '.######.', '..####..', '........')

# brazier 2x3 : red flame tips / yellow fire + bowl / gold stand
obj('brazier', [[0x75, 0x76], [0xD0, 0xD1], [0xD2, 0xD3]], [
    '.......#........',
    '.......#....#...',
    '...#..##....#...',
    '...#..###..##...',
    '..##..###..###..',
    '..###.####.###..',
    '.####.####.####.',
    '.##############.',
    '..############..',
    '..############..',
    '...##########...',
    '................',
    '################',
    '.##############.',
    '..############..',
    '....########....',
    '......####......',
    '.......##.......',
    '.......##.......',
    '......####......',
    '.....#.##.#.....',
    '....#..##..#....',
    '...#...##...#...',
    '..###..##..###..'])

# wall torch 1x3
obj('torch', [[0x77], [0xD4], [0xD5]], [
    '...#....', '...#....', '..##.#..', '..##.#..', '.###.##.', '.######.', '.######.', '..####..',
    '..####..', '..####..', '..####..', '...##...', '########', '.######.', '..####..', '...##...',
    '...##...', '...##...', '...##...', '..####..', '...##...', '...##...', '...##...', '..####..'])

# reclining Anubis jackal (gold) on an inscribed shrine chest
obj('anubis', [[0xC8, 0xC9, 0xCA], [0xCB, 0xCC, 0xCD]], [
    '.....#.#................',
    '.....#.#................',
    '.....###................',
    '....####................',
    '.####.##................',
    '########................',
    '....####................',
    '....#..#................',
    '....#####...............',
    '....##########.......##.',
    '....###############.###.',
    '....##################..',
    '....###################.',
    '...####################.',
    '.#########.####...#####.',
    '##########.#####.######.'])
OBJ['anubis'] = (3, 3, [0xC8, 0xC9, 0xCA, 0xCB, 0xCC, 0xCD, 0x0B, 0x14, 0x0E])

# seated cat (gold) on a plinth
obj('cat', [[0xCE], [0xCF]], [
    '.#.#....', '.###....', '####....', '.###....', '..##....', '..###...', '..####..', '..####..',
    '..#####.', '..#####.', '..#####.', '..######', '..######', '.#######', '.######.', '########'])
OBJ['cat'] = (1, 3, [0xCE, 0xCF, 0x13])

# gold mummiform coffin 2x4  (black ink on gold)
obj('coffin', [[0x18, 0x19], [0x1A, 0x1B], [0x1C, 0x1D], [0x1E, 0x1F]], [
    '#####......#####',
    '###..........###',
    '##..########..##',
    '#..#........#..#',
    '#.#..##..##..#.#',
    '#.#..........#.#',
    '#.#....##....#.#',
    '#.#...####...#.#',
    '#.##........##.#',
    '#.#.##....##.#.#',
    '#.#..#....#..#.#',
    '#.#..######..#.#',
    '#.#...####...#.#',
    '##.#...##...#.##',
    '#...########...#',
    '#.#.#.#..#.#.#.#',
    '#...########...#',
    '#..###....###..#',
    '#.#...#..#...#.#',
    '#..###.##.###..#',
    '#.....#..#.....#',
    '#..............#',
    '#.############.#',
    '#.#..........#.#',
    '#.#.##.##.##.#.#',
    '#.#..........#.#',
    '#.#.##.##.##.#.#',
    '#.############.#',
    '##............##',
    '##............##',
    '###..........###',
    '################'])

# obelisk 1x4 : gold pyramidion + red inscribed shaft
obj('obelisk', [[0xD6], [0x12], [0x14], [0x16]], None)
tile(0xD6, '...##...', '..####..', '..####..', '.######.', '.######.', '.######.', '########', '########')

# papyrus in a pot 2x3
obj('papyrus', [[0x84, 0x85], [0xF0, 0xF1], [0x5C, 0x5D]], [
    '#.#.#.....#.#.#.',
    '.#####...#####..',
    '..###.#.#.###...',
    '...#.#####.#....',
    '...#..###..#....',
    '...#...#...#....',
    '...#...#...#....',
    '....#..#..#.....',
    '....#..#..#.....',
    '.....#.#.#......',
    '.....#.#.#......',
    '......###.......',
    '......###.......',
    '......###.......',
    '.......#........',
    '.......#........',
    '..############..',
    '...##########...',
    '...#.#.#.#.#.#..',
    '...##########...',
    '....########....',
    '....########....',
    '.....######.....',
    '....########....'])
GROUP_COLORS[0x80 >> 3] = (3, 1)

# winged sun disk 3x1 (wall painting)
obj('wingsun', [[0xE8, 0x5F, 0xE9]], None)
tile(0xE8, '........', '##......', '.####...', '..######', '...#####', '....####', '......##', '........')
tile(0xE9, '........', '......##', '...####.', '######..', '#####...', '####....', '##......', '........')

# faience vase 1x2 (light blue)
obj('vase', [[0xEA], [0xEB]], [
    '..####..', '...##...', '...##...', '..####..', '.######.', '########', '#.#.#.##', '########',
    '.######.', '.######.', '..####..', '...##...', '...##...', '..####..', '.######.', '.######.'])

# eye of Horus 2x1, ankh 1x2, small ankh, scarab 2x1 (turquoise)
obj('eye', [[0x3C, 0x3D]], [   # yellow (digits group, light yellow)
    '..#############.',
    '................',
    '....#######.....',
    '..##..###..##...',
    '.#....###....###',
    '..##..###..##...',
    '....#######.#...',
    '.....#...#...#..'])
obj('ankh', [[0x2C], [0x2D]], [
    '..####..', '.##..##.', '.#....#.', '.#....#.', '.##..##.', '..####..', '########', '########',
    '...##...', '...##...', '...##...', '...##...', '...##...', '...##...', '..####..', '........'])
ANKH_SMALL = 0x29
tile(ANKH_SMALL, '..###...', '.#...#..', '.#...#..', '..###...', '#######.', '...#....', '...#....', '...#....')
# Egyptian water sign: parallel zig-zag waves (light blue, wall painting)
obj('waves', [[0xED, 0xEE]], [
    '................',
    '.#...#...#...#..',
    '#.#.#.#.#.#.#.#.',
    '...#...#...#...#',
    '.#...#...#...#..',
    '#.#.#.#.#.#.#.#.',
    '...#...#...#...#',
    '................'])

# ledge/platform (original char D8) restyled as gilded cornice; group 27 also holds the old DB border
GROUP_COLORS[0xD8 >> 3] = (11, 6)
tile(0xD8, '########', '........', '##.##.##', '##.##.##', '........', '########', '.#.#.#.#', '#.#.#.#.')
# original blue platform (0x94) redrawn as a red-on-lapis tile band (colours kept)
tile(0x94, '########', '........', '.######.', '.#....#.', '.#....#.', '.######.', '........', '########')


# ---- status words: PUNTOS in pink, VIDAS in green (copies of the original letters)
GROUP_COLORS[0xF8 >> 3] = (13, 1)
GROUP_COLORS[0xF0 >> 3] = (2, 1)
PINK = {ch: 0xF8 + i for i, ch in enumerate('PUNTOS')}
GREEN = {ch: 0xF2 + i for i, ch in enumerate('VIDAS')}
for mp in (PINK, GREEN):
    for ch, code in mp.items():
        T[code] = [''.join('#' if _g[0xCDA0 - 0x8500 + ord(ch) * 8 + y] & (0x80 >> x) else '.' for x in range(8)) for y in range(8)]

# ---- giant cyan lotus (goal of the maze): flower in group 0x20 (+0x2A, cyan group), leaves in 0xC4-0xC7
GROUP_COLORS[0x20 >> 3] = (7, 1)       # space group: 0x20 pattern is empty, so only 0x21-0x27 show it
GROUP_COLORS[0xC0 >> 3] = (2, 1)       # same green as before (original spider tiles C0-C3)
obj('biglotus', [[0x21, 0x22, 0x23, 0x24], [0x25, 0x26, 0x27, 0x2A], [0xC4, 0xC5, 0xC6, 0xC7]], [
    '...............##...............',
    '..............####..............',
    '.......#......####......#.......',
    '......###....######....###......',
    '......####...######...####......',
    '.......####..######..####.......',
    '..#.....####.######.####.....#..',
    '..###....###.######.###....###..',
    '...####...###.####.###...####...',
    '....######.###.##.###.######....',
    '.....######.###..###.######.....',
    '......######.######.######......',
    '.......####################.....',
    '........##################......',
    '.........################.......',
    '..........##############........',
    '...............##...............',
    '...............##...............',
    '..####.........##.........####..',
    '.######........##........######.',
    '########.......##.......########',
    '.#######......####......#######.',
    '..######....########....######..',
    '...####...##########.....####...'])


# ---- mirrored versions of the objects that face one way (variety)
def mirror_tile(src, dst):
    T[dst] = [r[::-1] for r in T[src]]
GROUP_COLORS[0xE0 >> 3] = (10, 1)       # gold group (the original goblet E1-E2 becomes golden)
for src, dst in ((0xC8, 0xE3), (0xCB, 0xE4), (0xCC, 0xE5), (0xCD, 0xE6), (0xCE, 0xE0), (0xCF, 0xE7)):
    mirror_tile(src, dst)
OBJ['anubis_r'] = (3, 3, [0xCA, 0xC9, 0xE3, 0xE6, 0xE5, 0xE4, 0x0E, 0x14, 0x0B])
OBJ['cat_r'] = (1, 3, [0xE0, 0xE7, 0x13])
mirror_tile(0x3D, 0x3E); mirror_tile(0x3C, 0x3F)
OBJ['eye_r'] = (2, 1, [0x3E, 0x3F])

# ---- cobwebs for the upper corners of the corridors (white, free statue-group slots B9-BE)
def _web():
    import math
    px = [[0] * 16 for _ in range(16)]
    for ang in (0, 22.5, 45, 67.5, 90):
        a = math.radians(ang)
        for k in range(0 if ang in (0, 45, 90) else 45, 120):
            r = k / 10
            x, y = int(round(r * math.cos(a))), int(round(r * math.sin(a)))
            if x < 16 and y < 16 and math.hypot(x, y) <= 11: px[y][x] = 1
    for R in (4.5, 8, 11):
        for k in range(0, 91):
            a = math.radians(k)
            x, y = int(round(R * math.cos(a))), int(round(R * math.sin(a)))
            if x < 16 and y < 16 and (x < 8 or y < 8): px[y][x] = 1
    return [''.join('#' if v else '.' for v in row) for row in px]
_w = _web()
big([[0xB9, 0xBA], [0xBB, None]], [r for r in _w])
assert all(r[8:] == '........' for r in _w[8:]), 'bottom-right of the web must stay empty'
mirror_tile(0xBA, 0xBC); mirror_tile(0xB9, 0xBD); mirror_tile(0xBB, 0xBE)
OBJ['web_l'] = (2, 2, [0xB9, 0xBA, 0xBB, 0xFF])
OBJ['web_r'] = (2, 2, [0xBC, 0xBD, 0xFF, 0xBE])
