# Offline generator of per-room decoration lists
import random
import art, sim
from rooms import Mem

OPEN = 0x20
FLOORS = {art.FLOOR_B, art.FLOOR_R, 0x94, 0xD8}
CEILS = {art.CEIL_A, art.CEIL_B, 0xD8}
MASON = set(range(0x60, 0x68))

FLOOR_OBJS = ['cobra', 'mummy', 'pillar', 'column', 'statue', 'bluevase', 'goblet', 'amphora', 'jar', 'brazier', 'anubis', 'anubis_r', 'cat', 'cat_r', 'coffin', 'obelisk', 'papyrus', 'vase']
FLOOR_W = {'amphora': 5, 'jar': 3, 'brazier': 5, 'anubis': 3, 'cat': 3, 'coffin': 2, 'obelisk': 2,
           'papyrus': 4, 'vase': 4}
WALL_OBJS = ['cartblue', 'cartgold', 'bluepanel', 'torch', 'eye', 'eye_r', 'waves', 'wingsun']
WALL_W = {'torch': 5, 'eye': 3, 'ankh': 2, 'scarab': 3, 'wingsun': 3}

def make_panels():
    """Inscription panels carved in the masonry (fixed set of defs)."""
    blues, reds = art.BLUE_GLYPHS, art.RED_GLYPHS + [0xA5, 0xA6, 0xA7]
    rng = random.Random(7)
    panels = {}
    for name, (gc, gr) in {'panel2x2': (2, 2), 'panel3x2': (3, 2), 'panel4x2': (4, 2),
                           'panel3x3': (3, 3), 'panel5x2': (5, 2), 'panel2x3': (2, 3),
                           'panel4x3': (4, 3), 'panel6x2': (6, 2)}.items():
        w = gc + 1; h = gr + 2
        chars = []
        for y in range(h):
            for x in range(w):
                if y == 0 or y == h - 1:
                    chars.append(art.FLOOR_B if x % 2 == 0 else art.FLOOR_R)
                elif x == gc:
                    chars.append(art.RULE)
                else:
                    pool = blues if x % 2 == 0 else reds
                    chars.append(rng.choice(pool))
        panels[name] = (w, h, chars)
    return panels

PANELS = make_panels()

# original ANUBIS graphics reused as decoration in the other rooms
def _orig(w, h, chars):
    return (w, h, [0xFF if c == 0x20 else c for c in chars])
ORIG = {
    'mummy':    _orig(4, 2, [0x00, 0x20, 0x20, 0x20, 0x01, 0x02, 0x03, 0x04]),
    'pillar':   _orig(2, 6, [0x05, 0x06] * 6),
    'column':   _orig(2, 6, list(range(0x68, 0x74))),
    'statue':   _orig(4, 6, [0xa8, 0xa9, 0x20, 0x20, 0xaa, 0xab, 0x20, 0x20, 0xac, 0xad, 0xae, 0x20,
                             0xaf, 0xb0, 0xb1, 0x20, 0xb2, 0xb3, 0xb4, 0x20, 0xb5, 0xb6, 0xb7, 0xb8]),
    'bluevase': _orig(2, 2, [0x98, 0x99, 0x9a, 0x9b]),
    'goblet':   _orig(1, 2, [0xe1, 0xe2]),
    'cartblue': _orig(8, 2, [0x90, 0x91] * 4 + [0x92, 0x93] * 4),
    'cartgold': _orig(8, 2, [0xa0, 0xa1] * 4 + [0xa2, 0xa3] * 4),
    'bluepanel': _orig(2, 2, [0x88, 0x89, 0x8a, 0x8b]),
    'cobra':    _orig(3, 4, list(range(0x78, 0x84))),
}
FULL = {'pillar', 'column', 'statue'}
OBJDEFS = dict(art.OBJ); OBJDEFS.update(PANELS); OBJDEFS.update(ORIG)
OBJ_IDS = {name: i for i, name in enumerate(OBJDEFS)}
ID_NAMES = {i: n for n, i in OBJ_IDS.items()}
OBJDEFS_BY_ID = {i: OBJDEFS[n] for n, i in OBJ_IDS.items()}

KEEP = set(sim.CHECK_CELLS)
LOTUS_ROOM = 240
# hand-decorated theme rooms: (object, row, col) placed before anything else; no random floor/wall objects there
def _row(name, row, cols): return [(name, row, c) for c in cols]
THEMES = {
    38:  _row('column', 7, [2, 11, 19, 28]),                                            # colonnade of red columns
    118: [('statue', 7, 14)] + _row('column', 7, [19, 22]),                             # seated pharaoh at a closed dead end
    140: _row('coffin', 9, [4, 6, 8]) + [('cat', 10, 21), ('waves', 8, 24)],            # three coffins watched by a cat
    104: [('cobra', 9, 14)],                                                            # cobra guarding a left dead end
    141: [('goblet', 11, 3), ('cartblue', 9, 5), ('goblet', 11, 14),                    # blue cartouches between goblets
          ('goblet', 11, 19), ('cartblue', 9, 21), ('goblet', 11, 29)],
    250: [('cartgold', 9, 4), ('brazier', 10, 15), ('cartgold', 9, 20)],                # gold cartouches around a brazier
    251: _row('torch', 8, [3, 12, 19, 28]) + _row('brazier', 10, [4, 10, 20, 26]),      # hall of torches and braziers
    252: _row('papyrus', 10, [3, 5]) + [('waves', 8, 3), ('anubis_r', 10, 21), ('amphora', 11, 26)],  # papyrus marsh
    50:  [('waves', 8, 4), ('bluevase', 11, 3), ('bluepanel', 9, 8), ('cartblue', 9, 19),          # lapis room
          ('bluevase', 11, 28)],
    55:  [('cat_r', 10, 4), ('cat', 10, 7), ('eye', 8, 5), ('jar', 12, 10)],                       # two cats face to face
    84:  [('cat_r', 10, 20), ('cat', 10, 23), ('cobra', 9, 26)],
    1:   [('cat_r', 10, 3), ('wingsun', 9, 5), ('cat', 10, 9), ('goblet', 11, 12), ('cartgold', 8, 19)],
    177: [('column', 7, 28), ('eye_r', 8, 22)],                                                    # + three ankh pickups
    217: [('waves', 8, 20), ('waves', 8, 24), ('anubis', 10, 28)],                                  # + three scarab pickups
}
THEMES.update({
    # the arrival: the giant lotus at the far end of the corridor, over the water
    240: _row('waves', 8, [20, 24, 28]) + _row('waves', 10, [22, 26]),
    # water hall: full of waves, one papyrus and a blue vase as accents (blue/cyan harmony)
    247: _row('waves', 8, [3, 7, 11, 20, 24, 28]) + _row('waves', 10, [5, 9, 22, 26]) +
         [('papyrus', 10, 15), ('bluevase', 11, 28)],
    # mirror symmetry around the shaft: torches, jackals facing the centre, amphorae, winged sun on the axis
    245: [('torch', 8, 3), ('anubis_r', 10, 4), ('amphora', 11, 8), ('wingsun', 8, 14),
          ('amphora', 11, 22), ('anubis', 10, 25), ('torch', 8, 28)],
    # contrast: one golden coffin lit by two braziers in an empty dark hall, a lone eye far away
    249: [('brazier', 10, 4), ('coffin', 9, 7), ('brazier', 10, 10), ('eye', 8, 25)],
    # golden tones only: cats, jackal, obelisk, golden goblets and the gold cartouche band
    248: [('cat_r', 10, 3), ('obelisk', 9, 5), ('anubis_r', 10, 7), ('goblet', 11, 20),
          ('cartgold', 8, 21), ('goblet', 11, 28), ('cat', 10, 30)],
    # hall of eyes: pairs of eyes facing each other, waves between, obelisks framing the room
    87:  [('obelisk', 9, 2), ('eye_r', 8, 4), ('waves', 10, 6), ('eye', 8, 9),
          ('eye_r', 8, 20), ('waves', 10, 23), ('eye', 8, 25), ('obelisk', 9, 29)],
    # crypt: mummy, coffins and golden goblets in white and gold
    174: [('mummy', 11, 3), ('coffin', 9, 8), ('goblet', 11, 11), ('goblet', 11, 20), ('coffin', 9, 22),
          ('column', 7, 28)],
    # the former random layout of room 174, kept on purpose
    168: [('torch', 9, 2), ('coffin', 9, 5), ('bluepanel', 8, 9), ('torch', 8, 20), ('mummy', 11, 23), ('cat', 10, 29)],
})

# rooms with a row of pickups: room -> list of pickup codes (bits0-4 col, bit6 ankh, bit7 elevated)
MULTI_PICKUPS = {177: [0x40 | 6, 0x40 | 8, 0x40 | 10], 217: [19, 22, 25]}

_DROPCOLS = None
def drop_columns(m, room):
    """screen columns crossed by a falling drop in this room (kept free of tall objects)"""
    global _DROPCOLS
    if _DROPCOLS is None:
        import monsters
        slots = monsters.type_slots(m); codes = monsters.room_codes(m, slots)
        _DROPCOLS = {}
        for r in range(256):
            b = (codes[r] >> 3) & 7
            if b in (6, 7):
                spid = list(slots[m[0xcb00 + r]][1]) + [0x40, 0x40]
                c = spid[b - 6] // 8
                _DROPCOLS[r] = [c - 1, c, c + 1, c + 2]
    return _DROPCOLS.get(room, [])
NO_OBJ = {0: {'coffin'}}      # room 0: no coffin
DROP_OBJ = {0: {'amphora'}}   # removed after placement (keeps the rest of the layout as it was)
LOTUS_POS = {}   # filled by room_entries

def room_entries(m, room):
    rng = random.Random(1000 + room * 7919)
    base = sim.compose(m, room, objects=False)[0x1800:0x1b00]
    full = sim.compose(m, room, objects=True)[0x1800:0x1b00]
    occ = set()
    for i in range(768):
        if base[i] != full[i]:
            r, c = divmod(i, 32)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    occ.add((r + dy) * 32 + c + dx)
    used = set(occ) | KEEP
    entries = []
    # cobwebs in the upper corners of the corridors
    HANG = (OPEN, art.LOTUS, art.BUD)
    def solid(i): return base[i] not in HANG
    for r in range(2, 17):
        for c in range(3, 29):
            i = r * 32 + c
            if base[i] not in HANG or base[i + 1] not in HANG or not solid(i - 32) or not solid(i - 31):
                continue
            if base[i + 32] != OPEN or base[i + 33] != OPEN:
                continue
            cellsw = [i, i + 1, i + 32, i + 33]
            if any(x in used for x in cellsw):
                continue
            if solid(i - 1) and rng.random() < 0.55:
                entries.append((OBJ_IDS['web_l'], i)); used.update(cellsw)
            elif solid(i + 2) and rng.random() < 0.55:
                entries.append((OBJ_IDS['web_r'], i)); used.update(cellsw)
    for c in drop_columns(m, room):
        for r in range(7, 13):
            used.add(r * 32 + c)
    theme = THEMES.get(room)
    if theme:
        for name, r, c in theme:
            w, h, chars = OBJDEFS[name]
            pos = r * 32 + c
            cl = [pos + y * 32 + x for y in range(h) for x in range(w)]
            assert not any(x in KEEP for x in cl), (room, name)
            assert all(base[x] in (OPEN, art.LOTUS, art.BUD) for x in cl), (room, name, r, c)
            if name not in WALL_OBJS:      # floor objects must stand on the floor
                assert all(base[(r + h) * 32 + c + x] not in (OPEN, art.LOTUS, art.BUD) for x in range(w)), (room, name)
            entries.append((OBJ_IDS[name], pos)); used.update(cl)
    if room == LOTUS_ROOM:
        w, h, _ = OBJDEFS['biglotus']
        for c in [14]:                     # against the dead-end wall: the end of the journey
            pos = (13 - h) * 32 + c
            cl = [pos + y * 32 + x for y in range(-1, h) for x in range(w)]
            if all(base[i] == OPEN and i not in used for i in cl) and all(base[13 * 32 + c + x] != OPEN for x in range(w)):
                entries.append((OBJ_IDS['biglotus'], pos)); LOTUS_POS[room] = pos
                for y in range(-2, h + 1):
                    for x in range(-3, w + 3): used.add(pos + y * 32 + x)
                break
        assert room in LOTUS_POS, 'no place for the lotus'

    def cells(pos, w, h):
        return [pos + y * 32 + x for y in range(h) for x in range(w)]

    def ok_open(pos, w, h):
        r, c = divmod(pos, 32)
        if c < 2 or c + w > 31 or r < 1 or r + h > 19:
            return False
        return all(base[i] == OPEN and i not in used for i in cells(pos, w, h))

    def reserve(pos, w, h, mx, my=1):
        r, c = divmod(pos, 32)
        for y in range(r - my, r + h + my):
            for x in range(c - mx, c + w + mx):
                used.add(y * 32 + x)

    # floor objects
    spots = []
    for name in ([] if theme else [n for n in FLOOR_OBJS if n not in NO_OBJ.get(room, ())]):
        w, h, _ = OBJDEFS[name]
        for r in range(1, 19):
            for c in range(2, 31 - w + 1):
                pos = r * 32 + c
                below = [(r + h) * 32 + c + x for x in range(w)]
                if r + h > 18 or not all(base[i] in FLOORS for i in below):
                    continue
                # keep at least one free row above the object under the lotus
                spots.append((name, pos))
    rng.shuffle(spots)
    want = rng.choice([1, 2, 2, 3, 3, 3, 4])
    placed = []
    for name, pos in spots:
        if len(placed) >= want:
            break
        w, h, _ = OBJDEFS[name]
        if name in [p for p in placed] and rng.random() < 0.7:
            continue
        r, c = divmod(pos, 32)
        if name in FULL:
            above = [pos - 32 + x for x in range(w)]
            if not all(base[i] in CEILS for i in above):
                continue
            if not all(base[i] in (OPEN, art.LOTUS, art.BUD) and i not in used for i in cells(pos, w, h)):
                continue
        elif not ok_open(pos - 32, w, h + 1):      # one free row above
            continue
        entries.append((OBJ_IDS[name], pos)); placed.append(name)
        reserve(pos, w, h, 2)
    # wall paintings: float on the back wall with free space below
    spots = []
    for name in ([] if theme else WALL_OBJS):
        w, h, _ = OBJDEFS[name]
        for r in range(1, 19):
            for c in range(2, 31 - w + 1):
                spots.append((name, r * 32 + c))
    rng.shuffle(spots)
    if rng.random() < 0.35:     # give the wide original cartouche bands a chance first
        spots.sort(key=lambda s: 0 if s[0] in ('cartblue', 'cartgold') else 1)
    want = rng.choice([1, 1, 2, 2, 3])
    n = 0
    for name, pos in spots:
        if n >= want:
            break
        w, h, _ = OBJDEFS[name]
        r, c = divmod(pos, 32)
        # need: row above is lotus/open-free, and 3 open rows below, and not resting on floor
        if c <= 18 and c + w >= 13:
            continue
        if not ok_open(pos, w, h + 1):
            continue
        above = [pos - 32 + x for x in range(w)]
        if not all(base[i] in (OPEN, art.LOTUS, art.BUD) for i in above):
            continue
        if not any(base[i] in (art.LOTUS, art.BUD) for i in above) and not ok_open(pos - 32, w, 1):
            continue
        entries.append((OBJ_IDS[name], pos)); n += 1
        reserve(pos, w, h, 3)
    # inscription panels inside thick masonry
    spots = []
    for name in PANELS:
        w, h, _ = PANELS[name]
        for r in range(1, 19):
            for c in range(2, 31 - w + 1):
                spots.append((name, r * 32 + c))
    rng.shuffle(spots)
    if rng.random() < 0.35:     # give the wide original cartouche bands a chance first
        spots.sort(key=lambda s: 0 if s[0] in ('cartblue', 'cartgold') else 1)
    want = rng.choice([1, 1, 2, 2, 3])
    n = 0
    for name, pos in spots:
        if n >= want:
            break
        w, h, _ = PANELS[name]
        r, c = divmod(pos, 32)
        if r < 2 or c < 3 or c + w > 30 or r + h > 18:
            continue
        area = [(r + y) * 32 + c + x for y in range(-1, h + 1) for x in range(-1, w + 1)]
        if all(base[i] in MASON and i not in used for i in area):
            entries.append((OBJ_IDS[name], pos)); n += 1
            for i in area: used.add(i)
            reserve(pos, w, h, 2)
    if room in DROP_OBJ:
        entries = [(o, p) for o, p in entries if ID_NAMES.get(o) not in DROP_OBJ[room]]
    return entries

if __name__ == '__main__':
    import sys
    from build import apply_art, patch_margins, sheet
    d = bytearray(open('game.bin', 'rb').read())
    apply_art(d); patch_margins(d)
    m = Mem(d)
    rooms = [int(x) for x in sys.argv[2:]]
    import os
    sheet(m, rooms, sys.argv[1], entries_for=lambda r: room_entries(m, r), objdefs=OBJDEFS_BY_ID,
          scale=int(os.environ.get('SCALE', '1')))
    for r in rooms:
        print(r, [(ID_NAMES[i], divmod(p, 32)) for i, p in room_entries(m, r)])
