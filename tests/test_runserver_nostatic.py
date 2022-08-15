from __future__ import annotations

from django.core.management import BaseCommand
from django.core.management import get_commands
from django.core.management import load_command_class


def get_command_instance(name: str) -> BaseCommand:
    app_name = get_commands()[name]
    # django-stubs incorrect type for get_commands() fixed in:
    # https://github.com/typeddjango/django-stubs/pull/1074
    return load_command_class(app_name, name)  # type: ignore [arg-type]


def test_command_output():
    command = get_command_instance("runserver")
    parser = command.create_parser("manage.py", "runserver")
    assert "Wrapped by 'whitenoise.runserver_nostatic'" in parser.format_help()
    assert not parser.get_default("use_static_handler")
