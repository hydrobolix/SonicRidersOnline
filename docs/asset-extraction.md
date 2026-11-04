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

## Disc layout (Phase 2.1 findings, UNVERIFIED)

Source: the user's US disc, `Sonic Riders (USA) (En,Ja,Fr,De,Es,It).ciso` (1,405,125,184 bytes). Read with a scratch CISO and FST reader kept in `.local/disc/` (not committed). Only the file table and the first bytes of two files were read.

- Image: CISO (compact GameCube). Magic `CISO`, 2 MiB blocks, block map at 0x0..0x8000. Disc ID at 0x8000 is `GXEE8P`, matching the US build.
- DOL offset 0x20300. FST offset 0x144000, size 0x72b1. Root entry count is 1,672.
- Name table: `NULL.bin`, `00.DAT`, `01.DAT`, `0501.DAT` to `0509.DAT`, `10*.DAT` (character files), `S1`… `S16` with `F`/`J`/`LE`/`LF`/`LG`/`LI`/`LJ`/`LS` suffixes, `P0`… `PZ` groups, `TG`, `TS`, `MF`, `SV`, and `*.ADX` audio.
- The suffixes `F` and `J` suggest one file set per region language (UNVERIFIED). `S1`… look like stage or track bundles, but this is not confirmed.

### Container candidates (UNVERIFIED)

- `0501.DAT`: starts with the ASCII magic `gcaxDTPK`, then big-endian words `0x024A0100`, `0x00056800`, `0x000008E0`, `0x00055400`, `0x00001000`. The first 0x24 bytes look like a packed archive header. Its length (354,304) and the DAT name pattern are not linked to stage data yet.
- `S11F` (2,229,697 bytes): starts with `0x80000001 0x0036B4A0` followed by zeros. This is not yet tied to a known container, so it is not identified as a stage file.

### gcaxDTPK container layout (UNVERIFIED, read from the plain ISO)

Checked on `0501.DAT`, `10AIAI.DAT` and `10ULALA.DAT` in `.local/disc/sonicriders.iso`. All share the same header fields, so this is probably one container family. Field meanings are not confirmed.

- +0x00: ASCII `gcaxDTPK`.
- +0x08: u32 BE `0x024A0100` in all three files (meaning unknown).
- +0x0C: u32 BE, equal to the file size on `0501.DAT` (`0x56800`). On `10AIAI.DAT` (`0x11800`) and `10ULALA.DAT` (`0x18000`), this is the data size or an offset. UNVERIFIED.
- +0x10: u32 BE, varies (`0x8E0`, `0x7E0`, `0x6C0`). Possibly an entry count or a table size. UNVERIFIED.
- +0x18: u32 BE, `0x55400` / `0x10CE0` / `0x17580`, varying. Possibly a second table offset. UNVERIFIED.
- +0x60: ASCII `gcaxTBLD`, a second header block that starts a table. UNVERIFIED.
- The bytes at `0x55400` on `0501.DAT` do not look like a plain table of 32-bit fields. They may be compressed or encrypted. Not yet checked.
- No entry names, stage IDs or record sizes have been confirmed. Entry parsing is not done.

### Runtime read trace (Dolphin DVD log, UNVERIFIED field meanings)

From a user-captured Dolphin DVD interface log (boot to the start of a normal race, `CoreHWDVDDVDInterface.cpp`):

- `0501.DAT` is read as one 0x20000-byte DMA at disc offset `0x03DC0000` (`03:43:812`), then a 0x800-byte read at `0x03DE0000`. Its 354 kB size is reported by the file monitor. So the 0x20-byte header is read inside the first DMA, with no separate header read.
- The bytes at `0x03DC0000` on the disc match the header above: `gcaxDTPK`, `0x024A0100` at +0x08, `0x00056800` at +0x0C, `0x000008E0` at +0x10, `0x00055400` at +0x18, `gcaxTBLD` at +0x60.
- Other DAT files read the same way: `10SONIC.DAT`, `10ER1.DAT`, `10STORM.DAT`, `10ER2.DAT`, `10WAVE.DAT`, `10KNUCK.DAT`, `10TAILS.DAT`, `10AMY.DAT`. Each is read as one large DMA, then a small tail read.
- The caller that reads the header and what +0x08 to +0x18 mean are still not identified. The debugger breakpoint trace is still needed to confirm them.

### gcaxDTPK magic check in the binary (static, found 2026-11-04)

Earlier notes said no code matches the magic. That is wrong: the check exists but is obfuscated, so a byte search for `gcaxDTPK` misses it. `func_80088594` (`0x80088594`) validates a registered DTPK header at `0x80088640`–`0x8008866C`:

- `lwz r3, 0(r5)`; `addis r3, r3, 0x989d`; `cmplwi r3, 0x6178` → accepts `0x67636178` = `gcax`.
- `lwz r3, 4(r5)`; `addis r3, r3, 0xbbac`; `cmplwi r3, 0x504b` → accepts `0x4454504B` = `DTPK`.
- `lwz r7, 8(r5)`; `lis r3, 0x249`; `cmplw r7, r3`; `bge` → the `+0x08` field must be at least `0x02490000`, consistent with the `0x024A0100` seen on disc.
- Failure codes: `-8` bad magic, `-7` version too low, `-6` slot already used, `-5` too many open packs, `-4` not initialised, `-3` slot index out of range.

The function takes one argument, a slot index below `0x20`. The header pointer is not an argument; it comes from the slot table at `lbl_8021C2D8 + 0x284 + slot*4`. On success it copies header fields `+0x84` (u32), `+0x89`, `+0x8C`, `+0x8D` (u8) and `+0x90`, `+0x94` (u32) into that table, alongside the slot's stride-`0x14` record (`+0x08` header pointer, `+0x0C`, `+0x0D`, `+0x0E` bytes) and two u32 slots at `0xF3C` and `0xF40`.

UNVERIFIED: which slot each DAT file occupies, whether `0501.DAT` is registered through this path, and what the copied fields mean.

### The DVD layer is the SDK's DVDFS, not game code (established 2026-11-04)

This settles the identification of the `0x80012000`–`0x80015000` block and supersedes the earlier reading of `lbl_801B3CC0` as a game read-request list. The assert strings next to that code name the library:

| Address | String |
|---|---|
| `0x80119F40` | `DVDReadAsync(): specified area is out of the file  ` |
| `0x80119F74` | `DVDRead(): specified area is out of the file  ` |
| `0x80119FF0` | `load fst\n` |
| `0x80119FFC` | `DVDChangeDisk(): FST in the new disc is too big.   ` |

Function mapping, used by the sections below:

- `func_8001319C` = `DVDOpen`/`DVDFastOpen`; `func_8001350C` = `DVDRead`; `func_800135FC` = `DVDReadAsync`; `func_800137A8` = DVD/FST init (it reports `load fst` at `0x80013848`).
- `func_80012408` and `func_80012598` are the SDK's DI-level read issuers; both write DILENGTH.
- `lbl_801B3CC0` is the SDK's DVD staging block for FST and small reads, not a game queue. See "`lbl_801B3CC0`: the SDK's FST staging block" below.
- The SDK readers assert `length <= 0x34(handle)` and `offset + length < filesize + 0x20`, and they do not split a request. Any chunking is therefore done by the caller.

Consequence: the `0x20000` in the DVD log is an argument the game passed to `DVDReadAsync`. It is not produced inside this layer.

### Static trace of the four `func_80012598` callers (UNVERIFIED)

- The four callers in `decomp/asm/lib.s` are: `lbl_800138D4` (line 11938), `func_800141A8` (line 12593), `lbl_80014364` (line 12714) and `lbl_80014B2C` (line 13282). None sets the literal length `0x20000` or offset `0x03DC0000`.
- `lbl_800138D4` and `lbl_80014364` take their length from the word at `0(r31)` and their offset from `0x38` of the pointer at `lbl_8021BD88`, so this is the SDK staging path, not a file-table struct.
- `func_800141A8` reads a fixed 0x20 bytes at offset 0x420 into `lbl_801B3CC0`.
- `lbl_80014B2C` (`lib.s` 13282) is a branch target inside `func_80014A4C`. Its arguments come from struct `r7`, which `func_80014A4C` sets from `lbl_8021BD80` (the request-state pointer). The length is clamped to `0x80000`. The buffer is read from `+0x18` and the offset from `+0x10`, both plus `+0x20`. `func_800153E4` (`lib.s` 13929) is the request builder that writes these fields from its caller's arguments. So `lbl_80014B2C` holds no literal `0x03DC0000`; the value comes from whichever caller builds the request.
- `func_8001350C` and `func_800135FC` are the SDK's bounds-checked readers (see the mapping above). They take the file handle, buffer, offset and length as arguments and check them against the file size at `+0x34`. They hold no literal offset or length.
- `func_800153E4` has seven direct callers in `lib.s`: 3722, 3794, 3990, 4059, 4125, 11704 and 11771. None loads a `0x20000` length. Two load a literal `0x40` (3794, 3990). The others take the length from a register or stack slot, or compute it (4125 rounds up to 0x20). Lines 11704 and 11771 pass the length through `r28`, which is copied from the wrapper argument.
- Callers of the SDK readers: `lib.s` 177460 and 177468 pass a register length (`r23`, from a loop). `text.s` 84 and 2782 pass a literal `0x20` or `0x2`, and `text.s` 109 passes `r28`. None loads `0x20000`.
- Line 4125 (`func_8000CF9C`'s caller path, in `func_8000CB18`, lib.s 3830) is a DVD-to-ARAM request. Its buffer is `0x81300000`, its offset is `[r30+0x14] + func_8000CA54() + 0x20`, and its length is `[r30+0x18]` rounded up to 0x20. `r30` is the 7th argument (`r9`) to `func_8000CB18`.
- Inside `func_8000CB18`, `r30` is reassigned at lib.s 3936 (`8000CC8C`). It becomes a fresh 0x20-byte block from `func_8000B198`, and `func_8000C99C` fills it with a 0x20-byte DVD read at offset `func_8000CA54()`. So the `[r30+0x14]` and `[r30+0x18]` fields at line 4125 are fields of a header read from disc, not code constants. `r9` is only used on the path that skips this reassignment.
- `func_8000CA54` returns the base offset for this read. It reads a 0x40-byte table at `lbl_8021BC94` and returns `[table+0x38] + base`, or the default `0x2440` when no table is set. That is UNVERIFIED as a file-layout claim.
- The table pointer is a low-memory global at `0x800030F4`, next to `0x800030F0`. No decomp code writes `0x800030F4`. Its only stores are two `stw r27` into `0x800030F0` (lib.s 4041, 4099), where `r27` is a fresh 0x20-byte block. So `0x800030F4` is set outside the decomp's own code, most likely by the OS or boot path. This is UNVERIFIED.
- So the header block that `func_8000C99C` reads is `[0x800030F4]`'s target, and its `+0x14` and `+0x18` fields are those of that block. Their meanings (offset and length) are inferred from how the read uses them, not confirmed.
- Checked against the ISO (UNVERIFIED): the 0x20 bytes at the default base `0x2440` look like a GameCube apploader header. They hold the date string `2004/11/10`, then entry `0x81200258`, size `0x1A98` and trailer `0x1C3A0`. So the default base is not a data-file base. Disassembling the apploader body (big-endian, `powerpc-eabi-objdump -EB`, UNVERIFIED): its entry is `0x81200258`, and its only `0xCC00xxxx` loads are four `lis r5, 0xCC00` at `0x812002D8`–`0x81200344`, which read `0xCC006400`-based tables. It never writes the DI command registers (`0xCC006000`–`0xCC006020`), and it has no `0x20000` DMA length. So the apploader does not issue the `0501.DAT` read; that read comes from the game's own code. The `0501.DAT` header at `0x03DC0000` has `+0x14 = 0` and `+0x18 = 0x55400`, not `0x20000`, so the line 4125 length does not come from `0501.DAT`'s own `+0x18`.
- Comparison of the 0x20-byte header fields across `0501.DAT`, `10AIAI.DAT` and `10ULALA.DAT` (UNVERIFIED): all three share `gcaxDTPK` at +0x00, `0x024A0100` at +0x08, and `0` at +0x14. Their +0x0C, +0x10, +0x18 and +0x1C values vary, but none of the fields equals `0x20000`. So the `0x20000` length is not stored in any header field of these files.
- Line 4125 reads its length from `[block+0x18]` and its offset from `[block+0x14]` plus the base. Neither value matches the `0501.DAT` read at `0x03DC0000` with the data checked so far.
- `func_8000CB18` has one direct caller, `func_8000CF9C` (lib.s 4265), which passes `r9` from a block it fills by copying a pointer array. That `r9` path is separate from the `r30` reassignment above.
- `func_8000CF9C` has one caller, `func_8000E9AC` (lib.s 6149), which passes a pointer to a zeroed stack word. `func_8000E9AC` is called from `func_8000EC7C` (lib.s 6356), a state dispatcher (`func_8000EC7C` does not write the request struct).
- So no static caller in the `func_800153E4` or SDK-reader paths carries a literal `0x20000` length. The value must be computed, or come from a caller not yet traced.
- The 31 `lis rN, 2` sites in `lib.s` (UNVERIFIED): the DVD-area ones (`80014CC0`, `80014CE8` and their neighbours) load `0x20000` into `r3` and call `func_80012BE0`, which ORs its argument into `0xE2000000` and writes `CC006008` (a DI command word). Those are `0xE2` audio-status subcommands, not file lengths. The other sites (`80017248`, `80043928`, `800439FC`, `8004DFC8`, `8007xxxx` and so on) feed `func_8000D814`, `func_8000D89C`, or are plain `lis r0, 2` bit-mask setups. None computes a length from a file size or chunk count.
- Conclusion: the `0501.DAT` read (length `0x20000`, offset `0x03DC0000`) is still unattributed. Attribution needs the Dolphin breakpoint trace.

### Loader search (UNVERIFIED)

- The magic check exists but is obfuscated; see "gcaxDTPK magic check in the binary" above. The earlier conclusion that no code matches the magic is withdrawn.
- `decomp/asm/_Main/text.s` (489,745 lines) has no named DVD symbols (`DVDOpen`, `DVDRead`, `DVDFastOpen`, `OSReport`); functions are labelled by address only, so calls appear as `bl func_8001xxxx`. It does call the SDK readers, e.g. one call at `0x00175D98` that reads the `BNR1` banner with a fixed length of `0x1960`.
- `_Main.rel` also has no reference to `lbl_801B3CC0` and no `0x20000` read length. Its 45 `lis rN, 2` sites pass `0x20000` to the heap allocator `func_800E2D68(align, size)` (e.g. `li r3, 0x20` with `lis r4, 2` is a 128 KiB, 0x20-aligned allocation) and to unrelated API calls.
- The only `0x4454` hits in `asm/lib.s` outside the magic check are unrelated stack offsets, not the `DTPK` magic.
- Runtime route blocked: the Cloud VM has no Dolphin, no X display and no Xvfb (x86_64, 8 cores, 48 GB free). A read trace needs an emulator with a display, so it has to run on a machine that has one.
- Headless attempt (Ubuntu 24.04, non-root): Xvfb was unpacked from apt into `.local/apt/root` with its libraries resolved, but it fails with `Failed to compile keymap` because it runs the absolute path `/usr/bin/xkbcomp`, which is absent (no root to install it). Ubuntu apt has no `dolphin-emu` package; `dolphin` there is the KDE file manager. A headless Dolphin needs a source build or an AppImage.
- No loader string or symbol in `decomp/` or in `baserom.dol` names a stage file, track, checkpoint or spawn table. `sonicriders.map` has no such symbols either. The code that maps stage IDs to FST entries is still unidentified.
- Geometry, collision, checkpoint and spawn field offsets are not documented. Nothing in this doc should be used as a format spec yet.

### Next steps

1. Run the Dolphin write breakpoint on `0xCC006018` and capture the caller of the `0x20000` write: return address, `r3`–`r6`, and the block the length came from.
2. Map the `lbl_8021C2D8` slot table to DAT files, starting with whether `0501.DAT` is registered through `func_80088594`.
3. Once the entry table at `+0x60` (`gcaxTBLD`) is parsed, confirm which section holds geometry, collision, checkpoints and spawns.
4. Only then write the field tables here, with each claim marked UNVERIFIED until it is checked against the binary.

## Status

Phase 2.1 partially done. Container candidates identified, the DTPK validation path located, and the DVD layer identified as the SDK's DVDFS. The `0x20000` read length is still unattributed. Phase 2 items 2.1–2.7 remain open.

## DI store trace (static, UNVERIFIED)

Searched `decomp/asm/lib.s` for DI register writes through a computed `0xCC006000` base, not only the literal `CC006018` pattern.

- `func_80012408` (`lib.s` 10409) writes the full DVD read-DMA sequence through `r4 = 0xCC006000`: `0x08 = 0xA8000000`, `0x0C = offset >> 2`, `0x10` and `0x18 = length` (`r29`), `0x14 = memory address` (`r28`), and `0x1C = 3`. The `0x18` store is the DILENGTH write (`lib.s` 10442 at `0x80012484`).
- Its arguments are `r3` = memory address, `r4` = length, `r5` = disc offset, `r6` = callback. Five callers, at `0x80012258`, `0x8001235C`, `0x80012608`, `0x800126E4` and `0x8001278C`, pass fields of a request struct as `r3`..`r6`.
- `func_80012518` (`lib.s` 10482) is a DI command dispatcher. It writes DICR and uses a 64-bit time conversion, not a file size.
- `func_80012598` (`lib.s` 10519) also writes `0xCC006000 + 0x18` (DILENGTH) with `r4` as the length. Its callers are at `lib.s` 11949, 12603, 12725 and 13292.
- `func_800137A8` (`lib.s` 11858) is the SDK's DVD/FST init; it reports `load fst` at `0x80013848`.
- `func_800141A8` (`lib.s` 12592) passes literal `0x20` and `0x420` to `func_80012598` at `0x800141C4`–`0x800141C8`. Neither is `0x20000`.
- Static result: no DILENGTH store in the decomp loads a literal `0x20000`. The length is an argument, so the runtime breakpoint on `0xCC006018` is still needed to confirm which caller issues the `0501.DAT` read.

### Request struct trace (static, UNVERIFIED)

- The DI read request for `func_80012408` is staged in `lbl_801B3BF0`. `func_80011FF4` (`lib.s` 10119) resets it, and `lbl_80012034` (10143) copies its fields to `+0xB8`–`+0xC0`.
- `func_800137A8` uses `lbl_801B3CC0 + 8` as its block pointer (`r31`), at `0x800137E8`–`0x800138A0`. It reads a `(length, ...)` pair from that block, rounds the length up to 0x20, and passes it to `func_80012598`.
- `lbl_801B3CC0` (`bss.s` 68) is a BSS staging block. No decomp instruction stores a literal `0x20000` into it, and its contents are filled from the SDK path described below.
- `lbl_8021BD88` (`sbss.s` 335) holds `0x80000000` (set at `0x800137EC`), so `+0x38` and `+0x3C` are fields of the SDK's low-memory boot block. The FST loader uses them as the destination buffer and as a limit. UNVERIFIED which boot-info fields those are.
- Conclusion: the `0x20000` length is not present in the source of this layer. It arrives as a caller argument.

### `lbl_801B3CC0`: the SDK's FST staging block (static, UNVERIFIED)

This replaces an earlier reading of the same block as a game request list, which was wrong.

- `lbl_801B3CC0` (`bss.s` 68) is a 0x20-byte BSS block used by the SDK's DVDFS. The FST-load callback `lbl_80013880` takes `base+8` as its pointer (`r31`, set at `0x800138A0`): the word at `0(r31)` (= `base+8`) is the byte count, and `base+4` is the offset (`lwz r5, 4(r5)` at `0x800138E8`). `func_80013FF8` instead uses the base directly and touches `+0x00`, `+0x20` and `+0x24` (`lib.s` 12469–12473), so those are separate fields, not the count and offset.
- The callback `lbl_80013880` (`0x80013880`) installs itself as the next callback (`lbl_8021BDC8`), bounds the length against `lbl_8021BD88+0x3C`, rounds it up to 0x20, and calls `func_80012598` with the buffer at `lbl_8021BD88+0x38`, the block offset and the rounded length. This is the FST-read loop.
- No `stw` in the decomp names `lbl_801B3CC0` directly; the block is addressed through a computed base throughout.
- The block is 0x20 bytes and unrelated to `0501.DAT`'s offset or length. It cannot explain the `0x20000` read.

### FST check for 0501.DAT (verified against the disc image)

- The FST at disc offset `0x144000` (size `0x72B1`) lists `0501.DAT` at offset `0x3DC0000`, size `0x56800` (354,304 bytes).
- `10AIAI.DAT` is at `0x4A70000`, size `0x11800`. `10ULALA.DAT` is at `0x4ED8000`, size `0x18000`.
- The disc header gives FST offset `0x144000`, FST size `0x72B1` and FST max size `0x72B1`, so the FST fields are not the source of `0x20000` either.
- The `0x20000` DMA at `0x3DC0000` is 131,072 bytes, about 37% of the file. It is a partial chunk, not the file size, so the value is a per-request length passed by the caller.

### Where the `0x20000` comes from (search result, 2026-11-04)

The value is not a constant, a table entry, or a header field in the DOL, the REL or the disc metadata. Checks, all against `decomp/baserom.dol`, `decomp/asm/` and `.local/disc/sonicriders.iso`:

1. No `0x20000`, `131072` or `1 << 17` literal in any `.c`, `.h`, `.s` file under `decomp/`, and no `slwi ..., 15` / `slwi ..., 17` in `lib.s`. The length is not built by a shift.
2. All 31 `lis rN, 2` sites load `0x00020000` as a DI command operand, not a length (see the jump table `lbl_80014C60`–`lbl_80014CEC`, `lib.s` 13367–13400, where `li r3, 0`, `lis r3, 1`, `lis r3, 2` and `lis r3, 3` feed `func_80012BE0`).
3. The only `0x00020000` words in the DOL data sections are unrelated: `0x800E4EE8` is a 4-word bitmask table `and`ed against flag bits (`0x8006F690`–`0x8006F6B8`); `0x800F3CEC` / `0x800F3EDC` are pixel pattern data; `0x80120C70` is part of the power-of-two table `0x2000 0x4000 0x8000 0x10000 0x20000 0x40000`; `0x80120E14`, `0x80120E54`, `0x80120E94` are offset tables.
4. `0501.DAT`'s header and TOC (first `0x8E0` bytes) contain no word-aligned `0x00020000` or `0x00000800` field, so the two logged reads are not size fields from the pack TOC.
5. `_Main.rel` has no `0x20000` length and no reference to `lbl_801B3CC0`.

The SDK readers do not split requests, so the chunking decision is made by game code before the call. That code is not among the decomp's direct call sites: the shipped build probably reaches `DVDReadAsync` through a function pointer or through code built differently from this decomp. Confirming it needs the Dolphin trace.
