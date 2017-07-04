from __future__ import unicode_literals

import django
from django.core.management import get_commands, load_command_class
from django.test import SimpleTestCase

django.setup()


def get_command_instance(name):
    app_name = get_commands()[name]
    return load_command_class(app_name, name)


class RunserverNostaticTest(SimpleTestCase):

    def test_command_output(self):
        command = get_command_instance('runserver')
        parser = command.create_parser('manage.py', 'runserver')
        self.assertIn("Wrapped by 'whitenoise.runserver_nostatic'", parser.format_help())
        self.assertFalse(parser.get_default('use_static_handler'))
