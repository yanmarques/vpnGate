"""
Main module to register application.
"""
import os

import click
import blueprints
from flask import Flask
from dotenv import load_dotenv


DEFAULT_CONFIG_VAR = 'APP_CONFIG'
DEFAULT_CONFIG_FILE = '.env'


def create_app():
    # load environment variables
    load_dotenv()

    # flask main object
    app = Flask(os.environ.get('APP_NAME', __name__))
    app.config.from_pyfile(os.environ.get(DEFAULT_CONFIG_VAR, DEFAULT_CONFIG_FILE))
    blueprints.register_all(app)
    return app


app = create_app()
    

@app.cli.command('gen:key')
@click.option('--block-size', default=256)
@click.option('--dest-file', default=DEFAULT_CONFIG_FILE)
def generate_secret_key(block_size, dest_file):
    from sys_util import run_shell
    from secrets import token_bytes
    from base64 import b64encode

    byte_size = int(block_size / 8)

    # generate pseudo-random key
    secret_key = b64encode(token_bytes(byte_size)).decode()

    command = f"sed -i 's|.*SECRET_KEY=.*|SECRET_KEY=\"{secret_key}\"|'"
    command += f' {dest_file}'
    run_shell(command)

    click.echo(f"[*] Key generated and saved at '{dest_file}'")