from __future__ import annotations

from django.urls import path


def avoid_django_default_welcome_page():
    pass


urlpatterns = [
    path('', avoid_django_default_welcome_page)
]
