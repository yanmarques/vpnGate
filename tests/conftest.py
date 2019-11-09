import os

import pytest
import contextlib
import reg_server
from sys_util import run_shell


def setup_environ(flask_app):
    # update running environment to load custom file
    os.environ[reg_server.DEFAULT_CONFIG_VAR] = 'tests/.env'
    os.environ['FLASK_APP'] = flask_app


@pytest.fixture
def reg_client():
    setup_environ('reg_server:create_app()')
    test_app = reg_server.create_app()
    
    with test_app.test_client() as client:
        with test_app.app_context():
            yield client


@pytest.fixture
def reg_get_clients():
    first_port = 5000
    def set_new_address():
        nonlocal first_port
        setup_environ('reg_server:create_app()')
        test_app = reg_server.create_app(first_port)
        first_port += 1
        return test_app.app_context()

    with contextlib.ExitStack() as stack:
        yield [stack.enter_context(set_new_address())
                for _ in range(3)]