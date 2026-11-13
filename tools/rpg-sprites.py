#!/usr/bin/env python3
# Draws RPG's pixel art as PNGs (no dependencies): the class sprites
# (stubby 16x16 adventurers with a one-pixel dark outline) and the castle
# scenery (wall, floor, mountains, clouds, sun, moon, stars, props).
#
#   python3 tools/rpg-sprites.py rpg/mods/rpg/art
#
# Edit the grids below (one character per pixel, "." is empty) and re-run.
# Everything is drawn at 8 image pixels per art pixel and shown at 4.
import os, struct, sys, zlib
if len(sys.argv) != 2:
    sys.exit("usage: rpg-sprites.py <output folder>")
out = sys.argv[1]
os.makedirs(out, exist_ok=True)
OUTLINE = "#141a26"
COMMON = {"s": "#f2c9a0", "k": "#1b2233"}
SPR = {
"wizard": ({"h":"#5a3dab","y":"#f2c14e","g":"#f2c14e","c":"#8fe3ff","C":"#ffffff","w":"#8a5a2b","b":"#f4f7fb","r":"#6b4bc4","R":"#5a3dab","d":"#3d2a80"}, [
"................",
".......hh.......",
"......hhhh...c..",
"......hyhh..cCc.",
".....gggggg..c..",
"....hhhhhhhh.w..",
".....ssssss..w..",
".....skssks..w..",
".....bssssb..w..",
".....bbbbbb..w..",
"....rrbbbbrr.w..",
"...srrrbbrrrsw..",
"....rrrRRrrr.w..",
"....gggggggg.w..",
".....dd..dd..w..",
"................",
]),
"healer": ({"t":"#2fae8e","h":"#e6dfcc","y":"#f3cf6b","g":"#f2c14e","m":"#7df0c0","w":"#c9a66b","r":"#f6f1e2","d":"#8a6f47"}, [
"................",
"................",
".....tttttt..g..",
"....tyyyyyytgmg.",
"....tsssssst.g..",
"....tsksskst.w..",
"....tsssssst.w..",
".....hssssh..w..",
".....rrrrrr..w..",
"....rrrttrrr.w..",
"...srrttttrrsw..",
"....rrrttrrr.w..",
"....rrrrrrrr.w..",
"....tttttttt.w..",
".....dd..dd..w..",
"................",
]),
"warrior": ({"p":"#c94040","a":"#9aa7b8","A":"#dfe6ee","u":"#3a6fc4","g":"#f2c14e","d":"#7a5230","b":"#5b6675"}, [
"................",
".......pp.......",
"......ppp....A..",
".....aaaaaa..A..",
"....aaAAAAaa.A..",
"....aaaaaaaa.A..",
"....askaaksa.A..",
"....assssssa.A..",
".....ssssss..A..",
"....AaaaaaaA.A..",
".uuuuaaaaaap.A..",
".ugguaaaaaapggg.",
".ugguddgdddpsd..",
".uuuuaa..aap....",
".....bb..bb.....",
"................",
]),
"archer": ({"p":"#e85d5d","n":"#3f8f55","N":"#2c6b3e","d":"#7a5230","c":"#f4ecd8","q":"#a06a3a","g":"#f2c14e"}, [
"................",
"......p.........",
".....ppnnnn.....",
".....nnnnnnn....",
"...NNNNNNNNN....",
"....ddssssddd...",
"....dskssksdcd..",
"....dssssssdcd..",
".....ssssss.c.d.",
".cc..nnnnnn.c.d.",
".qq.nndnnnnns.d.",
".qqsnnndnnnnc.d.",
".qq.ddddgdddcd..",
"....NNNNNNNNcd..",
".....dd..dd.d...",
"................",
]),
}

def canvas(rows, size, pad, dx=lambda y: 0):
    g = [[None] * size for _ in range(size)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".": g[y + pad][x + pad + dx(y)] = ch
    return g

def outlined(g):
    n = len(g)
    o = [r[:] for r in g]
    for y in range(n):
        for x in range(n):
            if g[y][x] is None and any(0 <= y+j < n and 0 <= x+i < n and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1))):
                o[y][x] = "#"
    return o

SCALE = 8  # 8 image pixels per sprite pixel: 2x a 4px on-screen pixel, so retina draws it 1:1

def png(g, pal):
    n = len(g)
    w = len(g[0])
    rgba = lambda ch: bytes.fromhex(pal.get(ch, ch)[1:]) + b"\xff"
    raw = b""
    for row in g:
        line = b"\x00" + b"".join((rgba(ch) if ch else b"\x00\x00\x00\x00") * SCALE for ch in row)
        raw += line * SCALE
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w * SCALE, n * SCALE, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))

def lift(rows, side):
    # tuck one foot up out of sight: blank its two boot pixels
    r = list(rows[14]); a = 5 if side > 0 else 9
    r[a] = r[a + 1] = "."
    return rows[:14] + ["".join(r)] + rows[15:]

for name, (pal, rows) in SPR.items():
    pal = {**COMMON, **pal, "#": OUTLINE}
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), (name, [len(r) for r in rows])
    w = lambda n, g: open(os.path.join(out, n), "wb").write(png(outlined(g), pal))
    w(f"{name}.png", canvas(rows, 18, 1))                       # 16x16 art, 1px margin for the outline
    for tag, side in (("l", -1), ("r", 1)):                     # lean a pixel, other foot lifted
        w(f"{name}-walk-{tag}.png", canvas(lift(rows, side), 18, 1, lambda y: side if y < 14 else 0))
    w(f"{name}-rag-c.png", canvas(rows, 22, 3))                 # dangling: straight, or sheared each way
    for tag, side in (("l", -1), ("r", 1)):
        w(f"{name}-rag-{tag}.png", canvas(rows, 22, 3, lambda y: side * round(y * 0.2)))


# ---- Scenery ---------------------------------------------------------------
import random

def save(name, g, pal={}):
    open(os.path.join(out, name), "wb").write(png(g, pal))

def chars(rows, pal):
    width = max(len(r) for r in rows)
    return [[pal[c] if c != "." else None for c in r.ljust(width, ".")] for r in rows]

def blank(w, h, fill=None):
    return [[fill] * w for _ in range(h)]

# Battlement wall, 32x16, tiles sideways: two merlons, then courses of stone.
def wall():
    rnd = random.Random(7)
    base, light, dark, mortar = "#7d8590", "#9aa3ad", "#646c78", "#4a515c"
    g = blank(32, 16)
    for x0 in (0, 16):
        for x in range(x0, x0 + 10):
            for y in range(5):
                g[y][x] = light if y == 0 else dark if x == x0 + 9 else base
    for x in range(32):
        g[5][x] = light
    y = 6
    for course, h in enumerate((3, 3, 2)):
        off = 0 if course % 2 == 0 else 4
        shade = {}
        for yy in range(y, y + h):
            for x in range(32):
                brick = ((x - off) % 32) // 8
                shade.setdefault(brick, rnd.choice([base, base, base, light, dark]))
                g[yy][x] = mortar if (x - off) % 8 == 7 else shade[brick]
        y += h
        if y < 16:
            for x in range(32): g[y][x] = mortar
            y += 1
    return g

# Wooden floor, 32x38, tiles sideways: planks with staggered joints and grain.
def floor():
    rnd = random.Random(3)
    gap, tones, grain = "#8a5a33", ["#b9834f", "#c08d58", "#ad7745", "#b9834f"], "#a06c3d"
    g = blank(32, 38)
    for y in range(38):
        course = y // 6
        r = random.Random(100 + course)
        joint = r.randrange(4, 28)
        left, right = r.choice(tones), r.choice(tones)
        for x in range(32):
            if y % 6 == 0 or y == 37: g[y][x] = gap
            elif x == joint: g[y][x] = gap
            else: g[y][x] = left if x < joint else right
    for _ in range(26):
        x, y = rnd.randrange(31), rnd.randrange(38)
        if y % 6 not in (0, 1) and g[y][x] != gap and g[y][x + 1] != gap: g[y][x] = g[y][x + 1] = grain
    return g

# Distant snowy mountains, 64x20, tiles sideways.
def mountains():
    peaks = [(8, 15, 1.0), (24, 19, 0.9), (40, 13, 1.1), (54, 17, 0.8)]
    g = blank(64, 20)
    for x in range(64):
        best = max(((ph - min(abs(x - px), 64 - abs(x - px)) * sl, px) for px, ph, sl in peaks))
        h = max(4, int(best[0]))
        lit = ((x - best[1] + 32) % 64) - 32 < 0
        for d in range(h):
            y = 19 - d
            snow = h >= 11 and d >= h - (3 if lit else 2)
            g[y][x] = "#eef3f8" if snow else ("#6f88a6" if lit else "#566e8b")
    return g

def disc(n, colour, spots=()):
    g = blank(n, n)
    c = (n - 1) / 2
    for y in range(n):
        for x in range(n):
            if (x - c) ** 2 + (y - c) ** 2 <= (n / 2) ** 2 - 0.5: g[y][x] = colour
    for x, y, col in spots:
        g[y][x] = col
    return g

def stars():
    rnd = random.Random(11)
    g = blank(64, 32)
    for _ in range(22):
        g[rnd.randrange(32)][rnd.randrange(64)] = rnd.choice(["#ffffff", "#ffffff", "#ffe9a8", "#bcd3ff"])
    return g

save("wall.png", wall())
save("floor.png", floor())
save("mountains.png", mountains())
save("stars.png", stars())
save("sun.png", disc(10, "#ffd75e", [(x, y, "#fff3b0") for x in range(3, 7) for y in range(3, 7)]))
save("moon.png", disc(10, "#e8eef7", [(3, 3, "#b9c6d8"), (4, 3, "#b9c6d8"), (6, 6, "#b9c6d8"), (3, 7, "#b9c6d8"), (7, 2, "#b9c6d8")]))
CLOUD = {"w": "#ffffff", "s": "#cfe0f2"}
save("cloud-a.png", chars([
    "......wwwwww............",
    "....wwwwwwwwww...www....",
    "..wwwwwwwwwwwwwwwwwwww..",
    ".wwwwwwwwwwwwwwwwwwwwww.",
    "wwwwwwwwwwwwwwwwwwwwwwww",
    "wsswwwwsssswwwwwsssswwws",
    ".ssssssssssssssssssssss.",
], CLOUD))
save("cloud-b.png", chars([
    "....wwwww.......",
    "..wwwwwwwww.ww..",
    ".wwwwwwwwwwwwww.",
    "wwwswwwwsswwwwww",
    ".ssssssssssssss.",
], CLOUD))
save("torch.png", chars([
    "..y...",
    ".yoy..",
    ".yoo..",
    "yoooy.",
    ".orro.",
    "mmmmm.",
    ".bbb..",
    ".bbb..",
    "..b...",
    "..b...",
    "..b...",
    "..b...",
], {"y": "#ffe27a", "o": "#ff9d3c", "r": "#e2552f", "m": "#4a515c", "b": "#7a5230"}))
save("banner.png", chars([
    "bbbbbbbbbb",
    ".rrrrrrrr.",
    ".rrrrrrrr.",
    ".rrrggrrr.",
    ".rrggggrr.",
    ".rggwwggr.",
    ".rrggggrr.",
    ".rrrggrrr.",
    ".rrrrrrrr.",
    ".rrrrrrrr.",
    ".RRRRRRRR.",
    ".rrr..rrr.",
    ".rr....rr.",
    ".r......r.",
], {"b": "#7a5230", "r": "#c94040", "R": "#a53030", "g": "#f2c14e", "w": "#fff3b0"}))
save("table.png", chars([
    "....................gg......",
    "..ccccc.............gg...y..",
    ".cc...cc...........pppp..o..",
    ".ccccccc...........pPPp..w..",
    "TTTTTTTTTTTTTTTTTTTTTTTTTTTT",
    "tttttttttttttttttttttttttttt",
    "dddddddddddddddddddddddddddd",
    ".dtt....................ttd.",
    ".dtt....................ttd.",
    ".dtt....................ttd.",
    ".dtt....................ttd.",
    ".dtt....................ttd.",
    ".dtt....................ttd.",
    ".ddd....................ddd.",
], {"c": "#f4ecd8", "g": "#9fd8e8", "p": "#c94040", "P": "#e86a6a", "y": "#ffe27a", "o": "#ff9d3c", "w": "#f4f7fb",
    "T": "#b98047", "t": "#9a6639", "d": "#6e4525"}))
save("barrel.png", chars([
    "..tttttttt..",
    ".tTTTTTTTTt.",
    "mmmmmmmmmmmm",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "tTtTTtTTtTTd",
    "mmmmmmmmmmmm",
    ".tTtTTtTTtd.",
    "..dddddddd..",
], {"T": "#b98047", "t": "#9a6639", "d": "#6e4525", "m": "#4a515c"}))
save("wrench.png", chars([  # double-ended: an open jaw at each end
    ".....w.w",
    ".....www",
    "....ww..",
    "...ww...",
    "..ww....",
    "www.....",
    "w.w.....",
    "........",
], {"w": "#dbe7f3"}))

# ---- Status icons, shown over an agent's head, outlined like the sprites ----
def icon(name, rows, pal):
    g = chars(rows, pal)
    h, w = len(g), len(g[0])
    big = [[None] * (w + 2) for _ in range(h + 2)]
    for y in range(h):
        for x in range(w): big[y + 1][x + 1] = g[y][x]
    o = [r[:] for r in big]
    for y in range(h + 2):
        for x in range(w + 2):
            if big[y][x] is None and any(0 <= y+j < h+2 and 0 <= x+i < w+2 and big[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1))):
                o[y][x] = OUTLINE
    save(name, o)

SWORD = {"A": "#dfe6ee", "a": "#9aa7b8", "g": "#f2c14e", "d": "#7a5230"}
BLADE = [
    "......A",
    ".....Aa",
    "....Aa.",
    ".g.Aa..",
    "..ga...",
    ".d.g...",
    "d......",
]
icon("sword-l.png", BLADE, SWORD)                       # working: two of these clash
icon("sword-r.png", [r[::-1] for r in BLADE], SWORD)
save("spark.png", chars(["..y..", ".yWy.", "yWWWy", ".yWy.", "..y.."], {"y": "#ffe27a", "W": "#ffffff"}))
Z = {"z": "#e6f0fa"}
icon("z-1.png", ["zzz", ".z.", "zzz"], Z)                # idle: three of these rise
icon("z-2.png", ["zzzz", "..z.", ".z..", "zzzz"], Z)
icon("z-3.png", ["zzzzz", "...z.", "..z..", ".z...", "zzzzz"], Z)
icon("alert.png", [                                     # blocked: it needs you
    ".rrrrr.",
    "rrrwrrr",
    "rrrwrrr",
    "rrrwrrr",
    "rrrrrrr",
    "rrrwrrr",
    ".rrrrr.",
    "..rr...",
], {"r": "#e2483f", "w": "#ffffff"})
icon("done.png", [                                      # done: finished while you were away
    ".ggggg.",
    "ggggggg",
    "gggggwg",
    "ggggwgg",
    "gwgwggg",
    "ggwgggg",
    ".ggggg.",
    "..gg...",
], {"g": "#3fbf6f", "w": "#ffffff"})

# ---- Monsters (battle mode): drawn from shapes, outlined like the sprites ----
class Pix:
    def __init__(self, w, h):
        self.w, self.h = w + 2, h + 2                 # 1px margin for the outline
        self.g = [[None] * self.w for _ in range(self.h)]
    def px(self, x, y, c):
        if 0 <= x < self.w - 2 and 0 <= y < self.h - 2: self.g[y + 1][x + 1] = c
    def rect(self, x, y, w, h, c):
        for j in range(h):
            for i in range(w): self.px(x + i, y + j, c)
    def ell(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1.0: self.px(x, y, c)
    def poly(self, pts, c):
        ys = [p[1] for p in pts]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
                if y1 == y2: continue
                if min(y1, y2) <= y + 0.5 < max(y1, y2): xs.append(x1 + (y + 0.5 - y1) * (x2 - x1) / (y2 - y1))
            xs.sort()
            for a, b in zip(xs[::2], xs[1::2]):
                for x in range(int(round(a)), int(round(b)) + 1): self.px(x, y, c)
    # `keep(x, y)` saves only part of the picture (art coordinates): the part
    # that rises and falls when the monster breathes.
    def save(self, name, outline=True, keep=None):
        g, o = self.g, [r[:] for r in self.g]
        for y in range(self.h if outline else 0):
            for x in range(self.w):
                if g[y][x] is None and any(0 <= y+j < self.h and 0 <= x+i < self.w and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1))):
                    o[y][x] = OUTLINE
        if keep:
            o = [[c if keep(x - 1, y - 1) else None for x, c in enumerate(row)] for y, row in enumerate(o)]
        save(name, o)

K, WHITE, BONE = "#1b2233", "#ffffff", "#f4ecd8"

def slime(name, squash=False, lids=False):                # 32x24; squash is the low half of its wobble
    p = Pix(32, 24)
    B, Bd, Bl = "#4fb3e0", "#3586b8", "#9bdcf5"
    if lids:
        p.rect(9, 12, 3, 4, B); p.rect(19, 12, 3, 4, B)
        return p.save(name, outline=False)
    d = 3 if squash else 0
    p.ell(16, 13 + d, 14 + d / 3, 10 - d, Bd); p.rect(2 - (1 if d else 0), 13 + d, 29 + (2 if d else 0), 10 - d, Bd)
    p.ell(15.5, 12 + d, 13 + d / 3, 9 - d, B); p.rect(3 - (1 if d else 0), 12 + d, 26 + (2 if d else 0), 9 - d, B)
    p.rect(2 - (1 if d else 0), 21, 29 + (2 if d else 0), 2, Bd)
    p.ell(9, 7 + d, 3, 2, Bl); p.px(13, 5 + d, Bl)
    p.rect(9, 12, 3, 5, K); p.rect(19, 12, 3, 5, K); p.px(9, 12, WHITE); p.px(19, 12, WHITE)
    p.rect(13, 18, 5, 1, K)
    p.save(name)

def ogre(name, roar=False, lids=False, keep=None):        # 48x48
    p = Pix(48, 48)
    G, Gd, Gl = "#6f9e3f", "#4f7a2c", "#93bf5a"
    Wd, Wl, Br = "#7a5230", "#9a6639", "#5a3d22"
    if lids:
        p.rect(16, 11, 4, 2, G); p.rect(27, 11, 4, 2, G); p.rect(16, 13, 4, 1, Gd); p.rect(27, 13, 4, 1, Gd)
        return p.save(name, outline=False)
    p.poly([(38, 24), (43, 24), (47, 5), (39, 2)], Wd)    # club, raised
    p.poly([(40, 22), (42, 22), (45, 6), (41, 4)], Wl)
    for x, y in ((39, 8), (46, 12), (40, 14), (45, 4)): p.rect(x, y, 2, 2, BONE)
    p.rect(14, 38, 8, 8, Gd); p.rect(26, 38, 8, 8, Gd)    # legs
    p.rect(12, 44, 11, 3, Br); p.rect(25, 44, 11, 3, Br)
    p.ell(24, 30, 15, 12, Gd); p.ell(23, 29, 14, 11, G); p.ell(24, 32, 9, 7, Gl)
    p.poly([(11, 36), (37, 36), (34, 43), (24, 40), (14, 43)], Wl); p.rect(10, 35, 28, 2, Br); p.rect(22, 34, 4, 4, "#f2c14e")
    p.ell(7, 29, 5, 8, Gd); p.ell(7, 28, 4, 7, G); p.ell(7, 38, 4, 4, G)          # left arm, fist
    p.ell(41, 29, 5, 7, Gd); p.ell(40, 28, 4, 6, G); p.ell(41, 23, 4, 4, G)       # right arm, fist on the club
    p.poly([(10, 8), (14, 12), (13, 18)], Gd); p.poly([(38, 8), (34, 12), (35, 18)], Gd)  # ears
    p.ell(24, 14, 11, 10, Gd); p.ell(23, 13, 10, 9, G)
    p.rect(15, 9, 17, 2, Gd)                              # brow
    p.rect(16, 11, 4, 3, "#ffe27a"); p.rect(27, 11, 4, 3, "#ffe27a"); p.px(18, 12, K); p.px(28, 12, K)
    p.rect(22, 13, 4, 4, Gd); p.px(22, 16, K); p.px(25, 16, K)
    if roar:                                              # jaw dropped wide
        p.rect(15, 10, 17, 1, Gd)
        p.rect(15, 18, 17, 8, "#3a1f1f"); p.rect(18, 23, 11, 3, "#c94040")
        p.rect(16, 18, 2, 4, BONE); p.rect(29, 18, 2, 4, BONE); p.rect(20, 18, 2, 2, BONE); p.rect(25, 18, 2, 2, BONE)
        p.rect(17, 24, 2, 2, BONE); p.rect(28, 24, 2, 2, BONE)
    else:
        p.rect(16, 19, 15, 3, "#3a1f1f"); p.rect(17, 17, 2, 4, BONE); p.rect(28, 17, 2, 4, BONE)
    p.save(name, keep=keep)

def dragon(name, sway=False, lids=False, keep=None):                 # 80x64, facing left; sway is the tail swung a little lower
    p = Pix(80, 64)
    R, Rd, Rl = "#c23b3b", "#8f2626", "#e06a5a"
    Wg, Wm, Cr = "#7a1f2b", "#b5483f", "#f2c98a"
    if lids:
        p.rect(17, 12, 4, 3, R); p.rect(17, 15, 4, 1, Rd)
        return p.save(name, outline=False)
    t = 4 if sway else 0
    p.poly([(54, 46), (72, 36 + t // 2), (79, 22 + t), (80, 26 + t), (76, 40 + t // 2), (60, 56)], Rd)  # tail
    p.poly([(77, 22 + t), (80, 14 + t), (80, 24 + t)], BONE)
    p.poly([(44, 34), (52, 6), (62, 14), (70, 4), (76, 26), (62, 38)], Wg)          # far wing
    p.ell(44, 45, 20, 13, Rd); p.ell(43, 44, 19, 12, R); p.ell(40, 51, 14, 5, Cr)   # body, belly
    p.rect(30, 52, 8, 9, Rd); p.rect(50, 52, 8, 9, Rd)                              # legs
    p.rect(27, 60, 12, 3, Rd); p.rect(47, 60, 12, 3, Rd)
    for x in (27, 31, 35, 47, 51, 55): p.px(x, 62, BONE)
    p.poly([(22, 20), (34, 18), (42, 38), (28, 44)], R)                             # neck
    p.poly([(22, 22), (26, 21), (32, 42), (28, 44)], Cr)
    for i in range(5): p.rect(22 + i, 24 + i * 4, 4, 1, "#d9a868")
    for x, y in ((34, 14), (38, 22), (42, 28), (48, 28), (54, 30), (60, 34)):       # back spikes
        p.poly([(x, y + 5), (x + 2, y), (x + 5, y + 5)], BONE)
    p.poly([(40, 36), (46, 8), (58, 16), (66, 2), (72, 22), (58, 36)], Wm)          # near wing
    p.poly([(46, 8), (48, 10), (44, 34), (40, 36)], Rd); p.poly([(66, 2), (68, 4), (60, 34), (58, 36)], Rd)
    p.ell(19, 17, 11, 7, Rd); p.ell(18, 16, 10, 6, R)                               # head
    p.rect(3, 14, 14, 8, R); p.rect(3, 14, 14, 1, Rl); p.rect(2, 16, 2, 5, R)       # snout
    p.rect(5, 22, 16, 3, Rd)                                                        # jaw
    for x in (6, 9, 12, 15): p.px(x, 22, WHITE)
    p.px(4, 16, K); p.rect(17, 12, 4, 4, "#ffe27a"); p.rect(18, 12, 1, 4, K)
    p.poly([(23, 12), (31, 3), (27, 14)], BONE); p.poly([(19, 10), (24, 2), (22, 11)], BONE)  # horns
    p.save(name, keep=keep)

# Each monster: its picture, a second frame it eases to and from (the slime's
# wobble, the dragon's tail, the ogre's roar), and eyelids to lay on top.
slime("monster-slime.png"); slime("monster-slime-2.png", squash=True); slime("monster-slime-blink.png", lids=True)
ogre("monster-ogre.png"); ogre("monster-ogre-2.png", roar=True); ogre("monster-ogre-blink.png", lids=True)
dragon("monster-dragon.png"); dragon("monster-dragon-2.png", sway=True); dragon("monster-dragon-blink.png", lids=True)
# Breathing: the head, shoulders and arms (the ogre) or the head, neck and wings
# (the dragon) as their own picture, which rises a little over the still body.
ogre("monster-ogre-top.png", keep=lambda x, y: y < 31)
dragon("monster-dragon-top.png", keep=lambda x, y: y < 38 and not (x >= 74 or (x >= 70 and y >= 28)))


# ---- Attacks (battle mode). "-r" flies or faces right, "-l" is its mirror. ----
def both(name, rows, pal):
    icon(f"{name}-r.png", rows, pal)
    icon(f"{name}-l.png", [r[::-1] for r in rows], pal)

both("arrow", [
    "f......A.",
    "fddddddAA",
    "f......A.",
], {"f": "#f4ecd8", "d": "#7a5230", "A": "#dfe6ee"})
both("fireball", [
    "...ooo..",
    ".yooyyo.",
    "royyWWyo",
    "royyWWyo",
    ".yooyyo.",
    "...ooo..",
], {"r": "#e2552f", "o": "#ff9d3c", "y": "#ffe27a", "W": "#ffffff"})
both("slash", [
    ".WW...",
    "...WW.",
    "....WW",
    "....WW",
    ".....W",
    "....WW",
    "....WW",
    "...WW.",
    ".WW...",
], {"W": "#ffffff"})
icon("burst.png", [
    "....y....",
    ".y.yoy.y.",
    "..yoWoy..",
    ".yoWWWoy.",
    "yoWWWWWoy",
    ".yoWWWoy.",
    "..yoWoy..",
    ".y.yoy.y.",
    "....y....",
], {"o": "#ff9d3c", "y": "#ffe27a", "W": "#ffffff"})
icon("potion.png", [
    ".bbb.",
    "..w..",
    ".www.",
    "wgggw",
    "wgGgw",
    "wgggw",
    ".www.",
], {"b": "#7a5230", "w": "#dff3ee", "g": "#3fbf8f", "G": "#9af0cf"})
icon("splash.png", [
    "g.........g",
    "..g..g..g..",
    ".g.ggGgg.g.",
    "..gGGGGGg..",
    ".ggGGGGGgg.",
    "..ggggggg..",
], {"g": "#3fbf8f", "G": "#9af0cf"})

# ---- Fighting poses (battle mode), on a 22x16 grid so a weapon can reach out.
# Drawn attacking to the right: "f" is the stance, "a1" the wind-up, "a2" the
# strike. "-l" is the mirror image, for attacking to the left.
def pose(cls, tag, rows):
    pal = {**COMMON, **SPR[cls][0], "#": OUTLINE}
    rows = [r.ljust(22, ".") for r in rows]
    assert len(rows) == 16 and all(len(r) == 22 for r in rows), (cls, tag, [len(r) for r in rows])
    icon(f"{cls}-{tag}-r.png", rows, pal)
    icon(f"{cls}-{tag}-l.png", [r[::-1] for r in rows], pal)

def swap(rows, changes):
    rows = list(rows)
    for y, text in changes.items(): rows[y] = text
    return rows

def dots(rows, pixels):
    g = [list(r.ljust(22, ".")) for r in rows]
    for x, y, ch in pixels: g[y][x] = ch
    return ["".join(r) for r in g]

W = SPR["warrior"][1]
pose("warrior", "f", W)
pose("warrior", "a1", swap(W, {            # sword held high
    0: ".............A..", 1: ".......pp....A..", 2: "......ppp....A..", 3: ".....aaaaaa..A..",
    4: "....aaAAAAaa.A..", 5: "....aaaaaaaa.A..", 6: "....askaaksaggg.", 7: "....assssssa.s..",
    8: ".....ssssss.a...", 9: "....AaaaaaaAa...", 10: ".uuuuaaaaaap....", 11: ".ugguaaaaaap....",
    12: ".ugguddgdddp....",
}))
pose("warrior", "a2", swap(W, {            # swung level, at full reach
    2: "......ppp.......", 3: ".....aaaaaa.....", 4: "....aaAAAAaa....", 5: "....aaaaaaaa....",
    6: "....askaaksa....", 7: "....assssssa....", 8: ".....ssssss.....", 9: "....AaaaaaaA..g.",
    10: ".uuuuaaaaaapasgAAAAAAA", 11: ".ugguaaaaaap..g.", 12: ".ugguddgdddp....",
}))

A = SPR["archer"][1]
SPR["archer"][0]["A"] = "#dfe6ee"  # arrowhead
pose("archer", "f", A)
pose("archer", "a1", swap(A, {             # bow drawn, arrow nocked
    5: "....ddssssdd..d.", 6: "....dskssksd..cd", 7: "....dssssssd..cd", 8: ".....ssssss..c..d",
    9: ".cc..nnnnnn..c..d", 10: ".qq.nndnnnnnsddddA", 11: ".qqsnnndnnnn.c..d", 12: ".qq.ddddgddd.c.d",
    13: "....NNNNNNNN..cd", 14: ".....dd..dd...d.",
}))
pose("archer", "a2", swap(A, {             # loosed
    5: "....ddssssdd..d.", 6: "....dskssksd..cd", 7: "....dssssssd..cd", 8: ".....ssssss...c.d",
    9: ".cc..nnnnnn...c.d", 10: ".qq.nndnnnnns.c.d", 11: ".qqsnnndnnnn..c.d", 12: ".qq.ddddgddd..cd",
    13: "....NNNNNNNN..cd", 14: ".....dd..dd...d.",
}))

Z = SPR["wizard"][1]
pose("wizard", "f", Z)
pose("wizard", "a1", swap(Z, {             # staff raised
    0: ".............c..", 1: ".......hh...cCc.", 2: "......hhhh...c..", 3: "......hyhh...w..",
    4: ".....gggggg..w..", 5: "....hhhhhhhh.w..", 6: ".....ssssss..w..", 7: ".....skssks..w..",
    8: ".....bssssb..w..", 9: ".....bbbbbb.sw..", 10: "....rrbbbbrrrw..", 11: "...srrrbbrrr....",
    12: "....rrrRRrrr....", 13: "....gggggggg....", 14: ".....dd..dd.....",
}))
pose("wizard", "a2", swap(Z, {             # staff thrust out
    2: "......hhhh......", 3: "......hyhh......", 4: ".....gggggg.....", 5: "....hhhhhhhh....",
    6: ".....ssssss.....", 7: ".....skssks.....", 8: ".....bssssb........c..", 9: ".....bbbbbb.swwwwwcCc.",
    10: "....rrbbbbrrr......c..", 11: "...srrrbbrrr....", 12: "....rrrRRrrr....",
    13: "....gggggggg....", 14: ".....dd..dd.....",
}))

# The healer throws with the free hand, so its stance is the mirror of the
# everyday sprite: staff on the far side, free hand toward the monster.
H = [r[::-1] for r in SPR["healer"][1]]
SPR["healer"][0]["P"] = "#3fbf8f"
pose("healer", "f", H)
pose("healer", "a1", dots(H, [(12, 10, "."), (12, 9, "r"), (13, 8, "s"), (13, 5, "h"), (13, 6, "P"), (14, 6, "P"), (13, 7, "P"), (14, 7, "P")]))  # potion held up
pose("healer", "a2", dots(H, [(13, 10, "r"), (14, 10, "s")]))                                                                         # arm flung out
