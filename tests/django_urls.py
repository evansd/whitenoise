import django
from django.http import HttpResponse


def hello_world(reqeust):
    return HttpResponse(content="Hello Word", content_type="text/plain")


if django.VERSION >= (2, 0):
    from django.urls import path

    urlpatterns = [path("hello", hello_world)]
else:
    from django.conf.urls import url

    urlpatterns = [url(r"^hello$", hello_world)]
