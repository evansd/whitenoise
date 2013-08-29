from django.conf.urls import patterns, url
from django.http import HttpResponse

def hello_world(reqeust):
    return HttpResponse(content='Hello Word', content_type='text/plain')

urlpatterns = patterns('',
    url(r'^hello$', hello_world),
)
