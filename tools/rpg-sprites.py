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
