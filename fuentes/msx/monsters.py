# Moving monsters (hardware sprites) for ANUBIS
import random
import art, sim
from rooms import Mem, run

# ---------------------------------------------------------------- sprite art (facing left)
# snake (Rafa's design, sitting on the floor like the other walkers)
SNAKE = [[
    '................',
    '................',
    '................',
    '................',
    '....#...........',
    '...#.#..........',
    '######..........',
    '.####...........',
    '...##...........',
    '..##....##......',
    '..##...####.....',
    '.##...######....',
    '.##..###..##....',
    '#######....##..#',
    '.#####......###.',
    '................'], [
    '................',
    '................',
    '................',
    '....#...........',
    '...#.#..........',
    '######..........',
    '.####...........',
    '...##...........',
    '..##............',
    '..##.###....#...',
    '.##.#####..#....',
    '.##.##.##..#....',
    '##.##.##.##.....',
    '#####.#####.....',
    '.###...##.......',
    '................']]
SCORPION = [[
    '................',
    '................',
    '...........###..',
    '..........#...#.',
    '..............#.',
    '.............##.',
    '............###.',
    '.##........###..',
    '#..#......###...',
    '.###.#########..',
    '...###########..',
    '....#########...',
    '....#.#.#.#.#...',
    '...#.#.#.#.#....',
    '..#.#.#.#.#.....',
    '................'], [
    '................',
    '................',
    '...........###..',
    '..........#...#.',
    '..............#.',
    '.............##.',
    '............###.',
    '##.........###..',
    '..#.......###...',
    '.###.#########..',
    '...###########..',
    '....#########...',
    '.....#.#.#.#.#..',
    '....#.#.#.#.#...',
    '....#.#.#.#.#...',
    '................']]
MUMMY = [[
    '.....####.......',
    '....######......',
    '....#.##.#......',
    '....######......',
    '.....####.......',
    '##########......',
    '...########.....',
    '.....#####......',
    '....######......',
    '....#.####......',
    '....######......',
    '....###.##......',
    '....######......',
    '...###..###.....',
    '...##....##.....',
    '..###....###....'], [
    '.....####.......',
    '....######......',
    '....#.##.#......',
    '....######......',
    '.....####.......',
    '##########......',
    '...########.....',
    '.....#####......',
    '....######......',
    '....###.##......',
    '....######......',
    '....#.####......',
    '.....#####......',
    '.....##.##......',
    '.....##.##......',
    '....###.###.....']]
SPIDER = [[
    '.......##.......',
    '.......##.......',
    '.......##.......',
    '.......##.......',
    '......####......',
    '#.#..######..#.#',
    '.#.#.######.#.#.',
    '..#.########.#..',
    '...##########...',
    '..#.########.#..',
    '.#.#..####..#.#.',
    '#.#..##..##..#.#',
    '....#......#....',
    '...#........#...',
    '................',
    '................'], [
    '.......##.......',
    '.......##.......',
    '.......##.......',
    '.......##.......',
    '......####......',
    '.....######.....',
    '#.#.#######.#.#.',
    '.#.#########.#.#',
    '...##########...',
    '.#.#########.#.#',
    '#.#...####...#.#',
    '.....##..##.....',
    '....#......#....',
    '...#........#...',
    '..#..........#..',
    '................']]

BAT = [[
    '................',
    '................',
    '................',
    '#..............#',
    '##.....##.....##',
    '###...####...###',
    '#####.#..#.#####',
    '################',
    '.######..######.',
    '..####....####..',
    '...##......##...',
    '................',
    '................',
    '................',
    '................',
    '................'], [
    '................',
    '................',
    '................',
    '................',
    '................',
    '.......##.......',
    '......####......',
    '..###.#..#.###..',
    '.##############.',
    '###.########.###',
    '##...######...##',
    '#.....####.....#',
    '.......##.......',
    '................',
    '................',
    '................']]
# falling drop and its two splash frames (Rafa's design)
DROP = [[
    '................',
    '................',
    '................',
    '................',
    '................',
    '................',
    '.......##.......',
    '.......##.......',
    '......####......',
    '......##.#......',
    '.....###.##.....',
    '.....######.....',
    '.....######.....',
    '......####......',
    '.......##.......',
    '................']]
SPLASH = [[
    '................',
    '................',
    '.......#........',
    '................',
    '.......#........',
    '.......#........',
    '................',
    '.....#.#...#....',
    '..#...##..#.....',
    '......#.#.....#.',
    '....#####....#..',
    '.#..#.###..#....',
    '..#....###......',
    '....####.##..#..',
    '..#..###.##.#...',
    '.....#####......'], [
    '................',
    '................',
    '................',
    '................',
    '.......#........',
    '................',
    '................',
    '......#.........',
    '..#......#...#..',
    '#..#..#...#....#',
    '...#....#.....#.',
    '.#...#..#.#..##.',
    '..#...#...#.....',
    '....#..##...#...',
    '.....#..#..#....',
    '................']]

def sprite_bytes(rows):
    out = []
    for half in (0, 8):
        for y in range(16):
            v = 0
            for x in range(8):
                if rows[y][half + x] == '#': v |= 0x80 >> x
            out.append(v)
    return out

def mirror(rows):
    return [r[::-1] for r in rows]

KINDS = [  # kind id: (name, frames, colour)
    (1, 'snake', SNAKE, 3),
    (2, 'scorpion', SCORPION, 9),
    (3, 'mummy', MUMMY, 15),
]
FIRST_PAT = 24          # player uses patterns 0..23
def pattern_data():
    data = []
    # walkers: L0 L1 R0 R1 ; spider: F0 F1
    for _, _, frames, _ in KINDS:
        for f in frames: data += sprite_bytes(f)
        for f in frames: data += sprite_bytes(mirror(f))
    for f in SPIDER: data += sprite_bytes(f)
    return data
def pattern_data2():
    # bat F0 F1, drop, splash 1, splash 2 (pattern numbers 80, 84, 88, 92, 96)
    data = []
    for f in BAT + DROP + SPLASH: data += sprite_bytes(f)
    return data
# monster kinds: 1 snake 2 scorpion 3 mummy (walk) 4 spider (vertical) 5 bat (flies at head height) 6 drop (falls)
BASES = [0, 24, 40, 56, 72, 80, 88]
COLORS = [0, 3, 9, 15, 13, 14, 7]

# ---------------------------------------------------------------- level analysis
def type_slots(m):
    """per room type: two walker segments (xmin,xmax) and two spider columns (x)."""
    res = []
    for t in range(15):
        vram = bytearray(16384)
        for i in range(0x300): vram[0x1800 + i] = 0x20
        run(m, vram, 0xb000 + 13 * t)
        nt = vram[0x1800:0x1b00]
        cols = [c for c in range(2, 31) if nt[13 * 32 + c] != 0x20 and nt[12 * 32 + c] == 0x20
                and nt[11 * 32 + c] == 0x20]
        segs = []
        run_ = []
        for c in cols + [99]:
            if run_ and c != run_[-1] + 1:
                lo, hi = run_[0] * 8, run_[-1] * 8 - 8
                lo, hi = max(lo, 0x28), min(hi, 0xC8)
                if hi - lo >= 40: segs.append((lo, hi))
                run_ = []
            run_.append(c)
        segs.sort(key=lambda s: s[0] - s[1])
        spid = []
        for c in range(5, 28):
            if nt[6 * 32 + c] != 0x20 and nt[6 * 32 + c + 1] != 0x20 and all(
                    nt[r * 32 + c] == 0x20 and nt[r * 32 + c + 1] == 0x20 for r in range(7, 13)) \
                    and not 12 <= c <= 18:
                spid.append(c * 8)
        rng = random.Random(t)
        rng.shuffle(spid)
        spid = spid[:2]
        if len(spid) == 2 and abs(spid[0] - spid[1]) < 40:
            spid = spid[:1]
        res.append((segs[:2], spid))
    return res

def room_codes(m, slots):
    """byte: bits0-1 A walker (0 none,1 snake,2 scorpion,3 mummy), bit2 A segment,
             bits3-5 B (0 none, 1/2 spider at column 0/1, 3 walker on the other segment,
                        4/5 bat over segment 0/1, 6/7 falling drop at column 0/1), bit6 spdA, bit7 spdB"""
    codes = []
    for r in range(256):
        rng = random.Random(4242 + r * 31)
        segs, spid = slots[m[0xcb00 + r]]
        if r in (0, 240):            # start room and the lotus room are monster-free
            codes.append(0); continue
        a = b = aseg = 0
        if segs and rng.random() < 0.85:
            a = rng.choice([1, 2, 3]); aseg = rng.randrange(len(segs))
        opts = [0]
        import gen
        theme = r in gen.THEMES
        if spid: opts += [1, 1] + ([] if theme else [6, 6])
        if len(spid) > 1: opts += [2] + ([] if theme else [7])
        if len(segs) > 1 and a: opts += [3, 3]
        if segs: opts += [4, 4]
        if len(segs) > 1: opts += [5]
        if rng.random() < 0.7: b = rng.choice(opts)
        if not a and not b and spid: b = 1
        sa = 1 if rng.random() < 0.35 else 0
        sb = 1 if rng.random() < 0.35 else 0
        codes.append(a | (aseg << 2) | (b << 3) | (sa << 6) | (sb << 7))
    return codes

# ---------------------------------------------------------------- pickups (ankh = +1 life, was = +25 points)
def pickup_table(m, entries_for, objdefs):
    """byte per room: bits0-4 column, bit6 = ankh (else green scarab, 2x2), bit7 = elevated (rows 8-9, else 11-12)"""
    tab = []
    stats = {'ankh': 0, 'scarab': 0}
    jars = {r for r, _ in canopic_rooms(m, entries_for, objdefs)}
    for r in range(256):
        rng = random.Random(777 + r * 13)
        if r == 240 or r in jars:            # the lotus room and the canopic-jar rooms have no other pickup
            tab.append(0); continue
        import gen
        if r in gen.MULTI_PICKUPS:
            nt = sim.compose(m, r, entries=entries_for(r), objdefs=objdefs)[0x1800:0x1b00]
            for code in gen.MULTI_PICKUPS[r]:
                w = 1 if code & 0x40 else 2
                c = code & 31; rows = (8, 9) if code & 0x80 else (11, 12)
                assert all(nt[y * 32 + c + x] == 0x20 for y in rows for x in range(w)), (r, code)
                assert all(y * 32 + c + x not in sim.CHECK_CELLS for y in rows for x in range(w))
            tab.append(gen.MULTI_PICKUPS[r][0])
            stats['ankh' if gen.MULTI_PICKUPS[r][0] & 0x40 else 'scarab'] += len(gen.MULTI_PICKUPS[r])
            continue
        nt = sim.compose(m, r, entries=entries_for(r), objdefs=objdefs)[0x1800:0x1b00]
        roll = rng.random()
        if roll < 0.20: kind = 0x40
        elif roll < 0.72: kind = 0
        else:
            tab.append(0); continue
        w = 1 if kind else 2
        cands = []
        for c in range(3, 30 - w):
            if any(cc in (12, 13, 14, 17, 18, 19) for cc in range(c, c + w)):
                continue
            if any(nt[13 * 32 + cc] == 0x20 for cc in range(c, c + w)):
                continue
            col_open = lambda rows, cc: all(nt[y * 32 + cc] == 0x20 for y in rows)
            if all(col_open((11, 12), cc) for cc in range(c - 1, c + w + 1)):
                cands.append(c)
            if all(col_open(range(8, 13), cc) for cc in range(c, c + w)) and \
                    all(col_open((8, 9), cc) for cc in (c - 1, c + w)):
                cands.append(c | 0x80)
        if not cands:
            tab.append(0); continue
        v = rng.choice(cands) | kind
        stats['ankh' if kind else 'scarab'] += 1
        tab.append(v)
    return tab, stats

# ---------------------------------------------------------------- the four canopic jars (needed to open the lotus)
JAR_NAMES = ['Imsety', 'Hapy', 'Duamutef', 'Qebehsenuef']
_CANOPIC = None
def connectivity(m):
    """per room (left, right, down, up) open, from the original layout (the 4 collision cells)"""
    from rooms import Mem
    info = {}
    for r in range(256):
        nt = sim.compose(m, r, decor=False)[0x1800:0x1b00]
        info[r] = (nt[11*32+13] == 0x20, nt[11*32+18] == 0x20, nt[16*32+16] == 0x20, nt[6*32+16] == 0x20)
    return info
def bfs(info, start):
    from collections import deque
    dist = {start: 0}; q = deque([start])
    while q:
        r = q.popleft(); L, R, D, U = info[r]
        for ok, n in ((L, (r-1) % 256), (R, (r+1) % 256), (D, (r+16) % 256), (U, (r-16) % 256)):
            if ok and n not in dist: dist[n] = dist[r] + 1; q.append(n)
    return dist
def canopic_rooms(m, entries_for, objdefs):
    """four reachable rooms, far from the start and from each other, each with a free floor spot
    (2 columns, rows 11-12 open over a solid row 13, away from the explorer's centre columns).
    Returns [(room, column)] in the order Imsety, Hapy, Duamutef, Qebehsenuef."""
    global _CANOPIC
    if _CANOPIC: return _CANOPIC
    import gen
    info = connectivity(m)
    d0 = bfs(info, 0)
    spots = {}
    for r in d0:
        if r in (0, gen.LOTUS_ROOM) or r in gen.MULTI_PICKUPS: continue
        nt = sim.compose(m, r, entries=entries_for(r), objdefs=objdefs)[0x1800:0x1b00]
        cands = []
        for c in range(4, 27):
            if any(cc in range(12, 20) for cc in (c, c + 1)): continue
            if any(nt[13*32+cc] == 0x20 for cc in (c, c + 1)): continue
            if all(nt[y*32+cc] == 0x20 for y in (10, 11, 12) for cc in range(c - 1, c + 3)):
                cands.append(c)
        if cands: spots[r] = min(cands, key=lambda c: abs(c - 16))
    anchors = {0: d0, gen.LOTUS_ROOM: bfs(info, gen.LOTUS_ROOM)}   # far from the start, the lotus and each other
    chosen = []
    while len(chosen) < 4:
        best = max((r for r in spots if r not in chosen and d0[r] >= 12),
                   key=lambda r: (min(a.get(r, 0) for a in anchors.values()), d0[r]))
        chosen.append(best); anchors[best] = bfs(info, best)
    chosen.sort(key=lambda r: d0[r])
    _CANOPIC = [(r, spots[r]) for r in chosen]
    return _CANOPIC
