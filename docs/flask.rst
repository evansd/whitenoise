Using WhiteNoise with Flask
============================

This guide walks you through setting up a Flask project with WhiteNoise.
In most cases it shouldn't take more than a couple of lines of configuration.

1. Make sure where your *static* is located
-------------------------------------------

If you're familiar with Flask you'll know what to do. If you're just getting
started with a new Flask project then the default is the ``static`` folder  in
the root path of the application.

Check the ``static_folder`` argument in `Flask Application Object documentation
<http://flask.pocoo.org/docs/api/#application-object>`_ for further
information.



2. Enable WhiteNoise
--------------------

In the file where you create your app you instantiate Flask Application Object
(the ``flask.Flask()`` object). All you have to do is to wrap it with
``WhiteNoise()`` object.

If you use Flask quick start approach it will look something like that:


.. code-block:: python

    from flask import Flask
    from whitenoise import WhiteNoise

    app = WhiteNoise(Flask(__name__), root='static/')

If you opt for the `pattern of creating your app with a function <http://flask.pocoo.org/snippets/20/>`_, then it would look like that:

.. code-block:: python

    from flask import Flask
    from sqlalchemy import create_engine
    from whitenoise import WhiteNoise

    from myapp import config
    from myapp.views import frontend

    def create_app(database_uri, debug=False):
        app = Flask(__name__)
        app.debug = debug

        # set up your database
        app.engine = create_engine(database_uri)

        # register your blueprints
        app.register_blueprint(frontend)

        # add whitenoise
        app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/')

        # other setup tasks

        return app


That's it -- WhiteNoise will now serve your static files.


3. Custom *static* folder
-------------------------

If it turns out that your are not using the Flask default for *static* folder,
fear not. You can instantiate WhiteNoise and add your *static* folders later:

.. code-block:: python

    from flask import Flask
    from whitenoise import WhiteNoise

    app = WhiteNoise(Flask(__name__))
    my_static_folders = (
        'static/folder/one/',
        'static/folder/two/',
        'static/folder/three/'
    )
    for static in my_static_folders:
        app.add_files(static)

And check ``WhiteNoise.add_file`` documentation for further customization.
