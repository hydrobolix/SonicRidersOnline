#!/usr/bin/env python3
"""Reader for the 0x30-byte-record tables in slots 130-132 of a stage package
(header magic 01 01 00 01). Layout from REL 0x46C70 (pointer fixup) and 0x46CE0
(count and kind scan), plus checking the data; field names are UNVERIFIED.

  +0x00  u32 magic 0x01010001 (record 0 only: record 0's first 8 bytes are the header)
  +0x04  u16 record count (record 0 only)
  +0x08  f32 x, y, z, radius   bounding sphere
  +0x18  u32 offset  index data            (REL fixes this to a pointer)
  +0x1c  u16 kind                          (REL special-cases 31, 50, 51, 52)
  +0x1e  u16 id
  +0x24  u32 offset  float triples, vertex positions
  +0x28  u32 offset  float triples, unit vectors (face normals)
  +0x2c  u8[4] counts / flags
"""
import struct, sys
import srpack


def records(blob: bytes):
    magic, count = struct.unpack(">IH", blob[:6])
    if magic != 0x01010001:
        raise ValueError("not a collision-style table")
    out = []
    for i in range(count):
        o = 0x30 * i
        x, y, z, r = struct.unpack(">4f", blob[o + 8:o + 0x18])
        idx, = struct.unpack(">I", blob[o + 0x18:o + 0x1c])
        kind, rid = struct.unpack(">HH", blob[o + 0x1c:o + 0x20])
        vtx, nrm = struct.unpack(">II", blob[o + 0x24:o + 0x2c])
        out.append(dict(i=i, sphere=(x, y, z, r), idx=idx, kind=kind, id=rid,
                        vtx=vtx, nrm=nrm, tail=blob[o + 0x2c:o + 0x30]))
    return out


def check(blob: bytes):
    """True if every non-null offset lies inside the blob and vertex/normal ranges are ordered."""
    rs = records(blob)
    return all(0 <= r["idx"] < len(blob) and 0 < r["vtx"] <= r["nrm"] <= len(blob) for r in rs)


if __name__ == "__main__":
    d = open(sys.argv[1], "rb").read()
    _, groups, _, slots = srpack.split(d)
    for si, _, b in slots:
        if b[:4] != bytes.fromhex("01010001"):
            continue
        rs = records(b)
        kinds = {}
        for r in rs:
            kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
        print("slot", si, "records", len(rs), "kinds", kinds, "offsets in range", check(b))
