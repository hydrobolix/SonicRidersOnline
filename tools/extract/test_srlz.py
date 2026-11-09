"""Offline tests for srlz (no disc needed): python3 -m unittest tools/extract/test_srlz.py"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(__file__))
import srlz


class Roundtrip(unittest.TestCase):
    def test_decode_encode(self):
        import random
        r = random.Random(1)
        blobs = [b"", b"a", b"abababababab" * 20, bytes(r.randrange(4) for _ in range(3000)),
                 bytes(range(256)) * 3]
        for blob in blobs:
            enc = srlz.encode(blob)
            dec, flag, size = srlz.decode(enc)
            self.assertEqual(dec, blob)
            self.assertEqual(flag, 0x80000001)
            self.assertEqual(size, len(blob))
            self.assertEqual(srlz.encode(dec), enc)  # stable

    def test_overrun_flag(self):
        blob = bytes(64) + b"abcabcabcabc" + bytes(7)
        for ov in (False, True):
            self.assertEqual(srlz.decode(srlz.encode(blob, overrun=ov))[0], blob)

    def test_header(self):
        enc = srlz.encode(b"hello hello hello")
        self.assertEqual(enc[:4], b"\x80\x00\x00\x01")
        self.assertEqual(enc[8:0x20], b"\0" * 24)


if __name__ == "__main__":
    unittest.main()
