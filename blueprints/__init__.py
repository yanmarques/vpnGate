from . import landing, panel, database, cli


def register_request_app(app):
    _register_all(app, [landing.web])
    name = who_am_i(app)
    landing.noob_chain.server_name = name 
    print(f'running on: {name}')


def register_panel_app(app):
    _register_all(app, [panel.web])


def who_am_i(app):
    return f'{app.config["FLASK_RUN_HOST"]}:{app.config["FLASK_RUN_PORT"]}'


def _register_all(app, blueprints, with_extra=True):
    @app.after_request
    def set_headers(response):
        response.headers['Content-Security-Policy'] = "default-src 'none'; style-src 'self'; script-src 'self'; connect-src 'self';"
        return response

    # register each application blueprint
    list(map(app.register_blueprint, blueprints))
    
    if with_extra:
        # pass app to another registers
        database.register(app)
        cli.register(app)
