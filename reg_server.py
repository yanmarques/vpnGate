"""
Main module to register application.
"""
import os

import blueprints
from flask import Flask
from dotenv import load_dotenv


DEFAULT_CONFIG_VAR = 'APP_CONFIG'


def _make_flask_app(default_name, default_config):
    """
    Instantiate flask application, given inital configuration. The default 
    parameters will be read from environment, when not set, the defaults passed
    to this function will be used instead. 
    """
    
    config_file = os.environ.get(DEFAULT_CONFIG_VAR, default_config)

    # load environment variables
    load_dotenv(config_file)

    # flask main object
    app = Flask(os.environ.get('APP_NAME', default_name))
    app.config.from_pyfile(config_file)
    return app


def create_app():
    """
    Helper function for creating the main application.
    """

    app = _make_flask_app(__name__, '.reg.env')

    # register request app blueprints
    blueprints.register_request_app(app)
    return app


def main():
    app = create_app()
    app.logger.debug('starting request server...')
    app.run(port=app.config.get('FLASK_RUN_PORT'))


if __name__ == '__main__':
    main()