from . import landing, panel, database, cli


def register_request_app(app):
    _register_all(app, [landing.web])


def register_panel_app(app):
    _register_all(app, [panel.web])


def _register_all(app, blueprints):
    # register each application blueprint
    list(map(app.register_blueprint, blueprints))

    # pass app to another registers
    database.register(app)
    cli.register(app)
