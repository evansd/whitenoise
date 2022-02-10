from __future__ import annotations


def decode_if_byte_string(s, force_text=False):
    if isinstance(s, bytes):
        s = s.decode()
    if force_text and not isinstance(s, str):
        s = str(s)
    return s


# Follow Django in treating URLs as UTF-8 encoded (which requires undoing the
# implicit ISO-8859-1 decoding applied in Python 3). Strictly speaking, URLs
# should only be ASCII anyway, but UTF-8 can be found in the wild.
def decode_path_info(path_info):
    return path_info.encode("iso-8859-1", "replace").decode("utf-8", "replace")


def ensure_leading_trailing_slash(path):
    path = (path or "").strip("/")
    return f"/{path}/" if path else "/"
