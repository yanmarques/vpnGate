from . import landing, panel, database, cli, blocks


def register_request_app(app):
    _register_all(app, [landing.web])
    
    blocks.register_app(app)


def register_panel_app(app):
    _register_all(app, [panel.web])


def _register_all(app, blueprints, with_extra=True):
    @app.after_request
    def set_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'self';script-src 'self';connect-src 'self';"

        return response

    # register each application blueprint
    list(map(app.register_blueprint, blueprints))
    
    if with_extra:
        # pass app to another registers
        database.register(app)
        cli.register(app)
