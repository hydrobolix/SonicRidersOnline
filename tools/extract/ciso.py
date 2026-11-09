"""Read-only access to a GameCube CISO disc image and its FST.

Usage:  python tools/extract/ciso.py <image.ciso>            # list files
        python tools/extract/ciso.py <image.ciso> <name> <out>   # extract one file

The image is supplied by the user and never committed (see docs/legal-and-assets.md).
Layout (verified on the US disc): 'CISO' magic, u32 LE block size at +4, a presence
map from +8 to 0x8000, then the present blocks back to back. Absent blocks read as zero.
"""
import struct
import sys


class Ciso:
    def __init__(self, path):
        self.f = open(path, "rb")
        head = self.f.read(0x8000)
        if head[:4] != b"CISO":
            raise ValueError("not a CISO image")
        self.block_size = struct.unpack("<I", head[4:8])[0]
        self._index = {}
        n = 0
        for i, present in enumerate(head[8:]):
            if present == 1:
                self._index[i] = n
                n += 1

    def read(self, offset, length):
        out = bytearray()
        while length > 0:
            blk, off = divmod(offset, self.block_size)
            n = min(length, self.block_size - off)
            if blk in self._index:
                self.f.seek(0x8000 + self._index[blk] * self.block_size + off)
                out += self.f.read(n)
            else:
                out += b"\0" * n
            offset += n
            length -= n
        return bytes(out)

    def files(self):
        """Return [(fst_index, name, disc_offset, size)] for every file entry (flat names)."""
        header = self.read(0, 0x440)
        fst_off, fst_size = struct.unpack(">II", header[0x424:0x42C])
        fst = self.read(fst_off, fst_size)
        count = struct.unpack(">I", fst[8:12])[0]
        names = count * 12
        result = []
        for i in range(1, count):
            word, off, size = struct.unpack(">III", fst[i * 12:i * 12 + 12])
            if word >> 24 == 0:  # file, not directory
                start = names + (word & 0xFFFFFF)
                name = fst[start:fst.index(b"\0", start)].decode("latin1")
                result.append((i, name, off, size))
        return result


if __name__ == "__main__":
    disc = Ciso(sys.argv[1])
    table = disc.files()
    if len(sys.argv) == 2:
        for i, name, off, size in table:
            print(f"{i:5} {off:#011x} {size:10} {name}")
    else:
        _, _, off, size = next(e for e in table if e[1] == sys.argv[2])
        open(sys.argv[3], "wb").write(disc.read(off, size))
