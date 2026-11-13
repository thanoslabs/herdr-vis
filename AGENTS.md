# AGENTS.md

## Purpose

Agent workspace visualizers for the [Herdr](https://herdr.dev) desktop app. Each top-level folder (currently `idle-rpg/`) is one layout, laid out like Herdr's config folder so `install.sh` can copy it into `~/.config/herdr-app`.

## Tech stack

- **Herdr layouts** (`layouts/*.json`), **themes** (`themes/*.json`) and **mods** (`mods/<name>/main.js`, JavaScript against gpui-kit; no HTML, CSS or Node APIs)
- **Python 3** (standard library only) for `tools/idle-rpg-sprites.py`, which draws the art, and a POSIX `sh` installer
- **Renovate** and **GitHub Actions** (CI, release)
- **MIT License**

## Structure

```
.
├── idle-rpg/                      # One visualizer
│   ├── layouts/              # idle-rpg.json, idle-rpg.svg (settings preview)
│   ├── mods/idle-rpg/             # main.js, rules.js, mod.json, art/*.png
│   ├── themes/               # idle-rpg.json
│   ├── RECIPE.md             # Brief another agent could rebuild it from
│   ├── PLAN.md               # Planning notes for growing it into an idle RPG
│   ├── preview.png           # Still, for Herdr's gallery
│   └── battle.gif            # Battle mode in motion, for the README
├── tools/                    # idle-rpg-sprites.py: generates every PNG in art/
├── install.sh                # Copies a visualizer into ~/.config/herdr-app
├── .github/                  # CODEOWNERS, Renovate config, workflows (CI, release, Renovate)
├── .tool-versions            # Pinned tool versions (asdf/mise)
├── AGENTS.md
├── CONTRIBUTING.md
├── README.md
├── SECURITY.md
└── renovate.json
```

## Working on a visualizer

- The reference for layouts, mods and the `herdr` module is `~/.config/herdr-app/AGENTS.md` and the `.d.ts` files beside it, rewritten by the app to match the installed version. Read them before changing a mod.
- Edit files in the repo, then run `./install.sh idle-rpg` to copy them into Herdr. After every mod change run `herdr-app check <mod folder>`, then `herdr-app status` with the layout shown. `check` renders with no agents, so test agent-dependent code with a hard-coded fake agent.
- `herdr-app shot <file.png>` captures the window for visual checks.
- Keep each visualizer's `RECIPE.md`, `preview.png` and `battle.gif` in step with its files.
- Art is original. Do not copy characters or artwork from existing games or products.
- `gpui-kit.d.ts` and `jsconfig.json` inside mod folders are written by Herdr and git-ignored.

## Conventions

- `.tool-versions` is the single source of truth for language and tool versions. Before building, testing, or running any tooling, check it and use the pinned versions (install via `asdf install` or `mise install`). When adding a new language or tool to the project, pin its version there first — never assume a globally installed version.
- Versioning: releases and tags follow [SemVer](https://semver.org/) as bare `X.Y.Z` — no `v` prefix (`1.4.2`, not `v1.4.2`). Bump MAJOR for breaking changes, MINOR for backwards-compatible features, PATCH for fixes.
- See `CONTRIBUTING.md` for branch naming, commit style and pull requests.
- Branch protection: never push directly to `main`; all changes via PR with review.

## Releases

- Releases are versioned with [SemVer](https://semver.org/) as bare `X.Y.Z` tags — no `v` prefix.
- **Automatic bumps**: when a PR merges to `main`, the next version is derived from the PR label:
  - `major` — breaking changes
  - `minor` — backwards-compatible features
  - `patch` — fixes
  - No label — defaults to a `patch` bump
- **Manual releases**: a specific version may be cut manually by supplying an explicit `X.Y.Z` version tag when needed (e.g. via a manual workflow dispatch). This bypasses the label-based bump.
- Release automation lives in `.github/workflows/release.yaml`: it computes the next version, tags, and creates the GitHub release. Nothing is built; a release is the repo at that tag.
