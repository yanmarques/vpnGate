import os

from reg_server import create_app

wsgi_name = os.getenv('APP_WSGI')

if wsgi_name == 'reg_server':
    app = create_app()
else:
    raise RuntimeError(f'Invalid wsgi name: {wsgi_name}')
