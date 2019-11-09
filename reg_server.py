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


def create_app(port=None, host=None, server=None, bootstraper=None):
    """
    Helper function for creating the main application.
    """

    app = _make_flask_app(__name__, '.reg.env')

    if port:
        app.config['FLASK_RUN_PORT'] = port

    if host:
        app.config['FLASK_RUN_HOST'] = host

    if server:
        app.config['CHAIN_SERVER_NAME'] = server

    if bootstraper:
        app.config['CHAIN_BOOTSTRAPER'] = bootstraper

    # register request app blueprints
    blueprints.register_request_app(app)
    return app


def main():
    parser = optparse.OptionParser(usage='%(prog)s [-b 127.0.0.1:5001] [-p 5000]')
    
    parser.add_option('-b', 
                    '--bootstraper',
                    help='List of nodes to listen on start.')
    
    parser.add_option('-p', 
                    '--port', 
                    help='Bind server to this port.')
                
    parser.add_option('-a', 
                    '--address', 
                    help='Bind server to this address.')

    parser.add_option('-s', 
                    '--server',
                    help='Server name to advertise.')
    
    args = parser.parse_args()[0]
    app = create_app(port=args.port, 
                    host=args.address,
                    server=args.server,
                    boostraper=args.bootstraper)

    app.logger.debug('starting request server...')
    app.run(port=app.config['FLASK_RUN_PORT'],
            host=app.config['FLASK_RUN_HOST'])


if __name__ == '__main__':
    main()