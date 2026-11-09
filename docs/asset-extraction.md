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
- The caller that issues the `0x20000` read is now identified: the pack wrapper `lbl_8008E2FC` calls `func_8008DA74` with `0x20000` passed explicitly. See "Runtime captures: wrapper hits and the DMA" below. What `+0x08`, `+0x0C`, `+0x10` and `+0x18` mean is still unknown, and the small `0x800` tail read at `0x03DE0000` still has no identified caller.

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
- The 31 `lis rN, 2` sites in `lib.s` (UNVERIFIED): the DVD-area ones (`80014CC0`, `80014CE8` and their neighbours) load `0x20000` into `r3` and call `func_80012BE0`, which ORs its argument into `0xE2000000` and writes `CC006008` (a DI command word). Those are `0xE2` audio-status subcommands, not file lengths. The other sites (`80017248`, `80043928`, `800439FC`, `8004DFC8`, `8007xxxx` and so on) feed `func_8000D814`, `func_8000D89C`, or are plain `lis r0, 2` bit-mask setups. The one exception found later is `0x8008DB10`, which stores `0x20000` as a request length; see "The pack-open default" below. This bullet's earlier "none computes a length" reading is withdrawn.
- Conclusion: the `0x20000` read has a static source — the pack loader's default request length (`func_8008DA74`). What still needs the runtime trace is which slot and pack it belongs to. See "The pack-open default".

### Loader search (UNVERIFIED)

- The magic check exists but is obfuscated; see "gcaxDTPK magic check in the binary" above. The earlier conclusion that no code matches the magic is withdrawn.
- `decomp/asm/_Main/text.s` (489,745 lines) has no named DVD symbols (`DVDOpen`, `DVDRead`, `DVDFastOpen`, `OSReport`); functions are labelled by address only, so calls appear as `bl func_8001xxxx`. It does call the SDK readers, e.g. one call at `0x00175D98` that reads the `BNR1` banner with a fixed length of `0x1960`.
- `_Main.rel` also has no reference to `lbl_801B3CC0`. Its 45 `lis rN, 2` sites are mostly heap-allocator calls `func_800E2D68(align, size)` (e.g. `li r3, 0x20` with `lis r4, 2` is a 128 KiB, 0x20-aligned allocation), but five of them, at `0x000B7FEC`, `0x000B80B0`, `0x000B83DC`, `0x000B8534` and `0x000B86A8`, load `0x20000` as the pack-open length argument. See "Stage-pack table" below. The earlier "no `0x20000` read length" reading was incomplete.
- The only `0x4454` hits in `asm/lib.s` outside the magic check are unrelated stack offsets, not the `DTPK` magic.
- Runtime route blocked: the Cloud VM has no Dolphin, no X display and no Xvfb (x86_64, 8 cores, 48 GB free). A read trace needs an emulator with a display, so it has to run on a machine that has one.
- Headless attempt (Ubuntu 24.04, non-root): Xvfb was unpacked from apt into `.local/apt/root` with its libraries resolved, but it fails with `Failed to compile keymap` because it runs the absolute path `/usr/bin/xkbcomp`, which is absent (no root to install it). Ubuntu apt has no `dolphin-emu` package; `dolphin` there is the KDE file manager. A headless Dolphin needs a source build or an AppImage.
- The stage-file strings and the stage/pack table were later found in `decomp/asm/_Main/data.s`; this conclusion is withdrawn. See "Stage-pack table" below.
- Geometry, collision, checkpoint and spawn field offsets are not documented. Nothing in this doc should be used as a format spec yet.

### Next steps

1. The DTPK layer is now statically accounted for: the pack to open comes from `lbl_001E9BE4` via the stage value in `lbl_10017928`, the name is resolved to an FST entry by `func_8009DCC8`, and the read length is `0x20000` unless the caller passes otherwise. This was caught live (see "Runtime captures: wrapper hits and the DMA"): the wrapper is entered from `0x000B83EC` and `0x000B8544` with `r6 = 0x00020000` and slot `2` or `4`. Still open: one hit correlated with the `0x03DC0000` DMA in the same frame, so a slot can be tied to `0501.DAT`. Cross-check the DI breakpoint on `0xCC006018` (`0xCC006014` `= 0x010D0320 + 0, DILENGTH `= 0x00020000`) when doing it.
2. The stage-ID writers are traced (see "Stage-ID writers" above): the normal course selector is `0x001235C8` writing through the 20-entry table `lbl_001CE598`, and stages 9–16 reuse the stage 1–8 packs. Still open there: identify which screen owns the ten-row table `lbl_001F222C`, and what the third byte of `lbl_001CE598` indexes (presumed mission id).
3. Explain the `0x800` read at `0x03DE0000` (`0501.DAT+0x20000`): statically it is 0x800-aligned data, not the TOC (`0x8E0` bytes at the pack start). The wrapper is never entered with `r6 = 0x00000800`, so it comes from another path: break on the `+0x18` file-object method called from `0x8008DDE4`/`0x8008E108`, or on the `func_800153E4` request builder, and read the caller.
4. The `0x8000000N` container is decoded (see "The `0x8000000N` container is decoded"). Next: decode `1` (4,746,688 bytes decoded; the first bytes are `02 02 02 03 02 03 01 01 06 ...`, which looks like a table or byte map, not a header) and find its sections; do the same for `1M`, `1V`, `0`, `11`, then confirm which section holds geometry, collision, checkpoints and spawns. The `gcaxTBLD` parse is lower priority if those packs are audio. Only then write the field tables here, with each claim marked UNVERIFIED until it is checked against the binary.

## Status

Phase 2.1 largely resolved statically: the DTPK packs are opened by name through the DOL's DVDFS (`func_8009DCC8` → `func_8008DA74`), the stage/pack table (`lbl_001E9BE4`, chosen by the stage value in `lbl_10017928`) maps `0501.DAT`–`0509.DAT` with FST entries 4–12, and the logged `0x20000` head read comes from the REL pack openers with an explicit `0x20000`. The stage-ID writers are now traced: the course selector `0x001235C8` picks stage 1–16 through `lbl_001CE598`, stage 1 is the startup default (`0x001134DC`), and stages ≥17 use `0509.DAT`. The runtime capture confirms the head read reaches `lbl_8008E2FC` with an explicit `0x20000`, and that the `0x800` tail read does not. Remaining unknowns are the `0x800` read's caller, which slot owned the logged `0501.DAT` DMA, the identity of the ten-row preload menu, and the format of the pack contents. Phase 2 items 2.1–2.7 remain open.

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

### The pack-open default: `0x20000` (static, 2026-11-05)

This is the static source of the logged `0x20000` DMA. It is a default request length in the pack loader, not a file size, a table entry or a DI command operand.

- `func_8008DA74` (`lib.s` 151439, `0x8008DA74`) starts a DTPK pack open. Arguments: `r3` = slot index (`< 0x20`), `r4` = the DVD FST entry number resolved from the pack name (stored at `req+0x0C` at `0x8008DC34`; see "Stage-pack table"), `r5` = mode, `r6` = requested length. An earlier revision of this bullet called `r4` a "pack id"; it is the FST entry number the thunk `lbl_8008E2FC` resolves from the name.
- Early-outs, all static, offsets from `lbl_8021C2D8`: `-1` slot `>= 0x20`; `-2` the word at `+0x304 + slot*4` is null; `-3` the byte at `+0x384 + slot` is non-zero (slot already busy); `-20` the word at `+0xE94 + slot*4` is not `0xFF`; `-12` the length is not `0x800`-aligned (`clrlwi. r0, r6, 0x15` at `0x8008DAEC` keeps the low 11 bits).
- `0x8008DB04`–`0x8008DB18`: when the caller passes length `0`, it loads `lis r4, 2` and stores `0x00020000` at `lbl_801DDD68 + slot*0x40 + 4`. When the caller passes a length, that value is stored at the same field instead (`0x8008DB20`–`0x8008DB30`).
- That `+0x04` field is the request length for the rest of the slot's life. It is the size argument of the allocator call at `0x8008DB90` (`func_8000ABB4(heap, size)`, which rounds up to 64 bytes), and it is passed as the length to the file object's `+0x18` method with the buffer slot at `req+0x1C` (`0x8008DDE4`, `0x8008E108`, `0x8008E11C`). Nothing in this layer or in the SDK reader rewrites it.
- The slot's request is completed at `0x8008E2A8`, which calls `func_80088594(slot)` — the `gcaxDTPK` validator — and then marks the slot done: `+0xD14 = 2` and `+0xE94 = 0xFF`.Consequence: a pack opened without an explicit size is read as `0x20000` bytes and the buffer is validated as `gcaxDTPK`. That is the sequence the DVD log shows for `0501.DAT` (one `0x20000` DMA at the file start, no separate header read), so this default is the best static match for the logged length.

Correction (2026-11-05, later the same day): every pack-open call site actually found in the REL passes the length explicitly as `0x00020000` (`lis r6, 2` in front of all five `lbl_8008E2FC` calls and the same constant at the equivalent call inside `lbl_000B8468`). So the value the shipped game uses comes from the REL callers, not from this default; the `r6 == 0` default path has no known caller. The alignment rule (`0x800`-multiple) and the header validation after the read still hold.

UNVERIFIED: that `0501.DAT` occupied the slot opened on that frame, and whether the following `0x800` read at `0x03DE0000` is a second request in the same slot. `0x800` passes the alignment check above, so it is a legal explicit length; the bytes at `0501.DAT+0x20000` are high-entropy, so that read is data rather than a second readable header. The runtime capture below confirms the wrapper is reached with `r6 = 0x00020000`, but it is never entered with `r6 = 0x00000800`, so the `0x800` read does not come through this wrapper. The slot question stays open.

### Stage-pack table (static, 2026-11-05)

This closes the "which pack, which caller" question statically, with the disk FST as witness.

**Disc FST entry numbers (verified against `sonicriders.iso` at `0x144000`, string table at FST+`0x4E48`, root entry's end index `0x686` = 1670 children):** entry 2 = `00.DAT`, entry 3 = `01.DAT`, entries 4–12 = `0501.DAT`–`0509.DAT`, entries 17–36 = the `10xxx.DAT` character packs. So `0501.DAT` is FST entry 4, at `0x3DC0000`, size `0x56800`.

**The DOL side: name → entry → slot.** The thunk `lbl_8008E2FC` (`lib.s` 152024) is the real pack-open entry. Its second argument is the pack name string: if null it returns `-128`, otherwise it calls `func_8009DCC8(name, 0)` to resolve the name against the DVD filesystem; a zero result returns `-21`, otherwise the resolved FST entry number travels in `r4` into `func_8008DA74(slot, entry, buffer, length, r7, r8)`. So `func_8008DA74`'s second argument (stored at `req+0x0C`) is the FST entry number resolved from the name, not a pack id and not a handle found by scanning. The wording in "The pack-open default" has been corrected to match.

**The REL side: five call sites, all with explicit `0x20000`.**

- Startup block (`lbl_000B7F2C`): opens `00.DAT` (name literal at `lbl_001E9670`) then `01.DAT` (`lbl_001E9678`), each with a fresh `func_800E2D68(0x20, 0x20000)` buffer, registers `(encounter id 0x9e0 / 0x2ee0, record)` at `lbl_10026620 + slot*4` and at `+0x80`, and waits on `lbl_8008D9F8(slot) == 2` (with `lbl_0014C32C` advancing frames).
- Character-pack helpers: struct arrays of 0x1C-byte records at `lbl_001E9BE4` (9 records, `05xx.DAT` stage packs), at `lbl_001E9EBC` / `lbl_001E9CE0` (17 records each, `10xxx.DAT` name strings and `10Jxxx.DAT` variants), each record holding `{ name (12 bytes), 0, TOC size at +0x10, bulk size at +0x14, section-ID list at +0x18 }`. The +0x10/+0x14 fields of all nine `05xx` records match the `gcaxDTPK` headers on disc (+0x10 = 0x8E0 TOC size for `0501.DAT`, +0x14 = 0x55400 bulk size). Verified for all nine packs.
- `lbl_000B8468` (the stage-pack opener, called from `0x0003C248` and `0x000AF678`): picks a record `lbl_001E9BE4 + (n-1)*0x1C` where `n` is the stage value in the global `lbl_10017928` (values 1–8 first eight records, 9–16 the same eight again, ≥17 record 8), allocates `0x20000` with `func_800E2D68(0x20, 0x20000)`, registers `(name, TOC size)` at `lbl_10026620 + slot*4` and `bulk size` at `+0x80` where slot is the byte at `lbl_1001A6E4` — the REL's next-free-slot counter, incremented after the open succeeds at `0x000B8590` — and calls `lbl_8008E2FC(slot, name, buffer, 0x20000, 0, 0)`.

**The stage/pack table `lbl_001E9BE4` (7 words × 9 records, `_Main/data.s` 20323):**

| idx | name | +0x10 (TOC size) | +0x14 (bulk size) | +0x18 (section-ID list) | FST entry | disc offset |
|---|---|---|---|---|---|---|
| 0 | `0501.DAT` | 0x8E0 | 0x55400 | `lbl_001CD514` | 4 | `0x3DC0000` |
| 1 | `0502.DAT` | 0xCC0 | 0xAB2C0 | `lbl_001CD538` | 5 | `0x3E18000` |
| 2 | `0503.DAT` | 0xDE0 | 0xA8840 | `lbl_001CD57C` | 6 | `0x3EC8000` |
| 3 | `0504.DAT` | 0x9C0 | 0x40EC0 | `lbl_001CD5D8` | 7 | `0x3F78000` |
| 4 | `0505.DAT` | 0xD40 | 0x9ECE0 | `lbl_001CD62C` | 8 | `0x3FC0000` |
| 5 | `0506.DAT` | 0xA80 | 0x9DFE0 | `lbl_001CD670` | 9 | `0x4060000` |
| 6 | `0507.DAT` | 0xEA0 | 0xAC180 | `lbl_001CD6B4` | 10 | `0x4100000` |
| 7 | `0508.DAT` | 0x14A0 | 0xA1380 | `lbl_001CD6D0` | 11 | `0x41B0000` |
| 8 | `0509.DAT` | 0x9A0 | 0x522C0 | `lbl_001CD708` | 12 | `0x4258000` |

The +0x18 pointers sit in `_Main/rodata.s` (`lbl_001CD514` onward) and hold lists of 0xA9xxxxxx IDs — e.g. `lbl_001CD514` for `0501.DAT` is four 0xA90F0100 then four 0xA90F0300, ending with 0 — the same 0xA90xxxxx ID family as the character-pack section-ID tables near `lbl_001E9610`. Presumed pack section IDs. UNVERIFIED semantics.

So, statically: `0501.DAT`'s `0x20000` head read comes from `lbl_000B8468` (or one of the four structurally identical sibling call sites), the name is resolved to FST entry 4 by the DOL's own DVD filesystem lookup, and the DTPK slot used is whatever byte `lbl_1001A6E4` held at that call — not a fixed slot. The stage-ID global's writers are traced in "Stage-ID writers" below. UNVERIFIED: whether the `0x800` read at `0x03DE0000` is the pack's TOC transfer (`0x50x` TOC ranges 0x8E0–0x14A0 bytes; the aligned 0x800 read cannot cover the whole 0x8E0 table).

### Runtime captures: wrapper hits and the DMA (Dolphin, 2026-11-06)

Captured by the user on a machine with a display (this project's Cloud VM cannot run Dolphin; see "Loader search"). Breakpoints were set on code addresses in the running image — `0x8008DA74` (`func_8008DA74` entry) and `0x8008E2FC` (`lbl_8008E2FC` wrapper entry). Session: boot to the start of a normal race.

**The head read.** The `0x20000` DMA for `0501.DAT` goes to disc offset `0x03DC0000` in buffer `0x010AE0A0` (physical; virtual `0x810AE0A0`). Dolphin shows no RAM at that address until the transfer completes, so it has to be read after the DMA. This matches the DVD log at the top of this doc.

**Wrapper hits.** At `lbl_8008E2FC` entry, `LR = 0x8008E364`, which is `bl func_8008DA74` at `0x8008E360` plus four — the wrapper-to-loader link is confirmed live. `r6 = 0x00020000` on every hit, so the length is explicit at runtime as the static reading says. `r3` (slot index) read `2` or `4` depending on the hit.

Two REL call sites were hit. Read as return addresses (`LR = call + 4`, the same convention as the wrapper's own `LR` above) they are the calls at `0x804B40E8` and `0x804B4240`, which with module base `0x803FBCFC` are REL `0x000B83EC` and `0x000B8544`:

| return address | REL call site | `text.s` line | containing block |
|---|---|---|---|
| `0x804B40EC` | `0x000B83EC` | 200002 | `lbl_000B8368`, the sibling pack loop (index byte at `r29+0xBA`, bounded by `0x11`, records of `0x1C` — presumably the 17-entry `10xxx` character-pack array, UNVERIFIED) |
| `0x804B4244` | `0x000B8544` | 200096 | `lbl_000B8468`, the stage-pack opener |

Both are `bl lbl_8008E2FC` instructions in `_Main/text.s`. Earlier notes derived the module base as `0x803FBD00`; that is four bytes high if these values are `LR`, and nothing else in the repo pins the base, so treat `0x803FBCFC` as the reading implied by the capture. Read instead as bare call-site addresses against `0x803FBD00`, the offsets are identical — the base is four bytes higher and the address four bytes lower. The REL offsets are the part that is solid. UNVERIFIED as a link-address claim either way.

At `0x000B8544` the static code takes `r3` from the byte at `lbl_1001A6E4` (the REL's next-free-slot counter), sets `r6 = 0x20000`, and points `r4` at the `lbl_001E9BE4` record for the stage. A slot value of `2` or `4` is therefore that counter's value at the call, not a fixed slot.

UNVERIFIED and unresolved: the capture also noted `r3` being loaded from `0x80615764` at the `0x804B40EC` hit. That address appears nowhere in `decomp/asm`, `_Main.map` or `sonicriders.map`, and the static code at `0x000B83EC` takes `r3` from `lbl_1001A6E4`, not from `0x80615764`. Either the note describes a different instruction in the opener, or `r3` is reloaded on a path not yet traced. What lives at `0x80615764` is unknown; it is not the slot counter.

**The `0x800` tail read.** About 156 ms after the DMA, a `0x800` read at disc `0x03DE0000` (= `0501.DAT + 0x20000`) goes to the same buffer. Its caller is not found. The wrapper is never entered with `r6 = 0x00000800`, so this read is not issued through `lbl_8008E2FC` — it comes from another path, or after the wrapper returns through a different request field.

**What this settles.** The `0x20000` head read is runtime-confirmed to pass through `lbl_8008E2FC` with an explicit `0x20000`, from one of the two REL sites above. Not settled: that the `0501.DAT` DMA at `0x03DC0000` is the request made by the same slot at that moment (the DVD log and the breakpoint hits are separate observations, not one correlated event), and the `0x800` caller.

### Disc survey and the second container family (read from the CISO, 2026-11-08)

Source: `tools/extract/ciso.py` run on the user's US `.ciso`. Verified means read from the image in this session; the interpretations are UNVERIFIED.

Verified:

- The FST lists 1,669 files. Counts by prefix: `S1`…`S9` bundles (many `*.ADX` music tracks plus extensionless files such as `S10F`), `0`…`19` and `M1`…`M12` (2–5 MB), `P000`…`PZ*` groups (50–120 kB each, many with an `M` variant), `TG*`, `TS*`, `E*.ADX`, `*.SFD` movies, `VOICE_E.AFS`, `V_CHAO_E.AFS`, `_Main.rel`.
- Every extensionless game file sampled (16 of them, including `1`, `1M`, `1V`, `1TE`, `0`, `11`, `S10F`, `S11F`, `M1`, `P000`, `TG0`, `TSC`, `AS`, `MB`, `ME`) starts with the same 0x20-byte header: `80 00 00 01`, then a big-endian u32, then zeros to `+0x20`. The payload starts at `+0x20`.
- That u32 is a multiple of `0x20` in all 16 files and is larger than the file size in all 16 (ratios 1.26 to 3.48; for example `1`: `0x486DC0` = 4,746,688 against a 2,597,560-byte file). The `.DAT` files (`gcaxDTPK`) do not use this header.
- `0501.DAT` read from the image matches the documented header. Its `gcaxTBLD` block (`+0x60`) contains repeated `0xAC44` (44,100) fields (11 in the TOC), 16-word signed 16-bit tables, a 0x100-byte monotone curve at `+0x170`, and `0xA9xx....` ID lists.

UNVERIFIED interpretations:

- The `0x80000001` u32 is the uncompressed size and the payload is compressed (confirmed below). The first payload bytes (`00 40 40 80 20 18 28 1c ...` in `1TE`) look bit-packed, not a plain byte-oriented LZ stream. (Superseded: the algorithm and decoder are identified below.)
- The `gcaxDTPK` packs hold audio (sample-rate fields, coefficient-like tables, ID lists), not stage geometry. If that holds, the `0501`–`0509` stage-pack table in the REL selects per-stage sound banks, and the earlier hypothesis that `05xx.DAT` is the stage container is wrong. The evidence is suggestive only: an 8-byte-frame ADPCM header test was inconclusive because the regions are zero-padded.
- Stage geometry, collision and checkpoints are most likely in the `0x80000001` files, with `1`…`9` and `11`…`19` (and their `M`/`V`/`TE`/`TJ` variants) the first candidates by size. Nothing in them has been decoded.

Decompressor search before the live catch (2026-11-08, all negative; superseded by the section on the decoded container below):

- The public decomp at the pinned commit `4f42e59` was cloned and searched. No instruction sequence compares a word against `0x80000001` directly, including the obfuscated `addis`/`xoris` forms used for the `gcax` check.
- A heuristic scan of every function in `asm/lib.s` and `asm/_Main/text.s` (reads word `+4`, adds `0x20`, byte load/store loop, top-bit test) returned eight weak hits, none a decoder. The two best were struct-copy code.
- `1TE` (24,800 bytes decompressed, 8,213-byte payload) was tried against Nintendo LZ10-style decoders (both flag-bit orders, both reference polarities, both length/displacement layouts). All fail within the first 16 input bytes, so it is not plain LZ10.
- The first payload bytes are the same prefix, `00 40 40 8x`, in every file sampled (`1TE`, `1TJ`, `2TE`, `P000`, `TG0`, `1`, `11`, `0`, `AS`), with payload entropy about 7.4 bits per byte. That points at an entropy-coded or bit-packed stream with a short fixed preamble, not a byte-oriented LZ.

Next: catch the decoder live. In Dolphin, load a stage, break on a code address that touches the compressed file's buffer (or set a memory write breakpoint on the destination of the first `0x80000001` read), then read LR and the callstack. The disc read of `1` or its sibling is visible in the DVD log, so the destination buffer address is available.

Consequence for the plan: Phase 2.1 should be re-aimed at the `0x80000001` container: find its loader and decompressor in the decomp (a reader of a 0x20-byte header, then a size-bounded decode loop), decompress `1` and `1TE`, and only then look for stage structures. The `gcaxDTPK` work above stays valid as loader documentation but is not on the stage-data path.

### The `0x8000000N` container is decoded (2026-11-08, caught live in Dolphin, verified on `1TE`)

Verified. The decoder is REL `lbl_001594F4` (init `lbl_00159DB8`), reached from the loader thread at REL `0x0014DD94`. It was found by a Dolphin read breakpoint on the decoded buffer: the stop was at PC `0x80555A6C` = REL `0x00159D6C`, LR `0x80549A98` = REL `0x0014DD98`, which is the return address of that call. The REL load base used is `0x803FBD00` (from LR `0x8054A0B0` at the memmove call `0x14E3AC`). This corrects the `0x803FBCFC` figure in commit `4c29e6f`.

Format (whole-buffer path, `lbl_00159B78`; the state-machine path at `lbl_00159790` is the same algorithm run on streamed chunks):

- Header (0x20 bytes, big-endian): `u32 flag`, `u32 decoded_size`, zeros to `+0x20`. The low byte of `flag` is the unit size `N` (1 or 2; the init stores it at struct `+0xC`). The high bit is not read by the decoder.
- Payload is a bit stream read MSB first, starting at `+0x20`:
  - flag bit `0` → literal: copy the next `N` bytes to the output.
  - flag bit `1` → match: read an `N`-byte big-endian offset, then an `N`-byte big-endian length, then copy `length` bytes from `output[-offset]` one byte at a time (overlap allowed).
- Data bytes are not byte aligned. After a flag bit they are read at the current bit position: `out = (src[p] << (8 - bits_left)) | (src[p+1] >> bits_left)`. When the flag bit was the last bit of a byte, the pointer moves to the next byte and `bits_left` resets to 8.
- Decoding stops when the output reaches `decoded_size`. The decoder has no minimum match length, no end marker and no checksum.

Evidence: `1TE` (8,245 bytes on disc) decodes to exactly 24,800 bytes, equal to the header size field. The output contains `St01_Map`, `St01_Name_E` and a `GCIX`/`GVRT` texture header with a valid GVR palette, so the decode is correct, not merely length-consistent. Disc-wide: all 1,562 files on the US disc that carry the `80 00 00 0N` header decode to exactly their header size, with no errors (107 other files, the `.ADX`/`.SFD`/`.AFS`/`.DAT` ones and the DOL/REL, have no such header). Every one has flag `0x80000001`, so `N = 1` everywhere: offsets and lengths are single bytes, the window is 255 bytes and the longest match is 255. `N = 2` is implemented by the decoder but never occurs on this disc.

Re-encoding: the disc's compressor was reconstructed from the token stream of `1TE` (5,678 tokens: 1,825 matches, minimum length 2, maximum 255, maximum offset 255, no match shorter than the longest available). Rules: greedy; at each position take the longest match in the 255-byte window; accept it if the length is at least 2; on a tie in length take the FARTHEST offset; otherwise emit a literal; pad the stream with zero bits to a byte, and the file with zeros after that.

Verified on the whole disc with `tools/extract/srlz_check.c` (decode, re-encode, compare with the original bytes): all 1,562 container files re-encode byte for byte. 1,554 do so with the rules above. The other eight (`P240`, `P240M`, `PO40`, `PO40M`, `PO70`, `PZ40`, `PZ40M`, `PZ70`) need one extra behaviour: the compressor let a match read one byte past the end of the data, so their last match runs one byte beyond the declared size (the decoder writes it into the slack, as the game's decoder would). With one virtual zero byte after the data those eight also reproduce exactly; this is the `overrun` option of `srlz.encode()`. Why exactly those eight and why the byte reads as zero is not explained (it fits a zero byte past the buffer, but that is a fit, not a finding). This closes the byte-identical round trip for the container layer (Phase 2.6, container part).

Tools: `tools/extract/srlz.py` (`decode`, `encode`), `tools/extract/srlz_check.c` (whole-disc check; about 1 s for a 2.6 MB file), `tools/extract/test_srlz.py` (offline tests).

Still UNVERIFIED: what the decoded sections hold. `1TE` decodes to a table starting `St01_Map` / `St01_Name_E` followed by a `GCIX` block, so it looks like a name/texture file (probably the stage-name text card), not geometry. The big files `1`…`9` are the stage candidates.

### The decoded package layout (survey of `1`, `1M`, `1V`, `0`, 2026-11-08)

Verified: `tools/extract/srpack.py` parses and rebuilds all four decoded files byte for byte (`1` = 4,746,688 bytes, `1M`, `1V`, `0`). The field meanings below are UNVERIFIED except where `srpack.py` checks them.

- `+0`: `u32` group count (45 for `1`, `1M`, `1V`; 25 for `0`).
- `+4`: one `u8` per group, the number of slots in that group (sum 187, 177, 175 and 115).
- Next 4-byte boundary: one `u16` per group, the cumulative first-slot index. This matches the byte list exactly in all four files (checked by `parse`).
- Then a few small tables not yet parsed (they contain values such as `0x1392`, `0x083e`; meaning unknown).
- Slot table (`+0xE8` in `1`, `1M`, `1V`; `+0x84` in `0`): one `u32` absolute offset per slot, `0` for an empty slot (13 empty in `1`). Offsets are 0x20-aligned and non-decreasing. Blob `i` runs to the next larger offset, so padding stays with the preceding blob.

Slot kinds in `1` (first four bytes, UNVERIFIED names): 107 `NGIF` blobs (`NGIF`, `0x18`, then a count and a 0x20 stride; likely model or mesh containers, since `st01_map_4141.gnm`/`.gnv` names sit inside them); about 40 texture archives (header `u16` count then `u32` offsets, with embedded names such as `ring`, `iron`, `chain`, `Item`, `boost_05`, `st01_sky`, and `GCIX`/`GVRT` textures inside); 3 `01 01 00 01` blobs (slots 130–132) holding records of 0x30 bytes that start with three floats and a bounding-box-like float, plus offsets into the same blob, which are the strongest candidates for stage object or collision placement; 5 `GC`-prefixed blobs (slots 178–182); small `AN`/`AI`/`AB` animation-looking blobs (slots 0, 1, 170, 171).

Not yet known: which slots are the drivable surface, collision, checkpoints and start positions. The next step is to find the REL code that reads slots 130–132 and 178–182 (search for the group indices used by the stage loader), or compare `1`, `1M` and `1V`, which are the same stage in different modes and should differ only in the object and checkpoint slots.

### What differs between `1`, `1M` and `1V`, and what the `NGIF` blobs are (2026-11-08)

Measured with `srpack.split` on the decoded files:

- `1M` has 177 slots and `1V` has 175, against 187 in `1`, and the group tables differ. By content hash, 142 (`1M`) and 144 (`1V`) of the 174 non-empty slots of `1` appear byte-identical in the other file.
- In `1` the per-stage content is concentrated in groups 0–6 (slots 0–44: the animation-style blobs, the large `NGIF` groups of 235 kB and 1.35 MB, and four archives) and group 16. Groups 7–15 and 17–44 are mostly shared with `1M` (all of 19–44, including the three `01 01 00 01` blobs, the `GC` blobs and the animation blobs, are 100 % identical). So the shared groups are common objects and effects, and groups 1–6 are the map itself.
- The `NGIF` blobs are chunked files: `NGIF` header (size fields at `+0x10`/`+0x14`, `0x18`, a table count), then a data chunk with its own four-letter tag, then `NOF0` and `NFN0` footer chunks, the latter holding a filename. Tags seen so far: `NGOB` (the large mesh-like blobs), `NGMO` (slot 6, name `st01_map_4141.gnm`), `NGMA` (slot 7, name `st01_map_4141.gnv`, starts with float triples such as `±40.0`), `NGTL` (slot 39, a texture list naming `st01_skroad00.gvr`, `st01_enseki01.gvr`, `st01_wallsk00.gvr`, ...). This looks like the SEGA Ninja GameCube chunk format; that identification is from recognizing the layout, UNVERIFIED against the binary.
- The `.gvr` names confirm that the texture archives hold GVR textures (`GCIX`/`GVRT`), as seen at `0x126700` in `1`.

Candidates for the drivable surface and collision: the `st01_map_4141.gnm` / `.gnv` pair (slots 6–7) for geometry, and the `NGMA` data for vertices; the checkpoint/path data is probably in the shared `01 01 00 01` blobs (slots 130–132), since those hold positional records, but they are identical between `1` and `1M`, which argues against them being stage-specific. Both statements are inference only.

### Slot roles in stage `1`, from the filenames inside the blobs (2026-11-08)

Names come from the `NFN0` footers and the texture-list chunks, so they are read from the data; the roles are inferences from the names and layout (UNVERIFIED against the REL).

- Groups 2–3 (slots 5–38): the map. `NGOB` blobs (models) alternate with small `NGMA` blobs named `st01_map_00NN.gnv` (`NN` = 41…49) and, at the ends, `NGMO` blobs named `st01_map_4141.gnm` / `st01_map_0049.gnm`. Slot 38 is a 70-texture archive for them.
- Groups 4–6 (slots 39–44): `NGTL` texture lists (`st01_skroad00.gvr`, `st01_enseki01.gvr`, `st01_wallsk00.gvr`, `car000.gvr`, `tratetu0.gvr`, ...) each followed by its texture archive.
- Groups 7–19 (slots 45–129): shared objects and effects by name: `P_DAS_002.gvr`, `DR_anim000.gvr`, `ITEM_000.gvr`, `tornado_05.gvr`, `item_inv.gnm`/`.gnv`, and so on.
- Group 22 (slot 133): `st01_sky.gvr` and `st01_Sky.gno`, the sky.
- Group 36 (slots 172–177): six `NGCA` blobs, camera paths (`st01_map_camera_Camera01.gnd`, `Camera02`, `st01_fullmenber_camera_Camera06.gnd`).
- Groups 37–41 (slots 178–182): five `GC`-prefixed blobs; unidentified.
- Groups 43–44 (slots 185–186): two 0xC0-byte blobs (`07 03 00 1b ...`, `05 00 00 03 ...`) with floats like 0.2, 0.7 and 3.6; unidentified.

Collision candidate, slots 130–132 (groups 20–21, `01 01 00 01`): slot 130 is 106,912 bytes with header `01 01 00 01`, `u16` 0x00B6 (182 records), then 0x30-byte records. Each record has a bounding sphere (centre xyz and radius as big-endian floats; record 0 is about (-48.97, -63.94, -405.26), r 64.36; record 2 has r 1973.37), five `u32` offsets into the same blob, and a `u32` of small counts (`0x02020000`, `0x04000000`). The offsets point to: an array of 16-bit pairs (index data) at 0x2228; floats that are vertex positions near the sphere centre at 0x2c1c; and unit-length float triples (face normals) at 0x2c94. Per-object sphere, index list, vertex positions and normals is what a collision mesh looks like, which makes these the best candidate for drivable-surface collision. Slots 131 (0xFC0 bytes) and 132 (0x2F40 bytes) have the same header with 0x19 and 0x0E records. They are byte-identical in `1` and `1M`, which fits collision shared between two variants of one stage. Tie to the REL (static, 2026-11-08): `lbl_00046C70` walks the table with stride `0x30` and adds the load base to the `u32` fields at record `+0x18`, `+0x24` and `+0x28`, which are exactly the three offsets above (index data, vertices, normals). `lbl_00046CE0` reads the record count as a `u16` at `+4`, loops records of `0x30`, reads a `u16` kind at `+0x1c` and a `u16` id at `+0x1e`, and for kinds `0x1f`, `0x32`, `0x33`, `0x34` tracks the largest id, then allocates two tables of `(max id + 1)` entries of 16 bytes (`lbl_10008224`, `lbl_10008228`). So the record layout is confirmed for the offsets, count, kind and id; the sphere (`+0x08`..`+0x17`), the index format and the meaning of the kinds are still inferred. `tools/extract/srcol.py` parses the three tables and checks that every offset lies inside its blob.

Results: in `1`, `1M` and `1V` the three tables are identical (182, 25 and 14 records; the slot numbers differ: 130–132, 120–122 and 118–120). Slot 130's kinds are 0 (68 records), 1 (72), 3 (29), 22 (3), 8 (4), 6 (2) and single records of 5, 9, 17 and 31. Slot 131 has kinds 1–4 and 20 with very large radii (9,051 for most), which fits trigger volumes rather than surface meshes; slot 132 is 14 records of kind 0. The only kind the REL singles out that occurs here is 31 (one record, id 1, in slot 130). The kind-to-surface mapping and the roles of slots 131 and 132 are UNVERIFIED.

### Stage-ID writers: what sets `lbl_10017928` (static, 2026-11-06)

Seven stores, five distinct paths, and they belong to different menus rather than one stage-select. All addresses are REL `_Main` offsets.

1. **Startup default — `0x001134DC`.** In the entry block `lbl_001134B0` of the state machine dispatched through `lbl_001F22C0` (states 0–0x26), it sets `lbl_10017928 = 1` next to `lbl_10017920 = 1`, `lbl_10017924 = 0`, then re-initialises the eight 0x1080-byte slot records. Every session therefore starts asking for stage 1 (`0501.DAT`) until a menu overwrites it.
2. **Ten-row preload menu — `0x00115888`, `0x0011589C`, `0x001158B0`** (handlers `lbl_00115880`, `lbl_00115894`, `lbl_001158A8`). The dispatcher at `lbl_001154D0` increments byte `lbl_001F2228` on entry (wrapping after 9) and jumps through the 10-entry table `lbl_001F222C` (`_Main/data.s` 29320). The ten handlers write these stage values: idx 0 → 1, 1 → 2, 2 → 3, 3 → 4, 4 → 5, 5 → 3, 6 → 4, 7 → 7, 8 → 0x11, 9 → 0x12. Each also fills the eight per-slot arrays (`lbl_00115FD4` with 0,1,2,3,4,5,6,0xF in various orders), sets `lbl_8021B8C0`/`C4`/`C8`, sets the timer `lbl_10017920` (0x2BC or 0x1F4) and calls `lbl_00037A38` to load the scene. Rows 5 and 6 repeat stages 3 and 4 with different slot lists, so the ten rows are not ten distinct tracks. UNVERIFIED which screen this is.
3. **The course selector — `0x001235C8`** (handler `lbl_001234E4`). On a pad-A press it builds a grid index from the cursor fields (row at `r30+0x16`, column at `+0x19`, page at `+0x1B`: pages 0 and 1 index two row tables loaded into `r28`, pages 2 and 3 use `row*5 + 0x50`), calls `lbl_000EE660(index)`, and writes the result pair out: `lbl_10017928 = entry[1]`, `lbl_10087DF4 = entry[2]`. `lbl_000EE660` searches the 20-entry, 3-byte table `lbl_001CE598` (`_Main/rodata.s` 14843) for `entry[0] == index`.

   The table, as `(id, stage, mission?)`:

   | id | stage | 3rd |
   |---|---|---|
   | 0 | 1 | 5 |
   | 1 | 2 | 5 |
   | 2 | 3 | 5 |
   | 3 | 4 | 5 |
   | 5 | 5 | 5 |
   | 9 | 5 | 6 |
   | 6 | 6 | 5 |
   | 7 | 7 | 5 |
   | 8 | 8 | 5 |
   | 4 | 8 | 6 |
   | 0xA | 9 | 5 |
   | 0xE | 9 | 6 |
   | 0xB | 0xA | 5 |
   | 0xC | 0xB | 5 |
   | 0xD | 0xC | 5 |
   | 0xF | 0xD | 5 |
   | 0x10 | 0xE | 5 |
   | 0x13 | 0xE | 6 |
   | 0x11 | 0xF | 5 |
   | 0x12 | 0x10 | 5 |

   Stages run 1–16, and tracks 5, 8, 9 and 14 carry a second entry with a different third byte (6 instead of 5) — consistent with two missions per track. This is what makes the reader's `9–16 → same eight packs` fold make sense: stages 9–16 are alternate missions on the same eight tracks, so the same DTPK is reused. UNVERIFIED that the third byte is a mission id, and that page 2/3 row arithmetic (`row*5 + 0x50`) addresses further entries.
4. **Three-entry special selector — `0x00139AD4`** (handler `lbl_00139970`, one of the 12 handlers in `lbl_001F3858` dispatched by `lbl_00138DC4`). On a pad-A press it stores `lbl_10017928 = r29+0x0D + 0x11`, where `r29+0x0D` is a 3-value cyclic cursor (0–2, wrapped at 3 with the `0xA9000100`/`0xA9000200` sound calls). That is stages **17, 18, 19**, all of which the reader resolves to record 8, i.e. `0509.DAT`.
5. **Four-per-page selector — `0x0014B4F0`** (`lbl_0014B44C`, spawned by `lbl_0003D4C0` when `lbl_10017920 == 0x320`). In state 2 it reads byte `lbl_1008CF74` as the page, steps the 4-value cursor `lbl_001F3DF0` (0–3, wraparound via `subfic`/`cntlzw`), and stores `lbl_10017928 = lbl_001D3B50[page*5 + step + 1]`: page 0 → stages 2, 3, 4, 5 and page 1 → 10, 11, 12, 13 (`lbl_001D3B50` holds `01 02 03 04 05` then `09 0A 0B 0C 0D`). It also sets `lbl_8021B8C0 = 8` and `lbl_10017920 = 0x320`.

**Consequence for the pack mapping.** Every stage value the five paths produce — 1–7 from the preload menu, 1–5 and 0x11–0x12 from the same table's other rows, 1–0x10 from the course table, 2–5 and 10–13 from the four-per-page selector, 0x11–0x13 from the special selector — lands inside the nine-record table: 1–8 → `0501.DAT`–`0508.DAT`, 9–16 → the same eight, and ≥17 → `0509.DAT`. So `0509.DAT` is not a ninth course in the normal rotation; it is the pack the ≥17 stages load, presumably a special-mode arena. UNVERIFIED.

### Where the `0x20000` comes from: search result and its limits (2026-11-04)

This was a search for the value as a literal. It found none because the constant is encoded as `lis rN, 2` (or `lis r4, 2` into a request field), which a text search for `0x20000` cannot see — see "The pack-open default" and "Stage-pack table" below. Checks made, all against `decomp/baserom.dol`, `decomp/asm/` and `.local/disc/sonicriders.iso`:

1. No `0x20000`, `131072` or `1 << 17` literal in any `.c`, `.h`, `.s` file under `decomp/`, and no `slwi ..., 15` / `slwi ..., 17` in `lib.s`. The length is not built by a shift.
2. The `lis rN, 2` sites that were checked load `0x00020000` as a DI command operand, not a length (see the jump table `lbl_80014C60`–`lbl_80014CEC`, `lib.s` 13367–13400, where `li r3, 0`, `lis r3, 1`, `lis r3, 2` and `lis r3, 3` feed `func_80012BE0`). This check was not exhaustive: it missed `0x8008DB10`, which stores `0x20000` as a request length. See "The pack-open default" above.
3. The only `0x00020000` words in the DOL data sections are unrelated: `0x800E4EE8` is a 4-word bitmask table `and`ed against flag bits (`0x8006F690`–`0x8006F6B8`); `0x800F3CEC` / `0x800F3EDC` are pixel pattern data; `0x80120C70` is part of the power-of-two table `0x2000 0x4000 0x8000 0x10000 0x20000 0x40000`; `0x80120E14`, `0x80120E54`, `0x80120E94` are offset tables.
4. `0501.DAT`'s header and TOC (first `0x8E0` bytes) contain no word-aligned `0x00020000` or `0x00000800` field, so the two logged reads are not size fields from the pack TOC.
5. `_Main.rel` has no reference to `lbl_801B3CC0`. The claim that it has no `0x20000` length was later withdrawn: five `lis r6, 2` sites before `bl lbl_8008E2FC` pass `0x20000` as the pack-open length. See "Stage-pack table".

The SDK readers do not split requests, so the length is decided by the caller before the call. The caller is the pack loader: the REL openers pass `0x20000` explicitly at all known call sites, and the file-object method that receives it is called through the function pointer at `+0x18`, which is why a scan for direct `DVDReadAsync` call sites did not find it. See "Stage-pack table" below.
