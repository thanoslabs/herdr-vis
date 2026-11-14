# Idle RPG: plan

Planning notes for growing this layout from a visualizer with a battle mode into an idle RPG. Steps 1 to 3 of the proposed order (bookkeeping, experience, and class skills with per-attacker cadence) are built, and the colours and hats of step 4 (a shop selling colourways and hats); the rest is not. "Decided" items come from the repo owner; "Default" items were chosen while building and are constants in `mods/idle-rpg/rules.js`, easy to retune; "Proposed" items are suggestions that still need a yes.

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
- Default: Crit adds 5% chance per rank of a blow dealing double damage (`CRIT_CHANCE`, `CRIT_MULTIPLIER`), shown as a gold damage number (or, with damage numbers off, a small gold number on a pill) where it lands.
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

### Customisation shop

- **Decided:** colours first, then hats and alternate sprites. **Colours built**, sold as "Armours": a shop opened from the gold on the sign, with the kinds of item down its left side (Armours, Weapons, Hats, and room for more). **Owner's decision:** the shop is laid out by category this way because much more is planned for it. **Hats built** (below). Weapons and alternate sprites are **not built**: the Weapons category is there and empty.
- Default: a look belongs to a class, not to an agent (agents are short-lived and forgotten after a week). Every character with that class on, agents and the player alike, wears the colourway the class has equipped.
- Default: each class has its default colourway (free, always owned) and three more to buy, priced 5, 10 and 20 gold (`COLOUR_PRICES`). Buying is permanent; an owned colourway can be equipped and swapped freely at no cost. No refunds, no selling.
- Default: buying a colourway also puts it on (one click; the default or any other owned one is a free click away).
- Gold can never go negative; a purchase that cannot be afforded does nothing (the Buy button is dimmed).
- **Owner's decision:** the codex, the shop and the skills are also reachable between raids, from stations on the rampart: a book on the table (codex), a merchant's stall (shop) and a training dummy (skills; the dummy was my pick, a **default**). **Built.** Starting or ending a raid closes whichever panel is open.
- **Owner's request:** a campfire in the middle of the non-raid screen. **Built:** scenery, not clickable, drawn among the characters by depth, kept clear of the stations, with its own pool of light at night.
- Colourways are palette swaps in `tools/idle-rpg-sprites.py` (`LOOKS`) of every picture a class has, drawn into `art/classes/<class>/<id>/`; the default's are in `art/classes/<class>/default/`. The catalogue (`SHOP` in `rules.js`) has one entry per kind of item with a list per class, and the state keeps owned and equipped per class per kind; hats were added as another kind this way, marked `shared` so that what is owned is kept once for every class.

#### Hats

- **Owner's decision:** hats are customisations that are not locked to a class (a jack-o'-lantern helmet, a party hat, a Santa hat), and buying a hat unlocks it to be worn by any character: bought once, owned by all four classes. **Built.** Ownership is kept once, in the state's `hats`, not per class.
- Default: which hat is on stays per class, like armours: every character with a class on wears the hat the class has picked (`looks.<class>.hat.equipped`), so each class can wear a different owned hat, or the same one. Buying also puts it on the class shown in the shop; the others pick it for free.
- Default: three hats, the same for every class: Party Hat (10 gold), Santa Hat (20) and Pumpkin (30) (`HAT_PRICES`), plus "No hat" (free, always owned): the class's own headgear.
- Default: hats and armours combine freely; a hat covers only the head, so it looks the same over every colourway.
- Default: hats are drawn as overlay layers: for each hat, class and picture, a see-through PNG the size of the picture it lies on (`art/hats/<id>/<class>/<frame>.png`), so the mod lays one image over the other with no anchor sums. The generator pushes each hat through the same canvas, lean, shear and mirror as the body, so it follows the head when walking and dangling, and in the healer's mirrored fighting poses.
- Default: each hat is drawn per class, because every head sits in its own place and three classes wear their own headgear: it covers the wizard's hat entirely, sits over the warrior's plume and the archer's cap and feather, and replaces the top of the healer's hood. The party and Santa hats leave the face showing; the jack-o'-lantern is a helmet over the whole head, with a carved face.
- Default: the shop's Hats tab shows the chosen class wearing each hat over the armour it has on, says "Bought once, for every class" under the kinds, and the armour previews show the class's hat too.

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
- (Who owns a purchase, whether looks are per class, where the shop lives and the prices of colourways now have defaults: per class, a panel under the sign, 5, 10 and 20 gold. See Customisation shop.)
- (How hats are drawn, their prices, whether they combine with colourways and who owns them now have answers: overlay layers, 10, 20 and 30 gold, freely, and every class. See Hats.)
- Alternate sprites: whether they replace a class's look entirely, and how they combine with colourways.

### Scaling

- Do monsters get more HP as levels or kills go up? Stronger attacks will otherwise shorten every fight, and gold income depends on monster HP. **Decided:** a later iteration; HP is fixed by kind for now.

### Display and settings

- **Owner's request:** damage numbers: each blow that lands shows its damage in a pixel font, drifting up and fading, and can be turned off in the settings. **Built** (crits gold and a size bigger; on by default; at most 12 on screen).
- **Owner's request:** a settings menu behind a pixel gear, the right-most thing in the top-right corner. **Built** as a panel in the codex's style with a pixel on/off switch per setting; `SETTINGS` in `rules.js` is the list, so a setting is one more entry.
- **Owner's request:** the agents' status counts moved off the sign to the top-right corner, each an icon with its count on a badge in the pixel font, hidden at 0. **Built**; below 640px wide the corner's strip sits under the sign.
- The pixel font is art: digits, "+" and "!" in white and gold, drawn by `tools/idle-rpg-sprites.py`. More characters or colours are more glyphs there and in `GLYPHS` / `GLYPH_COLOURS`.

## Technical notes

- **State today** (`idle-rpg.state` in Herdr's shared state, version 4): `version`, `you`, `spots`, `sprites`, `seen`, `battle`, `monster` (with `maxHp`), `slain`, `gold`, `kills` per monster kind, `xp` for `you` and each class (total XP only; levels are derived), `skills`: ranks per class (points left are derived), `looks`: per class and kind of item, the ids owned and the one equipped (`{ armour: { owned, equipped }, weapon: { owned, equipped }, hat: { equipped } }`), `hats`: the hats bought, owned by every class, and `settings` (`{ damageNumbers }`, booleans). Version 1 state loads with every rank at 0; ranks that claim more points than a class has earned reset that class. Version 1 and 2 state loads with every class owning and wearing only its default colourway; versions 1 to 3 load with no hats owned and none on; unknown or repeated ids are dropped and an equipped id that is not owned falls back to the default. Version 1 to 3 state loads with every setting at its default; unknown settings are dropped and one that is not a boolean gets its default. Each attacker's rhythm is in memory only. `loadState` in `rules.js` reads older state and malformed values without throwing. See `RECIPE.md`.
- **Saving (decided):** combat progress (monster HP, XP) is saved only when a monster is slain and when the next one spawns, not as damage lands: setting a shared value re-renders every mod in the window, and Power and Haste would make damage-based saves frequent. HP and XP earned since the last kill are lost if the app closes mid-fight. Deliberate actions save at once: spending or resetting points, buying or equipping in the shop, changing a setting, changing a class, the raid toggle, moving yourself or an agent, a newcomer getting a class.
- **State still to add:** weapons and alternate sprites, as more kinds under `looks`.
- **Existing kill total** cannot be split by monster kind after the fact. It is kept as the total and the per-kind counts start from zero.
- **Per-attacker cadence** replaced the single 3-second beat: each attacker keeps its own rhythm on one 250ms clock that runs only while someone is attacking and re-renders only while someone is mid-attack. **Built.**
- **Stronger attacks:** `fight()` takes a list of blows, each with its own damage.
- **Customisation art** is the costly part. Every character is drawn in a standing sprite, walk frames, dangling frames and three fighting poses in two directions: twelve pictures. Colours are generated by swapping palette entries in `tools/idle-rpg-sprites.py` (**built**: 3 colourways × 4 classes × 12 pictures, 144 more files, about 98 KB). Hats are drawn as a separate layer over each picture (**built**: 3 hats × 4 classes × 12 pictures, 144 more files, about 54 KB), so they do not multiply with colourways.
- **`main.js` is one class of about 2,100 lines.** A Herdr mod may import other files in its folder (`./rules.js`; Herdr's own `win98` mod does), so the game rules (experience, levels, skill points and what ranks give, attack gaps, the crit roll, monster HP, gold, kill counts, loading state) live in `rules.js` as plain functions, and `main.js` draws and runs the timers.
- **Progress only accrues while the layout is shown**, since the timers live in the mod. Whether that is acceptable for an idle game is worth a decision.

## Proposed order

1. State and bookkeeping: versioned state, kills per monster kind, gold on a kill, shown on the sign. **Built.**
2. Experience: player and class experience and levels, shown on the info cards. No unlocks yet. **Built** (levels also on the class picker, and a note over the head on a level-up).
3. Class unlocks: stronger and faster attacks, then buffs. Needs per-attacker cadence. **Built** as per-class skill points (Power, Haste, Crit), with per-attacker cadence and monster HP by kind; buffs not built.
4. Customisation shop: colours first (cheap to generate), then hats and alternate sprites. **Colours built** (a shop under the sign, colourways per class) and **hats built** (bought once for every class, worn per class); alternate sprites not built.
5. Monsters fighting back, once its design questions are answered.

Parked beyond this: what player levels unlock, maps, resources other than gold.
