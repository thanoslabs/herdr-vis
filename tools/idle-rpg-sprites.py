#!/usr/bin/env python3
# Draws Idle RPG's pixel art as PNGs (no dependencies): the class sprites
# (stubby 16x16 adventurers with a one-pixel dark outline, in every colourway
# the shop sells) and the castle scenery (wall, floor, mountains, clouds, sun,
# moon, stars, props).
#
#   python3 tools/idle-rpg-sprites.py idle-rpg/mods/idle-rpg/art
#
# Edit the grids below (one character per pixel, "." is empty) and re-run.
# Everything is drawn at 8 image pixels per art pixel and shown at 4.
import math, os, struct, sys, zlib
if len(sys.argv) != 2:
    sys.exit("usage: idle-rpg-sprites.py <output folder>")
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

# Colourways sold in the shop: each class's default (the palette above, drawn
# as <class>*.png) and three more, drawn as <class>-<id>*.png by swapping
# palette entries over the default's (clothing, armour, hair, trim; never skin,
# eyes or the outline). The ids, in this order, must match COLOUR_NAMES in
# mods/idle-rpg/rules.js, which names them (and COLOUR_PRICES prices them).
LOOKS = {
"wizard": {   # hat, robe and boots; the beard, staff and gold trim stay
    "crimson": {"h":"#a8323a","r":"#cf4747","R":"#a8323a","d":"#64202a","c":"#ffcf7a"},
    "moss":    {"h":"#2f7a46","r":"#45a05f","R":"#2f7a46","d":"#1f4d33","y":"#dfe6ee","g":"#dfe6ee","c":"#c4ff8f"},
    "frost":   {"h":"#4f86c6","r":"#9fd0f5","R":"#6fa8dc","d":"#35608f","y":"#ffffff","g":"#ffffff","c":"#ffffff","C":"#8fe3ff"},
},
"healer": {   # the cross, hood and trim; the robe stays pale so the cross shows
    "rose":  {"t":"#d4457c","h":"#a8552e","m":"#ffa8c8","r":"#fbf0f2","d":"#7a3b4f"},
    "sky":   {"t":"#3b78d0","h":"#3b2b22","m":"#a8d8ff","r":"#eef4fb","d":"#3a4e6e"},
    "plum":  {"t":"#8048bf","h":"#f4f0e6","m":"#d8b4ff","r":"#f6f0fb","d":"#4a3366"},
},
"warrior": {  # armour (and the blade, which shares its light tone), plume and shield
    "cobalt": {"a":"#4f74b8","A":"#b4cdf0","p":"#f4ecd8","u":"#c94040","b":"#34466e"},
    "jade":   {"a":"#5c9c84","A":"#c4ecdc","p":"#f2c14e","u":"#7a3fa8","b":"#3d5f55"},
    "ruby":   {"a":"#b04a4a","A":"#f4d2cc","p":"#f4ecd8","u":"#2f7a7a","b":"#5b3b3b"},
},
"archer": {   # tunic, hat, feather and quiver; the hair, bow and string stay
    "scarlet": {"n":"#c43a3a","N":"#8a2226","p":"#f2c14e","q":"#5b3b22"},
    "azure":   {"n":"#3f7fcc","N":"#285a96","p":"#f4ecd8"},
    "dusk":    {"n":"#8a56c2","N":"#5e3890","p":"#6fdc9a","q":"#c08a4a"},
},
}
# a look's id follows the class in every file name, so it must not read as a frame
# an id is one lower-case word, and not one a picture's name already uses, so no two files can share a name
assert all(i.isalpha() and i.islower() and i not in {"walk", "rag", "f", "a", "l", "r", "c", "default"} for c in LOOKS for i in LOOKS[c])

def looks(cls):
    # (file name prefix, palette entries to swap): the default first, unchanged
    return [(cls, {})] + [(f"{cls}-{look}", swaps) for look, swaps in LOOKS[cls].items()]

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
    rgba = lambda ch: (bytes.fromhex(pal.get(ch, ch)[1:]) + b"\xff")[:4]  # "#rrggbb", or "#rrggbbaa" for see-through
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

for cls, (base, rows) in SPR.items():
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), (cls, [len(r) for r in rows])
    for name, swaps in looks(cls):                              # every colourway, the default first
        pal = {**COMMON, **base, **swaps, "#": OUTLINE}
        w = lambda n, g: open(os.path.join(out, n), "wb").write(png(outlined(g), pal))
        w(f"{name}.png", canvas(rows, 18, 1))                   # 16x16 art, 1px margin for the outline
        for tag, side in (("l", -1), ("r", 1)):                 # lean a pixel, other foot lifted
            w(f"{name}-walk-{tag}.png", canvas(lift(rows, side), 18, 1, lambda y: side if y < 14 else 0))
        w(f"{name}-rag-c.png", canvas(rows, 22, 3))             # dangling: straight, or sheared each way
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
TABLE = chars([
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
    "T": "#b98047", "t": "#9a6639", "d": "#6e4525"})
save("table.png", TABLE)
# ---- Stations, on the rampart between raids: each opens one of the panels ----
# Each also comes as "<name>-hot": the same picture inside a one-pixel white
# outline (so one art pixel bigger on every side), shown under the pointer.
def lit(g):
    h, w = len(g), len(g[0])
    big = [[None] * (w + 2) for _ in range(h + 2)]
    for y in range(h):
        for x in range(w): big[y + 1][x + 1] = g[y][x]
    o = [r[:] for r in big]
    for y in range(h + 2):
        for x in range(w + 2):
            if big[y][x] is None and any(0 <= y+j < h+2 and 0 <= x+i < w+2 and big[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1))):
                o[y][x] = "#ffffff"
    return o

def station(name, rows, pal):
    g = chars(rows, pal)
    save(name + ".png", g)
    save(name + "-hot.png", lit(g))

save("table-hot.png", lit(TABLE))                 # the codex is the whole table, and the book on it
station("book", [                                # the codex, lying on the table
    ".bbbbbb.",
    "bBBBBBBb",
    "bBBggBBb",
    "bBBggBBb",
    "bBBBBBBb",
    "wwwwwwwb",
], {"b": "#3b2a6b", "B": "#6b4fbf", "g": "#f2c14e", "w": "#f4ecd8"})
station("stall", [                               # the shop: a merchant's stall
    "..rrwwrrwwrrwwrrwwrrwwrr..",
    ".rrwwrrwwrrwwrrwwrrwwrrww.",
    "rrwwrrwwrrwwrrwwrrwwrrwwrr",
    "RRWWRRWWRRWWRRWWRRWWRRWWRR",
    "R..WW..RR..WW..RR..WW..RR.",
    ".d......................d.",
    ".d......................d.",
    ".d......................d.",
    ".d...........pp.........d.",
    ".d..gg......pppp...yy...d.",
    ".d.gGGg.....pPPp..yYYy..d.",
    "TTTTTTTTTTTTTTTTTTTTTTTTTT",
    "tttttttttttttttttttttttttt",
    "dddddddddddddddddddddddddd",
    ".dtTttTttTttTttTttTttTttd.",
    ".dtTttTttTttTttTttTttTttd.",
    ".dtTttTttTttTttTttTttTttd.",
    ".dtTttTttTttTttTttTttTttd.",
    ".dtTttTttTttTttTttTttTttd.",
    ".dtTttTttTttTttTttTttTttd.",
    ".dddddddddddddddddddddddd.",
], {"r": "#c94040", "R": "#a53030", "w": "#f4ecd8", "W": "#d8cfb8", "g": "#c8891e", "G": "#f2c14e", "p": "#3f8fd0", "P": "#9fd8e8",
    "y": "#3fbf6f", "Y": "#9be6b4", "T": "#b98047", "t": "#9a6639", "d": "#6e4525"})
station("dummy", [                               # the skills: a straw training dummy
    "....ssss....",
    "...sSSSSs...",
    "...sSSSSs...",
    "....ssss....",
    "bbbbbbbbbbbb",
    "..yyYYYYyy..",
    "..yYYrrYYy..",
    "..yYrwwrYy..",
    "..yYrwwrYy..",
    "..yYYrrYYy..",
    "..yyYYYYyy..",
    "...yyyyyy...",
    ".....bb.....",
    ".....bb.....",
    ".....bb.....",
    ".....bb.....",
    "...bbbbbb...",
    "..bbbbbbbb..",
], {"s": "#b89a62", "S": "#d9c08a", "b": "#7a5230", "y": "#c9a03c", "Y": "#e6c766", "r": "#c94040", "w": "#f4ecd8"})
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

# ---- Night: darkness laid over the wall, the floor and everyone on it, with a
# pool of light left clear around a flame. The dark deepens away from the
# flame in six even steps (rings, not a smooth blur) up to half strength, so
# the far corners are dim, not black. 74 rows: 20 above the wall, where the dark
# thins out upward to nothing (so a tall monster is not cut in two at the wall's
# top), then the wall (16) and the floor (38). `cy` counts from the wall's top.
RISE = 20
def dark(name, w, cx=0, cy=0, near=0, far=0, stretch=1.0):
    g = blank(w, RISE + 54)
    for y in range(RISE + 54):
        for x in range(w):
            step = 6
            if far:
                d = math.hypot((x + 0.5 - cx) / stretch, y + 0.5 - RISE - cy)
                t = min(1.0, max(0.0, (d - near) / (far - near)))
                step = round(t * t * (3 - 2 * t) * 6)
            step = min(step, 6 * y // RISE)
            if step: g[y][x] = "#0a1030%02x" % round(128 * step / 6)
    save(name, g)

dark("dark-torch.png", 96, 48.5, 4.5, 9, 40, 1.15)      # one torch's stretch of wall, the flame near the top
dark("dark-candle.png", 68, 28.5, 9, 3, 24)             # the left end, lit only by the candle on the table
dark("dark-fill.png", 4)                                # no flame: stretched over whatever is left

# ---- Sign icons: the counts on the sign, drawn small (shown at 2 screen px a pixel) ----
icon("i-swords.png", [                                  # working
    "A.....A",
    ".A...A.",
    "..A.A..",
    "g..A..g",
    ".gA.Ag.",
    "..g.g..",
    ".d...d.",
], SWORD)
icon("i-sleep.png", [                                   # resting
    "zzzz...",
    "..z....",
    ".z.....",
    "zzzz...",
    "....zzz",
    ".....z.",
    "....zzz",
], Z)
icon("i-skull.png", [                                   # slain
    ".wwwww.",
    "wwwwwww",
    "wkkwkkw",
    "wkkwkkw",
    "wwwkwww",
    ".wwwww.",
    ".wkwkw.",
], {"w": "#ece6d6", "k": "#2a2433"})
icon("arrow.png", ["wwwww", ".www.", "..w.."], {"w": "#ffffff"})  # bobs over the station under the pointer
icon("i-armour.png", [                                  # the shop's armours
    "aa...aa",
    "aAaaaAa",
    ".aAAAa.",
    ".aAaAa.",
    ".aAAAa.",
    ".aaAaa.",
    "..aaa..",
], SWORD)
icon("i-hat.png", [                                     # the shop's hats
    "...b...",
    "..bb...",
    "..bBb..",
    ".bbBb..",
    ".ggggg.",
    "bbbbbbb",
], {"b": "#4a6fd0", "B": "#7fa0ee", "g": "#f2c14e"})
icon("i-coin.png", [                                    # gold
    "..ggg..",
    ".gyyyg.",
    "gyyhyyg",
    "gyhyyyg",
    "gyyyyyg",
    ".gyyyg.",
    "..ggg..",
], {"g": "#c8891e", "y": "#f2c14e", "h": "#fff0b0"})
icon("i-star.png", [                                    # skill points to spend
    "...y...",
    "..yhy..",
    "yyyhyyy",
    ".yhhhy.",
    "..yyy..",
    ".yy.yy.",
    ".y...y.",
], {"y": "#ffd166", "h": "#fff6cf"})

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

def slime(name, lids=False, keep=None):                   # 32x24
    p = Pix(32, 24)
    B, Bd, Bl = "#4fb3e0", "#3586b8", "#9bdcf5"
    if lids:
        p.rect(9, 12, 3, 4, B); p.rect(19, 12, 3, 4, B)
        return p.save(name, outline=False)
    p.ell(16, 13, 14, 10, Bd); p.rect(2, 13, 29, 10, Bd)
    p.ell(15.5, 12, 13, 9, B); p.rect(3, 12, 26, 9, B)
    p.rect(2, 21, 29, 2, Bd)
    p.ell(9, 7, 3, 2, Bl); p.px(13, 5, Bl)
    p.rect(9, 12, 3, 5, K); p.rect(19, 12, 3, 5, K); p.px(9, 12, WHITE); p.px(19, 12, WHITE)
    p.rect(13, 18, 5, 1, K)
    p.save(name, keep=keep)

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

def dragon(name, part=None, lids=False, keep=None, pose=None):  # 80x64, facing left; part: "tail" or "body" alone
    p = Pix(80, 64)
    R, Rd, Rl = "#c23b3b", "#8f2626", "#e06a5a"
    Wg, Wm, Cr = "#7a1f2b", "#b5483f", "#f2c98a"
    if lids:
        p.rect(17, 12, 4, 3, R); p.rect(17, 15, 4, 1, Rd)
        return p.save(name, outline=False)
    if part != "body":
        p.poly([(54, 46), (72, 36), (79, 22), (80, 26), (76, 40), (60, 56)], Rd)   # tail
        p.poly([(77, 22), (80, 14), (80, 24)], BONE)
    if part == "tail": return p.save(name)
    # A roar (pose): "rear" draws the head back and up and lifts the wings a
    # little, "roar" thrusts the head forward with the jaw wide and the wings
    # high. Only the head, the top of the neck and the wing tips move; the
    # neck's foot and everything below the breathing cut (y 38) stay put.
    hx, hy, lift = {None: (0, 0, 0), "rear": (2, -2, 1), "roar": (-1, 1, 2)}[pose]
    h = lambda pts: [(x + hx, y + hy) for x, y in pts]
    up = lambda pts, tips: [(x, y - lift) if i in tips else (x, y) for i, (x, y) in enumerate(pts)]
    p.poly(up([(44, 34), (52, 6), (62, 14), (70, 4), (76, 26), (62, 38)], (1, 2, 3)), Wg)  # far wing
    p.ell(44, 45, 20, 13, Rd); p.ell(43, 44, 19, 12, R); p.ell(40, 51, 14, 5, Cr)   # body, belly
    p.rect(30, 52, 8, 9, Rd); p.rect(50, 52, 8, 9, Rd)                              # legs
    p.rect(27, 60, 12, 3, Rd); p.rect(47, 60, 12, 3, Rd)
    for x in (27, 31, 35, 47, 51, 55): p.px(x, 62, BONE)
    p.poly(h([(22, 20), (34, 18)]) + [(42, 38), (28, 44)], R)                       # neck
    p.poly(h([(22, 22), (26, 21)]) + [(32, 42), (28, 44)], Cr)
    for i in range(5): p.rect(22 + i + round(hx * (4 - i) / 4), 24 + i * 4 + round(hy * (4 - i) / 4), 4, 1, "#d9a868")
    for x, y in ((34 + hx, 14 + hy), (38, 22), (42, 28), (48, 28), (54, 30), (60, 34)):  # back spikes
        p.poly([(x, y + 5), (x + 2, y), (x + 5, y + 5)], BONE)
    p.poly(up([(40, 36), (46, 8), (58, 16), (66, 2), (72, 22), (58, 36)], (1, 2, 3)), Wm)  # near wing
    p.poly(up([(46, 8), (48, 10), (44, 34), (40, 36)], (0, 1)), Rd); p.poly(up([(66, 2), (68, 4), (60, 34), (58, 36)], (0, 1)), Rd)
    p.ell(19 + hx, 17 + hy, 11, 7, Rd); p.ell(18 + hx, 16 + hy, 10, 6, R)           # head
    if pose == "roar":                                                              # jaws wide
        p.poly(h([(4, 17), (21, 17), (22, 24), (5, 30)]), "#3a1f1f")                # mouth
        p.poly(h([(7, 28), (19, 22), (21, 24), (9, 29)]), "#c94040")               # tongue
        p.poly(h([(2, 30), (19, 23), (22, 23), (22, 27), (6, 33)]), Rd)             # lower jaw, dropped
        for x, y in ((5, 29), (9, 28), (13, 26), (17, 25)): p.px(x + hx, y + hy, WHITE)
        p.rect(3 + hx, 10 + hy, 14, 7, R); p.rect(3 + hx, 10 + hy, 14, 1, Rl); p.rect(2 + hx, 12 + hy, 2, 4, R)  # snout, raised
        for x in (6, 9, 12, 15): p.px(x + hx, 17 + hy, WHITE)
        p.rect(4 + hx, 17 + hy, 1, 2, WHITE); p.rect(13 + hx, 17 + hy, 1, 2, WHITE)  # fangs
        p.px(4 + hx, 12 + hy, K); p.rect(17 + hx, 13 + hy, 4, 3, "#ffe27a"); p.rect(18 + hx, 13 + hy, 1, 3, K)
        p.rect(16 + hx, 12 + hy, 6, 1, Rd)                                          # brow, lowered
    else:
        p.rect(3 + hx, 14 + hy, 14, 8, R); p.rect(3 + hx, 14 + hy, 14, 1, Rl); p.rect(2 + hx, 16 + hy, 2, 5, R)  # snout
        p.rect(5 + hx, 22 + hy, 16, 3, Rd)                                          # jaw
        for x in (6, 9, 12, 15): p.px(x + hx, 22 + hy, WHITE)
        p.px(4 + hx, 16 + hy, K); p.rect(17 + hx, 12 + hy, 4, 4, "#ffe27a"); p.rect(18 + hx, 12 + hy, 1, 4, K)
    p.poly(h([(23, 12), (31, 3), (27, 14)]), BONE); p.poly(h([(19, 10), (24, 2), (22, 11)]), BONE)  # horns
    p.save(name, keep=keep)

# Each monster's whole picture, the pieces that move on their own, and eyelids
# to lay on top. Moving a piece over a still one never shows a ghost behind it,
# which easing between two whole frames did.
slime("monster-slime.png"); slime("monster-slime-blink.png", lids=True)
slime("monster-slime-base.png", keep=lambda x, y: y >= 19)          # the foot stays put (below the mouth)
slime("monster-slime-top.png", keep=lambda x, y: y < 19)            # the dome sinks into it and rises
ogre("monster-ogre.png"); ogre("monster-ogre-2.png", roar=True); ogre("monster-ogre-blink.png", lids=True)
ogre("monster-ogre-top.png", keep=lambda x, y: y < 31)              # head, shoulders, arms: breathing
dragon("monster-dragon.png"); dragon("monster-dragon-blink.png", lids=True)
dragon("monster-dragon-tail.png", part="tail")                      # sways behind the body
dragon("monster-dragon-body.png", part="body")
dragon("monster-dragon-top.png", part="body", keep=lambda x, y: y < 38)  # head, neck, wings: breathing
dragon("monster-dragon-rear.png", part="body", pose="rear")         # a roar: the wind-up, then
dragon("monster-dragon-roar.png", part="body", pose="roar")         # the roar itself,
dragon("monster-dragon-roar-top.png", part="body", pose="roar", keep=lambda x, y: y < 38)  # its upper body shaking
icon("roar-wave.png", [                                 # rings out of the roaring dragon's mouth, to the left
    "...ww",
    "..w..",
    ".w...",
    ".w...",
    "w....",
    "w....",
    "w....",
    "w....",
    ".w...",
    ".w...",
    "..w..",
    "...ww",
], {"w": "#f2c98a"})

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
# strike. "-l" is the mirror image, for attacking to the left. Each pose is
# drawn in every colourway, with the same swaps as the everyday sprite.
def pose(cls, tag, rows):
    rows = [r.ljust(22, ".") for r in rows]
    assert len(rows) == 16 and all(len(r) == 22 for r in rows), (cls, tag, [len(r) for r in rows])
    for name, swaps in looks(cls):
        pal = {**COMMON, **SPR[cls][0], **swaps, "#": OUTLINE}
        icon(f"{name}-{tag}-r.png", rows, pal)
        icon(f"{name}-{tag}-l.png", [r[::-1] for r in rows], pal)

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
