#!/usr/bin/env python3
"""Split a decoded Sonic Riders resource package (the output of srlz.decode)
into its slots, and reassemble it byte for byte.

Layout (big endian; the header fields are inferred from 4 files and are UNVERIFIED
beyond what `verify()` checks):
  +0      u32 group_count
  +4      group_count x u8   slots per group
  align4(4+gc)  group_count x u16  cumulative first-slot index of each group
  ...     more small tables (not parsed)
  table   total_slots x u32  absolute offset of each slot's blob, 0 = empty slot
Blobs follow in table order; blob i runs to the next larger offset (or EOF), so the
padding between blobs belongs to the blob before it and splitting loses nothing.
"""
import struct, sys

MAGICS = {b"NGIF": "NGIF", b"GCIX": "GCIX", b"GVRT": "GVRT"}


def parse(d: bytes):
    u32 = lambda o: struct.unpack(">I", d[o:o + 4])[0]
    gc = u32(0)
    groups = list(d[4:4 + gc])
    total = sum(groups)
    cum = [sum(groups[:i]) for i in range(gc)]
    base = (4 + gc + 3) & ~3          # the u16 list is 4-byte aligned
    got = [struct.unpack(">H", d[base + 2 * i:base + 2 * i + 2])[0] for i in range(gc)]
    if got != cum:
        raise ValueError("group index table does not match slot counts")
    # locate the slot table: `total` words, each 0 or a pointer into the file,
    # nonzero values never decreasing
    start = (base + 2 * gc + 3) & ~3
    for p in range(start, 0x400, 4):
        words = [u32(p + 4 * i) for i in range(total)]
        nz = [w for w in words if w]
        if nz and nz[0] >= p + 4 * total and nz == sorted(nz) and nz[-1] < len(d) \
                and all(w % 0x20 == 0 for w in nz):
            return gc, groups, p, words
    raise ValueError("slot table not found")


def split(d: bytes):
    gc, groups, p, words = parse(d)
    offs = sorted(set(w for w in words if w)) + [len(d)]
    end = {offs[i]: offs[i + 1] for i in range(len(offs) - 1)}
    slots = []
    for i, w in enumerate(words):
        slots.append((i, w, d[w:end[w]] if w else b""))
    return d[:offs[0]], groups, p, slots


def kind(blob: bytes):
    if not blob:
        return "empty"
    return MAGICS.get(blob[:4], blob[:4].hex())


def join(header: bytes, slots):
    seen, out = set(), bytearray(header)
    for i, w, b in slots:
        if w and w not in seen:
            seen.add(w)
            assert len(out) == w, (i, hex(w), hex(len(out)))
            out += b
    return bytes(out)


def verify(d: bytes):
    h, groups, p, slots = split(d)
    return join(h, slots) == d


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    h, groups, p, slots = split(d)
    print("groups", len(groups), "slots", len(slots), "table at", hex(p), "roundtrip", join(h, slots) == d)
    g, idx = 0, 0
    for i, w, b in slots:
        print(i, hex(w), hex(len(b)), kind(b))
