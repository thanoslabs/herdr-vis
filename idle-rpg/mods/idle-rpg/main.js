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
// with 100 HP and the party forms up around it, warriors up close and everyone
// else at range. Every few seconds each working agent attacks in its own way
// (sword swing, arrow, fireball, thrown potion) for 1 HP; when the monster
// falls another one turns up. Turning it off sends everyone back to their spots.
// Layout props: { inset } = left edge of the sign (84 leaves room for macOS buttons).

import { View, div, image } from "gpui-kit";
import { h_flex, v_flex } from "gpui-base";
import { agents, props, run, setShared, shared, spaces } from "herdr";

const ART = "mods/idle-rpg/art";
// shared: { you: {x, y}, spots: { <address>: {x, y} }, sprites: { you | <address>: <class> } }
const STATE = "idle-rpg.state";
const CLASSES = ["wizard", "healer", "warrior", "archer"];
const YOU = "you"; // the person's key in `sprites` and as an open card
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
// Battle mode. Sizes are on-screen px (art px x 4, plus the outline).
const MONSTERS = {
  slime: { name: "Slime", w: 136, h: 104, core: { x: 0, y: 44, r: 18, half: 60 } },
  ogre: { name: "Ogre", w: 200, h: 200, core: { x: 0, y: 86, r: 24, half: 62 } },
  dragon: { name: "Dragon", w: 328, h: 264, core: { x: 12, y: 74, r: 26, half: 84 } },
};
// `core` is the middle of the monster's bulk, where blows land: px right of
// its centre line and above its feet, how far a blow may stray from it, and
// half the bulk's width, which is how close a warrior stands. The picture is
// often much wider than that (the dragon's head, wings and tail).
const MONSTER_HP = 100;
const ATTACK_MS = 3000; // each working agent hits once per beat, for 1 HP
const RESPAWN_MS = 9000; // how long a fallen monster lies there before the next
const MONSTER_Y = 108; // where its feet are on the floor
const BAR_W = 120;
const MELEE = 90; // how close to the monster's bulk a warrior must be to reach it
const SWORD = 44; // how far outside the bulk a warrior stands, so the swing lands on it
const RANGE = 360; // how far the ranged classes stand from the monster: five characters
// An attack plays in phases, one TICK_STEP each: 1 is the wind-up, 2 and 3 the
// two halves of the strike or flight, 4 the impact, 0 rest. Everyone starts a
// different number of ticks into the beat, so the party does not move as one.
const TICK_STEP = 250;
const FLIGHT = TICK_STEP * 2;
const STAGGER = 5; // how many different starting ticks there are
const LAST_TICK = STAGGER - 1 + 4; // the tick on which the latest attacker's impact ends
const BLINK_MS = 5200; // monsters blink this often
const ROAR_MS = 14000; // and the ogre roars this often
const MOVE = { duration: 700, easing: "ease-in-out" }; // walking between spots and the formation

function clamp(n, lo, hi) {
  return Math.max(lo, Math.min(hi, n));
}

function summary(list) {
  const n = (s) => list.filter((a) => a.status === s).length;
  const parts = [];
  if (n("blocked")) parts.push(`${n("blocked")} need you`);
  if (n("working")) parts.push(`${n("working")} working`);
  if (n("done")) parts.push(`${n("done")} done`);
  if (n("idle")) parts.push(`${n("idle")} resting`);
  return parts.join(" · ");
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
    const saved = shared(STATE) ?? shared("raid-party.state") ?? shared("rpg.state") ?? shared("snow-loft.state") ?? {};
    this.now = Date.now();
    cx.timer.every(TICK_MS, (cx) => {
      this.now = Date.now();
      cx.notify();
    });
    this.size = { width: 900, height: 360 };
    this.wallH = 210; // the wall's height, learned from pointer events
    this.you = saved.you ?? { x: 154, y: 16 };
    this.spots = { ...(saved.spots ?? {}) };
    this.sprites = { ...(saved.sprites ?? {}) };
    this.seen = { ...(saved.seen ?? {}) }; // <address>: when it was last here
    this.battle = saved.battle ?? true;
    this.monster = saved.monster ?? null; // { kind, hp, id, slainAt? }
    this.slain = saved.slain ?? 0;
    this.unsaved = 0; // damage dealt since the last save
    this.tick = null; // how many TICK_STEPs into the current beat's attacks; null between beats
    this.beat = 0;
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
    cx.timer.every(ATTACK_MS, (cx) => {
      if (!this.battle) return;
      if (this.fight(0)) return cx.notify(); // a new monster walked in
      if (!(this.monster?.hp > 0)) return;
      const keys = agents()
        .filter((a) => a.status === "working")
        .map((a) => a.address);
      if (keys.length && this.joins(Math.max(320, this.size.width))) keys.push(YOU); // you fight alongside them
      if (!keys.length) return;
      this.strike(cx, keys);
      cx.notify();
    });
    if (!CLASSES.includes(this.sprites[YOU])) {
      this.sprites[YOU] = randomClass();
      this.save();
    }
    this.press = null; // { kind: "floor" | "critter" | YOU, address?, px, py }
    this.drag = null; // { address, x, y, vx, last } while a critter dangles
    this.card = null; // whose card is open: an agent's address, or YOU
    this.picking = false; // the open card is showing the class choices
    this.walking = false;
    this.walkTask = null;
  }

  // Agents can be missing for a while (the app just started, a machine is
  // offline), so one is only forgotten after a week away.
  save() {
    const old = Date.now() - 7 * 24 * 3600 * 1000;
    for (const k of Object.keys(this.seen)) {
      if (this.seen[k] >= old) continue;
      delete this.seen[k];
      delete this.spots[k];
      delete this.sprites[k];
    }
    setShared(STATE, {
      you: this.you,
      spots: this.spots,
      sprites: this.sprites,
      seen: this.seen,
      battle: this.battle,
      monster: this.monster,
      slain: this.slain,
    });
    this.unsaved = 0;
  }

  // Brings in a monster if one is due, otherwise takes `hits` off the one
  // there. Returns whether anything changed. HP is saved every tenth point and
  // on a kill, not on every hit.
  fight(hits) {
    if (!this.battle) return false;
    const m = this.monster;
    if (!m || !MONSTERS[m.kind] || (m.hp <= 0 && Date.now() - (m.slainAt ?? 0) >= RESPAWN_MS)) {
      const kinds = Object.keys(MONSTERS).filter((k) => k !== m?.kind);
      this.monster = { kind: kinds[Math.floor(Math.random() * kinds.length)], hp: MONSTER_HP, id: (m?.id ?? 0) + 1 };
      this.save();
      return true;
    }
    if (m.hp <= 0 || hits <= 0) return false;
    m.hp = Math.max(0, m.hp - hits);
    this.unsaved += hits;
    if (m.hp === 0) {
      m.slainAt = Date.now();
      this.slain += 1;
    }
    if (m.hp === 0 || this.unsaved >= 10) this.save();
    return true;
  }

  // Whether you join in when the party attacks: the ranged classes from
  // wherever you stand, a warrior only from beside the monster.
  joins(W) {
    const kind = MONSTERS[this.monster?.kind];
    if (!this.fighting || !kind || !(this.monster.hp > 0)) return false;
    return this.sprites[YOU] !== "warrior" || Math.abs(this.you.x - (W / 2 + kind.core.x)) - kind.core.half <= MELEE;
  }

  // Plays one beat of attacks by `keys`: counts `tick` up, re-rendering on
  // each. Each attacker's point of damage comes off on the tick its blow lands.
  strike(cx, keys) {
    const beat = (this.beat += 1);
    this.tick = 0;
    for (let i = 1; i <= LAST_TICK + 1; i++) {
      cx.timer.after(i * TICK_STEP, (cx) => {
        if (beat !== this.beat) return;
        this.tick = i > LAST_TICK ? null : i;
        this.fight(keys.filter((key) => this.phaseOf(key) === 4).length);
        cx.notify();
      });
    }
  }

  // A number from 0 to n - 1 for one attacker on this beat: the same all
  // through the beat, different on the next.
  roll(key, salt, n) {
    let h = 2166136261 ^ Math.imul(this.beat + 1, 40503) ^ Math.imul(salt, 2246822519);
    for (const ch of String(key)) h = Math.imul(h ^ ch.charCodeAt(0), 16777619);
    // stir it, so that keys one character apart land far apart
    h = Math.imul(h ^ (h >>> 16), 0x85ebca6b);
    h = Math.imul(h ^ (h >>> 13), 0xc2b2ae35);
    return ((h ^ (h >>> 16)) >>> 0) % n;
  }

  // Which phase of its attack someone is in right now.
  phaseOf(key) {
    if (this.tick === null) return 0;
    const k = this.tick - this.roll(key, 1, STAGGER);
    return k < 0 || k > 3 ? 0 : k + 1;
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
    // blows land around the middle of the monster's bulk, a little different each time
    const { x: cx0, y: cy0, r } = kind.core;
    const hit = {
      x: Math.round(W / 2 + cx0 + this.roll(who.key, 2, 2 * r + 1) - r),
      y: Math.round(MONSTER_Y - cy0 + this.roll(who.key, 3, r + 1) - r / 2),
    };
    const art = (name, w, h) => image(`${ART}/${name}.png`).w(w).h(h);
    const pop = (id, name, w, h, at, on) =>
      div()
        .id(`idle-rpg-${id}-${who.key}`)
        .absolute()
        .left(at.x - w / 2)
        .top(at.y - h / 2)
        .opacity(on ? 1 : 0)
        .transition("opacity", { duration: on ? 20 : 350, easing: "ease-out" })
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
    const tone = m.hp > 50 ? "#4cd47b" : m.hp > 20 ? "#ffd166" : "#ff5d5d";
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
            .child(div().child(dead ? "" : `${m.hp}/${MONSTER_HP}`)),
        )
        .child(
          div()
            .w(BAR_W)
            .h(8)
            .bg("#1b2233")
            .child(div().id("idle-rpg-monster-hp").h(8).w(Math.round((BAR_W * m.hp) / MONSTER_HP)).bg(tone).transition("width", { duration: 150, easing: "ease-out" })),
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
      fade(div().absolute().left(0).bottom(FLOOR_H).w(W).h(WALL_H - 20).bg(TINT), "idle-rpg-night-wall", night * 0.35),
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
      ? div().relative().w(72).h(72).child(div().absolute().left(dir > 0 ? 0 : -24).top(0).child(image(`${ART}/${c}-${frame}-${dir > 0 ? "r" : "l"}.png`).w(96).h(72)))
      : image(`${ART}/${c}.png`).w(72).h(72);
    const who = a.program?.name ?? a.app ?? "agent";
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
        .child(div().max_w(CELL_W - 4).px(5).rounded(7).bg("#00000066").truncate().text_size(10).font_semibold().text_color(CREAM).child(who))
        .child(div().max_w(CELL_W - 4).truncate().text_size(10).text_color("#2a1a0c").child(where)),
    ];
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
      .child(image(`${ART}/${c}-rag-${tilt}.png`).w(88).h(88));
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
                      `${ART}/${c}-${!this.youFights ? "f" : [0, "a1", "a2", "a2", 0][this.phaseOf(YOU)] || "f"}-${this.youDir > 0 ? "r" : "l"}.png`,
                    )
                      .w(96)
                      .h(72),
                  ),
              )
          : image(`${ART}/${c}${this.walking ? (this.step ? "-walk-r" : "-walk-l") : ""}.png`).w(72).h(72),
      )
      .child(div().px(6).rounded(7).bg(this.card === YOU ? "#00000080" : "#00000040").text_size(10).font_semibold().text_color(CREAM).child("You"));
  }

  // The four classes as buttons; the current one is ringed.
  picker(key) {
    return h_flex()
      .gap(4)
      .children(
        CLASSES.map((c) =>
          div()
            .id(`idle-rpg-pick-${c}`)
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
            .child(image(`${ART}/${c}.png`).w(36).h(36)),
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
      .child(div().absolute().left(-26).top(-10).child(image(`${ART}/${this.sprites[key]}.png`).w(108).h(108)))
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
    const cardH = (a ? 126 : 86) + (this.picking ? 56 : 0);
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
      .child(div().flex_1().truncate().text_size(12).font_semibold().text_color("#ffffff").child(a ? (a.program?.name ?? a.app ?? "Agent") : "You"))
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
        .child(row("Status", since ? `${word} ${since}` : word))
        .child(row("Where", `${a.space_name} · ${a.tab_name}`))
        .child(row("Doing", a.title || "—"));
    } else {
      facts = facts.child(row("Class", klass[0].toUpperCase() + klass.slice(1)));
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
    this.youFights = hits > 0 && this.joins(W);
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
    actors.sort((p, q) => p.y - q.y);

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
          .child(
            div()
              .id("idle-rpg-night-floor")
              .absolute()
              .left(0)
              .top(0)
              .w(W)
              .h(FLOOR_H)
              .bg(TINT)
              .opacity(this.night * 0.3)
              .transition("opacity", { duration: TICK_MS, easing: "linear" }),
          )
          .children(actors.flatMap((p) => p.draw()))
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
            this.card = this.card === YOU ? null : YOU;
            this.picking = false;
          }
        } else if (pr.kind === "critter") {
          this.card = this.card === pr.address ? null : pr.address;
          this.picking = false;
        } else if (still) {
          this.card = null;
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
                div()
                  .text_size(10)
                  .text_color("#d5e3f0")
                  .child([summary(list) || "nobody in yet", this.battle && this.slain ? `${this.slain} slain` : ""].filter(Boolean).join(" · ")),
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
                if (this.battle) this.fight(0); // someone to fight straight away
                this.save();
                cx.notify();
              })
              .child(this.battle ? "End Raid" : "Start Raid"),
          ),
      )
      .child(floor);
  }
}
