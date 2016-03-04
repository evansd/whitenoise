#!/usr/bin/env python
import pprint


EXTRA_MIMETYPES = {
    'apple-app-site-association': 'application/pkc7-mime',
    '.woff': 'application/font-woff',
    '.woff2': 'font/woff2'
}


FUNCTION_TEMPLATE = """
def default_types():
    {triple_quote}
    We use our own set of default media types rather than the system-supplied
    ones. This ensures consistent media type behaviour across varied
    environments.  The defaults are based on those shipped with nginx, with
    some custom additions.
    {triple_quote}

    return {{
        {types_map}
    }}
""".lstrip()


NGINX_CONFIG_FILE = '/etc/nginx/mime.types'


def get_default_types_function():
    types_map = get_types_map()
    types_map_str = pprint.pformat(types_map, indent=8).strip('{} ')
    return FUNCTION_TEMPLATE.format(
            triple_quote='"""',
            types_map=types_map_str)


def get_types_map():
    types_map = {}
    with open(NGINX_CONFIG_FILE, 'r') as f:
        for line in f:
            line = line.strip()
            if not line.endswith(';'):
                continue
            line = line.rstrip(';')
            bits = line.split()
            media_type = bits[0]
            # This is the default media type anyway, no point specifying
            # it explicitly
            if media_type == 'application/octet-stream':
                continue
            extensions = bits[1:]
            for extension in extensions:
                types_map['.'+extension] = media_type
    types_map.update(EXTRA_MIMETYPES)
    return types_map


if __name__ == '__main__':
    print get_default_types_function()
