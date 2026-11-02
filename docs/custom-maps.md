# Custom maps

Phases 3 and 4. Authoring, validating, packing, and loading new race tracks built from map assets.

## Relevant files

- `tools/mapkit/` — planned authoring kit (`validate`, `pack`, `unpack`).
- `maps/<name>/` — one directory per custom map (manifest plus source assets).
- `maps/reference/` — planned reference map, hand-authored from original geometry so it can be committed.
- `port/` — runtime loader (Phase 4).
- `docs/map-navigation.md` — nav data rules.

## Technical details

- Map source: a `manifest.json` per map with name, author, stage geometry reference, collision, checkpoints, item boxes, spawns, and nav sections.
- Packed form: a binary the runtime loads. Format depends on D1 (runtime target) and D4 (format choice). Both are open.
- Validator rules (Phase 3): checkpoints ordered and reachable; spawns inside track bounds; no zero-length segments; at least 2 spawns. Nav-section rules are added in Phase 5.
- Each custom map must declare its required assets, and mapkit must refuse to pack a map whose assets are missing.

## Decisions

- D4 (open, default): native stage format for runtime, JSON for authoring.
- D1 (open, default): Dolphin-first with a patched DOL; native port later.
- Committed maps must contain no extracted game data (see docs/legal-and-assets.md).

## Dependencies

- Phase 2 extractor output (for the reference map).
- A runtime loader in `port/` (Phase 4).

## Ordered steps

1. Decide D4 and record it here.
2. Define the manifest schema and put it in `maps/SCHEMA.md`.
3. Implement `validate`, then `pack` and `unpack`.
4. Write negative tests: one broken map per validator rule.
5. Build the reference map and pack it.
6. Implement the runtime loader and run the reference map in the chosen runtime.

## Verification

- `tools/mapkit validate maps/reference` passes.
- Each negative test fails with the expected rule message.
- The reference map packs, loads in the runtime, and finishes a lap.

## Status

Not started.
