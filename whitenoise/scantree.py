"""
Provides a `scantree` function which recurses a given directory, yielding
(pathname, os.stat(pathname)) pairs.

Attempts to use the much more efficient `scandir` function if this is available,
falling back to `os.walk` otherwise.
"""
import os
try:
    from os import scandir
except ImportError:
    try:
        from scandir import scandir
    except ImportError:
        scandir = None


if scandir:
    def scantree(root):
        for entry in scandir(root):
            if entry.is_dir():
                for item in scantree(entry.path):
                    yield item
            else:
                yield entry.path, entry.stat()
else:
    def scantree(root):
        for directory, _, filenames in os.walk(root, followlinks=True):
            for filename in filenames:
                path = os.path.join(directory, filename)
                yield path, os.stat(path)
