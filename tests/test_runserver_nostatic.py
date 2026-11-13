from __future__ import annotations

import importlib

from django.core.management import get_commands, load_command_class
from django.test.utils import override_settings


def get_command_instance(name):
    app_name = get_commands()[name]
    return load_command_class(app_name, name)


def test_command_output():
    command = get_command_instance("runserver")
    parser = command.create_parser("manage.py", "runserver")
    assert "Wrapped by 'whitenoise.runserver_nostatic'" in parser.description
    assert not parser.get_default("use_static_handler")


def test_falls_back_to_core_runserver():
    from django.core.management.commands.runserver import Command as CoreRunserver

    from whitenoise.runserver_nostatic.management.commands import runserver

    installed_apps = [
        "django.contrib.humanize",
        "whitenoise.runserver_nostatic",
        "django.contrib.messages",
    ]
    try:
        with override_settings(INSTALLED_APPS=installed_apps):
            assert list(runserver.get_lower_priority_apps()) == [
                "django.contrib.messages"
            ]
            importlib.reload(runserver)
        assert runserver.RunserverCommand is CoreRunserver
        parser = runserver.Command().create_parser("manage.py", "runserver")
        assert "Wrapped by 'whitenoise.runserver_nostatic'" not in parser.description
    finally:
        importlib.reload(runserver)
