# herdr-vis

[![Release](https://img.shields.io/github/v/release/thanoslabs/herdr-vis?sort=semver&display_name=tag)](https://github.com/thanoslabs/herdr-vis/releases/latest)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?logo=renovatebot)](https://github.com/thanoslabs/herdr-vis/pulls?q=is%3Apr+author%3Aapp%2Frenovate)
[![License: MIT](https://img.shields.io/github/license/thanoslabs/herdr-vis)](LICENSE)

Agent workspace visualizers for the [Herdr](https://herdr.dev) desktop app: layouts that show your coding agents as something more fun than a list.

## Raid Party

![Raid Party battle mode: the party attacking a dragon](raid-party/battle.gif)

A pixel-art castle rampart across the top of the window, under a sky with drifting clouds and a 20-minute day and night. You and every agent are pixel-art adventurers: a wizard, healer, warrior or archer, picked at random on arrival.

| Agent status | What the adventurer does |
|---|---|
| Working | Bounces under two clashing swords |
| Blocked (needs you) | A hopping red "!" bubble |
| Done | A green tick bubble |
| Idle | Rests while z's drift up |

- **Click the floor** to walk there.
- **Click an agent** for a card with its portrait, status, location and a "Go to terminal" button. The wrench on the portrait lets you pick a different class; click yourself to change your own.
- **Drag an agent** to carry it around; release to drop it. Positions and classes are remembered.
- **Battle mode** (the button by the sign, on by default): a random monster (slime, ogre or dragon) stands in the middle with 100 HP and the party forms up around it, warriors up close and the rest at range. Every 3 seconds each working agent attacks for 1 HP, each a moment apart, with its own animation: the warrior swings its sword, the archer draws and shoots, the wizard thrusts its staff and throws a fireball, and the healer lobs a potion that splashes. You join in whenever the party is attacking; as a warrior you have to stand next to the monster to reach it. The monsters are alive too: they blink, the slime squashes and rises, the dragon breathes and sways its tail, and the ogre roars now and then. When the monster falls, another one turns up and the sign counts the kill. Turning battle mode off sends everyone back to their own spots.

Full description of the design and how it is built: [`raid-party/RECIPE.md`](raid-party/RECIPE.md).

## Install

Each visualizer is a folder laid out like Herdr's config folder (`~/.config/herdr-app`): `layouts/`, `mods/`, `themes/`.

Clone the repo and copy the layout into Herdr:

```sh
git clone https://github.com/thanoslabs/herdr-vis.git
cd herdr-vis
./install.sh raid-party
herdr-app do layout.switch --name raid-party
```

`install.sh` copies the layout, theme and mod into `~/.config/herdr-app` (or `$HERDR_APP_HOME`), which is how Herdr expects layouts to be added. Run it again after a `git pull` to update. To remove the layout, delete `layouts/raid-party.json`, `layouts/raid-party.svg`, `themes/raid-party.json` and `mods/raid-party/` from that folder; your other layouts are untouched.

Alternatively, ask your agent inside Herdr to read `~/.config/herdr-app/AGENTS.md` and add the layout from this repo's `raid-party` folder.

## Developing

- Edit the files in this repo, then run `./install.sh raid-party` to copy them into Herdr. Herdr reloads layouts and mods as they change; if a mod edit does not show, switch layouts away and back.
- Run `herdr-app check raid-party/mods/raid-party` after every mod change, and `herdr-app status` to see errors.
- All the pixel art is generated: edit the grids in `tools/raid-party-sprites.py` and run `python3 tools/raid-party-sprites.py raid-party/mods/raid-party/art`.
- Herdr writes `gpui-kit.d.ts` and `jsconfig.json` into each mod folder; they are git-ignored.
- See [CONTRIBUTING.md](CONTRIBUTING.md) for branch, commit and release conventions.

## Layout

```
.
├── install.sh       # copies a visualizer into ~/.config/herdr-app
├── tools/           # raid-party-sprites.py: draws every PNG in art/
├── raid-party/
│   ├── layouts/     # raid-party.json (the window), raid-party.svg (settings preview)
│   ├── mods/        # raid-party/ (main.js, mod.json, art/)
│   ├── themes/      # raid-party.json
│   ├── RECIPE.md    # the brief the layout is built from
│   └── preview.png
└── .github/         # CI, release and Renovate workflows
```

## License

[MIT](LICENSE)
