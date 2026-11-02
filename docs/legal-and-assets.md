# Legal and assets

Phase 0. Rules for what may be committed, and how user-supplied game data is handled.

## Relevant files

- `.gitignore` — excludes game binaries, extracted assets, builds, and secrets (Phase 0).
- `AGENTS.md` — summary of the constraints.
- `decomp/` — submodule; the decomp project sets its own license terms.

## Technical details

Never commit:
- `baserom.dol`, disc images (`*.iso`, `*.gcm`), archives (`*.arc`, `*.szs`), or any extracted game file.
- Original models, textures, audio, or stage data, including extracted JSON under `assets/extracted/`.
- MWCC compiler binaries (GC_WII_COMPILERS.zip contents).
- `.env*` files, API keys, database URLs, tokens.

Allowed to commit:
- Tools, docs, tests, and original custom map content the contributor owns.
- Hashes and expected sha1 values.
- Format documentation written in the contributor's own words.

## Decisions

- Users supply their own game inputs. The project never distributes them.
- Custom maps must be original or owned by the contributor. Maps that copy original stages wholesale are not accepted.
- UNVERIFIED: exact copyright position for documentation of file formats. Maintainers should review before public release.

## Dependencies

- Upstream decomp license: not found. `doldecomp/sonicriders` has no top-level license file at pinned commit `4f42e59c`. UNVERIFIED until the upstream terms are confirmed.

## Ordered steps

1. Add `.gitignore` entries for the excluded patterns.
2. Verify with a dummy `baserom.dol`: it is ignored by `git status --ignored`.
3. Add a contributor note on custom map ownership to `maps/SCHEMA.md` (Phase 3).
4. Maintainer review before first public release (Phase 8).

## Verification

- `git status` is clean after placing dummy inputs in ignored locations.
- Review of every doc for copied game data before merge.

## Status

Not started.
