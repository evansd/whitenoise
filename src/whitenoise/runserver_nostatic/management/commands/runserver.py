"""
Subclass the existing 'runserver' command and change the default options
to disable static file serving, allowing WhiteNoise to handle static files.

There is some unpleasant hackery here because we don't know which command class
to subclass until runtime as it depends on which INSTALLED_APPS we have, so we
have to determine this dynamically.
"""
from __future__ import annotations

import argparse
from importlib import import_module
from typing import Generator

from django.apps import apps
from django.core.management import BaseCommand


def get_next_runserver_command() -> type[BaseCommand]:
    """
    Return the next highest priority "runserver" command class
    """
    for app_name in get_lower_priority_apps():
        module_path = "%s.management.commands.runserver" % app_name
        try:
            klass: type[BaseCommand] = import_module(module_path).Command
            return klass
        except (ImportError, AttributeError):
            pass
    raise ValueError("No lower priority app has a 'runserver' command")


def get_lower_priority_apps() -> Generator[str, None, None]:
    """
    Yield all app module names below the current app in the INSTALLED_APPS list
    """
    self_app_name = ".".join(__name__.split(".")[:-3])
    reached_self = False
    for app_config in apps.get_app_configs():
        if app_config.name == self_app_name:
            reached_self = True
        elif reached_self:
            yield app_config.name
    yield "django.core"


RunserverCommand = get_next_runserver_command()


class Command(RunserverCommand):  # type: ignore [misc,valid-type]
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        super().add_arguments(parser)
        if parser.get_default("use_static_handler") is True:
            parser.set_defaults(use_static_handler=False)
            assert parser.description is not None
            parser.description += (
                "\n(Wrapped by 'whitenoise.runserver_nostatic' to always"
                " enable '--nostatic')"
            )
