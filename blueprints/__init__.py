from . import landing, panel, database, cli
from lib.blockchain import Blockchain


def register_request_app(app):
    _register_all(app, [landing.web])
    name = who_am_i(app)
    config = parse_blockchain_config(app)
    blocks = Blockchain(name, config=config)
    setattr(app, 'blocks', blocks)
    print(f'running on: {name}')


def register_panel_app(app):
    _register_all(app, [panel.web])


def parse_blockchain_config(app):
    config = dict() 

    difficulty = app.config.get('CHAIN_DIFFICULTY')
    if difficulty:
        config['difficulty'] = difficulty

    validation_time = app.config.get('CHAIN_VALIDATION_TIME')
    if validation_time:
        config['validation_time'] = validation_time

    spreading_time = app.config.get('CHAIN_SPREADING_TIME')
    if spreading_time:
        config['spreading_time'] = spreading_time
    return config


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
