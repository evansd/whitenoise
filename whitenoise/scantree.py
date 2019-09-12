"""
Provides a `scantree` function which recurses a given directory, yielding
(pathname, os.stat(pathname)) pairs.

Attempts to use the more efficient `scandir` function if this is available,
falling back to `os.listdir` otherwise.
"""
import os
import stat

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
        for filename in os.listdir(root):
            path = os.path.join(root, filename)
            stat_result = os.stat(path)
            if stat.S_ISDIR(stat_result.st_mode):
                for item in scantree(path):
                    yield item
            else:
                yield path, stat_result
