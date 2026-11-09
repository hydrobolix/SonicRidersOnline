#!/usr/bin/env python3
"""Decoder/encoder for the Sonic Riders 0x8000000N container.

Ported from the REL routine lbl_001594F4 (whole-buffer path, lbl_00159B78) and
its init lbl_00159DB8. Verified against the disc (see docs/asset-extraction.md).

Layout: u32 BE flag (low byte = unit size N, 1 or 2), u32 BE decoded size,
zero pad to 0x20, then a bit stream (MSB first):
  bit 0 -> literal: N bytes follow
  bit 1 -> match: N-byte BE offset, N-byte BE length, copy from out[-offset]
Data bytes after a flag bit are NOT byte aligned: they are read at the
current bit offset.
"""
import struct, sys

HDR = 0x20


def decode(buf: bytes):
    flag, size = struct.unpack(">II", buf[:8])
    n = flag & 0xFF
    if n not in (1, 2):
        raise ValueError("unit size %d" % n)
    src = buf[HDR:] + b"\0\0"
    out = bytearray()
    p, left = 0, 8

    def rd(k):
        nonlocal p
        r = bytearray()
        for _ in range(k):
            r.append(((src[p] << (8 - left)) & 0xFF) | ((src[p + 1] >> left) if left < 8 else 0))
            p += 1
        return bytes(r)

    while len(out) < size:
        left -= 1
        bit = (src[p] >> left) & 1
        if left == 0:
            left, p = 8, p + 1
        if not bit:
            out += rd(n)
        else:
            off = int.from_bytes(rd(n), "big")
            ln = int.from_bytes(rd(n), "big")
            for _ in range(ln):
                out.append(out[-off])
    return bytes(out[:size]), flag, size


def encode(data: bytes, flag: int = 0x80000001, overrun: bool = False) -> bytes:
    """Re-encoder. For N=1 it reproduces the disc's compressor byte for byte
    on every file checked (see docs/asset-extraction.md): greedy, longest match
    within the 255-byte window, minimum match length 2, ties broken toward the
    FARTHEST offset. N=2 uses the same rules with a 65535 window (unverified:
    no N=2 file exists on the US disc).

    overrun=True lets a match read one virtual zero byte past the end of the data.
    8 of the 1,562 disc files (P240, P240M, PO40, PO40M, PO70, PZ40, PZ40M, PZ70)
    were compressed that way: their last match runs one byte past the declared
    size. All other files re-encode with overrun=False."""
    n = flag & 0xFF
    maxv = (1 << (8 * n)) - 1
    bits = []

    def put(byte_vals):
        for b in byte_vals:
            bits.extend((b >> i) & 1 for i in range(7, -1, -1))

    i = 0
    data = bytes(data)
    lim = len(data) + (1 if overrun else 0)
    pad = data + b"\0"
    while i < len(data):
        best_len = best_off = 0
        for off in range(1, min(i, maxv) + 1):
            l = 0
            while i + l < lim and l < maxv and pad[i + l - off] == pad[i + l]:
                l += 1
            if l >= best_len and l > 0:
                best_len, best_off = l, off
        if best_len >= 2:
            bits.append(1)
            put(best_off.to_bytes(n, "big"))
            put(best_len.to_bytes(n, "big"))
            i += best_len
        else:
            bits.append(0)
            chunk = data[i:i + n]
            chunk += b"\0" * (n - len(chunk))
            put(chunk)
            i += n
    while len(bits) % 8:
        bits.append(0)
    body = bytes(int("".join(map(str, bits[k:k + 8])), 2) for k in range(0, len(bits), 8))
    return struct.pack(">II", flag, len(data)) + b"\0" * (HDR - 8) + body


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    o, flag, size = decode(d)
    open(sys.argv[2], "wb").write(o)
    print("flag %08x size %d -> %d bytes" % (flag, size, len(o)))
