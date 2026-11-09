# Handoff: Phase 2 (asset extraction), state as of 2026-11-08

Read AGENTS.md and IMPLEMENTATION_PLAN.md first. Details live in `docs/asset-extraction.md`; this file is the short map of what is done, what is open, and how to work.

## Done and verified
- **Container decoder and encoder** (`tools/extract/srlz.py`): the `0x8000000N` container. Decoder ported from REL `lbl_001594F4`, found live in Dolphin. Re-encoder is byte-identical on 1,562 of 1,562 container files on the US disc (GXEE8P). Eight files (P240, P240M, PO40, PO40M, PO70, PZ40, PZ40M, PZ70) need `overrun=True`. `srlz_check.c` is the whole-disc check (exit 0 exact, 10 overrun).
- **REL load base** is `0x803FBD00` (corrects `0x803FBCFC` in commit `4c29e6f`).
- **Stage package split** (`srpack.py`): header, groups, slot table, blobs; `split` then `join` reproduces the file byte for byte on `1`, `1M`, `1V`, `0`.
- **Slot roles in stage `1`** (names come from NFN0 footers and texture lists): groups 2-3 map; 4-6 texture lists; 7-19 shared objects and effects; slot 133 sky; slots 172-177 cameras. Groups 19-44 are identical between `1` and `1M`.
- **Collision-style tables** (slots 130-132, magic `01 01 00 01`, 0x30-byte records): offsets, count, kind and id fields are tied to REL `lbl_00046C70` and `lbl_00046CE0`. `srcol.py` reads them.
- Tests: `python3 -I tools/extract/test_srlz.py` (offline, 3 tests, pass).

## Open (nothing below is ticked in IMPLEMENTATION_CHECKLIST.md; Phase 2 items 2.1-2.7 are all still unticked)
1. Checkpoints and start positions: not located. Likely candidates are the unidentified blobs in slots 178-182 (`GC` prefix) and 185-186 (two 0xC0-byte blobs with floats like 0.2, 0.7, 3.6). Find the REL code that reads them (look from the stage loader after the package is split) before guessing formats.
2. Kind meanings in the collision records (kinds 0, 1, 3, 22, 8, 6, 5, 9, 17, 31 in slot 130; REL special-cases 31, 50, 51, 52). Sphere fields, index format and normals use are inferred.
3. NGIF and NGOB internals (models, `.gnm`, `.gnv`, `.gnd` cameras) and the `AN/AI/AB` animation blobs: only identified by tag, not parsed.
4. The small unparsed header tables between the u16 group list and the slot table.
5. Phase 2 acceptance: extract, edit, repack with byte-identical round trip for a stage, then tick 2.3-2.7 only after that passes.
6. Housekeeping: AGENTS.md validation table still shows Phase 1 as "Planned" (it is resolved by D-4/D-5) and the extractor test command is not filled in; `README.md` is empty.

## How to work here
- The disc image is the user's and is never committed (see `docs/legal-and-assets.md`; `.gitignore` covers `*.ciso`, `assets/raw/`).
- Disc and Dolphin access is through the device bridge (`mcp__remote-devices__*`). The disc is `Sonic Riders (USA) (En,Ja,Fr,De,Es,It).ciso` in the user's connected Claude_workspace folder. `ciso.py` reads it and lists the FST.
- `device_bash` calls max out at 180 s and background processes die when a call ends. Run long jobs in chunks of 150 s or less with a state file (the whole-disc decode needed this). Do not use `pkill -f`.
- Mark every finding verified (tied to REL code or a byte-identical test) or UNVERIFIED in the docs.

## Git
- The cloud session cannot push: the proxy returns 403 for `hydrobolix/sonicridersonline`, and the GitHub MCP token has no write access. The user pushes from their own machine, so hand over a bundle or patch (`git bundle create ... origin/main..<branch>`).
- A GitHub token was pasted into chat on 2026-11-08; it should be revoked. Never reuse it.
- `origin/main` 18a086f holds an earlier snapshot of this work. The delta (overrun mode and test, REL ties and results in the collision section, pycache ignore rules, this file) is a separate commit on top.
