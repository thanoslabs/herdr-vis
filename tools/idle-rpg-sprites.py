#!/usr/bin/env python3
# Draws Idle RPG's pixel art as PNGs (no dependencies): the class sprites
# (stubby 16x16 adventurers with a one-pixel dark outline, in every colourway
# the shop sells, and every weapon and hat it sells drawn to lay over them),
# each weapon's attack, the castle
# scenery (wall, floor, mountains, clouds, sun, moon, stars, props), the icons,
# and a small pixel font for numbers.
#
#   python3 tools/idle-rpg-sprites.py mods/idle-rpg/art
#
# Edit the grids below (one character per pixel, "." is empty) and re-run.
# Everything is drawn at 8 image pixels per art pixel and shown at 4.
#
# The pictures go in folders by what they show, then by what it is doing, with
# short names inside (the paths in mods/idle-rpg/rules.js and main.js follow it):
#   scene/      the backdrop and props: wall, floor, mountains, stars, sun, moon,
#               cloud-a, cloud-b, banner, torch, barrel
#   classes/    <class>/<look>/stand, walk/{l,r}, rag/{c,l,r}, and the fighting
#               poses stance/, windup/, strike/ {l,r}; <look> is "default" or a
#               colourway's id; drawn without the weapon
#   weapons/    <class>/<weapon>/ the same pictures as a class (the healer's: only
#               windup/), to lay over them; <weapon> is "default" or the weapon's id
#   hats/       <hat>/<class>/ the same pictures as a class, to lay over them
#   attacks/    by what flies or lands, then the weapon's variant of it:
#               slash/<variant>/, arrow/<variant>/, spell/<element>/ {l,r};
#               burst/<element>, potion/<potion>, splash/<potion>, spark/<element>
#   monsters/   <kind>/ idle (the whole picture), blink, the pieces that move
#               (top, base, body, tail), and roar/ for the ogre and dragon
#   stations/   <station>/{idle,hot}, and the arrow over the one under the pointer
#   campfire/   base, flame-1 to flame-3
#   light/      the night's darkness: candle, torch, fill, fire-0 to fire-23
#   status/     over an agent's head: alert, done, z-1 to z-3, sword-l, sword-r, spark
#   icons/      the sign's, the shop's and the settings': swords, sleep, skull,
#               coin, star, armour, hat, gear, and the card's wrench
#   font/       <colour>/<character>, the pixel font
import math, os, struct, sys, zlib
if len(sys.argv) != 2 or sys.argv[1].startswith("-"):  # no options: "--help" is not a folder to fill
    sys.exit("usage: idle-rpg-sprites.py <output folder>")
out = sys.argv[1]
os.makedirs(out, exist_ok=True)

def write(name, data):
    # `name` is a path under the output folder ("scene/wall.png"); its folders are made as needed
    path = os.path.join(out, *name.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
OUTLINE = "#141a26"
COMMON = {"s": "#f2c9a0", "k": "#1b2233"}
# Each class without its weapon (a layer of its own: see Weapons, below), hands
# and all. The healer's staff stays here: the healer's "weapon" is the potion it
# throws.
SPR = {
"wizard": ({"h":"#5a3dab","y":"#f2c14e","g":"#f2c14e","b":"#f4f7fb","r":"#6b4bc4","R":"#5a3dab","d":"#3d2a80"}, [
"................",
".......hh.......",
"......hhhh......",
"......hyhh......",
".....gggggg.....",
"....hhhhhhhh....",
".....ssssss.....",
".....skssks.....",
".....bssssb.....",
".....bbbbbb.....",
"....rrbbbbrr....",
"...srrrbbrrrs...",
"....rrrRRrrr....",
"....gggggggg....",
".....dd..dd.....",
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
"......ppp.......",
".....aaaaaa.....",
"....aaAAAAaa....",
"....aaaaaaaa....",
"....askaaksa....",
"....assssssa....",
".....ssssss.....",
"....AaaaaaaA....",
".uuuuaaaaaap....",
".ugguaaaaaap....",
".ugguddgdddps...",
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
"....ddssssdd....",
"....dskssksd....",
"....dssssssd....",
".....ssssss.....",
".cc..nnnnnn.....",
".qq.nndnnnnns...",
".qqsnnndnnnn....",
".qq.ddddgddd....",
"....NNNNNNNN....",
".....dd..dd.....",
"................",
]),
}

# Colourways sold in the shop: each class's default (the palette above, drawn
# into classes/<class>/default/) and three more, drawn into classes/<class>/<id>/ by swapping
# palette entries over the default's (clothing, armour, hair, trim; never skin,
# eyes or the outline). A weapon keeps its own colours whatever the armour. The ids, in this order, must match COLOUR_NAMES in
# mods/idle-rpg/rules.js, which names them (and COLOUR_PRICES prices them).
LOOKS = {
"wizard": {   # hat, robe and boots; the beard and gold trim stay
    "crimson": {"h":"#a8323a","r":"#cf4747","R":"#a8323a","d":"#64202a"},
    "moss":    {"h":"#2f7a46","r":"#45a05f","R":"#2f7a46","d":"#1f4d33","y":"#dfe6ee","g":"#dfe6ee"},
    "frost":   {"h":"#4f86c6","r":"#9fd0f5","R":"#6fa8dc","d":"#35608f","y":"#ffffff","g":"#ffffff"},
},
"healer": {   # the cross, hood, hair and trim; the robe stays pale so the cross shows
    "rose":  {"t":"#d4457c","h":"#a8552e","m":"#ffa8c8","r":"#fbf0f2","d":"#7a3b4f"},
    "sky":   {"t":"#3b78d0","h":"#3b2b22","m":"#a8d8ff","r":"#eef4fb","d":"#3a4e6e"},
    "plum":  {"t":"#8048bf","h":"#f4f0e6","m":"#d8b4ff","r":"#f6f0fb","d":"#4a3366"},
},
"warrior": {  # armour, plume and shield
    "cobalt": {"a":"#4f74b8","A":"#b4cdf0","p":"#f4ecd8","u":"#c94040","b":"#34466e"},
    "jade":   {"a":"#5c9c84","A":"#c4ecdc","p":"#f2c14e","u":"#7a3fa8","b":"#3d5f55"},
    "ruby":   {"a":"#b04a4a","A":"#f4d2cc","p":"#f4ecd8","u":"#2f7a7a","b":"#5b3b3b"},
},
"archer": {   # tunic, hat, feather and quiver; the hair stays
    "scarlet": {"n":"#c43a3a","N":"#8a2226","p":"#f2c14e","q":"#5b3b22"},
    "azure":   {"n":"#3f7fcc","N":"#285a96","p":"#f4ecd8"},
    "dusk":    {"n":"#8a56c2","N":"#5e3890","p":"#6fdc9a","q":"#c08a4a"},
},
}
# a look's id names its folder, so it is one lower-case word, and not "default",
# which is the default's folder, so no two looks can share one
assert all(i.isalpha() and i.islower() and i != "default" for c in LOOKS for i in LOOKS[c])

def looks(cls):
    # (the look's folder, palette entries to swap): the default first, unchanged
    return [(f"classes/{cls}/default", {})] + [(f"classes/{cls}/{look}", swaps) for look, swaps in LOOKS[cls].items()]

def canvas(rows, size, pad, dx=lambda y: 0):
    g = [[None] * size for _ in range(size)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".": g[y + pad][x + pad + dx(y)] = ch
    return g

def outlined(g):
    h, w = len(g), len(g[0])
    o = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] is None and any(0 <= y+j < h and 0 <= x+i < w and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1))):
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

def box(rows):
    # a fighting pose's 22x16 rows on its 24x18 picture, as icon() lays them out
    g = [[None] * 24 for _ in range(18)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".": g[y + 1][x + 1] = ch
    return g

POSES = ("stance", "windup", "strike")

def pictures(rows, posed, tags=POSES):
    # every picture of a class as (frame, grid): `rows` in the everyday 16x16
    # grid (None for none of the everyday pictures), `posed(tag)` a pose's
    # 22-wide rows for each of `tags`. 16x16 art with a 1px margin for the
    # outline standing; leaning a pixel, the other foot lifted, walking;
    # straight, or sheared each way, dangling; and each fighting pose drawn
    # attacking to the right ("r") and its mirror image ("l"). The frames are
    # FRAMES in mods/idle-rpg/rules.js.
    out = []
    if rows is not None:
        out.append(("stand", canvas(rows, 18, 1)))
        for tag, side in (("l", -1), ("r", 1)):
            out.append((f"walk/{tag}", canvas(lift(rows, side), 18, 1, lambda y: side if y < 14 else 0)))
        out.append(("rag/c", canvas(rows, 22, 3)))
        for tag, side in (("l", -1), ("r", 1)):
            out.append((f"rag/{tag}", canvas(rows, 22, 3, lambda y: side * round(y * 0.2))))
    for tag in tags:
        out.append((f"{tag}/r", box(posed(tag))))
        out.append((f"{tag}/l", box([r[::-1] for r in posed(tag)])))
    return out


# ---- Scenery ---------------------------------------------------------------
import random

def save(name, g, pal={}):
    write(name, png(g, pal))

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

save("scene/wall.png", wall())
save("scene/floor.png", floor())
save("scene/mountains.png", mountains())
save("scene/stars.png", stars())
save("scene/sun.png", disc(10, "#ffd75e", [(x, y, "#fff3b0") for x in range(3, 7) for y in range(3, 7)]))
save("scene/moon.png", disc(10, "#e8eef7", [(3, 3, "#b9c6d8"), (4, 3, "#b9c6d8"), (6, 6, "#b9c6d8"), (3, 7, "#b9c6d8"), (7, 2, "#b9c6d8")]))
CLOUD = {"w": "#ffffff", "s": "#cfe0f2"}
save("scene/cloud-a.png", chars([
    "......wwwwww............",
    "....wwwwwwwwww...www....",
    "..wwwwwwwwwwwwwwwwwwww..",
    ".wwwwwwwwwwwwwwwwwwwwww.",
    "wwwwwwwwwwwwwwwwwwwwwwww",
    "wsswwwwsssswwwwwsssswwws",
    ".ssssssssssssssssssssss.",
], CLOUD))
save("scene/cloud-b.png", chars([
    "....wwwww.......",
    "..wwwwwwwww.ww..",
    ".wwwwwwwwwwwwww.",
    "wwwswwwwsswwwwww",
    ".ssssssssssssss.",
], CLOUD))
save("scene/torch.png", chars([
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
save("scene/banner.png", chars([
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
save("stations/table/idle.png", TABLE)
# ---- Stations, on the rampart between raids: each opens one of the panels ----
# Each has a folder, stations/<name>/: "idle", the picture, and "hot", the same
# picture inside a one-pixel white outline (so one art pixel bigger on every
# side), shown under the pointer.
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
    save(f"stations/{name}/idle.png", g)
    save(f"stations/{name}/hot.png", lit(g))

save("stations/table/hot.png", lit(TABLE))                 # the codex is the whole table, and the book on it
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
save("scene/barrel.png", chars([
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

# ---- The campfire, in the middle of the floor between raids (scenery, not a
# station), in campfire/. "base" is the ring of stones, the logs leaning together and the
# low heart of the flames, outlined like the sprites except the flames; it never
# changes. "flame-1" to "-3" are taller flames laid over it, each fading in
# and out on its own rhythm so the fire flickers. Their lower rows match the
# heart's colours, so only the tongues change as they fade. The flames are the
# torch's colours and, like the torch's, have no outline. 16x13, plus a pixel
# of margin all round for the outline.
FIRE = {"W": "#fff3b0", "y": "#ffe27a", "o": "#ff9d3c", "r": "#e2552f",
        "g": "#9aa3ad", "G": "#7d8590", "S": "#646c78", "m": "#4a515c",   # the wall's stone
        "b": "#7a5230", "B": "#9a6639", "d": "#5a3d22", "c": "#d9b27a"}   # wood, and its cut ends
# `heart`, for the stones and logs: outline them, then lay the flames' heart over that
def campfire(name, rows, heart=None):
    g = [[None] * 18 for _ in range(15)]
    for y, row in enumerate(chars(rows, FIRE)):
        for x, c in enumerate(row): g[y + 1][x + 1] = c
    if heart:
        g = [[OUTLINE if g[y][x] is None and any(0 <= y+j < 15 and 0 <= x+i < 18 and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1)))
              else g[y][x] for x in range(18)] for y in range(15)]
        for y, row in enumerate(heart):
            for x, c in enumerate(row):
                if c != ".": g[y + 1][x + 1] = FIRE[c]
    save(name, g)

FLAME_HEART = [
    "", "", "", "", "", "",
    "....royWWyor....",
    "....royWWyor....",
    ".....oyyyyo.....",
    "......oooo......",
]
campfire("campfire/base.png", [
    "",
    "",
    "",
    "",
    "",
    "......d..d......",
    ".....dB..Bd.....",
    "..c.dBr..rBd.c..",
    "..bBdBorroBdBb..",
    "...dbbbbbbbbd...",
    ".gGg.dbbbbd.gGg.",
    "gGGSgGgGgGgGgGGS",
    ".SSmSSmSSSmSSSm.",
], FLAME_HEART)
for i, tongues in enumerate([
    [".......r........",                                     # tall, leaning right, a wisp beside it
     "......ry...r....",
     "......ryr..r....",
     ".....ryyor.r....",
     ".....roWyorr....",
     "....rroWWyor...."],
    ["........r.......",                                     # tall, a wisp on the left
     "....r...yr......",
     "....r..ryr......",
     "....r.royyr.....",
     "....rroyWor.....",
     "....royWWyor...."],
    ["",                                                     # low and broad
     "",
     "........r.......",
     "......r.yr......",
     ".....ryryor.....",
     "....royyWyor...."],
], 1):
    campfire(f"campfire/flame-{i}.png", tongues + FLAME_HEART[6:])

save("icons/wrench.png", chars([  # the card's, to change class; double-ended: an open jaw at each end
    ".....w.w",
    ".....www",
    "....ww..",
    "...ww...",
    "..ww....",
    "www.....",
    "w.w.....",
    "........",
], {"w": "#dbe7f3"}))

# ---- Status icons (status/), shown over an agent's head, outlined like the sprites ----
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
icon("status/sword-l.png", BLADE, SWORD)                       # working: two of these clash
icon("status/sword-r.png", [r[::-1] for r in BLADE], SWORD)
save("status/spark.png", chars(["..y..", ".yWy.", "yWWWy", ".yWy.", "..y.."], {"y": "#ffe27a", "W": "#ffffff"}))
Z = {"z": "#e6f0fa"}
icon("status/z-1.png", ["zzz", ".z.", "zzz"], Z)                # idle: three of these rise
icon("status/z-2.png", ["zzzz", "..z.", ".z..", "zzzz"], Z)
icon("status/z-3.png", ["zzzzz", "...z.", "..z..", ".z...", "zzzzz"], Z)
icon("status/alert.png", [                                     # blocked: it needs you
    ".rrrrr.",
    "rrrwrrr",
    "rrrwrrr",
    "rrrwrrr",
    "rrrrrrr",
    "rrrwrrr",
    ".rrrrr.",
    "..rr...",
], {"r": "#e2483f", "w": "#ffffff"})
icon("status/done.png", [                                      # done: finished while you were away
    ".ggggg.",
    "ggggggg",
    "gggggwg",
    "ggggwgg",
    "gwgwggg",
    "ggwgggg",
    ".ggggg.",
    "..gg...",
], {"g": "#3fbf6f", "w": "#ffffff"})

# ---- Night (light/): darkness laid over the wall, the floor and everyone on it, with a
# pool of light left clear around a flame. The dark deepens away from the
# flame in six even steps (rings, not a smooth blur) up to half strength, so
# the far corners are dim, not black. 74 rows: 20 above the wall, where the dark
# thins out upward to nothing (so a tall monster is not cut in two at the wall's
# top), then the wall (16) and the floor (38). `cy` counts from the wall's top.
# Each light is (cx, cy, near, far, stretch): where the flame is, how far the
# pool stays clear, where the dark is whole, and how much wider than tall it is.
# Where pools overlap, the lighter wins.
RISE = 20
def dark(name, w, *lights):
    g = blank(w, RISE + 54)
    for y in range(RISE + 54):
        for x in range(w):
            step = 6
            for cx, cy, near, far, stretch in lights:
                d = math.hypot((x + 0.5 - cx) / stretch, y + 0.5 - RISE - cy)
                t = min(1.0, max(0.0, (d - near) / (far - near)))
                step = min(step, round(t * t * (3 - 2 * t) * 6))
            step = min(step, 6 * y // RISE)
            if step: g[y][x] = "#0a1030%02x" % round(128 * step / 6)
    save(name, g)

TORCH_LIGHT = (48.5, 4.5, 9, 40, 1.15)
dark("light/torch.png", 96, TORCH_LIGHT)                 # one torch's stretch of wall, the flame near the top
dark("light/candle.png", 68, (28.5, 9, 3, 24, 1.0))      # the left end, lit only by the candle on the table
dark("light/fill.png", 4)                                # no flame: stretched over whatever is left
# The campfire's stretch (between raids), 56 wide with the fire in the middle,
# cut into the row of pictures wherever the fire stands. The torches' pools
# reach into it, so it carries their light as well as its own. The torches'
# pictures start 68 art px from the left and repeat every 96, and the fire
# stands at 68 + 4n (16 screen px steps), so "fire-<i>" is the stretch for
# a fire 4i art px into a torch's picture (i = n mod 24). The fire's own pool is
# centred on its flames, just above the floor's back edge (its feet are 8 art
# px into the floor), and lights the floor around it.
FIRE_LIGHT = (28, 15, 5, 22, 1.25)
for i in range(24):
    torches = [(TORCH_LIGHT[0] + 28 - 4 * i + 96 * k,) + TORCH_LIGHT[1:] for k in (-1, 0, 1)]
    dark(f"light/fire-{i}.png", 56, FIRE_LIGHT, *torches)

# ---- Sign icons (icons/): the counts on the sign, drawn small (shown at 2 screen px a pixel) ----
icon("icons/swords.png", [                                  # working
    "A.....A",
    ".A...A.",
    "..A.A..",
    "g..A..g",
    ".gA.Ag.",
    "..g.g..",
    ".d...d.",
], SWORD)
icon("icons/sleep.png", [                                   # resting
    "zzzz...",
    "..z....",
    ".z.....",
    "zzzz...",
    "....zzz",
    ".....z.",
    "....zzz",
], Z)
icon("icons/skull.png", [                                   # slain
    ".wwwww.",
    "wwwwwww",
    "wkkwkkw",
    "wkkwkkw",
    "wwwkwww",
    ".wwwww.",
    ".wkwkw.",
], {"w": "#ece6d6", "k": "#2a2433"})
icon("stations/arrow.png", ["wwwww", ".www.", "..w.."], {"w": "#ffffff"})  # bobs over the station under the pointer
icon("icons/armour.png", [                                  # the shop's armours
    "aa...aa",
    "aAaaaAa",
    ".aAAAa.",
    ".aAaAa.",
    ".aAAAa.",
    ".aaAaa.",
    "..aaa..",
], SWORD)
icon("icons/hat.png", [                                     # the shop's hats
    "...b...",
    "..bb...",
    "..bBb..",
    ".bbBb..",
    ".ggggg.",
    "bbbbbbb",
], {"b": "#4a6fd0", "B": "#7fa0ee", "g": "#f2c14e"})
icon("icons/coin.png", [                                    # gold
    "..ggg..",
    ".gyyyg.",
    "gyyhyyg",
    "gyhyyyg",
    "gyyyyyg",
    ".gyyyg.",
    "..ggg..",
], {"g": "#c8891e", "y": "#f2c14e", "h": "#fff0b0"})
icon("icons/star.png", [                                    # skill points to spend
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

# Each monster's whole picture ("idle"), the pieces that move on their own,
# eyelids to lay on top, and for the ogre and dragon a roar/ folder, all in
# monsters/<kind>/. Moving a piece over a still one never shows a ghost behind it,
# which easing between two whole frames did.
slime("monsters/slime/idle.png"); slime("monsters/slime/blink.png", lids=True)
slime("monsters/slime/base.png", keep=lambda x, y: y >= 19)          # the foot stays put (below the mouth)
slime("monsters/slime/top.png", keep=lambda x, y: y < 19)            # the dome sinks into it and rises
ogre("monsters/ogre/idle.png"); ogre("monsters/ogre/roar/roar.png", roar=True); ogre("monsters/ogre/blink.png", lids=True)
ogre("monsters/ogre/top.png", keep=lambda x, y: y < 31)              # head, shoulders, arms: breathing
dragon("monsters/dragon/idle.png"); dragon("monsters/dragon/blink.png", lids=True)
dragon("monsters/dragon/tail.png", part="tail")                      # sways behind the body
dragon("monsters/dragon/body.png", part="body")
dragon("monsters/dragon/top.png", part="body", keep=lambda x, y: y < 38)  # head, neck, wings: breathing
dragon("monsters/dragon/roar/rear.png", part="body", pose="rear")         # a roar: the wind-up, then
dragon("monsters/dragon/roar/roar.png", part="body", pose="roar")         # the roar itself,
dragon("monsters/dragon/roar/top.png", part="body", pose="roar", keep=lambda x, y: y < 38)  # its upper body shaking
icon("monsters/dragon/roar/wave.png", [                                 # rings out of the roaring dragon's mouth, to the left
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

# ---- Attacks (battle mode), in attacks/, by what flies or lands, then by
# the weapon's variant of it (see ATTACK_ART in mods/idle-rpg/rules.js, which
# picks them for each weapon): the warrior's slash/, the archer's arrow/, the
# wizard's spell/ and the burst/ where it lands, the healer's potion/ and its
# splash/, and the spark/ where a fire or frost arrow lands (a plain one's is
# status/spark). Those that fly or face a way have a folder: "r" flies or faces
# right, "l" is its mirror. Every variant of one has the same size, so the mod
# draws them all alike; the first of each is what the class always had. ----
def both(name, rows, pal):
    icon(f"attacks/{name}/r.png", rows, pal)
    icon(f"attacks/{name}/l.png", [r[::-1] for r in rows], pal)

ARROW = {"f": "#f4ecd8", "d": "#7a5230", "A": "#dfe6ee"}
for name, rows, pal in [
    ("default", ["f......A.", "fddddddAA", "f......A."], ARROW),
    ("fire", ["f....r.o.", "fdddddyoW", "f....r.o."], {**ARROW, "r": "#e2552f", "o": "#ff9d3c", "y": "#ffe27a", "W": "#fff3b0"}),
    ("frost", ["f.....bi.", "fddddddiI", "f.....bi."], {**ARROW, "b": "#4f86c6", "i": "#9fd0f5", "I": "#ffffff"}),
    ("bolt", ["...kk..a.", "...kDDDaA", "...kk..a."], {"k": "#5b6675", "D": "#5a3d22", "a": "#9aa7b8", "A": "#dfe6ee"}),  # the crossbow's: short and heavy
]:
    assert len(rows) == 3 and all(len(r) == 9 for r in rows)
    both(f"arrow/{name}", rows, pal)
for name, rows, pal in [
    ("fire", [                                   # a fireball
        "...ooo..",
        ".yooyyo.",
        "royyWWyo",
        "royyWWyo",
        ".yooyyo.",
        "...ooo..",
    ], {"r": "#e2552f", "o": "#ff9d3c", "y": "#ffe27a", "W": "#ffffff"}),
    ("frost", [                                  # an ice shard
        "...bi...",
        ".bbiiI..",
        "biiiIIWW",
        "biiiIIWW",
        ".bbiiI..",
        "...bi...",
    ], {"b": "#4f86c6", "i": "#9fd0f5", "I": "#dff3ff", "W": "#ffffff"}),
    ("storm", [                                  # a bolt of lightning
        "........",
        "..yW...y",
        ".yWyW.yW",
        "yW..yWy.",
        "W....y..",
        "........",
    ], {"y": "#ffe27a", "W": "#ffffff"}),
    ("poison", [                                 # a glob of venom, dripping
        "...vvv..",
        ".vvVVvv.",
        "xvVLLVvv",
        "xvvVVvvv",
        ".xvvvvv.",
        "x..xxx..",
    ], {"x": "#2f7a22", "v": "#6fcf3f", "V": "#a8eb6a", "L": "#e4ffc4"}),
]:
    assert len(rows) == 6 and all(len(r) == 8 for r in rows)
    both(f"spell/{name}", rows, pal)
for name, rows, pal in [
    ("default", [".WW...", "...WW.", "....WW", "....WW", ".....W", "....WW", "....WW", "...WW.", ".WW..."], {"W": "#ffffff"}),
    ("heavy", ["WWW...", ".wWWW.", "...WWW", "...wWW", "....WW", "...wWW", "...WWW", ".wWWW.", "WWW..."],   # the axe's: a broad cleave
     {"W": "#ffffff", "w": "#c9d6e6"}),
    ("smash", ["..W..W", "W..W..", ".W.WW.", "..WyWW", "WWyyyW", "..WyWW", ".W.WW.", "W..W..", "..W..W"],  # the hammer's: a crunch
     {"W": "#ffffff", "y": "#ffe27a"}),
    ("flame", [".ry...", "...oy.", "....oy", "....oy", ".....y", "....oy", "....oy", "...oy.", ".ry..."],    # the flame blade's
     {"r": "#e2552f", "o": "#ff9d3c", "y": "#ffe27a"}),
]:
    assert len(rows) == 9 and all(len(r) == 6 for r in rows)
    both(f"slash/{name}", rows, pal)
for name, rows, pal in [
    ("fire", [
        "....y....",
        ".y.yoy.y.",
        "..yoWoy..",
        ".yoWWWoy.",
        "yoWWWWWoy",
        ".yoWWWoy.",
        "..yoWoy..",
        ".y.yoy.y.",
        "....y....",
    ], {"o": "#ff9d3c", "y": "#ffe27a", "W": "#ffffff"}),
    ("frost", [                                  # a burst of frost
        "....I....",
        ".I..i..I.",
        "..i.i.i..",
        "...iIi...",
        "IiiIWIiiI",
        "...iIi...",
        "..i.i.i..",
        ".I..i..I.",
        "....I....",
    ], {"i": "#9fd0f5", "I": "#ffffff", "W": "#ffffff"}),
    ("storm", [                                  # a crackle
        "y...W...y",
        ".y..y..y.",
        "..yyWyy..",
        "..yWWWy..",
        "WyWWWWWyW",
        "..yWWWy..",
        "..yyWyy..",
        ".y..y..y.",
        "y...W...y",
    ], {"y": "#ffe27a", "W": "#ffffff"}),
    ("poison", [                                 # a splat of venom
        ".v.....v.",
        "....v....",
        "..vvVvv..",
        ".vVVLVVv.",
        "vvVLLLVvv",
        ".vVVLVVv.",
        "..vvVvv..",
        "....v.x..",
        ".x.....v.",
    ], {"x": "#2f7a22", "v": "#6fcf3f", "V": "#a8eb6a", "L": "#e4ffc4"}),
]:
    assert len(rows) == 9 and all(len(r) == 9 for r in rows)
    icon(f"attacks/burst/{name}.png", rows, pal)
# The healer's potions, thrown, and their splashes, in each potion's colours
# (the liquid "g" and its shine "G"): heal (what it always threw), haste,
# might and hex.
POTION_COLOURS = {
    "heal": {"g": "#3fbf8f", "G": "#9af0cf"},
    "haste": {"g": "#e8b030", "G": "#fff0b0"},
    "might": {"g": "#d63a3a", "G": "#ff9a8a"},
    "hex": {"g": "#7a3fb8", "G": "#d8b4ff"},
}
for name, colours in POTION_COLOURS.items():
    icon(f"attacks/potion/{name}.png", [
        ".bbb.",
        "..w..",
        ".www.",
        "wgggw",
        "wgGgw",
        "wgggw",
        ".www.",
    ], {"b": "#7a5230", "w": "#dff3ee", **colours})
    icon(f"attacks/splash/{name}.png", [
        "g.........g",
        "..g..g..g..",
        ".g.ggGgg.g.",
        "..gGGGGGg..",
        ".ggGGGGGgg.",
        "..ggggggg..",
    ], colours)
# where a fire or frost arrow lands: status/spark (a plain arrow's) in its colours
for name, pal in (("fire", {"y": "#ff9d3c", "W": "#ffe27a"}), ("frost", {"y": "#9fd0f5", "W": "#ffffff"})):
    save(f"attacks/spark/{name}.png", chars(["..y..", ".yWy.", "yWWWy", ".yWy.", "..y.."], pal))

# ---- Fighting poses (battle mode), on a 22x16 grid so a weapon can reach out.
# Drawn attacking to the right: "stance", "windup" and "strike", each a folder
# in the look's; "r" faces right and "l" is the mirror image, for attacking to
# the left. Each pose is drawn in every colourway, with the same swaps as the
# everyday sprite, and like it without the weapon, which each weapon draws in
# its own rows for the pose (see Weapons, below).
POSED = {}  # (class, tag): the pose's rows, for the bodies, the weapons and the hats

def pose(cls, tag, rows):
    rows = [r.ljust(22, ".") for r in rows]
    assert len(rows) == 16 and all(len(r) == 22 for r in rows), (cls, tag, [len(r) for r in rows])
    POSED[(cls, tag)] = rows

def swap(rows, changes):
    rows = list(rows)
    for y, text in changes.items(): rows[y] = text
    return rows

def dots(rows, pixels):
    g = [list(r.ljust(22, ".")) for r in rows]
    for x, y, ch in pixels: g[y][x] = ch
    return ["".join(r) for r in g]

W = SPR["warrior"][1]
pose("warrior", "stance", W)
pose("warrior", "windup", swap(W, {            # weapon held high: the hand at the shoulder
    7: "....assssssa.s", 8: ".....ssssss.a", 9: "....AaaaaaaAa", 12: ".ugguddgdddp",
}))
pose("warrior", "strike", swap(W, {            # swung level, at full reach
    10: ".uuuuaaaaaapas", 12: ".ugguddgdddp",
}))

A = SPR["archer"][1]
for tag in POSES: pose("archer", tag, A)        # the bow does the drawing and loosing

Z = SPR["wizard"][1]
pose("wizard", "stance", Z)
for tag in ("windup", "strike"):                # raised, then thrust out: the hand at the chest
    pose("wizard", tag, swap(Z, {9: ".....bbbbbb.s", 10: "....rrbbbbrrr", 11: "...srrrbbrrr"}))

# The healer throws with the free hand, so its stance is the mirror of the
# everyday sprite: staff on the far side, free hand toward the monster.
H = [r[::-1] for r in SPR["healer"][1]]
pose("healer", "stance", H)
pose("healer", "windup", dots(H, [(12, 10, "."), (12, 9, "r"), (13, 8, "s")]))  # hand up, holding the potion
pose("healer", "strike", dots(H, [(13, 10, "r"), (14, 10, "s")]))              # arm flung out

# ---- Weapons: a layer of its own over the class's picture and under its hat.
# For each class, weapon and picture, a see-through PNG the size of the
# picture it lies on (weapons/<class>/<weapon>/<frame>.png), so the mod lays
# one over the other with no sums, and one serves every colourway: a weapon
# keeps its own colours whatever the armour. Each weapon is (palette, rows),
# its rows per pose sparse ({row: text}, "." empty): "stand" in the everyday
# 16x16 grid (also its stance: the warrior, wizard and archer stand ready),
# "windup" and "strike" in the 22-wide grid, held in the hand of the class's
# pose. Each is pushed through the same canvas, lean, shear and mirror as the
# body. The healer keeps its staff; its "weapon" is the potion it holds up in
# its wind-up and throws, so its weapons have only those two pictures. Each
# class's ids, in this order, must match WEAPON_NAMES in mods/idle-rpg/rules.js
# (the first, "default", is what the class always had), and the pictures each
# has WEAPON_FRAMES there. In the everyday grid a weapon stays inside columns
# 1 to 14, so walking and dangling keep its outline on the canvas.
STEEL = {"A": "#dfe6ee", "a": "#9aa7b8", "k": "#5b6675", "g": "#f2c14e", "d": "#7a5230", "D": "#5a3d22"}
FLAME = {"r": "#e2552f", "o": "#ff9d3c", "y": "#ffe27a", "W": "#fff3b0", "R": "#8f2626", "g": "#f2c14e", "d": "#7a5230"}
FROST = {"I": "#ffffff", "i": "#9fd0f5", "b": "#4f86c6"}
COLUMN = lambda x, ys, ch: {y: "." * x + ch for y in ys}   # one pixel per row, down column x
WEAPONS = {
"warrior": {
    "default": (STEEL, {                         # Longsword
        "stand": {**COLUMN(13, range(2, 11), "A"), 11: "............ggg", 12: ".............d"},
        "windup": {**COLUMN(13, range(0, 6), "A"), 6: "............ggg"},
        "strike": {9: "..............g", 10: "..............gAAAAAAA", 11: "..............g"},
    }),
    "axe": (STEEL, {                             # Battle Axe: a broad blade on a long haft
        "stand": {0: ".............d", 1: "............AdA", 2: "............AaA", 3: "............AdA",   # a blade each side, standing
                  **COLUMN(13, range(4, 13), "d"), 13: ".............D"},
        "windup": {0: ".............daA", 1: ".............daaA", 2: ".............daaA", 3: ".............daA",
                   **COLUMN(13, range(4, 7), "d"), 8: ".............D"},
        "strike": {9: "..................aa", 10: "..............ddddaad", 11: "..................aaA",
                   12: "..................aaaA", 13: "..................AAAA"},
    }),
    "hammer": (STEEL, {                          # War Hammer: a heavy iron head
        "stand": {0: "............aAa", 1: "............aaa", 2: "............kkk", **COLUMN(13, range(3, 13), "d"), 13: ".............D"},
        "windup": {0: "...........aaAaa", 1: "...........aaaaa", 2: "...........kkkkk", **COLUMN(13, range(3, 7), "d"), 8: ".............D"},
        "strike": {8: "...................aAk", 9: "...................aAk", 10: "..............dddddaAk",
                   11: "...................aAk", 12: "...................aAk"},
    }),
    "flame": (FLAME, {                           # Flame Blade: burning from guard to tip
        "stand": {1: ".............r", 2: ".............or", 3: ".............y", 4: ".............W", 5: ".............yo",
                  6: ".............W", 7: ".............y", 8: ".............Wr", 9: ".............y", 10: ".............o",
                  11: "............RgR", 12: ".............d"},
        "windup": {0: ".............o", 1: "............ryr", 2: ".............W", 3: ".............yo", 4: ".............W",
                   5: ".............y", 6: "............RgR"},
        "strike": {9: "..............R..r..o", 10: "..............goyWyWyo", 11: "..............R...r"},
    }),
},
"wizard": {
    "default": ({"c": "#8fe3ff", "C": "#ffffff", "w": "#8a5a2b"}, {   # Ember Staff
        "stand": {2: ".............c", 3: "............cCc", 4: ".............c", **COLUMN(13, range(5, 15), "w")},
        "windup": {0: ".............c", 1: "............cCc", 2: ".............c", **COLUMN(13, range(3, 11), "w")},
        "strike": {8: "...................c", 9: ".............wwwwwcCc", 10: "...................c"},
    }),
    "frost": ({**FROST, "v": "#c9d6e6"}, {     # Frost Wand: short and silver, tipped with an icicle
        "stand": {2: ".............I", 3: ".............I", 4: ".............i", 5: ".............b", **COLUMN(13, range(6, 13), "v")},
        "windup": {0: ".............I", 1: ".............I", 2: ".............i", 3: ".............b", **COLUMN(13, range(4, 11), "v")},
        "strike": {9: ".............vvvvbiII"},
    }),
    "storm": ({"k": "#3b3f5c", "n": "#6b7090", "Y": "#ffe27a", "W": "#ffffff"}, {   # Storm Staff: a forked iron head, a spark caught in it
        "stand": {0: ".............Y", 1: "............nWn", 2: "............kYk", 3: ".............k", **COLUMN(13, range(4, 15), "k")},
        "windup": {0: "............nWn", 1: "............kYk", 2: ".............k", **COLUMN(13, range(3, 11), "k")},
        "strike": {8: "..................kn", 9: ".............kkkkkkYWY", 10: "..................kn"},
    }),
    "venom": ({"V": "#c4ff8f", "v": "#6fcf3f", "x": "#2f7a22", "n": "#5a4326"}, {   # Venom Wand: short and crooked, a dripping glob
        "stand": {5: ".............Vv", 6: ".............vx", 7: "............n", 8: "..............v", **COLUMN(13, range(8, 13), "n")},
        "windup": {3: ".............Vv", 4: ".............vx", 5: "............n", 6: "..............v", **COLUMN(13, range(6, 11), "n")},
        "strike": {8: "................Vv", 9: ".............nnnvx", 10: ".................v"},
    }),
},
"archer": {
    "default": ({"d": "#7a5230", "c": "#f4ecd8", "A": "#dfe6ee"}, {   # Longbow
        "stand": {5: "............d", 6: "............cd", 7: "............cd", 8: "............c.d", 9: "............c.d",
                  10: "..............d", 11: "............c.d", 12: "............cd", 13: "............cd", 14: "............d"},
        "windup": {5: "..............d", 6: "..............cd", 7: "..............cd", 8: ".............c..d", 9: ".............c..d",
                   10: ".............ddddA", 11: ".............c..d", 12: ".............c.d", 13: "..............cd", 14: "..............d"},
        "strike": {5: "..............d", 6: "..............cd", 7: "..............cd", 8: "..............c.d", 9: "..............c.d",
                   10: "..............c.d", 11: "..............c.d", 12: "..............cd", 13: "..............cd", 14: "..............d"},
    }),
    "crossbow": ({"w": "#9a6639", "D": "#5a3d22", "a": "#9aa7b8", "A": "#dfe6ee", "k": "#5b6675"}, {   # Crossbow: held level, no string to draw
        "stand": {6: ".............A", 7: "............aka", 8: "............a.a", **COLUMN(13, range(9, 12), "w"), 12: ".............D", 13: ".............D"},
        "windup": {8: "................a", 9: ".................a", 10: ".............wwwwkA", 11: "..............D..a", 12: "................a"},
        "strike": {8: "................a", 9: ".................a", 10: ".............wwwwk", 11: "..............D..a", 12: "................a"},
    }),
    "flame": ({"R": "#a53030", "o": "#ff9d3c", "y": "#ffe9a8", "d": "#7a5230", "r": "#e2552f", "Y": "#ffe27a"}, {   # Flame Bow: fire arrows
        "stand": {5: "............o", 6: "............yR", 7: "............yR", 8: "............y.R", 9: "............y.R",
                  10: "..............R", 11: "............y.R", 12: "............yR", 13: "............yR", 14: "............o"},
        "windup": {5: "..............o", 6: "..............yR", 7: "..............yR", 8: ".............y..R", 9: ".............y..RY",
                   10: ".............dddRr", 11: ".............y..R", 12: ".............y.R", 13: "..............yR", 14: "..............o"},
        "strike": {5: "..............o", 6: "..............yR", 7: "..............yR", 8: "..............y.R", 9: "..............y.R",
                   10: "..............y.R", 11: "..............y.R", 12: "..............yR", 13: "..............yR", 14: "..............o"},
    }),
    "frost": ({**FROST, "d": "#7a5230"}, {      # Frost Bow: frost arrows
        "stand": {5: "............I", 6: "............Ib", 7: "............Ib", 8: "............I.i", 9: "............I.i",
                  10: "..............i", 11: "............I.i", 12: "............Ib", 13: "............Ib", 14: "............I"},
        "windup": {5: "..............I", 6: "..............Ib", 7: "..............Ib", 8: ".............I..i", 9: ".............I..iI",
                   10: ".............dddib", 11: ".............I..i", 12: ".............I.b", 13: "..............Ib", 14: "..............I"},
        "strike": {5: "..............I", 6: "..............Ib", 7: "..............Ib", 8: "..............I.i", 9: "..............I.i",
                   10: "..............I.i", 11: "..............I.i", 12: "..............Ib", 13: "..............Ib", 14: "..............I"},
    }),
},
"healer": {                                      # the potion held up: a cork over a little flask
    "default": ({"h": "#e6dfcc", "P": "#3fbf8f"}, {"windup": {5: ".............h", 6: ".............PP", 7: ".............PP"}}),   # Healing Potion
    "haste": ({"h": "#e6dfcc", "L": "#fff0b0", "P": "#f2c14e"}, {"windup": {5: ".............h", 6: ".............LP", 7: ".............PP"}}),
    "might": ({"h": "#e6dfcc", "L": "#ff9a8a", "P": "#d63a3a"}, {"windup": {5: ".............h", 6: ".............LP", 7: ".............PP"}}),
    "hex": ({"h": "#e6dfcc", "L": "#d8b4ff", "P": "#7a3fb8"}, {"windup": {5: ".............h", 6: ".............LP", 7: ".............PP"}}),
},
}
assert set(WEAPONS) == set(SPR) and all(list(w)[0] == "default" for w in WEAPONS.values())
assert all(i.isalpha() and i.islower() for w in WEAPONS.values() for i in w)

def sparse(rows, width):
    assert all(0 <= y < 16 and len(t) <= width for y, t in rows.items()), rows
    return [rows.get(y, "").ljust(width, ".") for y in range(16)]

def armed(poses):
    # a weapon's pictures as (frame, grid), like pictures(): the everyday ones
    # if it has a "stand", whose rows are its stance too, and each pose it has
    stand = sparse(poses["stand"], 16) if "stand" in poses else None
    tags = [t for t in POSES if t in poses or (t == "stance" and stand)]
    return pictures(stand, lambda t: sparse(poses.get(t, poses.get("stand")), 22), tags)

def near(g, y, x):
    return any(0 <= y+j < len(g) and 0 <= x+i < len(g[0]) and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1)))

def layer(weapon, body, pal):
    # The weapon's pixels, and the part of the one outline around body and
    # weapon that is the weapon's: around it, wherever the body's own outline
    # (drawn with the body) does not already go. Laid over the body, the two
    # make the picture with one outline around both.
    h, w = len(body), len(body[0])
    o = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if weapon[y][x]: o[y][x] = pal[weapon[y][x]]
            elif not body[y][x] and near(weapon, y, x) and not near(body, y, x): o[y][x] = OUTLINE
    return o

for cls, (base, rows) in SPR.items():
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), (cls, [len(r) for r in rows])
    body = pictures(rows, lambda tag: POSED[(cls, tag)])
    for name, swaps in looks(cls):                              # every colourway, the default first
        pal = {**COMMON, **base, **swaps, "#": OUTLINE}
        for frame, g in body:
            write(f"{name}/{frame}.png", png(outlined(g), pal))
    shape = dict(body)
    frames = None
    for weapon, (pal, poses) in WEAPONS[cls].items():
        pics = armed(poses)
        assert frames in (None, [f for f, _ in pics]), (cls, weapon)  # every weapon of a class has the same pictures
        frames = [f for f, _ in pics]
        for frame, g in pics:
            assert all(c != "." for row in g for c in row if c) and all(not c or c in pal for row in g for c in row), (cls, weapon, frame)
            write(f"weapons/{cls}/{weapon}/{frame}.png", png(layer(g, shape[frame], pal), {}))

# ---- The pixel font: digits and a few signs, 3x5, for damage numbers and the
# badges on the status icons. Each glyph is outlined all round (corners too, so
# it reads over a monster or the sky) and comes in every colour main.js uses.
# Its characters and colours must match GLYPHS and GLYPH_COLOURS in
# mods/idle-rpg/rules.js, which names the files (glyphArt): font/<colour>/<name>.
FONT = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", "..#", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
    "plus": ["...", ".#.", "###", ".#.", "..."],
    "bang": [".#.", ".#.", ".#.", "...", ".#."],
}
GLYPH_COLOURS = {"white": "#ffffff", "gold": "#ffd166"}  # a plain hit and a badge; a critical blow

def glyph(name, rows, colour):
    h, w = len(rows) + 2, len(rows[0]) + 2
    g = [[None] * w for _ in range(h)]
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch == "#": g[y + 1][x + 1] = colour
    o = [r[:] for r in g]
    for y in range(h):
        for x in range(w):
            if g[y][x] is None and any(0 <= y+j < h and 0 <= x+i < w and g[y+j][x+i] for i in (-1, 0, 1) for j in (-1, 0, 1)):
                o[y][x] = OUTLINE
    save(name, o)

for colour, hexa in GLYPH_COLOURS.items():
    for ch, rows in FONT.items():
        glyph(f"font/{colour}/{ch}.png", rows, hexa)

# ---- The settings menu: a gear (icons/), the right-most icon of the top-right corner ----
icon("icons/gear.png", [
    "..s..s..",
    ".ssssss.",
    "ssggggss",
    ".sg..gs.",
    ".sg..gs.",
    "ssggggss",
    ".ssssss.",
    "..s..s..",
], {"s": "#c3ccd8", "g": "#8f9bab"})
# ---- Hats: one overlay per hat, class and picture, the same size as that
# picture and see-through but for the hat, so the mod lays it over the picture
# with no sums. Hats are not tied to a class (any class can wear any hat), but
# every head sits in its own place and three wear their own headgear, so each
# hat is drawn per class in the everyday sprite's 16x16 grid, where it covers
# the class's headgear (the wizard's hat entirely) or sits on it. Each grid is
# then pushed through the same canvas, lean, shear and mirror as the class's
# pictures, so the hat follows the head; the healer's poses are its mirror
# image, so its hats are mirrored in them too. A hat's outline goes only where
# the picture under it is see-through, never across a face; "#" in a grid is
# outline drawn on purpose, over the picture. An overlay only covers, so one
# serves every colourway: hats/<id>/<class>/<frame>.png. The ids, in this order,
# must match HAT_NAMES in mods/idle-rpg/rules.js.
HAT_PAL = {
    "P": "#e8508f", "p": "#b8336c", "y": "#ffd75e", "o": "#f4f7fb",                   # party: cone, shade, stripes, pompom
    "R": "#d63a3a", "r": "#a52a2a", "W": "#f4f7fb", "w": "#c9d6e6",                   # santa: red, shade, fur, fur shade
    "O": "#ec8a2c", "Q": "#c4661c", "K": "#3a1f12", "Y": "#ffd75e", "G": "#3f8f55",   # pumpkin: skin, ribs, carving, glow, stem
}
HATS = {
"party": {
    "wizard": [
        ".......oo.......",
        ".......PP.......",
        "......yPPp......",
        "......PyPp......",
        ".....PPyPPp.....",
        "....yPPPyPPp....",
    ],
    "healer": [
        ".......oo.......",
        "......yPPp......",
        ".....PPyPPp.....",
        "....yPPPyPPp....",
    ],
    "warrior": [
        ".......oo.......",
        ".......PP.......",
        "......yPPp......",
        ".....PPyPPp.....",
        "....yPPPyPPp....",
    ],
    "archer": [
        ".......oo.......",
        "......yPPp......",
        ".....PPyPPp.....",
        ".....yPPPyPp....",
    ],
},
"santa": {
    "wizard": [
        ".....RRRR.......",
        "...RRRRRRr......",
        "..RR.RRRRr......",
        ".WW..RRRRr......",
        ".Ww.RRRRRRr.....",
        "....WWWWWWWW....",
    ],
    "healer": [
        "......RRRR......",
        "...RRRRRRRr.....",
        ".WW.RRRRRRr.....",
        ".Ww.WWWWWWWW....",
    ],
    "warrior": [
        "......RRR.......",
        "...RRRRRRr......",
        ".WW.RRRRRRr.....",
        ".Ww.WWWWWWWW....",
    ],
    "archer": [
        "......RRR.......",
        "...RRRRRRRr.....",
        ".WW.RRRRRRRr....",
        ".Ww.WWWWWWWW....",
    ],
},
"pumpkin": {
    "wizard": [
        "................",
        ".......GG.......",
        ".....OOOOOO.....",
        "....OOQOOQOO....",
        "....OKKOOKKO....",
        "....OOKOOKOO....",
        "....OQOOOOQO....",
        "....OKYKKYKO....",
        "....OQKKKKQO....",
        ".....OOOOOO.....",
    ],
    "healer": [
        "................",
        ".......GG.......",
        ".....OOOOOO.....",
        "....OOQOOQOO....",
        "....OKKOOKKO....",
        "....OOKOOKOO....",
        "....OKYKKYKO....",
        "....OQKKKKQO....",
        ".....OOOOOO.....",
    ],
    "warrior": [
        "................",
        ".......GG.......",
        ".....OOOOOO.....",
        "....OOQOOQOO....",
        "....OOQOOQOO....",
        "....OKKOOKKO....",
        "....OOKOOKOO....",
        "....OKYKKYKO....",
        "....OQKKKKQO....",
        ".....OOOOOO.....",
    ],
    "archer": [
        "................",
        "......GG........",
        ".....OOOOOO.....",
        "....OOQOOQOO....",
        "...OOOQOOQOOO...",
        "...OOKKOOKKOO...",
        "...OOOKOOKOOO...",
        "...OQKYKKYKQO...",
        "....OQKKKKQO....",
    ],
},
}
assert all(i.isalpha() and i.islower() and i != "default" for i in HATS)
assert all(set(HATS[i]) == set(SPR) for i in HATS)

def overlay(hat, body):
    # the hat's pixels, and its outline where the body's picture (outline and
    # all) leaves the canvas see-through
    h, w = len(body), len(body[0])
    near = lambda g, y, x: any(0 <= y+j < h and 0 <= x+i < w and g[y+j][x+i] for i, j in ((1,0),(-1,0),(0,1),(0,-1)))
    o = [[None] * w for _ in range(h)]
    for y in range(h):
        for x in range(w):
            if hat[y][x]: o[y][x] = OUTLINE if hat[y][x] == "#" else HAT_PAL[hat[y][x]]
            elif near(hat, y, x) and not body[y][x] and not near(body, y, x): o[y][x] = OUTLINE
    return o

for hat, by_class in HATS.items():
    for cls, top in by_class.items():
        rows = [r.ljust(16, ".") for r in top] + ["." * 16] * (16 - len(top))
        assert len(rows) == 16 and all(len(r) == 16 for r in rows), (hat, cls)
        # the wizard's hat must not show under any of them
        assert all(rows[y][x] != "." for y in range(6) for x in range(16) if SPR["wizard"][1][y][x] in "hyg") or cls != "wizard", hat
        mine = [r[::-1] for r in rows] if cls == "healer" else rows   # the healer's poses are mirrored
        body = pictures(SPR[cls][1], lambda tag: POSED[(cls, tag)])
        over = pictures(rows, lambda tag: [r.ljust(22, ".") for r in mine])
        for (frame, b), (_, g) in zip(body, over):
            save(f"hats/{hat}/{cls}/{frame}.png", overlay(g, b))
