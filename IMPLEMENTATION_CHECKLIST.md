# IMPLEMENTATION_CHECKLIST.md — Sonic Riders Online

Ordered task list. Work top to bottom. Mark `[x]` only after the acceptance and verification items are done and recorded. Plan: [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md). Context: [AGENTS.md](AGENTS.md).

## Phase 0 — Repository setup and legal guardrails

Doc: [docs/legal-and-assets.md](docs/legal-and-assets.md)

- [ ] 0.1 Add `.gitignore` for game binaries, extracted assets, builds, and secrets.
- [ ] 0.2 Verify with a dummy `baserom.dol` that `git status` ignores it.
- [ ] 0.3 Acceptance: no game files are tracked.

## Phase 1 — Decomp baseline

Doc: [docs/decomp-baseline.md](docs/decomp-baseline.md)

- [ ] 1.1 Add `decomp/` submodule at a pinned commit. Record the commit in the doc.
- [ ] 1.2 Install devkitPro, python3, gcc. Record versions.
- [ ] 1.3 User supplies `baserom.dol` and the MWCC compiler (blocker until provided).
- [ ] 1.4 Run `make` in `decomp/`.
- [ ] 1.5 Verify `sha1sum decomp/build/sonicriders.dol` equals `e90a13504974b917a675d59f07014e0e817c5e5d`.
- [ ] 1.6 Confirm upstream layout and update the AGENTS.md architecture table.
- [ ] 1.7 Acceptance: sha1 matches from a clean clone plus user inputs.

## Phase 2 — Asset and format extraction

Doc: [docs/asset-extraction.md](docs/asset-extraction.md)

- [ ] 2.1 Identify the stage container and header from decomp symbols.
- [ ] 2.2 Document section offsets and field types (mark UNVERIFIED items).
- [ ] 2.3 Implement readers for geometry, collision, checkpoints, and spawns in `tools/extract/`.
- [ ] 2.4 Implement matching encoders.
- [ ] 2.5 Add round-trip tests per section.
- [ ] 2.6 Extract one stage and confirm byte-identical re-encode.
- [ ] 2.7 Acceptance: extractor test command passes; formats documented.

## Phase 3 — Map format, authoring kit and validator

Doc: [docs/custom-maps.md](docs/custom-maps.md)

- [ ] 3.1 Decide D4 (map file format) and record it in the doc.
- [ ] 3.2 Define the manifest schema in `maps/SCHEMA.md`.
- [ ] 3.3 Implement `tools/mapkit validate`, `pack`, and `unpack`.
- [ ] 3.4 Implement validator rules: checkpoint order and reachability, spawn bounds, no zero-length segments, at least 2 spawns.
- [ ] 3.5 Write one negative test per validator rule.
- [ ] 3.6 Build an original, hand-authored reference map in `maps/reference/` (no extracted game data).
- [ ] 3.7 Acceptance: reference map validates; each broken map fails with the right rule.

## Phase 4 — Runtime port and custom-map loading

Doc: [docs/runtime-port.md](docs/runtime-port.md)

- [ ] 4.1 Decide D1 (Dolphin-first patched DOL vs. native port) with evidence from decomp coverage.
- [ ] 4.2 Implement the packed-map loader in `port/`.
- [ ] 4.3 Add a custom track entry for the reference map.
- [ ] 4.4 Build the runtime and run the reference map in Dolphin.
- [ ] 4.5 Complete one lap on the reference map and record the result.
- [ ] 4.6 Confirm original stages still load and complete a lap.
- [ ] 4.7 Acceptance: reference map is selectable and finishable; original stages unaffected.

## Phase 5 — Navigation layout and race flow

Doc: [docs/map-navigation.md](docs/map-navigation.md)

- [ ] 5.1 Add the nav schema (sections, route, shortcut flags, minimap bounds).
- [ ] 5.2 Extend the validator for section coverage and route connectivity.
- [ ] 5.3 Add validator negative tests for an unnamed section and a disconnected route.
- [ ] 5.4 Implement minimap and section labels in the port.
- [ ] 5.5 Implement route preview export in mapkit.
- [ ] 5.6 Playtest the reference map using only the minimap and labels; record notes in the doc.
- [ ] 5.7 Acceptance: tester completes the reference map with nav aids only.

## Phase 6 — Online rooms and netcode

Doc: [docs/online-multiplayer.md](docs/online-multiplayer.md)

- [ ] 6.1 Spike the GameCube transport (D6); then decide D2 (netcode model) and D3 (server stack) and record them in the doc.
- [ ] 6.2 Build the room service: create, join, list, ready, start, leave, expiry.
- [ ] 6.3 Write the race sync protocol in the doc.
- [ ] 6.4 Implement server validation for checkpoint order and time bounds.
- [ ] 6.5 Implement client networking in `port/net/` and the lobby UI in `port/`.
- [ ] 6.6 Implement reconnection and stall handling.
- [ ] 6.7 Server tests: room lifecycle, impossible times, checkpoint skips.
- [ ] 6.8 Two-client race on the reference map (local, then LAN); record the run.
- [ ] 6.9 Acceptance: two clients finish a race; server rejects impossible results.

## Phase 7 — Leaderboards

Doc: [docs/leaderboards.md](docs/leaderboards.md)

- [ ] 7.1 Decide D5 (identity model); record it in the doc.
- [ ] 7.2 Define schema and migrations.
- [ ] 7.3 Implement the submission endpoint with validation and rejection logging.
- [ ] 7.4 Implement read endpoints: top N, rank, paging.
- [ ] 7.5 Server tests: valid, implausible, out-of-order, and duplicate submissions; deterministic ties.
- [ ] 7.6 Add in-game submission after a finished race.
- [ ] 7.7 Add the leaderboard screen to the port.
- [ ] 7.8 Acceptance: a valid run ranks; an implausible run is rejected with a logged reason.

## Phase 8 — Polish, testing and release

Docs: all of the above.

- [ ] 8.1 Consolidate build instructions into `README.md`.
- [ ] 8.2 Run every feature doc's verification list.
- [ ] 8.3 Complete the legal review in docs/legal-and-assets.md.
- [ ] 8.4 Set up CI running the validator, extractor and server tests on every change.
- [ ] 8.5 Write the release checklist and release notes.
- [ ] 8.6 Acceptance: clean checkout plus user inputs builds, runs a race, and submits a leaderboard entry.
