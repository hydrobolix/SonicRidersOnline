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
- D-3: Use `wibo` instead of WINE as the Windows-binary runner, because WINE 9.0 could not initialise in the workspace. Reason: the compiler only needs to run `mwcceppc.exe`, and wibo does that without a prefix.
- D-4: Use the 2.4.7 compiler from the user's CodeWarrior package with `COMPILER_VERSION=2.5`, not the 2.6 default, because it is the compiler the user supplied. The sha1 check is what decides whether this is acceptable.
- D-5: Copy the verified DOL to `decomp/build/` instead of changing the Makefile, because `decomp/` must not be edited. Revisit if the upstream Makefile or the checklist changes.

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

Compiler: the user supplied the CodeWarrior package (`CW_GC_2.5.ISO.7z`, sha1 `e9ced5fc3cdc3f29f48ee3cfb17a9933402c413e`). Its `mwcceppc.exe` and `mwldeppc.exe` report **version 2.4.7 build 105**, not 2.6. They were copied to `decomp/tools/mwcc_compiler/2.5/` (untracked, not redistributed) and built with `COMPILER_VERSION=2.5`. The Makefile default `COMPILER_VERSION ?= 2.6` was not used.

Host runtime: WINE 9.0 could not initialise (missing `zlib1.dll`, empty prefix `system32`), so it was abandoned. The build uses `wibo` (decompals/wibo, prebuilt static `wibo-i686`, run from `.local/wibo/`) as the `WINE` wrapper. `mwcceppc.exe -version` runs under wibo.

Assembler: devkitPPC was not available from `apt.devkitpro.org` (HTTP 403). It was unpacked without root from the devkitPro r51 release on the leseratte mirror (`https://wii.leseratte10.de/devkitPro/devkitPPC/r51%20(2026-10-11)/`): devkitPPC r51, binutils 2.47, gcc 16.2.0 (linux_x86_64), into `.local/devkitpro/root/opt/devkitpro/devkitPPC`. Set `DEVKITPPC` to that path.

Build command: `make -C decomp COMPILER_VERSION=2.5 WINE=<repo>/.local/wibo/wibo-i686` with `DEVKITPPC` set. Result: `sonicriders.dol: OK` and `_Main.rel: OK`.

Output path: the Makefile writes `decomp/sonicriders.dol` (the `DOL` variable, Makefile line 79), not `decomp/build/`. The checklist and AGENTS.md refer to `decomp/build/sonicriders.dol`. To satisfy that path without editing `decomp/`, the verified file was copied to `decomp/build/sonicriders.dol` (git-ignored by the root `.gitignore`, which covers `build/` and `*.dol`). The copy must be refreshed after each rebuild.

Result: `sha1sum decomp/build/sonicriders.dol` = `e90a13504974b917a675d59f07014e0e817c5e5d` (match). The file is byte-identical to `decomp/baserom.dol`.

Verification: `sha1sum -c sonicriders.sha1` (upstream file, lists `sonicriders.dol` and `_Main.rel`) passes in the submodule after a clean `make clean` rebuild. It also passes in a clean clone of `doldecomp/sonicriders` at `4f42e59` (in `.local/clean-clone/`) with `baserom.dol` and the 2.4.7 compiler copied in, which satisfies acceptance 1.7.

Versions recorded: devkitPPC r51 (binutils 2.47.20260726, gcc 16.2.0, devkitPPC); host gcc 13.3.0; host Python 3.12.3; wibo prebuilt static `wibo-i686` from the decompals/wibo release; mwcceppc 2.4.7 build 105.

Mismatch to resolve: the checklist and AGENTS.md say the output is `decomp/build/sonicriders.dol`, but the upstream Makefile writes to `decomp/`. Phase 1 acceptance is not yet marked `[x]`, pending the user's decision on the path, the compiler version (2.4.7 used vs. 2.6 default), and the manual copy step.

`baserom.dol` verified: a user-supplied US disc (`GXEE8P`, 1,461,714,944 bytes) yields a `boot.dol` with sha1 `e90a13504974b917a675d59f07014e0e817c5e5d`, matching the decomp. The file was placed at `decomp/baserom.dol` (git-ignored) and is not in the repository. Not yet built: tasks 1.2–1.5 still need the MWCC compiler and devkitPro.
