from __future__ import annotations

from whitenoise.compress import Compressor

called = False


class CustomCompressor(Compressor):
    def compress(self, path):
        global called
        print("CALLLED")
        called = True
        return super().compress(path)
