from __future__ import annotations

import shutil
import tempfile
from contextlib import closing
from urllib.parse import urljoin, urlparse

import django
import pytest
from django.conf import settings
from django.contrib.staticfiles import finders, storage
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application
from django.test.utils import override_settings
from django.utils.functional import empty

from whitenoise.middleware import WhiteNoiseFileResponse, WhiteNoiseMiddleware

from .utils import AppServer, Files


def reset_lazy_object(obj):
    obj._wrapped = empty


def get_url_path(base, url):
    return urlparse(urljoin(base, url)).path


@override_settings()
@pytest.fixture(scope="module")
def static_files():
    files = Files("static", js="app.js", nonascii="nonascii\u2713.txt")
    settings.STATICFILES_DIRS = [files.directory]
    return files


@override_settings()
@pytest.fixture(scope="module")
def root_files():
    files = Files("root", robots="robots.txt")
    settings.WHITENOISE_ROOT = files.directory
    return files


@override_settings()
@pytest.fixture(scope="module")
def tmp():
    tmp_dir = tempfile.mkdtemp()
    settings.STATIC_ROOT = tmp_dir
    yield tmp_dir
    shutil.rmtree(tmp_dir)


@pytest.fixture(scope="module")
def _collect_static(static_files, root_files, tmp):
    reset_lazy_object(storage.staticfiles_storage)
    call_command("collectstatic", verbosity=0, interactive=False)


@pytest.fixture(scope="module")
def application(_collect_static):
    return get_wsgi_application()


@pytest.fixture(scope="module")
def server(application):
    app_server = AppServer(application)
    with closing(app_server):
        yield app_server


def test_get_root_file(server, root_files, _collect_static):
    response = server.get(root_files.robots_url)
    assert response.content == root_files.robots_content


def test_versioned_file_cached_forever(server, static_files, _collect_static):
    url = storage.staticfiles_storage.url(static_files.js_path)
    response = server.get(url)
    assert response.content == static_files.js_content
    assert (
        response.headers.get("Cache-Control")
        == f"max-age={WhiteNoiseMiddleware.FOREVER}, public, immutable"
    )


def test_unversioned_file_not_cached_forever(server, static_files, _collect_static):
    url = settings.STATIC_URL + static_files.js_path
    response = server.get(url)
    assert response.content == static_files.js_content
    assert response.headers.get("Cache-Control") == "max-age={}, public".format(
        WhiteNoiseMiddleware.max_age
    )


def test_get_gzip(server, static_files, _collect_static):
    url = storage.staticfiles_storage.url(static_files.js_path)
    response = server.get(url, headers={"Accept-Encoding": "gzip"})
    assert response.content == static_files.js_content
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.headers["Vary"] == "Accept-Encoding"


def test_get_brotli(server, static_files, _collect_static):
    url = storage.staticfiles_storage.url(static_files.js_path)
    response = server.get(url, headers={"Accept-Encoding": "gzip, br"})
    assert response.content == static_files.js_content
    assert response.headers["Content-Encoding"] == "br"
    assert response.headers["Vary"] == "Accept-Encoding"


def test_no_content_type_when_not_modified(server, static_files, _collect_static):
    last_mod = "Fri, 11 Apr 2100 11:47:06 GMT"
    url = settings.STATIC_URL + static_files.js_path
    response = server.get(url, headers={"If-Modified-Since": last_mod})
    assert "Content-Type" not in response.headers


def test_get_nonascii_file(server, static_files, _collect_static):
    url = settings.STATIC_URL + static_files.nonascii_path
    response = server.get(url)
    assert response.content == static_files.nonascii_content


@override_settings()
@pytest.fixture(params=[True, False], scope="module")
def finder_static_files(request):
    files = Files("static", js="app.js", index="with-index/index.html")
    settings.STATICFILES_DIRS = [files.directory]
    settings.WHITENOISE_USE_FINDERS = True
    settings.WHITENOISE_AUTOREFRESH = request.param
    settings.WHITENOISE_INDEX_FILE = True
    settings.STATIC_ROOT = None
    try:
        finders.get_finder.cache_clear()
    except AttributeError:
        finders._finders.clear()
    return files


def test_no_content_disposition_header(server, static_files, _collect_static):
    url = settings.STATIC_URL + static_files.js_path
    response = server.get(url)
    assert response.headers.get("content-disposition") is None


@pytest.fixture(scope="module")
def finder_application(finder_static_files):
    return get_wsgi_application()


@pytest.fixture(scope="module")
def finder_server(finder_application):
    app_server = AppServer(finder_application)
    with closing(app_server):
        yield app_server


def test_file_served_from_static_dir(finder_static_files, finder_server):
    url = settings.STATIC_URL + finder_static_files.js_path
    response = finder_server.get(url)
    assert response.content == finder_static_files.js_content


def test_non_ascii_requests_safely_ignored(finder_server):
    response = finder_server.get(settings.STATIC_URL + "test\u263A")
    assert 404 == response.status_code


def test_requests_for_directory_safely_ignored(finder_server):
    url = settings.STATIC_URL + "directory"
    response = finder_server.get(url)
    assert 404 == response.status_code


def test_index_file_served_at_directory_path(finder_static_files, finder_server):
    path = finder_static_files.index_path.rpartition("/")[0] + "/"
    response = finder_server.get(settings.STATIC_URL + path)
    assert response.content == finder_static_files.index_content


def test_index_file_path_redirected(finder_static_files, finder_server):
    directory_path = finder_static_files.index_path.rpartition("/")[0] + "/"
    index_url = settings.STATIC_URL + finder_static_files.index_path
    response = finder_server.get(index_url, allow_redirects=False)
    location = get_url_path(response.url, response.headers["Location"])
    assert response.status_code == 302
    assert location == settings.STATIC_URL + directory_path


def test_directory_path_without_trailing_slash_redirected(
    finder_static_files, finder_server
):
    directory_path = finder_static_files.index_path.rpartition("/")[0] + "/"
    directory_url = settings.STATIC_URL + directory_path.rstrip("/")
    response = finder_server.get(directory_url, allow_redirects=False)
    location = get_url_path(response.url, response.headers["Location"])
    assert response.status_code == 302
    assert location == settings.STATIC_URL + directory_path


def test_whitenoise_file_response_has_only_one_header():
    response = WhiteNoiseFileResponse(open(__file__, "rb"))
    response.close()
    headers = {key.lower() for key, value in response.items()}
    # This subclass should have none of the default headers that FileReponse
    # sets
    assert headers == {"content-type"}


@pytest.mark.skipif(django.VERSION[:2] < (3, 1), reason="feature added in Django 3.1")
@override_settings()
def test_relative_static_url(server, static_files, _collect_static):
    settings.STATIC_URL = "static/"
    url = storage.staticfiles_storage.url(static_files.js_path)
    response = server.get(url)
    assert response.content == static_files.js_content
