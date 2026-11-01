import sys
from collections import deque
from PIL import Image, ImageDraw, ImageFont
import gen, sim, monsters, art
from rooms import Mem
from build import apply_art, patch_margins
from render import render
B = 0x8500
d = bytearray(open('game.bin', 'rb').read()); apply_art(d); patch_margins(d)
m = Mem(bytes(d)); m0 = Mem(open('game.bin', 'rb').read())
ent = {r: gen.room_entries(m, r) for r in range(256)}
pk, _ = monsters.pickup_table(m, lambda r: ent[r], gen.OBJDEFS_BY_ID)
slots = monsters.type_slots(m); codes = monsters.room_codes(m, slots)
pat = monsters.pattern_data()
# connectivity
info = {}
for r in range(256):
    nt = sim.compose(m0, r, decor=False)[0x1800:0x1b00]
    info[r] = (nt[11*32+13] == 0x20, nt[11*32+18] == 0x20, nt[16*32+16] == 0x20, nt[6*32+16] == 0x20)
dist = {0: 0}; par = {}; q = deque([0])
while q:
    r = q.popleft(); L, R, D, U = info[r]
    for ok, n in ((L, (r-1) % 256), (R, (r+1) % 256), (D, (r+16) % 256), (U, (r-16) % 256)):
        if ok and n not in dist: dist[n] = dist[r] + 1; par[n] = r; q.append(n)
LOT = gen.LOTUS_ROOM
path = [LOT]
while path[-1] in par: path.append(par[path[-1]])
ordered = path[::-1]
path = set(path)
REGS = [0, 0xe2, 6, 0x80, 0, 0x36, 7, 0]
def room_img(r):
    v = sim.compose(m, r, entries=ent[r], objdefs=gen.OBJDEFS_BY_ID)
    c = pk[r]
    if c:
        row = 8 if c & 0x80 else 11; col = c & 31
        if c & 0x40:
            v[0x1800 + row*32 + col] = 0x2C; v[0x1800 + (row+1)*32 + col] = 0x2D
        else:
            for k, ch in enumerate((0xC0, 0xC1, 0xC2, 0xC3)):
                v[0x1800 + (row + k // 2)*32 + col + k % 2] = ch
    v[0x3800 + 24*8:0x3800 + 24*8 + len(pat)] = bytes(pat)
    p2 = monsters.pattern_data2(); v[0x3A80:0x3A80 + len(p2)] = bytes(p2)
    sat = []
    segs, spid = slots[m[0xcb00 + r]]
    code = codes[r]; a = code & 3; aseg = (code >> 2) & 1; bb = (code >> 3) & 7
    segs2 = list(segs) + [(0x28, 0x60)] * 2; spid2 = list(spid) + [0x40] * 2
    if a:
        lo, hi = segs2[aseg]; sat += [0x57, (lo + hi) // 2, monsters.BASES[a], monsters.COLORS[a]]
    if bb in (1, 2):
        sat += [0x44, spid2[bb-1], 72, 13]
    elif bb in (4, 5):
        lo, hi = segs2[bb - 4]; sat += [0x46, (lo + hi) // 2, 80, 14]
    elif bb in (6, 7):
        sat += [0x48, spid2[bb - 6], 88, 7]
    elif bb == 3:
        k = a % 3 + 1; lo, hi = segs2[1 - aseg]; sat += [0x57, (lo + hi) // 2, monsters.BASES[k] + 8, monsters.COLORS[k]]
    sat += [208]
    v[0x1b00:0x1b00 + len(sat)] = bytes(sat)
    render(v, REGS, '_tmp_render.png', sprites=True, scale=1)
    im = Image.open('_tmp_render.png').convert('RGB').crop((16, 8, 248, 152))
    return im
TW, TH = 232, 144; GAP = 0; TOP = 110; LEFT = 50
W = LEFT + 16 * (TW + GAP) + 50; H = TOP + 16 * (TH + GAP) + 140
sheet = Image.new('RGB', (W, H), (24, 22, 30))
dr = ImageDraw.Draw(sheet)
try:
    f = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 16)
    fb = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 40)
    fs = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
except Exception:
    f = fb = fs = ImageFont.load_default()
dr.text((LEFT, 25), 'ANUBIS  -  MAPA DEL LABERINTO (256 pantallas)', fill=(230, 200, 90), font=fb)
def pos(r): return LEFT + (r % 16) * (TW + GAP), TOP + (r // 16) * (TH + GAP)
for r in range(256):
    x, y = pos(r)
    im = room_img(r)
    if r not in dist:
        im = Image.blend(im, Image.new('RGB', im.size, (24, 22, 30)), 0.65)
    sheet.paste(im, (x, y))
    col = (90, 90, 100)
    if r in path: col = (240, 200, 60)
    if r == 0: col = (80, 230, 110)
    if r == LOT: col = (130, 160, 255)
    w = 4 if r in path or r in (0, LOT) else 1
    if r in (0, LOT):
        dr.rectangle([x, y, x + TW - 1, y + TH - 1], outline=col, width=w)
    lab = str(r)
    dr.rectangle([x, y, x + 8 + 9 * len(lab), y + 20], fill=(0, 0, 0))
    dr.text((x + 4, y + 1), lab, fill=(255, 255, 255) if r in dist else (120, 120, 120), font=f)
ov = Image.new('RGBA', sheet.size, (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
cen = [(pos(r)[0] + TW // 2, pos(r)[1] + TH // 2) for r in ordered]
od.line(cen, fill=(255, 210, 60, 200), width=8, joint='curve')
for c in cen: od.ellipse([c[0] - 7, c[1] - 7, c[0] + 7, c[1] + 7], fill=(255, 210, 60, 230))
sheet.paste(Image.alpha_composite(sheet.convert('RGBA'), ov).convert('RGB'))
dr = ImageDraw.Draw(sheet)
for r in (0, LOT):
    x, y = pos(r); col = (80, 230, 110) if r == 0 else (130, 160, 255)
    dr.rectangle([x, y, x + TW - 1, y + TH - 1], outline=col, width=5)
for i in range(16):
    dr.text((LEFT + i * (TW + GAP) + TW // 2 - 10, TOP - 26), str(i), fill=(180, 180, 180), font=f)
ly = TOP + 16 * (TH + GAP) + 25
items = [((80, 230, 110), 'Inicio (pantalla 0)'), ((130, 160, 255), 'Loto gigante (pantalla %d, final)' % LOT),
         ((240, 200, 60), 'Camino mas corto hasta el loto (linea dorada)')]
for k, (c, t) in enumerate(items):
    dr.rectangle([LEFT + k * 900, ly, LEFT + k * 900 + 30, ly + 30], outline=c, width=4)
    dr.text((LEFT + k * 900 + 45, ly + 2), t, fill=(230, 230, 230), font=fs)
dr.text((LEFT, ly + 50), ''
        'Ankh (+1 vida), escarabajos verdes (+25 puntos) y monstruos en su patrulla.  El numero de cada pantalla sirve para el modo secreto 5.',
        fill=(200, 200, 200), font=fs)
sheet.save('mapa_laberinto.png', optimize=True)
print(sheet.size, len(dist))
