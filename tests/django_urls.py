from django.http import HttpResponse
from django.urls import path


def hello_world(reqeust):
    return HttpResponse(content="Hello Word", content_type="text/plain")


urlpatterns = [path("hello", hello_world)]
