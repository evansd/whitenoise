#!/usr/bin/env python
from __future__ import absolute_import

import argparse
import gzip
import os
import re


CHUNK_SIZE = 64 * 1024


def main(root, extensions):
    file_re = re.compile(r'\.({})$'.format('|'.join(map(re.escape, extensions))))
    for dirpath, dirs, files in os.walk(root):
        for filename in files:
            if file_re.search(filename):
                path = os.path.join(dirpath, filename)
                compress(path)

def compress(path):
    gzip_path = path + '.gz'
    with open(path, 'rb') as in_file:
        with gzip.open(gzip_path, 'wb', compresslevel=9) as out_file:
            for chunk in iter(lambda: in_file.read(CHUNK_SIZE), ''):
                out_file.write(chunk)
    # If gzipped file isn't actually any smaller then get rid of it
    if os.path.getsize(gzip_path) >= os.path.getsize(path):
        os.unlink(gzip_path)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="Searches for all files inside <root> matching <extensions> "
                        "and produce gzipped versions with a '.gz' suffix (as long "
                        "this results in a smaller file.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('root', help='Path root from which to search for files')
    parser.add_argument('extensions', nargs='*', help='File extensions to match', default=('css', 'js'))
    args = parser.parse_args()
    main(**vars(args))
