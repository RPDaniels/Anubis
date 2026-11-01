from PIL import Image, ImageDraw
from render import PAL
W, H = 112, 136
S = 1.4
def P(pts): return [(round(x * S), round(y * S)) for x, y in pts]
def draw():
    im = Image.new('P', (W, H), 1)
    im.putpalette([c for p in PAL for c in p] + [0] * (768 - 48))
    d = ImageDraw.Draw(im)
    G, B, L, K, R, WH = 10, 4, 5, 1, 8, 15
    nem = P([(32, 24), (8, 32), (0, 56), (0, 80)]) + [(56, 112), (56, 34)]
    nem[3] = (0, 112)
    mask = Image.new('1', (W, H), 0); ImageDraw.Draw(mask).polygon(nem, fill=1)
    px = im.load(); mp = mask.load()
    for y in range(H):
        for x in range(W):
            if mp[x, y]: px[x, y] = G if (y % 8) < 4 else B
    d.polygon(P([(33, 0), (24, 30), (42, 28)]), fill=K, outline=G)
    d.polygon(P([(33, 8), (29, 25), (38, 24)]), fill=G)
    head = P([(24, 30), (42, 26), (50, 30), (79, 42), (79, 47), (60, 52), (48, 58), (38, 60), (28, 54), (22, 42)])
    d.polygon(head, fill=K, outline=G)
    d.polygon(P([(42, 36), (48, 33.5), (55, 37), (48, 39.5)]), fill=WH)
    d.rectangle(P([(47, 35), (49, 38.5)]), fill=K)
    d.line(P([(55, 37), (63, 39.5)]), fill=G, width=2)
    d.line(P([(40, 41.5), (50, 41.5)]), fill=G)
    d.line(P([(30, 46), (36, 52)]), fill=G)
    d.point(P([(76, 44)])[0], fill=G)
    d.line(P([(65, 50), (52, 54)]), fill=G)
    d.polygon(P([(30, 56), (46, 58), (49, 76), (27, 76)]), fill=K, outline=G)
    y0 = 104
    d.rectangle([0, y0, W - 1, H - 1], fill=K)
    d.line([(0, y0), (W - 1, y0)], fill=G)
    for x in range(1, W, 4):
        d.rectangle([x, y0 + 2, x + 2, y0 + 6], fill=G)
    for x in range(2, W, 4):
        d.ellipse([x - 1, y0 + 9, x + 2, y0 + 14], fill=L)
    for x in range(0, W, 8):
        d.polygon([(x + 1, y0 + 17), (x + 6, y0 + 17), (x + 4, y0 + 23), (x + 3, y0 + 23)], fill=R)
    for x in range(0, W, 8):
        d.rectangle([x + 1, y0 + 26, x + 6, y0 + 29], fill=G if (x // 8) % 2 == 0 else L)
    return im

def fix_cells(im):
    """force <=2 colours per 8x8 cell (keep the two most common, remap the rest to nearest)"""
    px = im.load()
    def dist(a, b): return sum((x - y) ** 2 for x, y in zip(PAL[a], PAL[b]))
    bad = 0
    for cy in range(H // 8):
        for cx in range(W // 8):
            cnt = {}
            for y in range(8):
                for x in range(8):
                    c = px[cx * 8 + x, cy * 8 + y]; cnt[c] = cnt.get(c, 0) + 1
            if len(cnt) <= 2: continue
            bad += 1
            if set(cnt) == {1, 10, 4}:
                for y in range(8):
                    for x in range(8):
                        if px[cx * 8 + x, cy * 8 + y] == 4: px[cx * 8 + x, cy * 8 + y] = 1
                continue
            keep = sorted(cnt, key=lambda c: -cnt[c])[:2]
            if 1 in cnt and 1 not in keep and cnt[1] >= 3:
                others = [c for c in sorted(cnt, key=lambda c: -cnt[c]) if c != 1]
                keep = [1, others[0]]
            for y in range(8):
                for x in range(8):
                    c = px[cx * 8 + x, cy * 8 + y]
                    if c not in keep: px[cx * 8 + x, cy * 8 + y] = min(keep, key=lambda k: dist(c, k))
    return bad

if __name__ == '__main__':
    im = draw()
    im.convert('RGB').resize((W * 6, H * 6), Image.NEAREST).save('end/raw.png')
    print('cells fixed', fix_cells(im))
    im.convert('RGB').resize((W * 6, H * 6), Image.NEAREST).save('end/fixed.png')
