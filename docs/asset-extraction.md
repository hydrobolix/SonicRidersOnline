# Asset extraction

Phase 2. Reads stage, collision, checkpoint, and spawn data from the baseline and exports it to JSON with a verified round trip.

## Relevant files

- `tools/extract/` — planned extractor (Python).
- `tools/extract/tests/` — planned round-trip tests.
- `docs/asset-extraction.md` — this file; holds the format notes.
- `decomp/` — source of symbol and layout information (read only).

## Technical details

- Input: `baserom.dol` and/or the extracted disc filesystem, supplied by the user.
- Output: JSON per stage under `assets/extracted/` (gitignored), which is generated and never committed.
- UNVERIFIED: container format for stage data. Expected to be a file archive inside the disc, with stage data sections; confirm against decomp symbols.
- UNVERIFIED: field offsets, endianness (GameCube is big-endian), and float layout for geometry and collision.
- Round-trip rule: extract, then re-encode, then compare bytes for each stage.

## Decisions

- D-3: Extractor is Python, matching the decomp's tooling. Revisit if the server or mapkit choose another language.
- D-4: Extracted output stays out of git.

## Dependencies

- Python 3 (standard library preferred).
- Phase 1 layout knowledge.

## Ordered steps

1. Identify the stage container and its header from decomp symbols.
2. Document each section's offsets and field types in this file, marked UNVERIFIED until confirmed.
3. Implement readers for geometry, collision, checkpoints, and spawns.
4. Implement encoders for the same sections.
5. Add a round-trip test per section and per stage.
6. Extract one stage end to end and record the result.

## Verification

- Round-trip test passes for at least one stage, byte identical.
- Extracted JSON validates against the schema written in Phase 3.

## Status

Not started.
