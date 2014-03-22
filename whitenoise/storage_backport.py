from __future__ import absolute_import, unicode_literals

import json

from django.contrib.staticfiles.storage import CachedStaticFilesStorage


class ManifestStaticFilesStorage(CachedStaticFilesStorage):
    """
    Basic emulation of ManifestStaticFilesStorage from Django 1.7
    """
    manifest_name = 'staticfiles.json'

    def __init__(self, *args, **kwargs):
        super(ManifestStaticFilesStorage, self).__init__(*args, **kwargs)
        self.cache = ManifestCache(self.path(self.manifest_name))

    def cache_key(self, name):
        return name


class ManifestCache(object):
    """
    Acts enough like a cache backend to be used with CachedStaticFilesStorage
    from Django < 1.7, but stores data in a manifest file like Django 1.7+
    """
    def __init__(self, manifest_file):
        self.manifest_file = manifest_file
        try:
            with open(self.manifest_file) as f:
                self.manifest = json.load(f)['paths']
        except IOError:
            self.manifest = {}
        # Wire up the get method directly to the dict getter
        self.get = self.manifest.get

    def set(self, key, value, **kwargs):
        self.manifest[key] = value

    def set_many(self, values, **kwargs):
        self.manifest.update(values)
        payload = {'paths': self.manifest, 'version': '1.0'}
        with open(self.manifest_file, 'w') as f:
            json.dump(payload, f)
