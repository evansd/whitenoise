#!/usr/bin/env python
from __future__ import absolute_import, print_function, division, unicode_literals

import argparse
import gzip
import os
import os.path
import re


# Makes the default extension list look a bit nicer
class PrettyTuple(tuple):
    def __repr__(self):
        return ', '.join(self)


CHUNK_SIZE = 64 * 1024

# Extensions that it's not worth trying to gzip
GZIP_EXCLUDE_EXTENSIONS = PrettyTuple((
    # Images
    'jpg', 'jpeg', 'png', 'gif', 'webp',
    # Compressed files
    'zip', 'gz', 'tgz', 'bz2', 'tbz',
    # Flash
    'swf', 'flv',
    # Fonts
    'woff', 'woff2'
))

null_log = lambda x: x


def main(root, extensions=None, quiet=False, log=print):
    excluded_re = extension_regex(extensions)
    if quiet:
        log = null_log
    for dirpath, dirs, files in os.walk(root):
        for filename in files:
            if not excluded_re.search(filename):
                path = os.path.join(dirpath, filename)
                compress(path, log)


def extension_regex(extensions):
    if not extensions:
        return re.compile('^$')
    else:
        return re.compile(
            r'\.({})$'.format('|'.join(map(re.escape, extensions))),
            re.IGNORECASE)


def compress(path, log=null_log):
    gzip_path = path + '.gz'
    with open(path, 'rb') as in_file:
        # Explicitly set mtime to 0 so gzip content is fully determined
        # by file content (0 = "no timestamp" according to gzip spec)
        with gzip.GzipFile(gzip_path, 'wb', compresslevel=9, mtime=0) as out_file:
            for chunk in iter(lambda: in_file.read(CHUNK_SIZE), b''):
                out_file.write(chunk)
    # If gzipped file isn't actually any smaller then get rid of it
    orig_size = os.path.getsize(path)
    gzip_size = os.path.getsize(gzip_path)
    if not is_worth_gzipping(orig_size, gzip_size):
        log('Skipping {} (Gzip not effective)'.format(path))
        os.unlink(gzip_path)
    else:
        log('Gzipping {} ({}K -> {}K)'.format(
            path, orig_size // 1024, gzip_size // 1024))


def is_worth_gzipping(orig_size, gzip_size):
    if orig_size == 0:
        return False
    ratio = gzip_size / orig_size
    return ratio <= 0.95


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
            description="Search for all files inside <root> *not* matching <extensions> "
                        "and produce gzipped versions with a '.gz' suffix (as long "
                        "this results in a smaller file)",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-q', '--quiet', help="Don't produce log output", action='store_true')
    parser.add_argument('root', help='Path root from which to search for files')
    parser.add_argument('extensions', nargs='*', help='File extensions to exclude from gzipping',
            default=GZIP_EXCLUDE_EXTENSIONS)
    args = parser.parse_args()
    main(**vars(args))
