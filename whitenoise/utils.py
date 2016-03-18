from __future__ import unicode_literals

import errno
import os
import stat


class NotARegularFileError(Exception):
    pass


class MissingFileError(NotARegularFileError):
    pass


def stat_regular_file(path):
    """
    Wrap os.stat to raise appropriate errors if `path` is not a regular file
    """
    try:
        file_stat = os.stat(path)
    except OSError as e:
        if e.errno == errno.ENOENT:
            raise MissingFileError(path)
        else:
            raise
    if not stat.S_ISREG(file_stat.st_mode):
        # We ignore directories and treat them as missing files
        if stat.S_ISDIR(file_stat.st_mode):
            raise MissingFileError('Path is a directory: {0}'.format(path))
        else:
            raise NotARegularFileError('Not a regular file: {0}'.format(path))
    return file_stat


def ensure_leading_trailing_slash(path):
    path = (path or '').strip('/')
    return '/{0}/'.format(path) if path else '/'
