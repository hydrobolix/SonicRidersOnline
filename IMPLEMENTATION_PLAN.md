# IMPLEMENTATION_PLAN.md — Sonic Riders Online

Phased plan from empty repository to a working game with custom maps, online rooms and leaderboards. Read [AGENTS.md](AGENTS.md) first. Track progress in [IMPLEMENTATION_CHECKLIST.md](IMPLEMENTATION_CHECKLIST.md). Feature details live in [docs/](docs/).

## Assumptions

- A1. Target is the US GameCube build (`sonicriders.dol`, sha1 `e90a13504974b917a675d59f07014e0e817c5e5d`) per the doldecomp/sonicriders README. Its source tree layout is UNVERIFIED until the submodule is cloned in Phase 1.
- A2. The user supplies `baserom.dol` and the MWCC compiler (GC_WII_COMPILERS.zip). Neither is committed.
- A3. The decomp build is the matching baseline. Shipping features come from a runtime port or a patched DOL, decided in Phase 4.
- A4. Online play for GameCube hardware requires a Broadband Adapter. Online play in this project is assumed to be new netcode, not a revival of the original servers (which are offline). UNVERIFIED.
- A5. Leaderboards and room services need a server. Hosting is Cloudflare (Workers, D1, Durable Objects), run by the maintainers. No other host is planned.

## Unresolved decisions

| ID | Question | Default until decided | Needed by |
|---|---|---|---|
| D1 | Shipping target: native PC port vs. patched DOL on GameCube/Dolphin | Dolphin-first, port later | Phase 4 |
| D2 | Netcode model: lockstep peer-to-peer vs. server-relayed authoritative | Server-relayed, authoritative results | Phase 6 |
| D3 | Server language and stack | TypeScript on Cloudflare Workers; D1 for storage; Durable Objects for live rooms; Miniflare for local tests | Phase 6 |
| D4 | Map file format: reuse game's native stage format vs. new JSON/glTF-based format | JSON for authoring; packed binary defined in Phase 3, runtime details finalized after D1 | Phase 3 |
| D5 | Leaderboard identity: anonymous player IDs vs. accounts | Anonymous IDs with a display name | Phase 7 |
| D6 | Network transport on GameCube: BBA driver in a patched DOL vs. Dolphin-only BBA emulation | Spike first; gates Phase 6 | Phase 6 |

## Phase summary

| Phase | Name | Depends on |
|---|---|---|
| 0 | Repository setup and legal guardrails | none |
| 1 | Decomp baseline and matching build | 0 |
| 2 | Asset and format extraction | 1 |
| 3 | Map format, authoring kit and validator | 2 |
| 4 | Runtime port and custom-map loading | 1, 3 |
| 5 | Navigation layout and race-flow features | 3, 4 |
| 6 | Online rooms and netcode | 4, 5 |
| 7 | Leaderboards service and in-game submission | 6 |
| 8 | Polish, testing, release | 5, 6, 7 |

## Phase 0 — Repository setup and legal guardrails

**Goal:** Make the repo safe to work in before any game data arrives.

**Steps**
1. Add `.gitignore` excluding `baserom.dol`, `*.iso`, `*.gcm`, `*.arc`, `*.szs`, `*.bin` under `assets/raw/`, `build/`, `decomp/build/`, `.env*`, `.dev.vars`, `.wrangler/`, `node_modules/`.
2. Add `docs/legal-and-assets.md` with the redistribution rules from AGENTS.md.

**Deliverables:** `.gitignore`, `docs/legal-and-assets.md`.

**Acceptance:** `git status` shows no game binaries after a dummy `baserom.dol` is placed in the root.

**Validation:** create a dummy file, run `git status --ignored`, confirm it is ignored.

## Phase 1 — Decomp baseline and matching build

**Goal:** Build `sonicriders.dol` from source and match the US sha1.

**Depends on:** Phase 0.

**Steps**
1. Add `decomp/` as a git submodule pinned to a specific commit of `doldecomp/sonicriders`. Record the commit in `docs/decomp-baseline.md`.
2. Install prerequisites: devkitPro, python3, gcc. Extract GC_WII_COMPILERS.zip to `decomp/tools/mwcc_compiler/` (user-supplied).
3. Place the user's `baserom.dol` in `decomp/`.
4. Run `make` and compare sha1 with `e90a13504974b917a675d59f07014e0e817c5e5d`.
5. Record the build recipe and any environment notes in `docs/decomp-baseline.md`.
6. Confirm the actual source layout (functions, data, config files) and update the table in AGENTS.md.

**Deliverables:** pinned submodule, build notes, validated layout.

**Acceptance:** sha1 matches; the build is reproducible from a clean checkout plus user-supplied inputs.

**Validation:** `make -C decomp` then `sha1sum decomp/build/sonicriders.dol`.

**Risks:** the MWCC zip is a third-party download; the Discord link may expire. Document a fallback location.

## Phase 2 — Asset and format extraction

**Goal:** Read the game's stage, collision, track, and item data from the baseline and document it.

**Depends on:** Phase 1.

**Steps**
1. Identify the file container for stage data in the disc or DOL (UNVERIFIED; check decomp symbols and the decomp source).
2. Write `tools/extract/` (Python) to read the container and export stage geometry, collision, track checkpoints, and spawn points into JSON.
3. Write a round-trip test: extract, then re-encode, then compare bytes for each stage.
4. Document each format in `docs/asset-extraction.md` with offsets, field meanings, and UNVERIFIED flags.

**Deliverables:** `tools/extract/`, format notes, round-trip tests.

**Acceptance:** at least one stage extracts to JSON and re-encodes byte-identical; formats documented.

**Validation:** the extractor test command (set in Phase 2) passes.

## Phase 3 — Map format, authoring kit and validator

**Goal:** Define how custom maps are authored, validated and packed.

**Depends on:** Phase 2.

**Steps**
1. Decide D4 (see Unresolved decisions) and record it in `docs/custom-maps.md`.
2. Define the map manifest schema: name, stage geometry reference, collision, checkpoints, item boxes, spawns. Nav data is added in Phase 5 (see `docs/map-navigation.md`).
3. Build `tools/mapkit/` with `validate`, `pack`, and `unpack` commands.
4. Validator rules: checkpoints ordered and reachable, spawns inside the track bounds, no zero-length segments, at least 2 spawns per map.
5. Add one reference map hand-authored from original geometry, so it can be committed. Maps built from extracted game data stay local and gitignored.

**Deliverables:** schema, `tools/mapkit/`, reference map in `maps/`.

**Acceptance:** the reference map passes `validate`; a deliberately broken map fails with a clear message per rule.

**Validation:** `tools/mapkit validate maps/<name>` and the negative-test suite.

## Phase 4 — Runtime port and custom-map loading

**Goal:** Load a packed custom map into a playable race.

**Depends on:** Phases 1 and 3. Decision D1 must be made here.

**Steps**
1. Decide D1. Record in `docs/runtime-port.md`.
2. Choose the mechanism: patched DOL with a custom track table, or a native port that reads the same data.
3. Implement the loader for packed maps.
4. Verify the reference map loads and completes a lap in the chosen runtime (Dolphin or port).
5. Verify the original stages still load unchanged.

**Deliverables:** loader, runtime build, reference race run.

**Acceptance:** reference map is selectable and finishable; original stages unaffected.

**Validation:** runtime smoke run (manual, documented steps) plus automated build check.

## Phase 5 — Navigation layout and race flow

**Goal:** Make custom maps easy to navigate: named sections, route data, minimap, and clear checkpoint order.

**Depends on:** Phases 3 and 4.

**Steps**
1. Add nav data to the map schema: sections with names, ordered route polyline, shortcut flags, and minimap bounds.
2. Extend the validator to check section coverage and that the route connects checkpoints.
3. Implement in-game minimap and section-name display in the port.
4. Add a route preview export (image or JSON) from mapkit for authors.

**Deliverables:** nav schema, validator rules, minimap, route preview.

**Acceptance:** a tester can finish the reference map using only the minimap and section labels; validator rejects maps with unnamed sections or disconnected routes.

**Validation:** validator tests; manual playtest notes recorded in `docs/map-navigation.md`.

## Phase 6 — Online rooms and netcode

**Goal:** Players can create or join a room and race over the network.

**Depends on:** Phases 4 and 5. Decisions D2, D3 and D6 must be made here; the D6 spike comes first.

**Steps**
1. Spike the GameCube transport (D6). The rest of this phase waits on the result.
2. Decide D2 and D3. Record in `docs/online-multiplayer.md`.
3. Build the room service: create, join, list, ready, start, leave. Rooms expire when empty.
4. Build the race sync protocol: player state at a fixed tick, server validates checkpoints and finish times.
5. Add reconnection handling and a timeout for stalled players.
6. Build the lobby UI in the port and integrate with its network layer.
7. Test with two clients on one machine and two machines on a LAN.

**Deliverables:** transport spike notes, room service, protocol doc, client networking, lobby UI, tests.

**Acceptance:** two clients finish a race on the reference map; server rejects impossible times and checkpoint skips.

**Validation:** server test suite, two-client run recorded in the doc.

## Phase 7 — Leaderboards

**Goal:** Per-map leaderboards with authenticated, validated submissions.

**Depends on:** Phase 6 (for server infrastructure and race results). Decision D5 must be made here.

**Steps**
1. Decide D5. Record in `docs/leaderboards.md`.
2. Define the schema: maps, players, runs, best-times per map and mode.
3. Implement submission endpoint: authenticate the submission with the session token issued by the room service, check the run's plausibility (checkpoint order, time bounds, duplicate run IDs), and store only the best run per player per map. Plausibility checks reject impossible runs; they cannot prove a run is honest.
4. Implement read endpoints: top N, player rank, paging.
5. Add in-game submission after a finished race and a leaderboard screen.

**Deliverables:** schema, endpoints, in-game UI.

**Acceptance:** a valid run appears on the board; an implausible or out-of-order run is rejected with a logged reason; ties are deterministic.

**Validation:** server tests for valid, implausible, out-of-order and duplicate submissions.

## Phase 8 — Polish, testing and release

**Goal:** A documented, reproducible release that a new contributor can build and run.

**Depends on:** Phases 5, 6, 7.

**Steps**
1. Consolidate build instructions into `README.md` and AGENTS.md validation table.
2. Run the full validation list from every feature doc.
3. Write the release checklist: legal check, sha1 check, server deploy notes.
4. Set up CI that runs the validator, extractor and server test commands on every change.
5. Tag a release.

**Deliverables:** README, release notes, tagged release.

**Acceptance:** a clean checkout plus user-supplied inputs builds, runs a race, and submits a leaderboard entry.

**Validation:** the full validation list passes; any failure is documented as a limitation.

## Completion criteria

The project is complete when Phase 8 acceptance is met and every item in IMPLEMENTATION_CHECKLIST.md is checked with verification recorded.
