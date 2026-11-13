# Contributing

## Getting Started

1. Fork the repository
2. Clone your fork
3. Install the pinned tool versions from `.tool-versions`: `asdf install` (or `mise install`)
4. Create a branch: `git checkout -b feat/your-feature-name`
5. Make your changes and try them in Herdr: `./install.sh raid-party`
6. Commit using [conventional commits](#commit-style)
7. Push and open a Pull Request

## Branch Naming

Branches should follow: `feat|bug|hotfix|release|chore/brief-3-5-word-description`

Examples:
- `feat/add-pinned-agent-marker`
- `bug/fix-card-position`
- `chore/update-dependencies`

## Commit Style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `chore`, `docs`, `test`, `refactor`, `perf`, `ci`

Examples:
- `feat(raid-party): add a marker for pinned agents`
- `fix(install): reject names containing a path`
- `chore(ci): bump actions/checkout`

## Versioning

Releases and tags follow [Semantic Versioning](https://semver.org/):

- Format is bare `X.Y.Z` — **no prefix** (`1.4.2`, not `v1.4.2`)
- **MAJOR** — breaking changes
- **MINOR** — backwards-compatible features
- **PATCH** — backwards-compatible fixes

Releases are cut automatically when a PR merges to `main`, based on its `major`/`minor`/`patch` label (default: `patch`). To release a specific version, run the **Release** workflow (`.github/workflows/release.yaml`) with an explicit `X.Y.Z` version.

## Pull Requests

- Link any related issues
- Ensure CI passes before requesting review
- Maintainers will review within 48 hours

## Code Standards

- Write clear, commented code
- Run `herdr-app check <mod folder>` after every mod change, and `herdr-app status` with the layout shown
- Art is original: do not copy characters or artwork from existing games or products
- Regenerate art with `python3 tools/raid-party-sprites.py raid-party/mods/raid-party/art` rather than editing PNGs by hand
- Keep the visualizer's `RECIPE.md`, `preview.png` and the README in step with user-facing changes
