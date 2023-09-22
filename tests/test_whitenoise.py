from __future__ import annotations

import os
import re
import shutil
import stat
import sys
import tempfile
import warnings
from contextlib import closing
from urllib.parse import urljoin
from wsgiref.headers import Headers
from wsgiref.simple_server import demo_app

import pytest

from tests.utils import AppServer
from tests.utils import Files
from whitenoise import WhiteNoise
from whitenoise.responders import StaticFile


@pytest.fixture(scope="module")
def files():
    return Files(
        "assets",
        js="subdir/javascript.js",
        gzip="compressed.css",
        gzipped="compressed.css.gz",
        custom_mime="custom-mime.foobar",
        index="with-index/index.html",
    )


@pytest.fixture(params=[True, False], scope="module")
def application(request, files):
    # When run all test the application with autorefresh enabled and disabled
    # When testing autorefresh mode we first initialise the application with an
    # empty temporary directory and then copy in the files afterwards so we can
    # test that files added after initialisation are picked up correctly
    if request.param:
        tmp = tempfile.mkdtemp()
        app = _init_application(tmp, autorefresh=True)
        copytree(files.directory, tmp)
        yield app
        shutil.rmtree(tmp)
    else:
        yield _init_application(files.directory)


def _init_application(directory, **kwargs):
    def custom_headers(headers, path, url):
        if url.endswith(".css"):
            headers["X-Is-Css-File"] = "True"

    return WhiteNoise(
        demo_app,
        root=directory,
        max_age=1000,
        mimetypes={".foobar": "application/x-foo-bar"},
        add_headers_function=custom_headers,
        index_file=True,
        **kwargs,
    )


@pytest.fixture(scope="module")
def server(application):
    app_server = AppServer(application)
    with closing(app_server):
        yield app_server


def assert_is_default_response(response):
    assert "Hello world!" in response.text


def test_get_file(server, files):
    response = server.get(files.js_url)
    assert response.content == files.js_content
    assert re.search(r"text/javascript\b", response.headers["Content-Type"])
    assert re.search(r'.*\bcharset="utf-8"', response.headers["Content-Type"])


def test_get_not_accept_gzip(server, files):
    response = server.get(files.gzip_url, headers={"Accept-Encoding": ""})
    assert response.content == files.gzip_content
    assert "Content-Encoding" not in response.headers
    assert response.headers["Vary"] == "Accept-Encoding"


def test_get_accept_star(server, files):
    response = server.get(files.gzip_url, headers={"Accept-Encoding": "*"})
    assert response.content == files.gzip_content
    assert "Content-Encoding" not in response.headers
    assert response.headers["Vary"] == "Accept-Encoding"


def test_get_accept_missing(server, files):
    response = server.get(
        files.gzip_url,
        # Using None is required to override requests’ default Accept-Encoding
        headers={"Accept-Encoding": None},
    )
    assert response.content == files.gzip_content
    assert "Content-Encoding" not in response.headers
    assert response.headers["Vary"] == "Accept-Encoding"


def test_get_accept_gzip(server, files):
    response = server.get(files.gzip_url)
    assert response.content == files.gzip_content
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.headers["Vary"] == "Accept-Encoding"


def test_cannot_directly_request_gzipped_file(server, files):
    response = server.get(files.gzip_url + ".gz")
    assert_is_default_response(response)


def test_not_modified_exact(server, files):
    response = server.get(files.js_url)
    last_mod = response.headers["Last-Modified"]
    response = server.get(files.js_url, headers={"If-Modified-Since": last_mod})
    assert response.status_code == 304


def test_not_modified_future(server, files):
    last_mod = "Fri, 11 Apr 2100 11:47:06 GMT"
    response = server.get(files.js_url, headers={"If-Modified-Since": last_mod})
    assert response.status_code == 304


def test_modified(server, files):
    last_mod = "Fri, 11 Apr 2001 11:47:06 GMT"
    response = server.get(files.js_url, headers={"If-Modified-Since": last_mod})
    assert response.status_code == 200


def test_modified_mangled_date_firefox_91_0b3(server, files):
    last_mod = "Fri, 16 Jul 2021 09:09:1626426577S GMT"
    response = server.get(files.js_url, headers={"If-Modified-Since": last_mod})
    assert response.status_code == 200


def test_etag_matches(server, files):
    response = server.get(files.js_url)
    etag = response.headers["ETag"]
    response = server.get(files.js_url, headers={"If-None-Match": etag})
    assert response.status_code == 304


def test_etag_doesnt_match(server, files):
    etag = '"594bd1d1-36"'
    response = server.get(files.js_url, headers={"If-None-Match": etag})
    assert response.status_code == 200


def test_etag_overrules_modified_since(server, files):
    """
    Browsers send both headers so it's important that the ETag takes precedence
    over the last modified time, so that deploy-rollbacks are handled correctly.
    """
    headers = {
        "If-None-Match": '"594bd1d1-36"',
        "If-Modified-Since": "Fri, 11 Apr 2100 11:47:06 GMT",
    }
    response = server.get(files.js_url, headers=headers)
    assert response.status_code == 200


def test_max_age(server, files):
    response = server.get(files.js_url)
    assert response.headers["Cache-Control"], "max-age=1000 == public"


def test_other_requests_passed_through(server):
    response = server.get("/%s/not/static" % AppServer.PREFIX)
    assert_is_default_response(response)


def test_non_ascii_requests_safely_ignored(server):
    response = server.get(f"/{AppServer.PREFIX}/test\u263A")
    assert_is_default_response(response)


def test_add_under_prefix(server, files, application):
    prefix = "/prefix"
    application.add_files(files.directory, prefix=prefix)
    response = server.get(f"/{AppServer.PREFIX}{prefix}/{files.js_path}")
    assert response.content == files.js_content


def test_response_has_allow_origin_header(server, files):
    response = server.get(files.js_url)
    assert response.headers.get("Access-Control-Allow-Origin") == "*"


def test_response_has_correct_content_length_header(server, files):
    response = server.get(files.js_url)
    length = int(response.headers["Content-Length"])
    assert length == len(files.js_content)


def test_gzip_response_has_correct_content_length_header(server, files):
    response = server.get(files.gzip_url)
    length = int(response.headers["Content-Length"])
    assert length == len(files.gzipped_content)


def test_post_request_returns_405(server, files):
    response = server.request("post", files.js_url)
    assert response.status_code == 405


def test_head_request_has_no_body(server, files):
    response = server.request("head", files.js_url)
    assert response.status_code == 200
    assert not response.content


def test_custom_mimetype(server, files):
    response = server.get(files.custom_mime_url)
    assert re.search(r"application/x-foo-bar\b", response.headers["Content-Type"])


def test_custom_headers(server, files):
    response = server.get(files.gzip_url)
    assert response.headers["x-is-css-file"] == "True"


def test_index_file_served_at_directory_path(server, files):
    directory_url = files.index_url.rpartition("/")[0] + "/"
    response = server.get(directory_url)
    assert response.content == files.index_content


def test_index_file_path_redirected(server, files):
    directory_url = files.index_url.rpartition("/")[0] + "/"
    response = server.get(files.index_url, allow_redirects=False)
    location = urljoin(files.index_url, response.headers["Location"])
    assert response.status_code == 302
    assert location == directory_url


def test_directory_path_without_trailing_slash_redirected(server, files):
    directory_url = files.index_url.rpartition("/")[0] + "/"
    no_slash_url = directory_url.rstrip("/")
    response = server.get(no_slash_url, allow_redirects=False)
    location = urljoin(no_slash_url, response.headers["Location"])
    assert response.status_code == 302
    assert location == directory_url


def test_request_initial_bytes(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=0-13"})
    assert response.content == files.js_content[0:14]


def test_request_trailing_bytes(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=-3"})
    assert response.content == files.js_content[-3:]


def test_request_middle_bytes(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=21-30"})
    assert response.content == files.js_content[21:31]


def test_overlong_ranges_truncated(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=21-100000"})
    assert response.content == files.js_content[21:]


def test_overlong_trailing_ranges_return_entire_file(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=-100000"})
    assert response.content == files.js_content


def test_out_of_range_error(server, files):
    response = server.get(files.js_url, headers={"Range": "bytes=10000-11000"})
    assert response.status_code == 416
    assert response.headers["Content-Range"] == "bytes */%s" % len(files.js_content)


def test_warn_about_missing_directories(application):
    # This is the one minor behavioural difference when autorefresh is
    # enabled: we don't warn about missing directories as these can be
    # created after the application is started
    if application.autorefresh:
        pytest.skip()
    with warnings.catch_warnings(record=True) as warning_list:
        application.add_files("/dev/null/nosuchdir\u2713")
    assert len(warning_list) == 1


def test_handles_missing_path_info_key(application):
    response = application(environ={}, start_response=lambda *args: None)
    assert response


def test_cant_read_absolute_paths_on_windows(server):
    response = server.get(rf"/{AppServer.PREFIX}/C:/Windows/System.ini")
    assert_is_default_response(response)


def test_no_error_on_very_long_filename(server):
    response = server.get("/blah" * 1000)
    assert response.status_code != 500


def copytree(src, dst):
    for name in os.listdir(src):
        src_path = os.path.join(src, name)
        dst_path = os.path.join(dst, name)
        if os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy2(src_path, dst_path)


def test_immutable_file_test_accepts_regex():
    instance = WhiteNoise(None, immutable_file_test=r"\.test$")
    assert instance.immutable_file_test("", "/myfile.test")
    assert not instance.immutable_file_test("", "file.test.txt")


@pytest.mark.skipif(sys.version_info < (3, 4), reason="Pathlib was added in Python 3.4")
def test_directory_path_can_be_pathlib_instance():
    from pathlib import Path

    root = Path(Files("root").directory)
    # Check we can construct instance without it blowing up
    WhiteNoise(None, root=root, autorefresh=True)


def fake_stat_entry(
    st_mode: int = stat.S_IFREG, st_size: int = 1024, st_mtime: int = 0
) -> os.stat_result:
    return os.stat_result(
        (
            st_mode,
            0,  # st_ino
            0,  # st_dev
            0,  # st_nlink
            0,  # st_uid
            0,  # st_gid
            st_size,
            0,  # st_atime
            st_mtime,
            0,  # st_ctime
        )
    )


def test_last_modified_not_set_when_mtime_is_zero():
    stat_cache = {__file__: fake_stat_entry()}
    responder = StaticFile(__file__, [], stat_cache=stat_cache)
    response = responder.get_response("GET", {})
    response.file.close()
    headers_dict = Headers(response.headers)
    assert "Last-Modified" not in headers_dict
    assert "ETag" not in headers_dict


def test_file_size_matches_range_with_range_header():
    stat_cache = {__file__: fake_stat_entry()}
    responder = StaticFile(__file__, [], stat_cache=stat_cache)
    response = responder.get_response("GET", {"HTTP_RANGE": "bytes=0-13"})
    file_size = len(response.file.read())
    assert file_size == 14


def test_chunked_file_size_matches_range_with_range_header():
    stat_cache = {__file__: fake_stat_entry()}
    responder = StaticFile(__file__, [], stat_cache=stat_cache)
    response = responder.get_response("GET", {"HTTP_RANGE": "bytes=0-13"})
    file_size = 0
    assert response.file is not None
    while response.file.read(1):
        file_size += 1
    assert file_size == 14
