// Idle RPG: a castle rampart under a moving sky (drifting clouds, and a day
// and a night every 20 minutes), staffed by a small adventuring party. You and
// every agent are one of four classes: wizard, healer, warrior or archer. The
// class is picked at random the first time someone appears and is remembered.
// What an agent is doing shows its status:
//   working  bounces, with two swords clashing overhead
//   blocked  a red "!" bubble that hops (it needs you)
//   done     a green tick bubble (finished while you weren't looking)
//   idle     resting, with z's drifting up
// Click the floor: you walk there. Click anyone: a card with their portrait and
// status; the wrench on the portrait shows the classes to choose from. Press
// and drag an agent: it dangles from the
// pointer; let go to drop it where it is (it falls to the floor). Spots and
// classes are remembered.
// Battle mode (the Start Raid / End Raid button by the sign): a random monster stands in the middle
// (a slime has 100 HP, an ogre 300, a dragon 500) and the party forms up
// around it, warriors up close and everyone else at range. Every working agent
// attacks in its own way (sword swing, arrow, fireball, thrown potion) on its
// own rhythm, every 3 seconds or less; when the monster falls another one
// turns up. Turning it off sends everyone back to their spots.
// Progress (rules.js): every point of damage that lands earns experience for
// the attacker's class and for you; a kill earns gold. Each class level earns
// that class a skill point, spent in the skills panel on Power (damage),
// Haste (attack speed) or Crit (double damage now and then). Levels show on
// the cards and the class choices, gold, kills and points to spend on the sign.
// Gold buys colourways for a class in the shop (the coin on the sign); everyone
// with that class on wears the one it has equipped.
// Layout props: { inset } = left edge of the sign (84 leaves room for macOS buttons).

import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { agents, props, run, setShared, shared, spaces } from "herdr";
import {
  ATTACK_PHASES,
  CLASSES,
  CLASS_SKILLS,
  MAX_RANK,
  SHOP,
  SHOP_KINDS,
  STATE_VERSION,
  TICK_STEP,
  YOU,
  attackGap,
  attackTicksOf,
  blow,
  buy,
  canBuy,
  canRaise,
  catalogue,
  classLevel,
  credit,
  critChanceOf,
  damageOf,
  equip,
  equipped,
  firstAttack,
  loadState,
  lookArt,
  monsterHp,
  owns,
  playerLevel,
  pointsEarned,
  pointsLeft,
  pointsLeftAll,
  pointsSpent,
  raise,
  resetSkills,
  slay,
} from "./rules.js";

const ART = "mods/idle-rpg/art";
// shared: { version, you: {x, y}, spots: { <address>: {x, y} }, sprites: { you | <address>: <class> },
//   seen, battle, monster, slain, gold, kills: { <kind>: n }, xp: { you | <class>: n },
//   skills: { <class>: { power, haste, crit } },
//   looks: { <class>: { armour | weapon | hat: { owned: [<id>], equipped: <id> } } } } (see loadState)
const STATE = "idle-rpg.state";
const randomClass = () => CLASSES[Math.floor(Math.random() * CLASSES.length)];
const STATUS = {
  working: ["Working", "#ffd166"],
  blocked: ["Needs you", "#ff7b7b"],
  done: ["Finished", "#6fdc9a"],
  idle: ["Resting", "#9fb4cc"],
};

// The scene's own paint (it is a picture, so it keeps its colours in any theme).
const NIGHT = "#0b1230";
const DAY = "#6db6ee";
const DUSK = "#f2924e";
const TINT = "#0a1030"; // laid over the scenery at night
const FLOOR = "#b9834f";
const INK = "#1b2233";
const CREAM = "#f4ecd8";

// The floor is a fixed band along the bottom. Everyone's position is where their
// feet are, in floor coordinates: x from the left, y down from the top of the floor.
const FLOOR_H = 152;
const WALL_H = 64; // the battlements, standing on the floor's back edge
const CYCLE_MS = 20 * 60 * 1000; // one day and one night
const TICK_MS = 10000; // how often the sky moves on; everything glides between ticks
// Clouds: art, size, how far up the sky (0 the wall top, 1 the ceiling), speed
// in px/s, head start in px.
const CLOUDS = [
  { art: "a", w: 96, h: 28, up: 0.7, speed: 9, off: 0 },
  { art: "b", w: 64, h: 20, up: 0.45, speed: 6, off: 520 },
  { art: "a", w: 96, h: 28, up: 0.25, speed: 12, off: 930 },
  { art: "b", w: 64, h: 20, up: 0.9, speed: 7.5, off: 1410 },
];
const CELL_W = 88;
const YOU_Y = [12, FLOOR_H - 24];
const CRITTER_Y = [16, FLOOR_H - 42];
const CARD_W = 232;
const SHOP_NAV_W = 78; // the kinds of item down the shop's left side
const SHOP_ITEM_H = 78; // one thing for sale: picture, name, button
const SHOP_ICONS = { armour: "i-armour", weapon: "sword-l", hat: "i-hat" };
// Battle mode. Sizes are on-screen px (art px x 4, plus the outline). A new
// kind also needs its HP in MONSTER_HP in rules.js, which lists the kinds.
const MONSTERS = {
  slime: { name: "Slime", w: 136, h: 104, core: { x: 0, y: 44, r: 18, half: 60 } },
  ogre: { name: "Ogre", w: 200, h: 200, core: { x: 0, y: 86, r: 24, half: 62 } },
  dragon: { name: "Dragon", w: 328, h: 264, core: { x: 12, y: 74, r: 26, half: 84 } },
};
// `core` is the middle of the monster's bulk, where blows land: px right of
// its centre line and above its feet, how far a blow may stray from it, and
// half the bulk's width, which is how close a warrior stands. The picture is
// often much wider than that (the dragon's head, wings and tail).
const WATCH_MS = 1000; // how often to look for a monster due, or someone ready to attack
const RESPAWN_MS = 9000; // how long a fallen monster lies there before the next
const MONSTER_Y = 108; // where its feet are on the floor
const BAR_W = 120;
const MELEE = 90; // how close to the monster's bulk a warrior must be to reach it
const SWORD = 44; // how far outside the bulk a warrior stands, so the swing lands on it
const RANGE = 360; // how far the ranged classes stand from the monster: five characters
// An attack plays in phases, one TICK_STEP each: 1 is the wind-up, 2 and 3 the
// two halves of the strike or flight, 4 (ATTACK_PHASES) the impact, 0 rest.
// Each attacker keeps its own rhythm (see tick), so the party does not move as one.
const FLIGHT = TICK_STEP * 2;
const POP_FADE = 350; // an impact fades out this long; rules.js counts on it being under two ticks
const BLINK_MS = 5200; // monsters blink this often
const ROAR_MS = 14000; // and the ogre roars this often
const MOVE = { duration: 700, easing: "ease-in-out" }; // walking between spots and the formation
const CHEER_MS = 2400; // a level-up note over someone's head rises and fades this long
const CRIT_MS = 1200; // a critical blow's number rises and fades this long
// What a class's skill ranks give, in words, for the skills panel.
const SKILL_TEXT = {
  power: (ranks) => `${damageOf(ranks)} damage`,
  haste: (ranks) => `attacks every ${(attackTicksOf(ranks) * TICK_STEP) / 1000}s`,
  crit: (ranks) => `${Math.round(critChanceOf(ranks) * 100)}% crit`,
};
const GOLD = "#ffd166";

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

const capital = (word) => (typeof word === "string" && word ? word[0].toUpperCase() + word.slice(1) : "");

// The sign's counts of agents by status, as [icon, w, h, n], skipping zeros.
function tally(list) {
  const n = (st) => list.filter((a) => a.status === st).length;
  return [
    ["alert", 18, 20, n("blocked")],
    ["i-swords", 18, 18, n("working")],
    ["done", 18, 20, n("done")],
    ["i-sleep", 18, 18, n("idle")],
  ].filter((t) => t[3] > 0);
}

function ago(ms) {
  if (!ms) return "";
  const s = Math.max(0, Math.round((Date.now() - ms) / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

export default class RaidParty extends View {
  init(_props, cx) {
    // the later keys are this layout's earlier names, so a rename keeps what was saved
    const read = [STATE, "raid-party.state", "rpg.state", "snow-loft.state"].map((key) => shared(key)).find((v) => v && typeof v === "object");
    let saved;
    try {
      saved = loadState(read);
    } catch {
      saved = loadState(undefined); // only a live object another mod shared could get here
    }
    // State from a later version of this mod is read, never written: saving
    // would drop what this version does not know. Progress then lasts only
    // until the layout is closed.
    this.readOnly = saved.version > STATE_VERSION;
    this.now = Date.now();
    cx.timer.every(TICK_MS, (cx) => {
      this.now = Date.now();
      cx.notify();
    });
    this.size = { width: 900, height: 360 };
    this.wallH = 210; // the wall's height, learned from pointer events
    this.you = saved.you;
    this.spots = saved.spots;
    this.sprites = saved.sprites;
    this.seen = saved.seen; // <address>: when it was last here
    this.battle = saved.battle;
    this.monster = saved.monster; // { kind, hp, maxHp, id, slainAt? }
    this.progress = { slain: saved.slain, gold: saved.gold, kills: saved.kills, xp: saved.xp, skills: saved.skills, looks: saved.looks };
    this.cheerSeq = 0;
    // These three are keyed by address, so they have no prototype to collide with.
    this.cheers = Object.create(null); // YOU | <address>: { lines, id, at } while a level-up note shows
    this.crits = Object.create(null); // YOU | <address>: { n, seed, id, at } while a critical blow's number shows
    // The attack clock (see tick), in memory only: TICK_STEPs counted since the
    // view started, and each attacker's rhythm, { start, next, seed }: the tick
    // its attack in progress started (null between attacks), the tick the next
    // one is due, and the start of the latest, which places its blow.
    this.clock = 0;
    this.rhythm = Object.create(null);
    this.ticking = false; // whether the clock is running
    this.blink = false;
    this.roar = false;
    // A blink and a roar are each two renders: on, then off a moment later.
    const flick = (key, ms, ok) => (cx) => {
      if (!this.fighting || !(this.monster?.hp > 0) || !ok()) return;
      this[key] = true;
      cx.notify();
      cx.timer.after(ms, (cx) => {
        this[key] = false;
        cx.notify();
      });
    };
    cx.timer.every(BLINK_MS, flick("blink", 170, () => !this.roar));
    cx.timer.every(ROAR_MS, flick("roar", 1100, () => this.monster.kind === "ogre"));
    cx.timer.every(WATCH_MS, (cx) => {
      // nothing happens while the scene is too narrow to show the fight
      if (!this.battle || Math.max(320, this.size.width) < 640) return;
      if (this.fight()) cx.notify(); // a new monster walked in
      this.wake(cx);
    });
    if (!CLASSES.includes(this.sprites[YOU])) {
      this.sprites[YOU] = randomClass();
      this.save();
    }
    this.press = null; // { kind: "floor" | "critter" | YOU, address?, px, py }
    this.drag = null; // { address, x, y, vx, last } while a critter dangles
    this.card = null; // whose card is open: an agent's address, or YOU
    this.codex = false; // the list of kills by kind is open under the sign
    this.skillsOpen = null; // the class the skills panel under the sign shows, while it is open
    this.shopOpen = null; // the class the shop under the sign shows, while it is open
    this.shopKind = SHOP_KINDS[0]; // the kind of item it shows: the one picked down its left side
    this.picking = false; // the open card is showing the class choices
    this.walking = false;
    this.walkTask = null;
  }

  // Combat is only saved on a kill, so a fight in progress is saved once more
  // as the layout goes (switching layouts, or quitting, when the host allows
  // it the time).
  close() {
    this.save();
  }

  // Agents can be missing for a while (the app just started, a machine is
  // offline), so one is only forgotten after a week away.
  save() {
    if (this.readOnly) return;
    const old = Date.now() - 7 * 24 * 3600 * 1000;
    for (const k of Object.keys(this.seen)) {
      if (this.seen[k] >= old) continue;
      delete this.seen[k];
      delete this.spots[k];
      delete this.sprites[k];
    }
    setShared(STATE, {
      version: STATE_VERSION,
      you: this.you,
      spots: this.spots,
      sprites: this.sprites,
      seen: this.seen,
      battle: this.battle,
      monster: this.monster,
      ...this.progress,
    });
  }

  // Brings in a monster if one is due, otherwise lands `blows` on the one
  // there, in order: each { key, damage, crit, seed } (see blow in rules.js).
  // Only damage that lands earns experience: a monster with 3 HP left takes 3
  // of a 4-point blow, and nothing of the blows after it. Returns whether
  // anything changed. HP and experience are saved only on a kill (and the
  // spawn): saving re-renders every mod in the window, so not on hits. What a
  // fight earns since the last kill is lost if the app closes mid-fight.
  fight(blows = []) {
    if (!this.battle) return false;
    const m = this.monster;
    if (!m || !MONSTERS[m.kind] || (m.hp <= 0 && Date.now() - (m.slainAt ?? 0) >= RESPAWN_MS)) {
      const kinds = Object.keys(MONSTERS).filter((k) => k !== m?.kind);
      const kind = kinds[Math.floor(Math.random() * kinds.length)];
      this.monster = { kind, hp: monsterHp(kind), maxHp: monsterHp(kind), id: (m?.id ?? 0) + 1 };
      this.save();
      return true;
    }
    // no blow lands while the scene is too narrow to show the fight
    if (Math.max(320, this.size.width) < 640) return false;
    let landed = false;
    for (const { key, damage, crit, seed } of blows) {
      if (m.hp <= 0) break;
      const dealt = Math.min(damage, m.hp);
      m.hp -= dealt;
      landed = true;
      if (crit) this.crits[key] = { n: damage, seed, id: (this.cheerSeq += 1), at: Date.now() };
      for (const up of credit(this.progress, this.sprites[key], dealt)) {
        // a class's level-up shows over whoever earned it, yours over you
        if (up === YOU) this.cheer(YOU, `Level ${playerLevel(this.progress.xp[YOU]).level}`);
        else this.cheer(key, `${capital(up)} ${classLevel(this.progress.xp[up]).level}`);
      }
    }
    if (!landed) return false;
    if (m.hp === 0) {
      m.slainAt = Date.now();
      slay(this.progress, m);
      this.save();
    }
    return true;
  }

  // Shows a short note over someone's head (see cheerNote). Level-ups from the
  // same blow share one note.
  cheer(key, line) {
    const c = this.cheers[key];
    if (c && Date.now() - c.at < TICK_STEP / 2) c.lines.push(line);
    else this.cheers[key] = { lines: [line], id: (this.cheerSeq += 1), at: Date.now() };
  }

  // Whether you join in when the party attacks: the ranged classes from
  // wherever you stand, a warrior only from beside the monster.
  joins(W) {
    const kind = MONSTERS[this.monster?.kind];
    if (!this.fighting || !kind || !(this.monster.hp > 0)) return false;
    return this.sprites[YOU] !== "warrior" || Math.abs(this.you.x - (W / 2 + kind.core.x)) - kind.core.half <= MELEE;
  }

  // Who attacks now: every working agent, and you alongside them if you can
  // reach (see joins). Nobody while battle mode is off, the scene is too
  // narrow to show the fight, or the monster is down.
  attackers() {
    const W = Math.max(320, this.size.width);
    if (!this.battle || W < 640 || !MONSTERS[this.monster?.kind] || !(this.monster.hp > 0)) return [];
    const keys = agents()
      .filter((a) => a.status === "working")
      .map((a) => a.address);
    // you fight alongside them, once you have arrived: `you` is already the
    // spot you are walking to
    if (keys.length && !this.walking && this.joins(W)) keys.push(YOU);
    return keys;
  }

  // The skill ranks of the class someone has on (undefined counts as all 0).
  ranksOf(key) {
    return this.progress.skills[this.sprites[key]];
  }

  // The path of one of class `cls`'s pictures in the colourway it has
  // equipped, or in `colour` (the shop's previews). `frame` is what follows
  // the name, one of FRAMES in rules.js: "" standing, "-walk-l", "-f-r" and so on.
  look(cls, frame = "", colour = equipped(this.progress, cls, "armour")) {
    return `${ART}/${lookArt(cls, colour)}${frame}.png`;
  }

  // Starts the attack clock if it is stopped and anyone is ready to attack.
  // It runs one tick every TICK_STEP for as long as tick() says, so only one
  // chain of timers is ever running; one that fails stops, and the watch
  // starts it again.
  wake(cx) {
    if (this.ticking || !this.attackers().length) return;
    this.ticking = true;
    const next = (cx) => {
      let more = false;
      try {
        more = this.tick(cx);
      } finally {
        if (more) cx.timer.after(TICK_STEP, next);
        else this.ticking = false;
      }
    };
    cx.timer.after(TICK_STEP, next);
  }

  // One tick of the attack clock. Each attacker keeps its own rhythm: someone
  // who joins starts somewhere in their first gap, and each attack starts the
  // next one's countdown (attackGap: their class's Haste, give or take a tick
  // or two, so nobody falls into step). An attack runs ATTACK_PHASES ticks,
  // then one of rest; its blow lands on the last phase. Whoever stops
  // attacking (stops working, walks out of reach, the monster falls) loses
  // their rhythm. Re-renders only while someone is mid-attack or something
  // changed. Returns whether to keep ticking: not once nobody is attacking.
  tick(cx) {
    const t = (this.clock += 1);
    const keys = this.attackers();
    let changed = false;
    for (const key of Object.keys(this.rhythm)) {
      if (keys.includes(key)) continue;
      if (this.rhythm[key].start !== null) changed = true; // cut off mid-attack: draw them at rest
      delete this.rhythm[key];
    }
    for (const key of keys) {
      const ranks = this.ranksOf(key);
      const r = (this.rhythm[key] ??= { start: null, next: t + firstAttack(ranks, Math.random()), seed: 0 });
      if (r.start !== null && t - r.start > ATTACK_PHASES) r.start = null; // its rest has been drawn
      if (r.start === null && t >= r.next) {
        r.start = r.seed = t;
        r.next = t + attackGap(ranks, Math.random());
      }
    }
    const blows = keys
      .filter((key) => this.phaseOf(key) === ATTACK_PHASES)
      .map((key) => ({ key, seed: this.rhythm[key].seed, ...blow(this.ranksOf(key), Math.random()) }));
    if (blows.length && this.fight(blows)) changed = true;
    if (changed || keys.some((key) => this.rhythm[key].start !== null)) cx.notify();
    return keys.length > 0;
  }

  // A number from 0 to n - 1 for one attacker's attack that started on tick
  // `seed`: the same all through the attack, different on the next.
  roll(key, seed, salt, n) {
    let h = 2166136261 ^ Math.imul(seed + 1, 40503) ^ Math.imul(salt, 2246822519);
    for (const ch of String(key)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
    // stir it, so that keys one character apart land far apart
    h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    return ((h ^ (h >>> 16)) >>> 0) % n;
  }

  // Which phase of its attack someone is in right now.
  phaseOf(key) {
    const r = this.rhythm[key];
    const k = r && r.start !== null ? this.clock - r.start : -1;
    return k >= 0 && k < ATTACK_PHASES ? k + 1 : 0;
  }

  // Where the blow of someone's attack that started on tick `seed` lands:
  // around the middle of the monster's bulk, a little different each attack.
  hitOf(key, seed, W, kind) {
    const { x, y, r } = kind.core;
    return {
      x: Math.round(W / 2 + x + this.roll(key, seed, 2, 2 * r + 1) - r),
      y: Math.round(MONSTER_Y - y + this.roll(key, seed, 3, r + 1) - r / 2),
    };
  }

  // Where everyone stands for the fight: warriors beside the monster, the
  // others RANGE away (less if the scene is narrow), alternating sides.
  formation(list, W, kind) {
    const mid = Math.round(W / 2);
    const half = kind.w / 2;
    const reach = Math.max(110, Math.min(RANGE, mid - half - 60));
    const rows = [96, 60]; // each next one on a side stands a step further out, staggered
    const spots = {};
    const count = { melee: 0, ranged: 0 };
    for (const a of list) {
      const melee = this.sprites[a.address] === "warrior";
      const i = melee ? count.melee++ : count.ranged++;
      const side = i % 2 ? 1 : -1; // left first
      const n = Math.floor(i / 2);
      // Warriors close on the bulk itself and stand a little in front of the
      // monster, so its picture does not hide them; the rest keep their range.
      const x = melee ? mid + kind.core.x + side * (kind.core.half + SWORD + n * 62) : mid + side * (half + reach + n * 62);
      spots[a.address] = {
        x: Math.round(clamp(x, 36, W - 36)),
        y: melee ? MONSTER_Y + 6 : clamp(rows[n % rows.length], CRITTER_Y[0], CRITTER_Y[1] + 12),
        dir: -side, // which way the monster is
      };
    }
    return spots;
  }

  // What flies and lands for one agent's attack (the sprite itself strikes the
  // pose, see critter). Things that fly sit hidden at the hand, glide to the
  // monster during phases 2 and 3, then vanish and slip back unseen; the impact
  // pops in at phase 4 and fades.
  // `who` is { key, cls, x, y, dir }: an agent in formation, or you.
  attack(who, W, kind) {
    const s = who;
    const c = who.cls;
    const d = who.dir;
    const side = d > 0 ? "r" : "l";
    const phase = this.phaseOf(who.key);
    const flying = phase === 2 || phase === 3;
    const hit = this.hitOf(who.key, this.rhythm[who.key]?.seed ?? 0, W, kind);
    const art = (name, w, h) => image(`${ART}/${name}.png`).w(w).h(h);
    const pop = (id, name, w, h, at, on) =>
      div()
        .id(`idle-rpg-${id}-${who.key}`)
        .absolute()
        .left(at.x - w / 2)
        .top(at.y - h / 2)
        .opacity(on ? 1 : 0)
        .transition("opacity", { duration: on ? 20 : POP_FADE, easing: "ease-out" })
        .child(art(name, w, h));
    const shot = (name, w, h, hand, inner = (el) => el) =>
      div()
        .id(`idle-rpg-shot-${who.key}`)
        .absolute()
        .left((flying ? hit.x : hand.x) - w / 2)
        .top((flying ? hit.y : hand.y) - h / 2)
        .opacity(flying ? 1 : 0)
        .transition("left", { duration: FLIGHT, easing: "linear" })
        .transition("top", { duration: FLIGHT, easing: "linear" })
        .child(inner(div().relative()).child(art(name, w, h)));
    const from = (dx, dy) => ({ x: s.x + d * dx, y: s.y - dy });

    // the warrior swings its own sword; only the slash is extra
    if (c === "warrior") return [pop("slash", `slash-${side}`, 32, 44, from(62, 24), phase === 2)];
    if (c === "archer") return [shot(`arrow-${side}`, 44, 20, from(40, 22)), pop("hit", "spark", 20, 20, hit, phase === 4)];
    if (c === "wizard") return [shot(`fireball-${side}`, 40, 32, from(46, 26)), pop("hit", "burst", 44, 44, hit, phase === 4)];
    // healer: the potion is lobbed, rising for the first half and falling for the second
    const lob = (el) =>
      el
        .id(`idle-rpg-lob-${who.key}`)
        .top(phase === 2 ? -44 : 0)
        .transition("top", { duration: FLIGHT / 2, easing: phase === 2 ? "ease-out" : "ease-in" });
    return [shot("potion", 28, 36, from(24, 40), lob), pop("hit", "splash", 52, 32, hit, phase === 4)];
  }

  // The monster and its health bar. `hits` is how many agents are attacking it.
  foe(W, hits) {
    const m = this.monster;
    const kind = m && MONSTERS[m.kind];
    if (!this.battle || !kind || W < 640) return [];
    const left = Math.round(W / 2 - kind.w / 2);
    const top = MONSTER_Y - kind.h + 4;
    const dead = m.hp <= 0;
    const hurt = hits > 0 && !dead;
    const roaring = m.kind === "ogre" && this.roar;
    const lids = this.blink && !dead && !roaring;
    // one piece of the monster's art, laid over the whole picture's box
    const layer = (part) =>
      div()
        .absolute()
        .left(0)
        .top(0)
        .child(image(`${ART}/monster-${m.kind}${part ? `-${part}` : ""}.png`).w(kind.w).h(kind.h));
    const tone = m.hp > m.maxHp / 2 ? "#4cd47b" : m.hp > m.maxHp / 5 ? "#ffd166" : "#ff5d5d";
    return [
      div()
        .id(`idle-rpg-monster-${m.id}`)
        .absolute()
        .left(left)
        .top(top)
        .opacity(dead ? 0 : 1)
        .transition("opacity", { duration: 1600, easing: "ease-in" })
        .child(
          div()
            .id(`idle-rpg-monster-body-${m.id}`)
            .relative()
            .w(kind.w)
            .h(kind.h)
            // It recoils a little when a blow lands. Otherwise each monster
            // is a still picture with pieces that move over or behind it, so
            // nothing ever shows through: the slime's dome sinks into its foot
            // and rises, the dragon's tail sways behind its body, and the ogre
            // and dragon breathe with their upper body while the feet stay
            // planted. The ogre now and then roars, and all blink.
            .top(this.struck && hurt ? -4 : 0)
            .transition("top", { duration: 90, easing: "ease-out" })
            .when(m.kind === "dragon", (el) => el.child(layer("tail").loop("top", { from: 0, to: 5, period: 2600 })))
            .child(layer(roaring ? "2" : m.kind === "slime" ? "base" : m.kind === "dragon" ? "body" : null))
            .when(!roaring, (el) =>
              el.child(
                layer("top")
                  .loop("top", m.kind === "slime" ? { from: 0, to: 8, period: 1700 } : { from: 0, to: -3, period: m.kind === "dragon" ? 3200 : 2600 })
                  .when(lids, (top) => top.child(layer("blink"))),
              ),
            ),
        ),
      v_flex()
        .absolute()
        .left(left + Math.round(kind.w / 2) - BAR_W / 2 - 4)
        .top(top - 34)
        .w(BAR_W + 8)
        .p(3)
        .gap(2)
        .bg("#000000a0")
        .child(
          h_flex()
            .justify_between()
            .text_size(10)
            .font_semibold()
            .text_color(CREAM)
            .child(div().child(dead ? `${kind.name} slain!` : kind.name))
            .child(div().child(dead ? "" : `${m.hp}/${m.maxHp}`)),
        )
        .child(
          div()
            .w(BAR_W)
            .h(8)
            .bg("#1b2233")
            .child(div().id("idle-rpg-monster-hp").h(8).w(Math.round((BAR_W * m.hp) / m.maxHp)).bg(tone).transition("width", { duration: 150, easing: "ease-out" })),
        ),
    ];
  }

  // A pointer event on the root, as a point in floor coordinates.
  point(e) {
    const b = e.bounds ?? { x: 0, y: 0, height: this.wallH + FLOOR_H }; // absent before the first paint
    this.wallH = Math.max(0, b.height - FLOOR_H);
    return { x: e.position.x - b.x, y: e.position.y - b.y - this.wallH };
  }

  // Where a critter sits: its remembered spot, else the next free one along the floor.
  place(list, W) {
    const live = new Set(list.map((a) => a.address));
    for (const a of list) this.seen[a.address] = Date.now();
    // A newcomer gets a random class, kept from then on.
    let joined = false;
    for (const a of list) {
      if (CLASSES.includes(this.sprites[a.address])) continue;
      this.sprites[a.address] = randomClass();
      joined = true;
    }
    if (joined) this.save();
    const perRow = Math.max(1, Math.floor((W - 250 - 60) / CELL_W));
    for (const a of list) {
      if (this.spots[a.address]) continue;
      for (let i = 0; ; i++) {
        const s = { x: 250 + (i % perRow) * CELL_W, y: Math.floor(i / perRow) % 2 ? 104 : 64 };
        const taken = Object.entries(this.spots).some(([k, o]) => live.has(k) && Math.abs(o.x - s.x) < 50 && Math.abs(o.y - s.y) < 30);
        if (!taken || i > 200) {
          this.spots[a.address] = s;
          break;
        }
      }
    }
  }

  walkTo(p, W, cx) {
    const to = { x: Math.round(clamp(p.x, 30, W - 30)), y: Math.round(clamp(p.y, YOU_Y[0], YOU_Y[1])) }; // whole pixels keep the sprite sharp
    const dist = Math.hypot(to.x - this.you.x, to.y - this.you.y);
    this.walkMs = clamp(Math.round(dist * 4), 150, 3000);
    this.you = to;
    this.walking = true;
    this.walkTask?.cancel?.();
    const walk = (this.walkId = (this.walkId ?? 0) + 1);
    this.walkTask = cx.timer.after(this.walkMs, (cx) => {
      if (walk !== this.walkId) return;
      this.walking = false;
      cx.notify();
    });
    const step = (cx) => {
      if (walk !== this.walkId || !this.walking) return;
      this.step = this.step ? 0 : 1;
      cx.notify();
      cx.timer.after(160, step);
    };
    cx.timer.after(160, step);
    this.save();
  }

  // Everything behind the floor, back to front: stars, daylight, sunset glow,
  // sun and moon, clouds, mountains, then the wall with its banners and torches.
  // The time of day comes from the clock, so every window agrees on it.
  scenery(W) {
    const turn = ((this.now % CYCLE_MS) / CYCLE_MS) * Math.PI * 2;
    const up = Math.sin(turn); // the sun's height: 1 at noon, -1 at midnight
    const day = clamp(up * 3 + 0.5, 0, 1);
    const dusk = clamp(1 - Math.abs(up) * 2.5, 0, 1);
    const night = (this.night = 1 - day);
    const glide = { duration: TICK_MS, easing: "linear" };
    const fade = (el, id, o) => el.id(id).opacity(o).transition("opacity", glide);
    const tiles = (art, w, h, place) =>
      Array.from({ length: Math.ceil(W / w) }, (_, i) => place(div().absolute().left(i * w)).child(image(`${ART}/${art}.png`).w(w).h(h)));
    const horizon = FLOOR_H + WALL_H;
    const sky = Math.max(40, this.wallH - WALL_H); // the room above the wall

    // The sun and moon ride one circle, half a turn apart, and set behind the wall.
    const orb = (id, art, a) =>
      div()
        .id(id)
        .absolute()
        .left(Math.round(W / 2 - Math.cos(a) * (W / 2 - 60)) - 20)
        .top(Math.round(-Math.sin(a) * clamp(sky - 34, 30, 130)) - 20)
        .transition("left", glide)
        .transition("top", glide)
        .child(image(`${ART}/${art}.png`).w(40).h(40));

    // A cloud that leaves on the right comes back on the left as a new element,
    // so it does not glide back across the sky.
    const seconds = this.now / 1000;
    const clouds = CLOUDS.map((c, i) => {
      const lane = W + 320;
      const gone = seconds * c.speed + c.off;
      const lap = Math.floor(gone / lane);
      return div()
        .id(`idle-rpg-cloud-${i}-${lap}`)
        .absolute()
        .left(Math.round(gone - lap * lane) - 160)
        .top(-Math.round(c.up * Math.max(0, sky - c.h - 6)) - c.h - 4)
        .opacity(0.3 + 0.7 * day)
        .transition("left", glide)
        .child(image(`${ART}/cloud-${c.art}.png`).w(c.w).h(c.h));
    });

    const fittings = [];
    for (let x = 256; x < W - 120; x += 384) {
      fittings.push(div().absolute().left(x).bottom(FLOOR_H + 2).child(image(`${ART}/banner.png`).w(40).h(56)));
      if (x + 232 > W - 60) continue;
      fittings.push(
        fade(div().absolute().left(x + 188).bottom(FLOOR_H + 30).w(48).h(48), `idle-rpg-glow-${x}`, 0.25 + 0.75 * night).child(
          div().size_full().rounded(24).bg("#ffb34750").loop("opacity", { from: 0.55, to: 1, period: 640 }),
        ),
      );
      fittings.push(div().absolute().left(x + 200).bottom(FLOOR_H + 8).child(image(`${ART}/torch.png`).w(24).h(48)));
    }

    return [
      fade(div().absolute().left(0).top(0).w(W).h(128), "idle-rpg-stars", night).children(tiles("stars", 256, 128, (el) => el.top(0))),
      fade(div().absolute().left(0).top(0).bottom(0).w(W).bg(DAY), "idle-rpg-day", day),
      ...[0.75, 0.6, 0.45, 0.3, 0.15].map((o, i) =>
        fade(div().absolute().left(0).bottom(horizon - 8 + i * 20).w(W).h(20).bg(DUSK), `idle-rpg-dusk-${i}`, dusk * o),
      ),
      div()
        .absolute()
        .left(0)
        .bottom(horizon)
        .w(W)
        .h(1)
        .child(orb("idle-rpg-sun", "sun", turn))
        .child(orb("idle-rpg-moon", "moon", turn + Math.PI))
        .children(clouds),
      ...tiles("mountains", 256, 80, (el) => el.bottom(horizon - 24)),
      fade(div().absolute().left(0).top(0).bottom(FLOOR_H).w(W).bg(TINT), "idle-rpg-night-sky", night * 0.5),
      ...tiles("wall", 128, WALL_H, (el) => el.bottom(FLOOR_H)),
      ...fittings,
    ];
  }

  // The status icon over an agent's head, in pixel art. Every motion here is a
  // native loop, so none of it re-renders the view.
  bubble(a, x, y) {
    const art = (name, w, h) => image(`${ART}/${name}.png`).w(w).h(h);
    if (a.status === "working") {
      // Two swords swing together and apart; a spark flashes as they meet.
      const swing = (from, to) => ({ from, to, period: 520, easing: "ease-in" });
      return div()
        .absolute()
        .left(x - 30)
        .top(y - 104)
        .w(60)
        .h(40)
        .child(div().absolute().left(0).top(4).loop("left", swing(0, 7)).child(art("sword-l", 36, 36)))
        .child(div().absolute().left(24).top(4).loop("left", swing(24, 17)).child(art("sword-r", 36, 36)))
        .child(div().absolute().left(20).top(0).loop("opacity", swing(0, 1)).child(art("spark", 20, 20)));
    }
    if (a.status === "blocked")
      return div().absolute().left(x - 18).top(y - 108).loop("top", { from: y - 108, to: y - 114, period: 560 }).child(art("alert", 36, 40));
    if (a.status === "done") return div().absolute().left(x - 18).top(y - 108).child(art("done", 36, 40));
    // idle: three z's drift up and take turns fading
    const doze = (from, to) => ({ from, to, period: 2400 });
    return div()
      .absolute()
      .left(x + 4)
      .top(y - 116)
      .w(64)
      .h(60)
      .loop("top", { from: y - 116, to: y - 120, period: 2400 })
      .child(div().absolute().left(0).top(40).loop("opacity", doze(1, 0.25)).child(art("z-1", 20, 20)))
      .child(div().absolute().left(16).top(20).loop("opacity", doze(0.5, 1)).child(art("z-2", 24, 24)))
      .child(div().absolute().left(36).top(0).loop("opacity", doze(0.25, 1)).child(art("z-3", 28, 28)));
  }

  // An agent at rest: shadow, sprite, bubble, name. Returns elements for the floor.
  critter(a) {
    const c = this.sprites[a.address];
    const { x, y } = this.at[a.address];
    const fighting = this.fighting && a.status === "working";
    // In formation everyone faces the monster in a fighting stance, on a wider
    // picture (96px) so a weapon can reach out; a working agent winds up on
    // phase 1 and strikes on 2 and 3.
    const dir = this.at[a.address].dir;
    const phase = this.phaseOf(a.address);
    const frame = !fighting || !(this.monster?.hp > 0) ? "f" : phase === 1 ? "a1" : phase === 2 || phase === 3 ? "a2" : "f";
    const pose = this.fighting
      ? div().relative().w(72).h(72).child(div().absolute().left(dir > 0 ? 0 : -24).top(0).child(image(this.look(c, `-${frame}-${dir > 0 ? "r" : "l"}`)).w(96).h(72)))
      : image(this.look(c)).w(72).h(72);
    const where = `${a.space_name} · ${a.tab_name}`;
    const open = this.card === a.address;
    return [
      div()
        .id(`idle-rpg-shadow-${a.address}`)
        .absolute()
        .left(x - 26)
        .top(y - 7)
        .transition("left", MOVE)
        .transition("top", MOVE)
        .w(52)
        .h(14)
        .rounded(7)
        .bg("#00000038")
        .border(2)
        .border_color(a.focused || open ? "#fdf3c4" : "#00000000"),
      div()
        .id(`critter-${a.address}`)
        .absolute()
        .left(x - 36)
        .top(y - 66)
        .transition("left", MOVE)
        .transition("top", this.fighting ? MOVE : { duration: 260, easing: "ease-in" })
        .cursor_pointer()
        .on_mouse_down("left", (e) => {
          this.press = { kind: "critter", address: a.address, px: e.position.x, py: e.position.y };
        })
        .child(
          div()
            .relative()
            .when(a.status === "working" && !fighting, (el) => el.loop("top", { from: 0, to: -7, period: 520 }))
            .child(pose),
        ),
      // in a fight a working agent attacks instead of showing the swords overhead
      ...(fighting ? [] : [this.bubble(a, x, y)]),
      v_flex()
        .id(`idle-rpg-label-${a.address}`)
        .transition("left", MOVE)
        .transition("top", MOVE)
        .absolute()
        .left(x - CELL_W / 2)
        .top(y + 11)
        .w(CELL_W)
        .items_center()
        // named for where it works; what kind of agent it is, is on its card
        .child(div().max_w(CELL_W - 4).px(5).rounded(7).bg("#00000066").truncate().text_size(10).font_semibold().text_color(CREAM).child(where)),
    ];
  }

  // A level-up note over someone whose feet are at x, y: it pops in, then on
  // the next render (the next tick of the attack clock) rises and fades natively.
  cheerNote(key, x, y) {
    const c = this.cheers[key];
    const fresh = Date.now() - c.at < TICK_STEP * 0.8;
    return v_flex()
      .id(`idle-rpg-cheer-${key}-${c.id}`)
      .absolute()
      .left(x - 50)
      .top(Math.max(fresh ? y - 98 : y - 116, 4 - this.wallH)) // kept inside the scene when the wall is low
      .w(100)
      .gap(2)
      .items_center()
      .opacity(fresh ? 1 : 0)
      .transition("left", MOVE)
      .transition("top", { duration: CHEER_MS, easing: "ease-out" })
      .transition("opacity", { duration: CHEER_MS, easing: "ease-in" })
      .children(c.lines.map((line) => div().px(5).rounded(6).bg("#000000a0").text_size(10).font_semibold().text_color(GOLD).child(`${line}!`)));
  }

  // A critical blow's damage, a small gold number where it landed: it pops in
  // like a level-up note, then on the next render (the attacker's rest) rises
  // and fades natively.
  critNote(key, W, kind) {
    const c = this.crits[key];
    const at = this.hitOf(key, c.seed, W, kind);
    const fresh = Date.now() - c.at < TICK_STEP * 0.8;
    return h_flex()
      .id(`idle-rpg-crit-${key}-${c.id}`)
      .absolute()
      .left(at.x - 20)
      .top(fresh ? at.y - 30 : at.y - 48)
      .w(40)
      .justify_center()
      .opacity(fresh ? 1 : 0)
      .transition("top", { duration: CRIT_MS, easing: "ease-out" })
      .transition("opacity", { duration: CRIT_MS, easing: "ease-in" })
      .child(div().px(4).rounded(5).bg("#000000a0").text_size(10).font_semibold().text_color(GOLD).child(`${c.n}!`));
  }

  // Night on the rampart: darkness over the wall, the floor and everyone on it
  // (but under the cards), fading in with the night. Each torch keeps a pool of
  // light clear around its flame and the candle a small one on the table; past
  // those the dark is even, at half strength, so nothing is ever black, and
  // above the wall it thins out over 80px. The pictures hold all of that, so
  // this is a row of them: the candle's, one per torch, and a plain one
  // stretched over what is left.
  gloom(W) {
    const RISE = 80;
    const H = RISE + WALL_H + FLOOR_H;
    const piece = (left, w, art) =>
      div()
        .absolute()
        .left(left)
        .top(0)
        .child(image(`${ART}/dark-${art}.png`).w(w).h(H));
    const pieces = [piece(0, 272, "candle")];
    let x = 272; // each torch's picture is 384px wide with the flame in the middle; see the torches in scenery
    for (; x + 276 <= W; x += 384) pieces.push(piece(x, 384, "torch"));
    if (x < W) pieces.push(piece(x, W - x, "fill"));
    return div()
      .id("idle-rpg-gloom")
      .absolute()
      .left(0)
      .top(-WALL_H - RISE)
      .w(W)
      .h(H)
      .opacity(this.night)
      .transition("opacity", { duration: TICK_MS, easing: "linear" })
      .children(pieces);
  }

  // An agent being carried: it dangles from the pointer and swings against the motion.
  ragdoll(a) {
    const c = this.sprites[a.address];
    const d = this.drag;
    const tilt = d.vx > 1.2 ? "l" : d.vx < -1.2 ? "r" : "c";
    return div()
      .absolute()
      .left(d.x - 44)
      .top(d.y - 78)
      .child(image(this.look(c, `-rag-${tilt}`)).w(88).h(88));
  }

  you_() {
    const { x, y } = this.you;
    const ms = this.walkMs ?? 300;
    const c = this.sprites[YOU];
    return v_flex()
      .id("idle-rpg-you")
      .absolute()
      .left(x - 36)
      .top(y - 66)
      .w(72)
      .items_center()
      .transition("left", { duration: ms, easing: "linear" })
      .transition("top", { duration: ms, easing: "linear" })
      .cursor_pointer()
      .on_mouse_down("left", (e) => {
        this.press = { kind: YOU, px: e.position.x, py: e.position.y };
      })
      .child(
        // Walking: lean left and right in turn, one foot lifted. Sprites are
        // 16x16 pixel art on an 18x18 canvas (room for the outline), drawn at
        // 72 so every pixel is a crisp 4x4. They are PNGs at twice that size:
        // SVGs came out soft on retina screens.
        // In a fight, standing still, you face the monster in the same stance
        // and attack frames as the agents (see critter).
        this.fighting && !this.walking
          ? div()
              .relative()
              .w(72)
              .h(72)
              .child(
                div()
                  .absolute()
                  .left(this.youDir > 0 ? 0 : -24)
                  .top(0)
                  .child(
                    image(
                      this.look(c, `-${!this.youFights ? "f" : [0, "a1", "a2", "a2", 0][this.phaseOf(YOU)] || "f"}-${this.youDir > 0 ? "r" : "l"}`),
                    )
                      .w(96)
                      .h(72),
                  ),
              )
          : image(this.look(c, this.walking ? (this.step ? "-walk-r" : "-walk-l") : "")).w(72).h(72),
      )
      .child(div().px(6).rounded(7).bg(this.card === YOU ? "#00000080" : "#00000040").text_size(10).font_semibold().text_color(CREAM).child("You"));
  }

  // One line of a card: a level, and a bar and numbers for the way to the next.
  // `lv` is { level, into, need } (see levelOf). `spare`, a class's skill
  // points to spend, shows as a star and the number when there are any.
  meter(label, lv, spare = 0) {
    return h_flex()
      .gap(6)
      .items_center()
      .text_size(10)
      .child(div().w(46).flex_none().truncate().text_color("#8ea3bb").child(label))
      .child(div().w(30).flex_none().font_semibold().text_color(GOLD).child(`Lv ${lv.level}`))
      .child(
        div()
          .flex_1()
          .h(5)
          .rounded(2)
          .bg("#0b1626")
          .child(div().h(5).rounded(2).w(`${Math.floor((lv.into / lv.need) * 100)}%`).bg(GOLD)),
      )
      .child(div().flex_none().text_color("#8ea3bb").child(`${lv.into}/${lv.need}`))
      .when(spare > 0, (el) =>
        el.child(
          h_flex()
            .flex_none()
            .gap(2)
            .items_center()
            .font_semibold()
            .text_color(GOLD)
            .child(image(`${ART}/i-star.png`).w(18).h(18))
            .child(div().child(String(spare))),
        ),
      );
  }

  // The four classes as buttons, each with its level; the current one is ringed.
  picker(key) {
    return h_flex()
      .gap(4)
      .children(
        CLASSES.map((c) =>
          v_flex()
            .id(`idle-rpg-pick-${c}`)
            .items_center()
            .p(3)
            .rounded(7)
            .border(1)
            .border_color(this.sprites[key] === c ? "#5cc8ff" : "#00000000")
            .bg(this.sprites[key] === c ? "#5cc8ff22" : "#ffffff0a")
            .cursor_pointer()
            .hover((st) => st.bg("#ffffff1c"))
            .on_click((_e, cx) => {
              this.sprites[key] = c;
              this.picking = false;
              this.save();
              cx.notify();
            })
            .child(image(this.look(c)).w(36).h(36))
            .child(div().text_size(9).font_semibold().text_color(GOLD).child(`Lv ${classLevel(this.progress.xp[c]).level}`)),
        ),
      );
  }

  // A framed close-up of someone's face, with a wrench in the corner that
  // opens the class choices.
  portrait(key) {
    return div()
      .relative()
      .w(56)
      .h(56)
      .flex_none()
      .rounded(8)
      .overflow_hidden()
      .bg("#22395a")
      .border(1)
      .border_color("#31506f")
      // the sprite at 6px a pixel, shifted so the head fills the frame
      .child(div().absolute().left(-26).top(-10).child(image(this.look(this.sprites[key])).w(108).h(108)))
      .child(
        div()
          .id("idle-rpg-card-wrench")
          .absolute()
          .left(36)
          .top(2)
          .w(18)
          .h(18)
          .rounded(5)
          .bg(this.picking ? "#5cc8ff" : "#14243ae0")
          .cursor_pointer()
          .hover((st) => st.bg("#3a6fa0"))
          .on_click((_e, cx) => {
            this.picking = !this.picking;
            cx.notify();
          })
          .child(div().absolute().left(1).top(1).child(image(`${ART}/wrench.png`).w(16).h(16))),
      );
  }

  // The card over whoever was clicked: `a` is an agent, or null for you.
  infoCard(a, W) {
    const key = a ? a.address : YOU;
    const s = a ? this.at[a.address] : this.you;
    const row = (k, v) =>
      h_flex()
        .gap(6)
        .text_size(11)
        .child(div().w(38).flex_none().text_color("#8ea3bb").child(k))
        .child(div().flex_1().truncate().text_color("#dbe7f3").child(v));
    const [word, color] = a ? (STATUS[a.status] ?? [a.status, "#9fb4cc"]) : ["", "#5cc8ff"];
    // Above their head when there is room, else beside them.
    const cardH = (a ? 146 : 123) + (this.picking ? 70 : 0);
    const above = s.y - 72 - cardH;
    const minTop = 4 - this.wallH;
    const fits = above >= minTop;
    const side = s.x + 44 + CARD_W + 8 <= W ? s.x + 44 : s.x - 44 - CARD_W;
    const left = clamp(fits ? s.x - CARD_W / 2 : side, 8, Math.max(8, W - CARD_W - 8));
    const top = fits ? above : Math.max(minTop, Math.min(s.y - cardH + 24, FLOOR_H - cardH - 6));
    const klass = this.sprites[key];
    const title = h_flex()
      .gap(6)
      .items_center()
      .child(div().w(8).h(8).rounded(4).flex_none().bg(color))
      .child(div().flex_1().truncate().text_size(12).font_semibold().text_color("#ffffff").child(a ? `${a.space_name} · ${a.tab_name}` : "You"))
      .child(
        div()
          .id("idle-rpg-card-x")
          .px(5)
          .rounded(5)
          .text_size(12)
          .text_color("#8ea3bb")
          .cursor_pointer()
          .hover((st) => st.bg("#ffffff14"))
          .on_click((_e, cx) => {
            this.card = null;
            this.picking = false;
            cx.notify();
          })
          .child("×"),
      );
    let facts = v_flex().flex_1().min_w(0).gap(3).child(title);
    if (a) {
      const tab = spaces().find((sp) => sp.id === a.space)?.tabs.find((tb) => tb.id === a.tab);
      const since =
        a.status === "working" && tab?.working_since
          ? `for ${ago(tab.working_since)}`
          : tab?.changed_at
            ? `${ago(tab.changed_at)} ago`
            : "";
      facts = facts
        .child(row("Agent", a.program?.name ?? a.app ?? "Agent"))
        .child(row("Status", since ? `${word} ${since}` : word))
        .child(row("Doing", a.title || "—"));
    } else {
      facts = facts.child(row("Class", capital(klass)));
    }
    return v_flex()
      .id("idle-rpg-card")
      .absolute()
      .left(left)
      .top(top)
      .w(CARD_W)
      .p(10)
      .gap(6)
      .rounded(10)
      .bg("#14243a")
      .border(1)
      .border_color("#31506f")
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(h_flex().gap(8).items_start().child(this.portrait(key)).child(facts))
      // your own level, then the level of the class this character has on,
      // which opens the skills panel on that class
      .child(
        v_flex()
          .gap(3)
          .when(!a, (el) => el.child(this.meter("You", playerLevel(this.progress.xp[YOU]))))
          .child(
            this.meter(capital(klass), classLevel(this.progress.xp[klass]), pointsLeft(this.progress, klass))
              .id("idle-rpg-card-skills")
              .rounded(4)
              .cursor_pointer()
              .hover((st) => st.bg("#ffffff14"))
              .on_click((_e, cx) => {
                this.openSkills(klass);
                cx.notify();
              }),
          ),
      )
      .when(this.picking, (el) => el.child(this.picker(key)))
      .when(Boolean(a), (el) =>
        el.child(
          div()
            .id("idle-rpg-card-go")
            .py(4)
            .rounded(6)
            .bg("#5cc8ff")
            .text_center()
            .text_size(11)
            .font_semibold()
            .text_color("#06243a")
            .cursor_pointer()
            .hover((st) => st.bg("#8ad8ff"))
            .on_click((_e, cx) => {
              run("agent.focus", { terminal: a.address });
              this.card = null;
              this.picking = false;
              cx.notify();
            })
            .child("Go to terminal"),
        ),
      );
  }

  render() {
    const W = Math.max(320, this.size.width);
    const list = agents();
    this.place(list, W);
    if (this.card && this.card !== YOU && !list.some((a) => a.address === this.card)) this.card = null;
    const you = { x: Math.round(clamp(this.you.x, 30, W - 30)), y: Math.round(clamp(this.you.y, YOU_Y[0], YOU_Y[1])) };
    this.you = you;

    // Whoever stands lower on the floor is drawn in front.
    const hits = list.filter((a) => a.status === "working").length;
    // In a fight everyone stands in formation; otherwise at their own spots.
    const foeKind = this.battle && W >= 640 ? MONSTERS[this.monster?.kind] : null;
    this.fighting = Boolean(foeKind);
    this.at = foeKind ? this.formation(list, W, foeKind) : this.spots;
    const youDir = you.x <= W / 2 + (foeKind?.core.x ?? 0) ? 1 : -1; // which way the monster is from you
    this.youFights = hits > 0 && !this.walking && this.joins(W);
    this.struck = (this.youFights && this.phaseOf(YOU) === 4) || list.some((a) => a.status === "working" && this.phaseOf(a.address) === 4);
    this.youDir = youDir;
    const actors = [{ y: you.y, draw: () => [this.you_()] }, { y: MONSTER_Y, draw: () => this.foe(W, hits) }];
    if (this.youFights) actors.push({ y: FLOOR_H, draw: () => this.attack({ key: YOU, cls: this.sprites[YOU], x: you.x, y: you.y, dir: youDir }, W, foeKind) });
    for (const a of list) {
      if (this.drag?.address === a.address) continue;
      const s = this.spots[a.address];
      s.x = Math.round(clamp(s.x, 36, W - 36));
      s.y = Math.round(s.y);
      actors.push({ y: this.at[a.address].y, draw: () => this.critter(a) });
      if (this.fighting && a.status === "working" && this.monster.hp > 0) actors.push({ y: FLOOR_H, draw: () => this.attack({ key: a.address, cls: this.sprites[a.address], ...this.at[a.address] }, W, foeKind) });
    }
    for (const [key, c] of Object.entries(this.cheers)) {
      if (Date.now() - c.at > CHEER_MS + 1000) delete this.cheers[key];
    }
    for (const key of Object.keys(this.cheers)) {
      const s = key === YOU ? !this.walking && you : list.some((a) => a.address === key && this.drag?.address !== key) && this.at[key];
      if (s) actors.push({ y: FLOOR_H + 1, draw: () => [this.cheerNote(key, s.x, s.y)] });
    }
    for (const [key, c] of Object.entries(this.crits)) {
      if (Date.now() - c.at > CRIT_MS + 1000) delete this.crits[key];
      else if (foeKind) actors.push({ y: FLOOR_H + 1, draw: () => [this.critNote(key, W, foeKind)] });
    }
    actors.sort((p, q) => p.y - q.y);

    const { slain, gold } = this.progress;
    const spare = pointsLeftAll(this.progress); // skill points to spend, all classes together
    const earned = CLASSES.some((c) => pointsEarned(this.progress.xp[c]) > 0);
    const counts = tally(list);
    // one count on the sign: a small icon and its number
    const stat = (art, w, h, n) =>
      h_flex()
        .gap(3)
        .items_center()
        .child(image(`${ART}/${art}.png`).w(w).h(h))
        .child(div().child(String(n)));
    const scenery = this.scenery(W); // also works out how dark it is
    const boards = Array.from({ length: Math.ceil(W / 128) }, (_, i) =>
      div().absolute().left(i * 128).top(0).child(image(`${ART}/floor.png`).w(128).h(FLOOR_H)),
    );
    const carried = this.drag && list.find((a) => a.address === this.drag.address);
    const carded = this.card && !carried && list.find((a) => a.address === this.card);

    const floor = div()
      .absolute()
      .left(0)
      .bottom(0)
      .w(W)
      .h(FLOOR_H)
      .bg(FLOOR)
      .child(
        div()
          .relative()
          .w(W)
          .h(FLOOR_H)
          .children(boards)
          // the table and the barrel stand at the back, clear of the monster's corner
          .child(div().absolute().left(12).top(-34).child(image(`${ART}/table.png`).w(112).h(56)))
          .child(div().absolute().left(136).top(-30).child(image(`${ART}/barrel.png`).w(48).h(52)))
          .children(actors.flatMap((p) => p.draw()))
          .child(this.gloom(W))
          .when(list.length === 0, (el) =>
            el.child(
              v_flex()
                .absolute()
                .left(250)
                .top(50)
                .gap(4)
                .text_color("#5a3d22")
                .child(div().text_size(13).font_semibold().child("The rampart is quiet"))
                .child(div().text_size(11).child("Start an agent from the + in the tab bar")),
            ),
          )
          .when(Boolean(carded), (el) => el.child(this.infoCard(carded, W)))
          .when(this.card === YOU && !carried, (el) => el.child(this.infoCard(null, W)))
          .when(Boolean(carried), (el) => el.child(this.ragdoll(carried))),
      );

    const drop = (cx) => {
      if (this.drag) {
        this.spots[this.drag.address] = {
          x: Math.round(clamp(this.drag.x, 36, W - 36)),
          y: Math.round(clamp(this.drag.y, CRITTER_Y[0], CRITTER_Y[1])),
        };
        this.save();
      }
      this.press = this.drag = null;
      cx.notify();
    };

    return div()
      .id("idle-rpg")
      .relative()
      .size_full()
      .overflow_hidden()
      .bg(NIGHT)
      .on_size_change((size, cx) => {
        this.size = size;
        this.wallH = Math.max(0, size.height - FLOOR_H);
        cx.notify();
      })
      .on_mouse_down("left", (e, cx) => {
        cx.stop_propagation();
        this.point(e);
        if (!this.press) this.press = { kind: "floor", px: e.position.x, py: e.position.y };
      })
      .on_mouse_move((e, cx) => {
        const pr = this.press;
        if (!pr || pr.kind !== "critter" || this.fighting) return;
        const moved = Math.abs(e.position.x - pr.px) + Math.abs(e.position.y - pr.py);
        if (!this.drag && moved <= 4) return;
        const p = this.point(e);
        const x = Math.round(clamp(p.x, 20, W - 20));
        const y = Math.round(clamp(p.y, 70 - this.wallH, FLOOR_H - 8));
        const last = this.drag?.x ?? x;
        this.drag = { address: pr.address, x, y, vx: (this.drag?.vx ?? 0) * 0.6 + (x - last) * 0.4 };
        this.card = null;
        cx.notify();
      })
      .on_mouse_up("left", (e, cx) => {
        const pr = this.press;
        if (!pr) return;
        if (this.drag) return drop(cx);
        const still = Math.abs(e.position.x - pr.px) + Math.abs(e.position.y - pr.py) <= 4;
        if (pr.kind === YOU) {
          if (still) {
            this.codex = false;
            this.skillsOpen = this.shopOpen = null;
            this.card = this.card === YOU ? null : YOU;
            this.picking = false;
          }
        } else if (pr.kind === "critter") {
          this.codex = false;
          this.skillsOpen = this.shopOpen = null;
          this.card = this.card === pr.address ? null : pr.address;
          this.picking = false;
        } else if (still) {
          this.card = null;
          this.codex = false;
          this.skillsOpen = this.shopOpen = null;
          this.walkTo(this.point(e), W, cx);
        }
        this.press = null;
        cx.notify();
      })
      .on_hover((hovered, cx) => {
        if (!hovered && this.press) drop(cx);
      })
      .children(scenery)
      .child(
        h_flex()
          .absolute()
          .left(props()?.inset ?? 84)
          .top(8)
          .gap(8)
          .items_center()
          .px(6)
          .py(2)
          .rounded(6)
          .bg("#00000050")
          .child(
            v_flex()
              .child(div().text_size(13).font_semibold().text_color(CREAM).child("Raid Party"))
              .child(
                h_flex()
                  .gap(8)
                  .items_center()
                  .text_size(10)
                  .text_color("#d5e3f0")
                  .children(counts.length ? counts.map(([art, w, h, n]) => stat(art, w, h, n)) : [div().child("nobody in yet")])
                  .when(this.battle && (slain > 0 || gold > 0), (el) =>
                    el
                      .child(
                        // the kill count opens the codex
                        stat("i-skull", 18, 18, slain)
                          .id("idle-rpg-slain")
                          .px(3)
                          .rounded(4)
                          .bg(this.codex ? "#ffffff30" : "#ffffff00")
                          .cursor_pointer()
                          .hover((st) => st.bg("#ffffff30"))
                          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
                          .on_click((_e, cx) => {
                            this.codex = !this.codex;
                            if (this.codex) {
                              // only one panel or card at a time
                              this.skillsOpen = this.shopOpen = this.card = null;
                              this.picking = false;
                            }
                            cx.notify();
                          }),
                      )
                      .child(
                        // the gold opens the shop, on your own class
                        stat("i-coin", 18, 18, gold)
                          .id("idle-rpg-gold")
                          .px(3)
                          .rounded(4)
                          .bg(this.shopOpen ? "#ffffff30" : "#ffffff00")
                          .cursor_pointer()
                          .hover((st) => st.bg("#ffffff30"))
                          .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
                          .on_click((_e, cx) => {
                            this.openShop(this.shopOpen ? null : this.sprites[YOU]);
                            cx.notify();
                          }),
                      ),
                  )
                  // once any class has a point, a star with the points to spend
                  // opens the skills panel; gold while there are some, dim when not
                  .when(earned, (el) =>
                    el.child(
                      stat("i-star", 18, 18, spare)
                        .id("idle-rpg-points")
                        .px(3)
                        .rounded(4)
                        .opacity(spare > 0 || this.skillsOpen ? 1 : 0.55)
                        .text_color(spare > 0 ? GOLD : "#d5e3f0")
                        .bg(this.skillsOpen ? "#ffffff30" : spare > 0 ? "#ffd16630" : "#ffffff00")
                        .cursor_pointer()
                        .hover((st) => st.bg("#ffffff30"))
                        .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
                        .on_click((_e, cx) => {
                          // on the first class with points to spend, else your own
                          this.openSkills(this.skillsOpen ? null : (CLASSES.find((c) => pointsLeft(this.progress, c) > 0) ?? this.sprites[YOU]));
                          cx.notify();
                        }),
                    ),
                  ),
              ),
          )
          .child(
            div()
              .id("idle-rpg-battle-toggle")
              .px(6)
              .py(2)
              .rounded(5)
              .text_size(10)
              .font_semibold()
              .bg(this.battle ? "#c94040" : "#ffffff1c")
              .text_color(this.battle ? "#ffffff" : "#d5e3f0")
              .cursor_pointer()
              .hover((st) => st.bg(this.battle ? "#e05555" : "#ffffff30"))
              .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
              .on_click((_e, cx) => {
                this.battle = !this.battle;
                // the codex and the shop open from chips the sign shows only in a raid
                this.codex = false;
                this.shopOpen = null;
                if (this.battle) this.fight(); // someone to fight straight away
                this.save();
                this.wake(cx);
                cx.notify();
              })
              .child(this.battle ? "End Raid" : "Start Raid"),
          ),
      )
      .child(floor)
      // last, so they lie over the floor and everyone on it
      .when(this.codex && this.battle, (el) => el.child(this.codexCard(props()?.inset ?? 84)))
      .when(CLASSES.includes(this.skillsOpen), (el) => el.child(this.skillsCard(props()?.inset ?? 84)))
      .when(this.battle && CLASSES.includes(this.shopOpen), (el) => el.child(this.shopCard(props()?.inset ?? 84)));
  }

  // Opens the skills panel on class `cls` (null closes it), closing the codex,
  // the shop and any card: only one of them is open at a time.
  openSkills(cls) {
    this.skillsOpen = cls;
    if (!cls) return;
    this.codex = false;
    this.shopOpen = this.card = null;
    this.picking = false;
  }

  // Opens the shop on class `cls` (null closes it), closing the codex, the
  // skills panel and any card.
  openShop(cls) {
    this.shopOpen = cls;
    if (!cls) return;
    this.codex = false;
    this.skillsOpen = this.card = null;
    this.picking = false;
  }

  // The codex, under the sign: every kind of monster and how many have fallen.
  // A kind not yet slain is a dim shape with no name. Kills from before the
  // counts by kind began are in the total only, so they get a line of their own.
  codexCard(left) {
    const { slain, kills } = this.progress;
    const known = Object.keys(MONSTERS).reduce((sum, k) => sum + (kills[k] ?? 0), 0);
    const line = (picture, name, n) =>
      h_flex()
        .gap(8)
        .items_center()
        .child(div().w(32).h(24).flex_none().flex().items_center().justify_center().child(picture))
        .child(div().flex_1().truncate().text_color("#dbe7f3").child(name))
        .child(div().font_semibold().text_color(CREAM).child(String(n)));
    return v_flex()
      .id("idle-rpg-codex")
      .absolute()
      .left(left)
      .top(54)
      .w(176)
      .p(8)
      .gap(3)
      .rounded(8)
      .bg("#101a2cf0")
      .border(1)
      .border_color("#ffffff24")
      .text_size(11)
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(
        h_flex()
          .gap(6)
          .items_center()
          .child(image(`${ART}/i-skull.png`).w(18).h(18))
          .child(div().flex_1().text_size(12).font_semibold().text_color("#ffffff").child("Codex"))
          .child(
            div()
              .id("idle-rpg-codex-x")
              .px(5)
              .rounded(5)
              .text_color("#8ea3bb")
              .cursor_pointer()
              .hover((st) => st.bg("#ffffff1c"))
              .on_click((_e, cx) => {
                this.codex = false;
                cx.notify();
              })
              .child("×"),
          ),
      )
      .children(
        Object.entries(MONSTERS).map(([k, kind]) => {
          const n = kills[k] ?? 0;
          const scale = 24 / Math.max(kind.w, kind.h);
          const picture = image(`${ART}/monster-${k}.png`)
            .w(Math.round(kind.w * scale))
            .h(Math.round(kind.h * scale));
          return line(div().opacity(n > 0 ? 1 : 0.25).child(picture), n > 0 ? kind.name : "???", n);
        }),
      )
      .when(slain > known, (el) => el.child(line(div(), "Before the codex", slain - known)));
  }

  // A small button in a panel: live, or dimmed and dead. `act` does what it
  // says and returns whether anything changed, which is then saved straight away.
  button(id, label, live, act) {
    return div()
      .id(id)
      .flex_none()
      .px(5)
      .rounded(5)
      .text_size(10)
      .font_semibold()
      .bg(live ? "#5cc8ff" : "#ffffff0a")
      .text_color(live ? "#06243a" : "#5d7088")
      .when(live, (el) =>
        el
          .cursor_pointer()
          .hover((st) => st.bg("#8ad8ff"))
          .on_click((_e, cx) => {
            if (act()) this.save();
            cx.notify();
          }),
      )
      .child(label);
  }

  // The skills panel, under the sign like the codex: the four classes to pick
  // from, each with its level and any points it has to spend; then for the
  // one picked, its points, a Reset that gives them all back, and a line per
  // skill with its rank, what it gives now, and a + that spends a point on it.
  // Short enough for the scene at its lowest (230px, the sign taking 54).
  skillsCard(left) {
    const cls = this.skillsOpen;
    const ranks = this.progress.skills[cls];
    const spare = pointsLeft(this.progress, cls);
    const spent = pointsSpent(ranks) > 0;
    const tab = (c) => {
      const n = pointsLeft(this.progress, c);
      return v_flex()
        .id(`idle-rpg-skills-${c}`)
        .flex_1()
        .items_center()
        .py(2)
        .rounded(6)
        .border(1)
        .border_color(c === cls ? "#5cc8ff" : n > 0 ? "#ffd16660" : "#00000000")
        .bg(c === cls ? "#5cc8ff22" : "#ffffff0a")
        .cursor_pointer()
        .hover((st) => st.bg("#ffffff1c"))
        .on_click((_e, cx) => {
          this.skillsOpen = c;
          cx.notify();
        })
        .child(image(this.look(c)).w(24).h(24))
        .child(
          h_flex()
            .gap(3)
            .text_size(9)
            .font_semibold()
            .child(div().text_color(CREAM).child(`Lv ${classLevel(this.progress.xp[c]).level}`))
            .when(n > 0, (el) => el.child(div().text_color(GOLD).child(`+${n}`))),
        );
    };
    const skill = (k) =>
      h_flex()
        .gap(6)
        .items_center()
        .child(div().w(38).flex_none().text_color("#dbe7f3").child(capital(k)))
        .child(div().w(22).flex_none().font_semibold().text_color(GOLD).child(`${ranks[k]}/${MAX_RANK}`))
        .child(div().flex_1().min_w(0).truncate().text_size(10).text_color("#8ea3bb").child(SKILL_TEXT[k]?.(ranks) ?? ""))
        .child(this.button(`idle-rpg-skill-${k}`, "+", canRaise(this.progress, cls, k), () => raise(this.progress, cls, k)));
    return v_flex()
      .id("idle-rpg-skills")
      .absolute()
      .left(left)
      .top(54)
      .w(CARD_W)
      .p(8)
      .gap(3)
      .rounded(8)
      .bg("#101a2cf0")
      .border(1)
      .border_color("#ffffff24")
      .text_size(11)
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(
        h_flex()
          .gap(6)
          .items_center()
          .child(image(`${ART}/i-star.png`).w(18).h(18))
          .child(div().flex_1().text_size(12).font_semibold().text_color("#ffffff").child("Skills"))
          .child(
            div()
              .id("idle-rpg-skills-x")
              .px(5)
              .rounded(5)
              .text_color("#8ea3bb")
              .cursor_pointer()
              .hover((st) => st.bg("#ffffff1c"))
              .on_click((_e, cx) => {
                this.skillsOpen = null;
                cx.notify();
              })
              .child("×"),
          ),
      )
      .child(h_flex().gap(4).children(CLASSES.map(tab)))
      .child(
        h_flex()
          .gap(6)
          .items_center()
          .child(
            div()
              .flex_1()
              .truncate()
              .text_color(spare > 0 ? GOLD : "#8ea3bb")
              .child(`${capital(cls)}: ${spare > 0 ? `${spare} point${spare === 1 ? "" : "s"} to spend` : "no points to spend"}`),
          )
          .child(this.button("idle-rpg-skills-reset", "Reset", spent, () => resetSkills(this.progress, cls))),
      )
      .children((CLASS_SKILLS[cls] ?? []).map(skill));
  }

  // The shop, under the sign like the skills panel: your gold, the four
  // classes to pick from (each in the colourway it has on), then for the one
  // picked, everything of one kind the shop sells: a preview of the sprite in
  // it, its name, and "Equipped", an Equip button (owned) or a Buy button with
  // its price, dimmed and dead while the gold is short. Buying puts it on as
  // well; buying and equipping save straight away. Down its left side are the
  // kinds of item (SHOP in rules.js): armours, weapons, hats, with room under
  // them for more. A kind with nothing for sale yet says so. Short enough for
  // the scene at its lowest (230px, the sign taking 54).
  shopCard(left) {
    const cls = this.shopOpen;
    const kind = SHOP_KINDS.includes(this.shopKind) ? this.shopKind : SHOP_KINDS[0];
    const items = catalogue(cls, kind);
    const preview = { armour: (it) => image(this.look(cls, "", it.id)).w(36).h(36) };
    const nav = (k) =>
      h_flex()
        .id(`idle-rpg-shop-kind-${k}`)
        .gap(5)
        .items_center()
        .px(4)
        .py(3)
        .rounded(6)
        .border(1)
        .border_color(k === kind ? "#5cc8ff" : "#00000000")
        .bg(k === kind ? "#5cc8ff22" : "#ffffff0a")
        .cursor_pointer()
        .hover((st) => st.bg("#ffffff1c"))
        .on_click((_e, cx) => {
          this.shopKind = k;
          cx.notify();
        })
        .child(image(`${ART}/${SHOP_ICONS[k] ?? "i-coin"}.png`).w(18).h(18))
        .child(div().text_size(10).font_semibold().text_color(CREAM).child(SHOP[k].name));
    const tab = (id, on, act, ...content) =>
      v_flex()
        .id(id)
        .flex_1()
        .items_center()
        .py(2)
        .rounded(6)
        .border(1)
        .border_color(on ? "#5cc8ff" : "#00000000")
        .bg(on ? "#5cc8ff22" : "#ffffff0a")
        .cursor_pointer()
        .hover((st) => st.bg("#ffffff1c"))
        .on_click((_e, cx) => {
          act();
          cx.notify();
        })
        .children(content);
    const item = (it) => {
      const on = equipped(this.progress, cls, kind) === it.id;
      return v_flex()
        .id(`idle-rpg-shop-item-${it.id}`)
        .flex_1()
        .min_w(0)
        .h(SHOP_ITEM_H)
        .items_center()
        .gap(2)
        .py(3)
        .rounded(6)
        .border(1)
        .border_color(on ? "#5cc8ff" : "#00000000")
        .bg(on ? "#5cc8ff22" : "#ffffff0a")
        .child(preview[kind]?.(it) ?? div().h(36))
        .child(div().max_w_full().truncate().text_size(10).text_color("#dbe7f3").child(it.name))
        .child(
          on
            ? div().text_size(9).font_semibold().text_color("#5cc8ff").child("Equipped")
            : owns(this.progress, cls, kind, it.id)
              ? this.button(`idle-rpg-shop-equip-${it.id}`, "Equip", true, () => equip(this.progress, cls, kind, it.id))
              : this.button(`idle-rpg-shop-buy-${it.id}`, `Buy ${it.price}`, canBuy(this.progress, cls, kind, it.id), () => {
                  if (!buy(this.progress, cls, kind, it.id)) return false;
                  equip(this.progress, cls, kind, it.id);
                  return true;
                }),
        );
    };
    return v_flex()
      .id("idle-rpg-shop")
      .absolute()
      .left(left)
      .top(54)
      .w(SHOP_NAV_W + 8 + CARD_W)
      .p(8)
      .gap(6)
      .rounded(8)
      .bg("#101a2cf0")
      .border(1)
      .border_color("#ffffff24")
      .text_size(11)
      .on_mouse_down("left", (_e, cx) => cx.stop_propagation())
      .child(
        h_flex()
          .gap(6)
          .items_center()
          .child(image(`${ART}/i-coin.png`).w(18).h(18))
          .child(div().flex_1().text_size(12).font_semibold().text_color("#ffffff").child("Shop"))
          .child(div().font_semibold().text_color(GOLD).child(`${this.progress.gold} gold`))
          .child(
            div()
              .id("idle-rpg-shop-x")
              .px(5)
              .rounded(5)
              .text_color("#8ea3bb")
              .cursor_pointer()
              .hover((st) => st.bg("#ffffff1c"))
              .on_click((_e, cx) => {
                this.shopOpen = null;
                cx.notify();
              })
              .child("×"),
          ),
      )
      .child(
        h_flex()
          .gap(8)
          .items_start()
          .child(
            // down the left: the kinds of item, and room for more
            v_flex()
              .w(SHOP_NAV_W)
              .flex_none()
              .gap(3)
              .children(SHOP_KINDS.map(nav))
              .child(div().px(4).pt(2).text_size(9).text_color("#8ea3bb").child("More soon")),
          )
          .child(
            v_flex()
              .flex_1()
              .min_w(0)
              .gap(3)
              .child(
                h_flex()
                  .gap(4)
                  .children(
                    CLASSES.map((c) =>
                      tab(
                        `idle-rpg-shop-${c}`,
                        c === cls,
                        () => (this.shopOpen = c),
                        image(this.look(c)).w(24).h(24),
                        div().text_size(9).font_semibold().text_color(CREAM).child(capital(c)),
                      ),
                    ),
                  ),
              )
              .child(
                items.length
                  ? h_flex().gap(4).children(items.map(item))
                  : // the same height as a row of items, so the panel does not jump between kinds
                    v_flex()
                      .h(SHOP_ITEM_H)
                      .items_center()
                      .justify_center()
                      .rounded(6)
                      .bg("#ffffff0a")
                      .text_color("#8ea3bb")
                      .child(`No ${SHOP[kind].name.toLowerCase()} for sale yet`),
              ),
          ),
      );
  }
}
