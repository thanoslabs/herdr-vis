// Idle RPG's game rules: experience, levels, gold, kill counts, and loading the
// saved state. Plain functions with no host calls, so main.js does the drawing
// and these can be run on their own.
//
// Progress never belongs to an agent (agents come and go): it belongs to you
// and to the four classes. Every point of damage that lands earns experience
// for the class of whoever dealt it, and for you, who leads the raid. Killing a
// monster earns gold and counts towards its kind. Levels are worked out from
// total experience, never stored.

export const CLASSES = ["wizard", "healer", "warrior", "archer"];
export const KINDS = ["slime", "ogre", "dragon"]; // the keys of MONSTERS in main.js
export const YOU = "you"; // the person's key in `sprites`, `xp` and as an open card
export const STATE_VERSION = 1;
export const MONSTER_HP = 100; // every kind, for now; kept on each monster as `maxHp`

// Defaults chosen to be retuned; nothing else depends on their values.
export const CLASS_XP_PER_HP = 1; // to a class, per point of damage one of its characters deals
export const PLAYER_XP_PER_HP = 1; // to you, per point of damage anyone in the party deals
export const CLASS_LEVEL_XP = 100; // a class goes from level n to n + 1 for CLASS_LEVEL_XP * n
export const PLAYER_LEVEL_XP = 250; // you go from level n to n + 1 for PLAYER_LEVEL_XP * n
export const HP_PER_GOLD = 100; // gold on a kill: one per this much of the monster's max HP

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

// Fresh progress: what a new party starts with.
export function newProgress() {
  return {
    slain: 0,
    gold: 0,
    kills: Object.fromEntries(KINDS.map((k) => [k, 0])),
    xp: Object.fromEntries([YOU, ...CLASSES].map((k) => [k, 0])),
  };
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

// The saved monster, or null if it is not one: { kind, hp, maxHp, id, slainAt? }.
// An absurd max HP is cut down, and a time of death in the future is brought
// back to now, so neither can leave a monster that never falls or never leaves.
function monsterOf(m, now) {
  if (!record(m) || !KINDS.includes(m.kind)) return null;
  const maxHp = Math.min(count(m.maxHp) || MONSTER_HP, MAX_MONSTER_HP);
  const out = { kind: m.kind, hp: Math.min(count(m.hp), maxHp), maxHp, id: count(m.id) };
  if (finite(m.slainAt)) out.slainAt = Math.max(0, Math.min(m.slainAt, now));
  return out;
}

// The saved state as this version keeps it, from whatever was read back:
// older versions without the progress fields, or anything malformed. Never
// throws; a bad field falls back to its default, a bad entry is dropped.
//
// State written by a later version keeps its version number: this version can
// read what it knows of it, but must not save over it (see save in main.js),
// since it would drop whatever it does not know.
export function loadState(saved, now = Date.now()) {
  const s = record(saved) ? saved : {};
  const fresh = newProgress();
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
    xp: Object.fromEntries(Object.keys(fresh.xp).map((k) => [k, count(record(s.xp) ? s.xp[k] : 0)])),
  };
}
