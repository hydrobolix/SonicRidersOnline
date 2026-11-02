# Decomp baseline

Phase 1. Builds the US Sonic Riders DOL from the decomp source as a verification baseline.

## Relevant files

- `decomp/` — git submodule of `doldecomp/sonicriders` (to be added, pinned commit).
- `decomp/baserom.dol` — user-supplied, never committed.
- `decomp/tools/mwcc_compiler/` — user-supplied MWCC compiler from GC_WII_COMPILERS.zip.
- `docs/decomp-baseline.md` — this file.

## Technical details

- Target: US build, `sonicriders.dol`, sha1 `e90a13504974b917a675d59f07014e0e817c5e5d` (from the upstream README).
- Upstream prerequisites: devkitPro, python3, gcc.
- Upstream build: place `baserom.dol`, extract the compiler, run `make`.
- Upstream status: WIP. Not every function or data block is matched; the DOL build is the target sha1, not full coverage.
- UNVERIFIED: the upstream file layout and make targets. Confirm in Phase 1 step 6.

## Decisions

- D-1: Use a pinned submodule, not a copy, so upstream history stays separate. Pinned to `doldecomp/sonicriders` commit `4f42e59cb5b6089a2aba413d344f804e5362f06f` (upstream `HEAD` on 2026-11-02; last upstream commit dated 2022-02-06, Merge PR #7).
- D-2: Do not edit files under `decomp/` in feature work. Local shims go in `port/`.

## Dependencies

- Upstream decomp project (external, GPL-compatible license to be confirmed).
- devkitPro, python3, gcc (system).
- MWCC compiler (user-supplied, third party).

## Ordered steps

1. Add submodule at a pinned commit.
2. Install prerequisites and record versions.
3. Place user inputs (`baserom.dol`, compiler).
4. Run the build.
5. Compare the sha1 to the target.
6. Record the build recipe, environment notes, pinned commit, and confirmed layout here.

## Verification

- `sha1sum decomp/build/sonicriders.dol` equals the target sha1.
- A clean clone plus user inputs reproduces the same sha1.

## Status

Submodule added (task 1.1). Pinned commit: `4f42e59cb5b6089a2aba413d344f804e5362f06f`.

Upstream layout (confirmed from the checkout, task 1.6): top-level `Makefile`, `README.md`, `asm/`, `partial.lcf`, `static.lcf`, `resolveLinkerErrors.py`, `sonicriders.sha1`, `tools/`. No top-level license file was found, so upstream licensing is UNVERIFIED.

Compiler blocker: `GC_WII_COMPILERS.zip` is not available. The upstream README only links a Discord CDN copy. The Makefile expects `tools/mwcc_compiler/2.6/mwcceppc.exe` and `mwldeppc.exe` (`COMPILER_VERSION ?= 2.6`), run through `WINE` on non-Windows hosts. Not redistributed here. Phase 1 build is on hold until the user supplies the compiler.

Not yet built: tasks 1.2–1.5 need the user's `baserom.dol`, the MWCC compiler, and devkitPro.
