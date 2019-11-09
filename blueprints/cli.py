"""
This module provides commands to run with flask binary.
"""
import click
import dotenv


def register(app):
    @app.cli.command('gen:key')
    @click.argument('dest_file')
    @click.option('--block-size', default=256)
    def generate_secret_key(dest_file, block_size):
        from sys_util import run_shell
        from secrets import token_bytes
        from base64 import b64encode

        byte_size = int(block_size / 8)

        # generate pseudo-random key
        secret_key = b64encode(token_bytes(byte_size)).decode()

        command = dotenv.get_cli_string(path=dest_file,
                                        action='set',
                                        key='SECRET_KEY',
                                        value=secret_key)

        run_shell(command)

        click.echo(f"[*] Key generated and saved at '{dest_file}'")
    
    @app.cli.command('gen:database')
    def create_database():
        # creates database when not exists
        db = app.get_db()
        with app.open_resource(app.get_db_schema(), mode='r') as f:
            # create schemas from text
            db.cursor().executescript(f.read())
        
        # save our work
        db.commit()
        db.close()
        click.echo('[*] Database generated!')