// Idle RPG's game rules: experience, levels, skill points, the blows they buy,
// gold, kill counts, and loading the saved state. Plain functions with no host
// calls, so main.js does the drawing and these can be run on their own.
//
// Progress never belongs to an agent (agents come and go): it belongs to you
// and to the four classes. Every point of damage that lands earns experience
// for the class of whoever dealt it, and for you, who leads the raid. Each
// level a class gains earns it a skill point, spent on that class's skills,
// which make every character on that class hit harder, faster or with a
// chance of a critical blow. Killing a monster earns gold and counts towards
// its kind. Gold buys looks in the shop, which also belong to a class: every
// character with that class on wears its colourway, its weapon and its hat (a
// hat, once bought, can be worn by any class). Levels are worked out from total
// experience, never stored; skill ranks are stored, and points left are
// worked out from levels and ranks. Settings (SETTINGS) are kept with the
// rest of the state.

export const CLASSES = ["wizard", "healer", "warrior", "archer"];
export const YOU = "you"; // the person's key in `sprites`, `xp` and as an open card
export const STATE_VERSION = 5;
// Each kind's HP, kept on a monster as `maxHp` when it turns up. The kinds are
// the keys of MONSTERS in main.js, which draws them (each needs its pictures
// in MONSTER_ART below too).
export const MONSTER_HP = { slime: 100, ogre: 300, dragon: 500 };
export const KINDS = Object.keys(MONSTER_HP);
const OLD_MONSTER_HP = 100; // what every monster had before HP by kind, for one saved without `maxHp`

// Defaults chosen to be retuned; nothing else depends on their values.
export const CLASS_XP_PER_HP = 1; // to a class, per point of damage one of its characters deals
export const PLAYER_XP_PER_HP = 1; // to you, per point of damage anyone in the party deals
export const CLASS_LEVEL_XP = 100; // a class goes from level n to n + 1 for CLASS_LEVEL_XP * n
export const PLAYER_LEVEL_XP = 250; // you go from level n to n + 1 for PLAYER_LEVEL_XP * n
export const HP_PER_GOLD = 100; // gold on a kill: one per this much of the monster's max HP

// Skills. Every class has the same three for now; CLASS_SKILLS keeps a list per
// class so one can get its own later. Ranks are per class, so a skill applies
// to everyone with that class on, agents and you alike.
export const SKILLS = ["power", "haste", "crit"];
export const CLASS_SKILLS = Object.fromEntries(CLASSES.map((c) => [c, SKILLS]));
export const POINTS_PER_LEVEL = 1; // skill points a class earns per level past 1
export const RANK_COST = 1; // skill points per rank
export const MAX_RANK = 5;
export const BASE_DAMAGE = 1; // a blow at Power 0
export const POWER_DAMAGE = 1; // added to every blow per rank of Power
export const CRIT_CHANCE = 0.05; // chance of a critical blow per rank of Crit
export const CRIT_MULTIPLIER = 2; // a critical blow deals this many times the damage

// Attacks run on a clock of TICK_STEP ticks. One attack is ATTACK_PHASES ticks
// (wind-up, two of strike or flight, impact); the impact then fades for 350ms
// (main.js), which ends inside the second tick after it. So a character starts
// an attack at most every MIN_ATTACK_TICKS, and never before its last one is
// gone.
export const TICK_STEP = 250; // ms
export const ATTACK_PHASES = 4;
export const MIN_ATTACK_TICKS = ATTACK_PHASES + 2;
// Ticks between the starts of one character's attacks, by rank of Haste: one
// tick (250ms) less per rank, from 3s at rank 0 to 1.75s at rank 5.
export const ATTACK_TICKS = [12, 11, 10, 9, 8, 7];
// Each gap is that many ticks either way off its rank's, at random, so
// characters on the same rank do not fall into step (narrower where it would
// go under MIN_ATTACK_TICKS, so the average stays the rank's).
export const ATTACK_JITTER = 2;

// The shop. Gold buys looks for a class (never an agent, which is short-lived):
// everyone with that class on, agents and you alike, wears what the class has
// equipped. Each kind of item has a catalogue per class, and each class keeps,
// per kind, which one it has on and, for most kinds, what it owns. Armours
// (colourways of the whole outfit) are each class's own. Hats are not tied to
// a class: every class has the same catalogue, and a hat bought once is owned
// by all four, kept once in the state under the kind's `shared` key, though
// each class still puts on its own. Weapons are each class's own, like
// armours: what it fights with, and what its attacks look like (see
// attackArt); for now every weapon deals the same damage. The first item of
// every catalogue is the class's default look: free, always owned. Buying is
// for good (no refunds), and changing between owned items is free.
export const DEFAULT_LOOK = "default";
export const COLOUR_PRICES = [5, 10, 20]; // gold for each class's three colourways after the default, in order
export const HAT_PRICES = [10, 20, 30]; // gold for each hat after the default, in order, bought once for every class
export const WEAPON_PRICES = [15, 30, 50]; // gold for each class's three weapons after the default, in order
// Each class's colourways as [id, name]. The ids after the default, in this
// order, must match LOOKS in tools/idle-rpg-sprites.py, which draws them.
const COLOUR_NAMES = {
  wizard: [[DEFAULT_LOOK, "Violet"], ["crimson", "Crimson"], ["moss", "Moss"], ["frost", "Frost"]],
  healer: [[DEFAULT_LOOK, "Teal"], ["rose", "Rose"], ["sky", "Sky"], ["plum", "Plum"]],
  warrior: [[DEFAULT_LOOK, "Steel"], ["cobalt", "Cobalt"], ["jade", "Jade"], ["ruby", "Ruby"]],
  archer: [[DEFAULT_LOOK, "Forest"], ["scarlet", "Scarlet"], ["azure", "Azure"], ["dusk", "Dusk"]],
};
// Every hat as [id, name]; the default is the class's own headgear. The ids
// after the default, in this order, must match HATS in
// tools/idle-rpg-sprites.py, which draws each over every class.
const HAT_NAMES = [[DEFAULT_LOOK, "No hat"], ["party", "Party Hat"], ["santa", "Santa Hat"], ["pumpkin", "Pumpkin"]];
const HATS = HAT_NAMES.map(([id, name], i) => ({ id, name, price: i ? HAT_PRICES[i - 1] : 0 }));
// What a weapon's attacks will one day carry (they do nothing yet): an
// element, or null for none, and for the healer's potions, which potion it is.
export const ELEMENTS = ["fire", "frost", "storm", "poison"];
export const POTIONS = ["heal", "haste", "might", "hex"];
// Each class's weapons as [id, name, element] and, for the healer, whose
// "weapon" is the potion it throws, [id, name, element, potion]. The default is
// what the class always had. The ids after the default, in this order, must
// match WEAPONS in tools/idle-rpg-sprites.py, which draws each; ids repeat
// across classes (a warrior's "flame" is not an archer's).
const WEAPON_NAMES = {
  wizard: [[DEFAULT_LOOK, "Fire Staff", "fire"], ["frost", "Ice Wand", "frost"], ["storm", "Bolt Staff", "storm"], ["venom", "Toxic Rod", "poison"]],
  healer: [[DEFAULT_LOOK, "Heal Vial", null, "heal"], ["haste", "Haste Vial", null, "haste"], ["might", "Might Vial", null, "might"], ["hex", "Hex Vial", null, "hex"]],
  warrior: [[DEFAULT_LOOK, "Sword", null], ["axe", "War Axe", null], ["hammer", "Hammer", null], ["flame", "Fire Blade", "fire"]],
  archer: [[DEFAULT_LOOK, "Longbow", null], ["crossbow", "Crossbow", null], ["flame", "Fire Bow", "fire"], ["frost", "Ice Bow", "frost"]],
};
// Kinds of item: { name (for the shop), items: { <class>: [{ id, name, price }] },
// shared? }; a weapon also has { element } and the healer's { potion }. `shared` names the state's key for a kind whose items are bought
// once for every class: it sells the same to each, and what is owned is kept
// there, once, instead of per class.
export const SHOP = {
  armour: {
    name: "Armours",
    items: Object.fromEntries(
      CLASSES.map((c) => [c, COLOUR_NAMES[c].map(([id, name], i) => ({ id, name, price: i ? COLOUR_PRICES[i - 1] : 0 }))]),
    ),
  },
  weapon: {
    name: "Weapons",
    items: Object.fromEntries(
      CLASSES.map((c) => [
        c,
        WEAPON_NAMES[c].map(([id, name, element, potion], i) => ({ id, name, price: i ? WEAPON_PRICES[i - 1] : 0, element, ...(potion ? { potion } : {}) })),
      ]),
    ),
  },
  hat: { name: "Hats", items: Object.fromEntries(CLASSES.map((c) => [c, HATS])), shared: "hats" },
};
export const SHOP_KINDS = Object.keys(SHOP);

// Every picture a class has, as its path inside the look's folder (see
// lookArt), the weapon's (see weaponArt) and the hat's (see hatArt), without
// ".png": standing, walking, dangling, and the fighting poses (stance,
// wind-up, strike) facing each way. main.js draws them;
// tools/idle-rpg-sprites.py draws each of them in every colourway, and every
// weapon and hat to lay over each.
export const POSES = ["stance", "windup", "strike"];
export const FRAMES = ["stand", "walk/l", "walk/r", "rag/c", "rag/l", "rag/r", ...POSES.flatMap((p) => [`${p}/l`, `${p}/r`])];
const frameOf = (frame) => (FRAMES.includes(frame) ? frame : FRAMES[0]);
// The pictures each class's weapons have: all of them, but the healer's, whose
// weapon is the potion it holds up only as it winds up to throw (its staff is
// part of its body).
export const WEAPON_FRAMES = Object.fromEntries(CLASSES.map((c) => [c, c === "healer" ? ["windup/l", "windup/r"] : FRAMES]));

// What each weapon's attack looks like, per class and weapon id: { shot, hit },
// paths in art/ without ".png", "*" standing for the way it faces ("l" or "r").
// "shot" is the warrior's slash, the arrow, the spell or the thrown potion;
// "hit" is where it lands (the warrior's slash is its own hit). Every variant of
// one is the same size (see Attacks in tools/idle-rpg-sprites.py).
export const ATTACK_PARTS = ["shot", "hit"];
const ATTACK_ART = {
  wizard: {
    [DEFAULT_LOOK]: { shot: "attacks/spell/fire/*", hit: "attacks/burst/fire" },
    frost: { shot: "attacks/spell/frost/*", hit: "attacks/burst/frost" },
    storm: { shot: "attacks/spell/storm/*", hit: "attacks/burst/storm" },
    venom: { shot: "attacks/spell/poison/*", hit: "attacks/burst/poison" },
  },
  healer: Object.fromEntries(WEAPON_NAMES.healer.map(([id, , , potion]) => [id, { shot: `attacks/potion/${potion}`, hit: `attacks/splash/${potion}` }])),
  warrior: {
    [DEFAULT_LOOK]: { shot: "attacks/slash/default/*" },
    axe: { shot: "attacks/slash/heavy/*" },
    hammer: { shot: "attacks/slash/smash/*" },
    flame: { shot: "attacks/slash/flame/*" },
  },
  archer: {
    [DEFAULT_LOOK]: { shot: "attacks/arrow/default/*", hit: "status/spark" },
    crossbow: { shot: "attacks/arrow/bolt/*", hit: "status/spark" },
    flame: { shot: "attacks/arrow/fire/*", hit: "attacks/spark/fire" },
    frost: { shot: "attacks/arrow/frost/*", hit: "attacks/spark/frost" },
  },
};

// The pictures in art/ are in folders by what they show, then by what it is
// doing (see tools/idle-rpg-sprites.py). The functions here build the path,
// inside art/ and with ".png", of every picture whose name depends on the
// state or an agent (a class, a look, a hat, a monster, a character), so no
// saved string can reach a path unchecked. main.js names the rest itself.
//
// Each monster's pictures in monsters/<kind>/, without ".png": its whole
// picture ("idle", also the codex's), the eyelids laid over it ("blink"), the
// pieces that move on their own (see foe in main.js), and its roar. Every kind
// in KINDS has one.
export const MONSTER_ART = {
  slime: ["idle", "blink", "top", "base"],
  ogre: ["idle", "blink", "top", "roar/roar"],
  dragon: ["idle", "blink", "top", "body", "tail", "roar/rear", "roar/roar", "roar/top", "roar/wave"],
};

// The path in art/ of picture `part` of monster `kind` ("monsters/dragon/roar/top.png"),
// or null for a kind or a part it does not have.
export function monsterArt(kind, part = "idle") {
  return KINDS.includes(kind) && MONSTER_ART[kind].includes(part) ? `monsters/${kind}/${part}.png` : null;
}

// The settings menu (the gear in the top-right corner): one switch per entry,
// in this order, each { key, name, default }. A setting is a boolean saved under
// `settings.<key>`; adding one is adding an entry here and reading it in main.js.
export const SETTINGS = [{ key: "damageNumbers", name: "Show damage numbers", default: true }];

// The pixel font (main.js lays numbers out with it): the characters it has,
// each drawn in every one of GLYPH_COLOURS by tools/idle-rpg-sprites.py.
export const GLYPHS = "0123456789+!";
export const GLYPH_COLOURS = ["white", "gold"];
const GLYPH_NAMES = { "+": "plus", "!": "bang" };

// The path in art/ of one character of the pixel font in `colour`
// ("font/gold/7.png", "font/white/plus.png"), or null for a character or
// colour it does not have, so no other string can end up in a path.
export function glyphArt(colour, ch) {
  if (!GLYPH_COLOURS.includes(colour) || typeof ch !== "string" || ch.length !== 1 || !GLYPHS.includes(ch)) return null;
  return `font/${colour}/${GLYPH_NAMES[ch] ?? ch}.png`;
}

const MAX = Number.MAX_SAFE_INTEGER;
const MAX_MONSTER_HP = 1e6; // the most a saved monster is believed to have

// A count read back from disk: a whole number from 0 up, else 0.
function count(v) {
  return typeof v === "number" && Number.isFinite(v) && v > 0 ? Math.min(Math.floor(v), MAX) : 0;
}

function finite(v) {
  return typeof v === "number" && Number.isFinite(v);
}

function record(v) {
  return v !== null && typeof v === "object" && !Array.isArray(v);
}

// Whether `key` is `map`'s own, not something its prototype lends it.
const has = (map, key) => Object.prototype.hasOwnProperty.call(map, key);

// The own entries of a saved map whose values pass `keep`, minus any key that
// would reach the object's prototype.
function entries(map, keep) {
  if (!record(map)) return {};
  const out = {};
  for (const [k, v] of Object.entries(map)) {
    if (k === "__proto__") continue;
    const kept = keep(v);
    if (kept !== undefined) out[k] = kept;
  }
  return out;
}

const point = (p) => (record(p) && finite(p.x) && finite(p.y) ? { x: p.x, y: p.y } : undefined);

// Experience it takes to reach `level` from level 1, when going from n to n + 1
// costs `step * n`.
export function xpFor(level, step) {
  return (step * (level - 1) * level) / 2;
}

// Where `xp` total experience puts someone: { level, into, need }, where `into`
// is how far they are into this level and `need` what the whole level takes.
// No cap.
export function levelOf(xp, step) {
  const total = count(xp);
  let level = Math.max(1, Math.floor((1 + Math.sqrt(1 + (8 * total) / step)) / 2));
  // the square root can be a hair off; step to the exact level
  while (level > 1 && xpFor(level, step) > total) level -= 1;
  while (xpFor(level + 1, step) <= total) level += 1;
  return { level, into: total - xpFor(level, step), need: step * level };
}

export const classLevel = (xp) => levelOf(xp, CLASS_LEVEL_XP);
export const playerLevel = (xp) => levelOf(xp, PLAYER_LEVEL_XP);

// Gold for killing a monster with `maxHp`, rounded down.
export function goldFor(maxHp) {
  return Math.floor(count(maxHp) / HP_PER_GOLD);
}

// The HP a new monster of `kind` turns up with.
export function monsterHp(kind) {
  return MONSTER_HP[kind] ?? OLD_MONSTER_HP;
}

// A class's skill ranks with every rank at 0: { power: 0, haste: 0, crit: 0 }.
function noRanks(cls) {
  return Object.fromEntries((CLASS_SKILLS[cls] ?? []).map((k) => [k, 0]));
}

// The kinds bought once for every class, and the state's key for what of each is owned.
const SHARED = SHOP_KINDS.filter((k) => SHOP[k].shared).map((k) => [k, SHOP[k].shared]);

// A class's slot for one kind with nothing bought: { owned: [DEFAULT_LOOK],
// equipped: DEFAULT_LOOK }, or only { equipped } for a kind bought for every class.
const noSlot = (kind) => (SHOP[kind].shared ? { equipped: DEFAULT_LOOK } : { owned: [DEFAULT_LOOK], equipped: DEFAULT_LOOK });

// Every class in its default look, owning nothing else:
// { <class>: { <kind>: { owned: [DEFAULT_LOOK], equipped: DEFAULT_LOOK } | { equipped: DEFAULT_LOOK } } }.
function noLooks() {
  return Object.fromEntries(CLASSES.map((c) => [c, Object.fromEntries(SHOP_KINDS.map((k) => [k, noSlot(k)]))]));
}

// Fresh progress: what a new party starts with.
export function newProgress() {
  return {
    slain: 0,
    gold: 0,
    kills: Object.fromEntries(KINDS.map((k) => [k, 0])),
    xp: Object.fromEntries([YOU, ...CLASSES].map((k) => [k, 0])),
    skills: Object.fromEntries(CLASSES.map((c) => [c, noRanks(c)])),
    looks: noLooks(),
    ...Object.fromEntries(SHARED.map(([, key]) => [key, []])), // hats: [<id>], bought for every class
  };
}

// One rank, as a whole number from 0 to MAX_RANK (anything else is 0).
function rank(ranks, skill) {
  const r = record(ranks) ? ranks[skill] : 0;
  return typeof r === "number" && Number.isInteger(r) && r > 0 ? Math.min(r, MAX_RANK) : 0;
}

// Skill points a class has earned with `xp` experience: POINTS_PER_LEVEL for
// each level past 1.
export function pointsEarned(xp) {
  return (classLevel(xp).level - 1) * POINTS_PER_LEVEL;
}

// Skill points tied up in a class's `ranks`.
export function pointsSpent(ranks) {
  return Object.keys(record(ranks) ? ranks : {}).reduce((sum, k) => sum + rank(ranks, k) * RANK_COST, 0);
}

// A class's skill points still to spend.
export function pointsLeft(progress, cls) {
  return Math.max(0, pointsEarned(progress.xp[cls]) - pointsSpent(progress.skills[cls]));
}

// Every class's points still to spend, added up (the count on the sign).
export function pointsLeftAll(progress) {
  return CLASSES.reduce((sum, c) => sum + pointsLeft(progress, c), 0);
}

// Whether `cls` can put a point into `skill`: it is one of the class's
// skills, below MAX_RANK, and the class has the points.
export function canRaise(progress, cls, skill) {
  const ranks = progress.skills[cls];
  return CLASSES.includes(cls) && Boolean(ranks) && CLASS_SKILLS[cls].includes(skill) && rank(ranks, skill) < MAX_RANK && pointsLeft(progress, cls) >= RANK_COST;
}

// Raises `skill` one rank for `cls` if it can. Returns whether it did.
export function raise(progress, cls, skill) {
  if (!canRaise(progress, cls, skill)) return false;
  progress.skills[cls][skill] = rank(progress.skills[cls], skill) + 1;
  return true;
}

// Takes every rank off `cls`, which gets all its points back (free). Returns
// whether anything changed.
export function resetSkills(progress, cls) {
  if (!CLASSES.includes(cls) || pointsSpent(progress.skills[cls]) === 0) return false;
  progress.skills[cls] = noRanks(cls);
  return true;
}

// What each rank gives. `ranks` is a class's ranks; a missing one counts as 0.
export const damageOf = (ranks) => BASE_DAMAGE + POWER_DAMAGE * rank(ranks, "power");
export const critChanceOf = (ranks) => CRIT_CHANCE * rank(ranks, "crit");
export const attackTicksOf = (ranks) => ATTACK_TICKS[rank(ranks, "haste")];

// One blow by a character whose class has `ranks`, given a random number `r`
// from 0 up to 1: { damage, crit }. It is critical when `r` falls under the
// crit chance.
export function blow(ranks, r) {
  const crit = r < critChanceOf(ranks);
  return { damage: damageOf(ranks) * (crit ? CRIT_MULTIPLIER : 1), crit };
}

// How many ticks after one attack starts the next one does, given a random
// number `r` from 0 up to 1: the rank's gap give or take up to ATTACK_JITTER,
// evenly, and never under MIN_ATTACK_TICKS.
export function attackGap(ranks, r) {
  const base = attackTicksOf(ranks);
  const spread = Math.max(0, Math.min(ATTACK_JITTER, base - MIN_ATTACK_TICKS));
  return base - spread + Math.min(2 * spread, Math.floor(r * (2 * spread + 1)));
}

// How many ticks from now a character who has just joined the fight starts
// its first attack, given a random number `r`: anywhere in its first gap, so
// a party that starts together does not attack as one.
export function firstAttack(ranks, r) {
  const base = attackTicksOf(ranks);
  return 1 + Math.min(base - 1, Math.floor(r * base));
}

// Credits `hp` points of damage that landed, dealt by a character of class
// `cls`: experience to that class and to you. Returns the keys (the class,
// YOU) that went up a level on it, in that order.
export function credit(progress, cls, hp = 1) {
  const up = [];
  const gain = (key, by, levels) => {
    const before = levels(progress.xp[key]).level;
    progress.xp[key] = Math.min(count(progress.xp[key]) + by, MAX);
    if (levels(progress.xp[key]).level > before) up.push(key);
  };
  if (CLASSES.includes(cls)) gain(cls, hp * CLASS_XP_PER_HP, classLevel);
  gain(YOU, hp * PLAYER_XP_PER_HP, playerLevel);
  return up;
}

// Books a kill: the total, the count for its kind and the gold.
export function slay(progress, monster) {
  progress.slain = Math.min(progress.slain + 1, MAX);
  if (KINDS.includes(monster.kind)) progress.kills[monster.kind] = Math.min(progress.kills[monster.kind] + 1, MAX);
  progress.gold = Math.min(progress.gold + goldFor(monster.maxHp), MAX);
}

// What the shop sells of `kind` for class `cls`: [{ id, name, price }], the
// default first (empty for an unknown class or kind).
export function catalogue(cls, kind) {
  return (has(SHOP, kind) && CLASSES.includes(cls) && SHOP[kind].items[cls]) || [];
}

// One item of a catalogue, or undefined.
function itemOf(cls, kind, id) {
  return catalogue(cls, kind).find((it) => it.id === id);
}

// What `cls` has bought of `kind` (a known kind): the class's own list, or for
// a kind bought for every class, everyone's.
function bought(progress, cls, kind) {
  const list = SHOP[kind].shared ? progress[SHOP[kind].shared] : progress.looks?.[cls]?.[kind]?.owned;
  return Array.isArray(list) ? list : [];
}

// Whether `cls` owns item `id` of `kind`. The default always counts as owned,
// and a hat bought for any class counts for every one.
export function owns(progress, cls, kind, id) {
  if (!itemOf(cls, kind, id)) return false;
  return id === DEFAULT_LOOK || bought(progress, cls, kind).includes(id);
}

// The id of the item of `kind` that `cls` has on: the default unless it has
// put on something it owns.
export function equipped(progress, cls, kind) {
  const id = progress.looks?.[cls]?.[kind]?.equipped;
  return owns(progress, cls, kind, id) ? id : DEFAULT_LOOK;
}

// Whether `cls` can buy item `id` of `kind`: it is for sale, not owned yet,
// and the gold is there.
export function canBuy(progress, cls, kind, id) {
  const item = itemOf(cls, kind, id);
  return Boolean(item) && !owns(progress, cls, kind, id) && count(progress.gold) >= item.price;
}

// Buys item `id` of `kind` for `cls` if it can: the price comes off the gold
// and the class owns it for good (a hat, every class does). It is not put on.
// Returns whether it bought it.
export function buy(progress, cls, kind, id) {
  if (!canBuy(progress, cls, kind, id)) return false;
  progress.gold = count(progress.gold) - itemOf(cls, kind, id).price;
  const key = SHOP[kind].shared;
  if (key) {
    if (!Array.isArray(progress[key])) progress[key] = [];
    progress[key].push(id);
  } else {
    const slot = (((progress.looks ??= {})[cls] ??= {})[kind] ??= noSlot(kind));
    slot.owned.push(id);
  }
  return true;
}

// Puts item `id` of `kind` on `cls`, free, if the class owns it and does not
// have it on already. Returns whether anything changed.
export function equip(progress, cls, kind, id) {
  if (!owns(progress, cls, kind, id) || equipped(progress, cls, kind) === id) return false;
  (((progress.looks ??= {})[cls] ??= {})[kind] ??= noSlot(kind)).equipped = id; // a hat bought for another class may find no slot
  return true;
}

// The path in art/ of class `cls`'s picture `frame` (one of FRAMES) in
// colourway `colour`: classes/<class>/<look>/<frame>.png, where <look> is
// "default" or the colourway's id ("classes/wizard/crimson/walk/l.png").
// Anything that is not one of the class's colourways gets the default, an
// unknown class the first one and an unknown frame the first, standing, so no
// other string can end up in a path.
export function lookArt(cls, colour, frame = FRAMES[0]) {
  const c = CLASSES.includes(cls) ? cls : CLASSES[0];
  const look = colour !== DEFAULT_LOOK && itemOf(c, "armour", colour) ? colour : DEFAULT_LOOK;
  return `classes/${c}/${look}/${frameOf(frame)}.png`;
}

// The id of `cls`'s weapon `weapon` if it is one of the class's (an unknown
// class counts as the first), else the default.
function weaponOf(cls, weapon) {
  const c = CLASSES.includes(cls) ? cls : CLASSES[0];
  return [c, itemOf(c, "weapon", weapon) ? weapon : DEFAULT_LOOK];
}

// The path in art/ of weapon `weapon`'s picture `frame` for class `cls`:
// weapons/<class>/<weapon>/<frame>.png ("weapons/warrior/axe/walk/l.png"),
// laid over the class's picture of the same frame at the same size and under
// its hat. Anything that is not one of the class's weapons gets its default
// (a class always holds one), an unknown class or frame the first, as in
// lookArt, so no other string can end up in a path. Null for a picture the
// weapon has none for (WEAPON_FRAMES): the healer's potion shows only as it
// winds up.
export function weaponArt(cls, weapon, frame = FRAMES[0]) {
  const [c, w] = weaponOf(cls, weapon);
  const f = frameOf(frame);
  return WEAPON_FRAMES[c].includes(f) ? `weapons/${c}/${w}/${f}.png` : null;
}

// The path in art/ of the picture for `part` (one of ATTACK_PARTS) of an
// attack by class `cls` with weapon `weapon`, facing `side` ("l" or "r"; for
// those that face a way): "attacks/arrow/fire/r.png". The weapon and class are
// checked as in weaponArt, any side but "l" is "r", and a part the attack does
// not have (the warrior's "hit") is null.
export function attackArt(cls, weapon, part, side = "r") {
  const [c, w] = weaponOf(cls, weapon);
  const art = ATTACK_PARTS.includes(part) ? ATTACK_ART[c][w]?.[part] : undefined;
  return art ? `${art.replace("*", side === "l" ? "l" : "r")}.png` : null;
}

// The path in art/ of hat `hat`'s picture `frame` for class `cls`:
// hats/<hat>/<class>/<frame>.png ("hats/party/wizard/walk/l.png"), laid over
// the class's picture of the same frame at the same size. Null for no hat:
// the default, or anything that is not a hat for sale, so no other string can
// end up in a path (an unknown class or frame gets the first, as in lookArt).
export function hatArt(cls, hat, frame = FRAMES[0]) {
  const c = CLASSES.includes(cls) ? cls : CLASSES[0];
  return hat !== DEFAULT_LOOK && itemOf(c, "hat", hat) ? `hats/${hat}/${c}/${frameOf(frame)}.png` : null;
}

// The ids of `items` after the default that a saved list holds, in
// catalogue order, each once; nothing else.
function kept(list, items) {
  const saved = Array.isArray(list) ? list : [];
  return items.map((it) => it.id).filter((id) => id !== DEFAULT_LOOK && saved.includes(id));
}

// The version that first sold weapons: state saved before it owns and holds
// only each class's default weapon, whatever it says, since nothing else could
// have been bought.
const WEAPONS_SINCE = 5;

// A class's saved looks, from state saved by version `version`: per kind, the
// items it owns, in catalogue order with the default always among them and
// anything unknown or repeated dropped, and the one it has on, which falls
// back to the default if it is not owned. A kind bought for every class keeps
// only the one on, checked against `shared`, what everyone owns ({ hats:
// [<id>] }, already checked).
function looksOf(saved, cls, shared, version) {
  return Object.fromEntries(
    SHOP_KINDS.map((kind) => {
      // armours were first saved as "colour"
      const key = record(saved) && !has(saved, kind) && kind === "armour" ? "colour" : kind;
      const sold = kind !== "weapon" || version >= WEAPONS_SINCE;
      const slot = sold && record(saved) && has(saved, key) && record(saved[key]) ? saved[key] : {};
      // the default always, also for a kind with nothing for sale yet
      const owned = [DEFAULT_LOOK, ...(SHOP[kind].shared ? shared[SHOP[kind].shared] : kept(slot.owned, catalogue(cls, kind)))];
      const on = owned.includes(slot.equipped) ? slot.equipped : DEFAULT_LOOK;
      return [kind, SHOP[kind].shared ? { equipped: on } : { owned, equipped: on }];
    }),
  );
}

// The saved settings: every one of SETTINGS, its saved value if that is a
// boolean, else its default. Anything else saved there is dropped.
export function settingsOf(saved) {
  return Object.fromEntries(SETTINGS.map(({ key, default: on }) => [key, record(saved) && has(saved, key) && typeof saved[key] === "boolean" ? saved[key] : on]));
}

// The saved monster, or null if it is not one: { kind, hp, maxHp, id, slainAt? }.
// An absurd max HP is cut down, and a time of death in the future is brought
// back to now, so neither can leave a monster that never falls or never leaves.
function monsterOf(m, now) {
  if (!record(m) || !KINDS.includes(m.kind)) return null;
  const maxHp = Math.min(count(m.maxHp) || OLD_MONSTER_HP, MAX_MONSTER_HP);
  const out = { kind: m.kind, hp: Math.min(count(m.hp), maxHp), maxHp, id: count(m.id) };
  if (finite(m.slainAt)) out.slainAt = Math.max(0, Math.min(m.slainAt, now));
  return out;
}

// A class's saved skill ranks, given its experience `xp`. Each rank must be a
// whole number from 0 to MAX_RANK, else it is 0. Ranks that would cost more
// points than the class has earned cannot have been bought: the class gets
// all its points back instead.
function ranksOf(saved, cls, xp) {
  const ranks = Object.fromEntries((CLASS_SKILLS[cls] ?? []).map((k) => {
    const r = record(saved) ? saved[k] : 0;
    return [k, typeof r === "number" && Number.isInteger(r) && r >= 0 && r <= MAX_RANK ? r : 0];
  }));
  return pointsSpent(ranks) > pointsEarned(xp) ? noRanks(cls) : ranks;
}

// The saved state as this version keeps it, from whatever was read back:
// older versions without the progress fields, skill ranks, looks, weapons,
// hats or settings, or anything malformed. Never throws; a bad field falls back to
// its default, a bad entry is dropped.
//
// State written by a later version keeps its version number: this version can
// read what it knows of it, but must not save over it (see save in main.js),
// since it would drop whatever it does not know.
export function loadState(saved, now = Date.now()) {
  const s = record(saved) ? saved : {};
  const fresh = newProgress();
  const xp = Object.fromEntries(Object.keys(fresh.xp).map((k) => [k, count(record(s.xp) ? s.xp[k] : 0)]));
  // version 3 and before sold no hats: none owned. Every class sells the same
  // hats, so the first class's catalogue checks them.
  const shared = Object.fromEntries(SHARED.map(([kind, key]) => [key, kept(has(s, key) ? s[key] : undefined, catalogue(CLASSES[0], kind))]));
  return {
    version: Math.max(STATE_VERSION, count(s.version)),
    you: point(s.you) ?? { x: 154, y: 16 },
    spots: entries(s.spots, point),
    sprites: entries(s.sprites, (c) => (CLASSES.includes(c) ? c : undefined)),
    seen: entries(s.seen, (t) => (finite(t) ? t : undefined)),
    battle: typeof s.battle === "boolean" ? s.battle : true,
    monster: monsterOf(s.monster, now),
    // `slain` predates the counts by kind, which start from zero
    slain: count(s.slain),
    gold: count(s.gold),
    kills: Object.fromEntries(KINDS.map((k) => [k, count(record(s.kills) ? s.kills[k] : 0)])),
    xp,
    // version 1 had no skills: every rank starts at 0
    skills: Object.fromEntries(CLASSES.map((c) => [c, ranksOf(record(s.skills) ? s.skills[c] : undefined, c, xp[c])])),
    // versions 1 and 2 had no shop: every class owns and wears its default;
    // versions 1 to 4 sold no weapons: every class owns and holds its default
    looks: Object.fromEntries(CLASSES.map((c) => [c, looksOf(record(s.looks) && has(s.looks, c) ? s.looks[c] : undefined, c, shared, count(s.version))])),
    ...shared, // hats: [<id>], owned by every class
    // versions 1 to 3 had no settings: every one starts at its default
    settings: settingsOf(s.settings),
  };
}
