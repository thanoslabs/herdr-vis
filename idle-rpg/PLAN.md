# Idle RPG: plan

Planning notes for growing this layout from a visualizer with a battle mode into an idle RPG. Steps 1 to 3 of the proposed order (bookkeeping, experience, and class skills with per-attacker cadence) are built; the rest is not. "Decided" items come from the repo owner; "Default" items were chosen while building and are constants in `mods/idle-rpg/rules.js`, easy to retune; "Proposed" items are suggestions that still need a yes.

## Principles

- **It stays a visualizer first.** Nothing needs clicking to keep progressing, and nothing rewards leaving agents running for no reason.
- **Progress never belongs to an agent.** Agents are short-lived, and the mod forgets one after a week. Progress belongs to the player and to the classes.

## Decided

### Player experience

- The player has their own experience and level. **Built.**
- What player levels unlock is **not decided yet** (parked).
- Default: the player earns 1 XP per point of damage dealt by anyone in the party, their own blows included (`PLAYER_XP_PER_HP`). The player leads the raid.
- Default: going from level n to n + 1 costs `250 * n` XP (`PLAYER_LEVEL_XP`), no cap. Total XP is stored and the level derived from it.

### Class experience

- Each class (wizard, healer, warrior, archer) has its own level. **Built.**
- A class earns experience whenever it is equipped on an agent or on the player and that character attacks. **Built**, counting only blows that land.
- Class levels unlock stronger attacks, faster attacks, buffs and similar. **Built** as skill points (below); buffs not built.
- Default: per point of damage, not per attack: 1 XP per point a character of that class deals (`CLASS_XP_PER_HP`). Now that blows can deal more than 1, stronger blows earn more; overkill counts only what lands.
- Default: going from level n to n + 1 costs `100 * n` XP (`CLASS_LEVEL_XP`), no cap. Everyone starts at level 1 with 0 XP.
- Default: several agents on one class each earn that class XP, so it levels faster. Intended.

### Skill points

- **Decided:** skill points are earned and spent per class: each class earns 1 point per class level gained (points earned = class level - 1), spent on that class's skills, which apply to every character with that class on, agents and the player alike. **Built**, with a skills panel opened from a star on the sign (points left to spend) and from the class line on a card.
- **Decided:** skills are generic for now, the same for every class. Class-specific perks are **not decided** (parked); `CLASS_SKILLS` in `rules.js` keeps a list per class so one can get its own without a rewrite.
- **Decided:** the player's own level still unlocks nothing.
- Default: three skills, Power, Haste and Crit (`SKILLS`).
- Default: Power adds 1 damage per blow per rank, from 1 at rank 0 (`BASE_DAMAGE`, `POWER_DAMAGE`).
- Default: Haste shortens the time between one character's attacks by one 250ms tick per rank: 3s at rank 0, then 2.75, 2.5, 2.25, 2 and 1.75s at rank 5 (`ATTACK_TICKS`). Each gap is the rank's give or take up to 2 ticks at random (`ATTACK_JITTER`), never under 6 ticks (`MIN_ATTACK_TICKS`, so an attack and its impact have finished before the next starts).
- Default: Crit adds 5% chance per rank of a blow dealing double damage (`CRIT_CHANCE`, `CRIT_MULTIPLIER`), shown as a small gold number where it lands.
- Default: max rank 5 per skill (`MAX_RANK`), 1 point per rank (`RANK_COST`), 1 point per level (`POINTS_PER_LEVEL`).
- Default: Reset is free and refunds all of a class's points.

### Gold

- 1 gold per 100 HP of monster slain. **Built**, shown on the sign.
- Awarded only when the monster is slain, not as damage is dealt.
- Default: `Math.floor(maxHp / 100)` (`HP_PER_GOLD`): rounded down. Each monster records its `maxHp` when it spawns.

### Monster HP

- **Decided:** HP by kind: slime 100, ogre 300, dragon 500 (`MONSTER_HP`), so gold is 1, 3 and 5. **Built.** A monster saved with `maxHp` 100 keeps it until slain.
- **Decided:** scaling monsters with levels or kills is a later iteration, not built (see Scaling).
- For now gold only buys customisation for characters: different sprites, colours, hats and so on.

### Kill counts

- Keep a count of each type of monster slain, not just the total. **Built**: saved, and shown in the codex that opens from the kill count on the sign. Not used for anything else yet.

### Monsters fighting back

- Not built today. Likely to be introduced as part of this work, but the design is open (see below).

## Open questions

### Experience

- Class-specific perks, and whether any arrive at particular levels (skills are generic for now).
- Whether the skill numbers above feel right in play; they are defaults.
- (How experience is earned, per attack or per point, several agents on one class, and the level curve and cap now have defaults; see Decided.)

### Monsters fighting back

- What does damage to the party mean when agents are short-lived? Options: a shared party HP bar, HP per class, or knock-outs that sit a character out for a few beats.
- What happens at zero: the monster heals, the party retreats, or progress on that monster is lost?
- Does the healer start healing the party instead of (or as well as) throwing potions at the monster?
- Does the player take damage, and can they dodge by walking away?

### Gold and customisation

- (Rounding when monster HP is not a multiple of 100 now has a default: round down. See Decided.)
- Who owns a purchase: the player's account, with items applied per class or per character?
- An agent's look is forgotten with the agent. Should looks be set per class so they survive?
- Where the shop lives. The scene is a strip of at most 560px above the terminals; the info card is small.
- Prices.

### Scaling

- Do monsters get more HP as levels or kills go up? Stronger attacks will otherwise shorten every fight, and gold income depends on monster HP. **Decided:** a later iteration; HP is fixed by kind for now.

## Technical notes

- **State today** (`idle-rpg.state` in Herdr's shared state, version 2): `version`, `you`, `spots`, `sprites`, `seen`, `battle`, `monster` (with `maxHp`), `slain`, `gold`, `kills` per monster kind, `xp` for `you` and each class (total XP only; levels are derived), and `skills`: ranks per class (points left are derived). Version 1 state loads with every rank at 0; ranks that claim more points than a class has earned reset that class. Each attacker's rhythm is in memory only. `loadState` in `rules.js` reads older state and malformed values without throwing. See `RECIPE.md`.
- **Saving (decided):** combat progress (monster HP, XP) is saved only when a monster is slain and when the next one spawns, not as damage lands: setting a shared value re-renders every mod in the window, and Power and Haste would make damage-based saves frequent. HP and XP earned since the last kill are lost if the app closes mid-fight. Deliberate actions save at once: spending or resetting points, changing a class, the raid toggle, moving yourself or an agent, a newcomer getting a class.
- **State still to add:** owned and equipped customisations.
- **Existing kill total** cannot be split by monster kind after the fact. It is kept as the total and the per-kind counts start from zero.
- **Per-attacker cadence** replaced the single 3-second beat: each attacker keeps its own rhythm on one 250ms clock that runs only while someone is attacking and re-renders only while someone is mid-attack. **Built.**
- **Stronger attacks:** `fight()` takes a list of blows, each with its own damage.
- **Customisation art** is the costly part. Every character is drawn in a standing sprite, walk frames and three fighting poses in two directions. Colours can be generated by swapping palettes in `tools/idle-rpg-sprites.py`. Hats either multiply the sprite count or are drawn as a separate layer placed over the head in each pose.
- **`main.js` is one class of about 1,600 lines.** A Herdr mod may import other files in its folder (`./rules.js`; Herdr's own `win98` mod does), so the game rules (experience, levels, skill points and what ranks give, attack gaps, the crit roll, monster HP, gold, kill counts, loading state) live in `rules.js` as plain functions, and `main.js` draws and runs the timers.
- **Progress only accrues while the layout is shown**, since the timers live in the mod. Whether that is acceptable for an idle game is worth a decision.

## Proposed order

1. State and bookkeeping: versioned state, kills per monster kind, gold on a kill, shown on the sign. **Built.**
2. Experience: player and class experience and levels, shown on the info cards. No unlocks yet. **Built** (levels also on the class picker, and a note over the head on a level-up).
3. Class unlocks: stronger and faster attacks, then buffs. Needs per-attacker cadence. **Built** as per-class skill points (Power, Haste, Crit), with per-attacker cadence and monster HP by kind; buffs not built.
4. Customisation shop: colours first (cheap to generate), then hats and alternate sprites.
5. Monsters fighting back, once its design questions are answered.

Parked beyond this: what player levels unlock, maps, resources other than gold.
