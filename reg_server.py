"""
Main module to register application.
"""
import os
import sys
import optparse

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


def create_app(port=None):
    """
    Helper function for creating the main application.
    """

    app = _make_flask_app(__name__, '.reg.env')

    if port:
        app.config['FLASK_RUN_PORT'] = port

    # register request app blueprints
    blueprints.register_request_app(app)
    return app


def main():
    parser = optparse.OptionParser(usage='%(prog)s [-b 127.0.0.1:5000] [-p 50001]')
    
    parser.add_option('-b', 
                    '--bootstraper',
                    help='List of nodes to listen on start.')
    
    parser.add_option('-p', 
                    '--port', 
                    help='Bind server to this port.')
    
    args = parser.parse_args()[0]
    app = create_app(port=args.port)

    if args.bootstraper:
        blueprints.landing.noob_chain.register_node(args.bootstraper, spread=False)

    app.logger.debug('starting request server...')
    app.run(port=app.config['FLASK_RUN_PORT'])


if __name__ == '__main__':
    main()