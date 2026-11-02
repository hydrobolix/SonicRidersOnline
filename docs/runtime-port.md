# Runtime port

Phase 4. Loads packed custom maps into a playable race. Decision D1 is made here.

## Relevant files

- `port/` — planned runtime code (loader, custom track table, network hooks).
- `port/net/` — network layer (Phase 6).
- `decomp/` — read-only source of game behavior.
- `maps/` — packed map inputs.

## Technical details

- Option A, patched DOL: add a custom track table and loader inside the decomp build. Pros: runs on hardware and Dolphin, closest to original behavior. Cons: harder to change, limited by the decomp's coverage (WIP), and has no network layer (see D6 in docs/online-multiplayer.md).
- Option B, native port: reimplement or wrap game logic in a new runtime that reads the same data. Pros: easier to extend, networking and UI are simpler. Cons: large effort, risk of behavior differences.
- Dolphin is the default test platform (D1 default).
- UNVERIFIED: whether the upstream decomp is complete enough for Option A to load custom stages without hitting unmatched code.

## Decisions

- D1 (open, default): Dolphin-first with Option A. Revisit at the end of Phase 4 with evidence.
- Original stages must keep loading unchanged under either option.

## Dependencies

- Phase 1 baseline build.
- Phase 3 packed map format.
- Dolphin (external, for testing).

## Ordered steps

1. Compare Option A and B against decomp coverage. Record the result and decide D1.
2. Implement the packed-map loader.
3. Add a custom track entry that points at the packed reference map.
4. Build the runtime and launch the reference map in the chosen runtime.
5. Confirm original stages still load and complete a lap.

## Verification

- Build succeeds and the sha1 of the unpatched baseline still matches (Phase 1 check).
- Reference map is selectable and a lap can be completed.
- Original stage smoke test passes.

## Status

Not started. D1 not decided.
