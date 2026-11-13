# herdr-vis

[![Release](https://img.shields.io/github/v/release/thanoslabs/herdr-vis?sort=semver&display_name=tag)](https://github.com/thanoslabs/herdr-vis/releases/latest)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?logo=renovatebot)](https://github.com/thanoslabs/herdr-vis/pulls?q=is%3Apr+author%3Aapp%2Frenovate)
[![License: MIT](https://img.shields.io/github/license/thanoslabs/herdr-vis)](LICENSE)

Agent workspace visualizers for the [Herdr](https://herdr.dev) desktop app: layouts that show your coding agents as something more fun than a list.

## Idle RPG

Turn your agents into a raid party. Collect loot and upgrades as you progress.

![Idle RPG battle mode: the party attacking a dragon through a day and a night](idle-rpg/battle.gif)

*The day and night are sped up here: a full cycle takes 20 minutes, not 18 seconds.*

A pixel-art castle rampart across the top of the window, under a sky with drifting clouds and a 20-minute day and night. At night the rampart goes dim, lit by pools of torchlight. You and every agent are pixel-art adventurers: a wizard, healer, warrior or archer, picked at random on arrival.

| Agent status | What the adventurer does |
|---|---|
| Working | Bounces under two clashing swords |
| Blocked (needs you) | A hopping red "!" bubble |
| Done | A green tick bubble |
| Idle | Rests while z's drift up |

- **Click the floor** to walk there.
- **Click an agent** for a card with its portrait, what kind of agent it is, its status and a "Go to terminal" button. Each agent is named for the space and tab it works in. The wrench on the portrait lets you pick a different class; click yourself to change your own.
- **Drag an agent** to carry it around; release to drop it. Positions and classes are remembered.
- **Battle mode** (the Start Raid / End Raid button by the sign, on by default): a random monster (a slime with 100 HP, an ogre with 300 or a dragon with 500) stands in the middle and the party forms up around it, warriors up close and the rest at range. Each working agent attacks on its own rhythm, every 3 seconds to begin with (faster with Haste, below), the damage coming off as the blow lands, with its own animation: the warrior swings its sword, the archer draws and shoots, the wizard thrusts its staff and throws a fireball, and the healer lobs a potion that splashes. You join in whenever the party is attacking; as a warrior you have to stand next to the monster to reach it. The monsters are alive too: they blink, the slime squashes and rises, the dragon breathes and sways its tail, and the ogre roars now and then. When the monster falls, another one turns up, and the sign counts the kill and the gold it dropped (1 gold per 100 HP: 1, 3 or 5). Turning battle mode off sends everyone back to their own spots.
- **Experience and levels:** progress belongs to you and to the four classes, never to an agent. Every point of damage that lands earns experience for the attacker's class and for you, who lead the raid. Each class levels on its own, and so do you; a gold note pops up over the head of whoever levels up. Your card shows your level, and every card the level of that character's class, with progress to the next, and the class picker shows every class's level. Your own level unlocks nothing yet. Combat progress is saved each time a monster falls.
- **Skill points:** each level a class gains earns it a skill point, spent on that class's skills, which then apply to everyone with that class on, agents and you alike. Three skills for every class, up to rank 5 each: **Power** (+1 damage a blow per rank), **Haste** (a quarter of a second less between attacks per rank, from 3s down to 1.75s) and **Crit** (+5% chance per rank of a blow dealing double damage, shown as a small gold number where it lands). A gold star on the sign shows the points you have to spend; click it, or the class line on any card, to open the skills panel, pick a class and spend them. Reset gives a class all its points back for free.
- **The shop:** click the gold on the sign to spend it on colourways. Like progress, a look belongs to a class, not an agent: every character with that class on, agents and you alike, wears the colourway the class has equipped. Each class has its own colours plus three more to buy for 5, 10 and 20 gold (the wizard in Crimson, Moss or Frost, the healer in Rose, Sky or Plum, the warrior in Cobalt, Jade or Ruby, the archer in Scarlet, Azure or Dusk). Each one is shown as the sprite in that colourway; once bought it is yours for good, and you can switch between the ones you own for free. Hats and other sprites are planned.
- **The sign and the codex:** the sign counts your agents by status with pixel icons (crossed swords for working, a "Zz" for resting), then a skull with the monsters slain, a coin with your gold (1 gold for every 100 HP of a monster, paid when it falls) and a star with skill points to spend. Click the skull to open the codex, which lists how many of each kind you have slain; a kind you have not beaten yet shows as "???". Click the coin to open the shop.

Full description of the design and how it is built: [`idle-rpg/RECIPE.md`](idle-rpg/RECIPE.md).

## Install

Each visualizer is a folder laid out like Herdr's config folder (`~/.config/herdr-app`): `layouts/`, `mods/`, `themes/`.

Clone the repo and copy the layout into Herdr:

```sh
git clone https://github.com/thanoslabs/herdr-vis.git
cd herdr-vis
./install.sh idle-rpg
herdr-app do layout.switch --name idle-rpg
```

`install.sh` copies the layout, theme and mod into `~/.config/herdr-app` (or `$HERDR_APP_HOME`), which is how Herdr expects layouts to be added. Run it again after a `git pull` to update. To remove the layout, delete `layouts/idle-rpg.json`, `layouts/idle-rpg.svg`, `themes/idle-rpg.json` and `mods/idle-rpg/` from that folder; your other layouts are untouched.

Alternatively, ask your agent inside Herdr to read `~/.config/herdr-app/AGENTS.md` and add the layout from this repo's `idle-rpg` folder.

## Developing

- Edit the files in this repo, then run `./install.sh idle-rpg` to copy them into Herdr. Herdr reloads layouts and mods as they change; if a mod edit does not show, switch layouts away and back.
- Run `herdr-app check idle-rpg/mods/idle-rpg` after every mod change, and `herdr-app status` to see errors.
- All the pixel art is generated: edit the grids in `tools/idle-rpg-sprites.py` and run `python3 tools/idle-rpg-sprites.py idle-rpg/mods/idle-rpg/art`.
- Herdr writes `gpui-kit.d.ts` and `jsconfig.json` into each mod folder; they are git-ignored.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for branch, commit and release conventions.

## Layout

```
.
├── install.sh       # copies a visualizer into ~/.config/herdr-app
├── tools/           # idle-rpg-sprites.py: draws every PNG in art/
├── idle-rpg/
│   ├── layouts/     # idle-rpg.json (the window), idle-rpg.svg (settings preview)
│   ├── mods/        # idle-rpg/ (main.js, rules.js, mod.json, art/)
│   ├── themes/      # idle-rpg.json
│   ├── RECIPE.md    # the brief the layout is built from
│   └── preview.png
└── .github/         # CI, release and Renovate workflows
```

## License

[MIT](LICENSE)
