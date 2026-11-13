# CLAUDE.md

## Purpose

Agent workspace visualizers for the [Herdr](https://herdr.dev) desktop app. Each top-level folder (currently `rpg/`) is one layout, laid out like Herdr's config folder so it can be linked or copied into `~/.config/herdr-app`.

## Tech stack

- **Herdr layouts** (`layouts/*.json`), **themes** (`themes/*.json`) and **mods** (`mods/<name>/main.js`, JavaScript against gpui-kit; no HTML, CSS or Node APIs)
- **Renovate**, **GitHub Actions** (release, docs) and **[nebula-md](https://github.com/thanoslabs/nebula-md)** for the docs site, from the org template
- **MIT License**

## Structure

```
.
├── rpg/                # One visualizer
│   ├── layouts/              # rpg.json, rpg.svg (settings preview)
│   ├── mods/rpg/       # main.js, mod.json, art/*.png
│   ├── themes/               # rpg.json
│   ├── RECIPE.md             # Brief another agent could rebuild it from
│   └── preview.png
├── tools/                    # rpg-sprites.py: generates every PNG in art/
├── install.sh                # Copies a visualizer into ~/.config/herdr-app
├── .agents/                  # Agent instructions and skills
├── .github/                  # CODEOWNERS, Renovate config, workflows
├── docs/                     # Docs site source
├── AGENTS.md
├── CONTRIBUTING.md
├── README.md
└── renovate.json
```

## Working on a visualizer

- The reference for layouts, mods and the `herdr` module is `~/.config/herdr-app/AGENTS.md` and the `.d.ts` files beside it, rewritten by the app to match the installed version. Read them before changing a mod.
- After every mod change run `herdr-app check <mod folder>`, then `herdr-app status` with the layout shown. `check` renders with no agents, so test agent-dependent code with a hard-coded fake agent.
- `herdr-app shot <file.png>` captures the window for visual checks.
- Keep each visualizer's `RECIPE.md` and `preview.png` in step with its files.
- Art is original. Do not copy characters or artwork from existing games or products.
- `gpui-kit.d.ts` and `jsconfig.json` inside mod folders are written by Herdr and git-ignored.

## Conventions

- `.tool-versions` is the single source of truth for language and tool versions. Before building, testing, or running any tooling, check it and use the pinned versions (install via `asdf install` or `mise install`). When adding a new language or tool to the project, pin its version there first — never assume a globally installed version.
- Versioning: project artifacts (releases, tags, packages, images) follow [SemVer](https://semver.org/) as bare `X.Y.Z` — no `v` prefix (`1.4.2`, not `v1.4.2`). Bump MAJOR for breaking changes, MINOR for backwards-compatible features, PATCH for fixes.
- See `AGENTS.md` for full agent workflow, code style, testing, and git/PR guidance.
- Branch protection: never push directly to `main`; all changes via PR with review.
- When adapting this template for a new project, update `renovate.json` managers/schedules and enable the repo in the Renovate GitHub App.
- Project-specific `CLAUDE.md` / `AGENTS.md` content should be filled in once the actual stack is added (`src/`, `tests/`, build commands, etc. are placeholders in `AGENTS.md`, not present here).

## Releases

- All released artifacts (images, binaries, packages) are versioned with [SemVer](https://semver.org/) as bare `X.Y.Z` tags — no `v` prefix.
- **Automatic bumps**: when a PR merges to `main`, the next version is derived from the PR label:
  - `major` — breaking changes
  - `minor` — backwards-compatible features
  - `patch` — fixes
  - No label — defaults to a `patch` bump
- **Manual releases**: a specific version may be cut manually by supplying an explicit `X.Y.Z` version tag when needed (e.g. via a manual workflow dispatch). This bypasses the label-based bump.
- Release automation lives in `.github/workflows/release.yaml`: it computes the next version, tags, and creates the GitHub release. Building and publishing artifacts (images, binaries) is project-specific and left as a TODO stub in the workflow.

## Docs

- Project documentation lives in `docs/` as markdown and is the source for the project's docs site. Do not introduce another static site generator (MkDocs, Docusaurus, etc.) — docs are built with [nebula-md](https://github.com/thanoslabs/nebula-md).
- `.github/workflows/docs.yaml` calls nebula-md's reusable workflow (`thanoslabs/nebula-md/.github/workflows/deploy.yml`) on pushes to `main` that touch `docs/`. Generation happens in CI only — do not commit built HTML.
- Deployment to GitHub Pages runs only when the repository is **public**; private repos skip the job. Public repos must set **Settings → Pages → Source** to **GitHub Actions**.
- Pages are Obsidian-flavoured markdown: YAML frontmatter (`title`, `tags`, `date`), `[[wikilinks]]` between pages, and callouts. `docs/index.md` is the site's landing page.
