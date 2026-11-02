# AGENTS.md — Sonic Riders Online

Guidance for AI agents and humans working in this repository. Read this first, then the planning documents linked below.

## Overview

Sonic Riders Online is a fan project that rebuilds Sonic Riders (GameCube, USA) from its decompilation as a base and adds:

1. **Custom maps** — new race tracks built from map assets (geometry, collision, checkpoints, item boxes, spawn points) arranged for easy navigation.
2. **Online play** — rooms/lobbies and networked races.
3. **Leaderboards** — per-track best times and scores, submitted by the game and verified server-side.

## Goals

- G1. Byte-matching build of the US DOL from the decomp source (verification baseline, not the shipped product).
- G2. Extract and document the game's stage/track data formats from a user-supplied disc or DOL.
- G3. A map pipeline: author a track from exported assets, validate it, and load it in-game.
- G4. A navigation-friendly map layout: named sections, checkpoint order, minimap/route data, and spawn/respawn points.
- G5. Online rooms and races with a server-side source of truth for results.
- G6. Leaderboards with authenticated, validated submissions.

Non-goals (until a later decision): modding Sonic Riders DX/TE ports, art asset creation, monetization, mobile builds.

## Architecture (planned, see docs/)

| Area | Location | Doc |
|---|---|---|
| Decomp baseline (matching DOL) | `decomp/` (git submodule, pinned) | docs/decomp-baseline.md |
| Asset and format extraction | `tools/extract/` | docs/asset-extraction.md |
| Map authoring and validation | `tools/mapkit/`, `maps/` | docs/custom-maps.md |
| Navigation data and layout | `maps/*/nav/`, `tools/mapkit/` | docs/map-navigation.md |
| Runtime port and custom-map loading | `port/` | docs/runtime-port.md |
| Online rooms and netcode | `port/net/`, `server/` | docs/online-multiplayer.md |
| Leaderboards API and storage | `server/` | docs/leaderboards.md |
| Legal and asset handling | repo root | docs/legal-and-assets.md |

Directories marked "planned" do not exist yet. Update this table when a directory is created.

## Constraints

- **Never commit copyrighted game material**: no `baserom.dol`, disc images, ARC/archive dumps, original models, textures, audio, or extracted game assets. `.gitignore` must exclude them (see docs/legal-and-assets.md).
- Custom map files contain only original content or converted content the contributor owns.
- The matching build requires a user-supplied `baserom.dol` (sha1 `e90a13504974b917a675d59f07014e0e817c5e5d`, from the decomp README) and the MWCC compiler (GC_WII_COMPILERS.zip), which is not redistributed here.
- Server-side code must treat every client value (times, positions, item use, room IDs) as untrusted.
- No secrets in the repository: API keys, DB URLs, and tokens go in untracked env files.
- Server hosting is Cloudflare (Workers, D1, Durable Objects). Secrets live in `.dev.vars` or the Cloudflare dashboard, never in the repo. `.dev.vars` and `.wrangler/` are gitignored.
- Keep the decomp submodule clean: do not edit files under `decomp/` in feature work. Upstream changes go to the decomp project; local shims go in `port/`.

## Working conventions

- Work in the order of `IMPLEMENTATION_CHECKLIST.md`. Mark a task `[x]` only after its acceptance criteria and verification are done.
- Before implementing a feature, read its doc in `docs/`. If the doc and the code disagree, update the doc in the same change.
- Record decisions in the relevant doc under "Decisions" with date and reason. Do not silently change a decision.
- Keep changes small and reviewable. Prefer editing existing files over adding new ones.
- Do not add dependencies without recording them in the feature doc's "Dependencies" section.
- Use Git for all changes. Commit messages: imperative, one line summary, body explains why. Do not push without the user's approval.
- Unverified claims about the game (formats, addresses, behavior) must be marked "UNVERIFIED" in the docs until confirmed against the binary or decomp source.

## Validation commands

Commands are defined as each phase lands. Current status:

| Check | Command | Status |
|---|---|---|
| Decomp matching build | `make -C decomp` then `sha1sum decomp/build/sonicriders.dol` (must equal `e90a13504974b917a675d59f07014e0e817c5e5d`) | Planned (Phase 1) |
| Extractor tests | `tools/extract/` test command, TBD in Phase 2 | Planned |
| Map validator | `tools/mapkit validate maps/<name>` , TBD in Phase 3 | Planned |
| Server tests | `server/` test command, TBD in Phase 6 | Planned |
| Port build | `port/` build command, TBD in Phase 4 | Planned |

No command in this table has been run yet.

## Planning documents

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — phases, dependencies, deliverables, acceptance criteria.
- [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md) — ordered task list. Start here to pick up work.
- docs/ — one document per feature:
  - [docs/decomp-baseline.md](docs/decomp-baseline.md)
  - [docs/asset-extraction.md](docs/asset-extraction.md)
  - [docs/custom-maps.md](docs/custom-maps.md)
  - [docs/map-navigation.md](docs/map-navigation.md)
  - [docs/runtime-port.md](docs/runtime-port.md)
  - [docs/online-multiplayer.md](docs/online-multiplayer.md)
  - [docs/leaderboards.md](docs/leaderboards.md)
  - [docs/legal-and-assets.md](docs/legal-and-assets.md)

## Open decisions

See "Unresolved decisions" in IMPLEMENTATION_PLAN.md. The most important: the shipping target (native port vs. patched DOL), the online netcode model, the GameCube network transport (D6), and the language/stack for the server.
