#!/usr/bin/env python
from __future__ import absolute_import, print_function, division

import argparse
import gzip
import os
import re


CHUNK_SIZE = 64 * 1024

def main(root, extensions, quiet=False):
    file_re = re.compile(r'\.({})$'.format('|'.join(map(re.escape, extensions))))
    log = (lambda x:x) if quiet else print
    for dirpath, dirs, files in os.walk(root):
        for filename in files:
            if file_re.search(filename):
                path = os.path.join(dirpath, filename)
                compress(path, log)

def compress(path, log):
    gzip_path = path + '.gz'
    with open(path, 'rb') as in_file:
        with gzip.open(gzip_path, 'wb', compresslevel=9) as out_file:
            for chunk in iter(lambda: in_file.read(CHUNK_SIZE), ''):
                out_file.write(chunk)
    # If gzipped file isn't actually any smaller then get rid of it
    orig_size = os.path.getsize(path)
    gzip_size = os.path.getsize(gzip_path)
    if gzip_size >= orig_size:
        log('Skipping {} (No gzip saving)'.format(path))
        os.unlink(gzip_path)
    else:
        log('Gzipping {} ({}K -> {}K)'.format(
            path, orig_size // 1024, gzip_size // 1024))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="Searches for all files inside <root> matching <extensions> "
                        "and produce gzipped versions with a '.gz' suffix (as long "
                        "this results in a smaller file.",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--quiet', help="Don't produce log output", action='store_true')
    parser.add_argument('root', help='Path root from which to search for files')
    parser.add_argument('extensions', nargs='*', help='File extensions to match', default=('css', 'js'))
    args = parser.parse_args()
    main(**vars(args))
