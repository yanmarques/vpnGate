import os

import pytest
import reg_server
from sys_util import run_shell


@pytest.fixture
def reg_client():
    # update running environment to load custom file
    os.environ[reg_server.DEFAULT_CONFIG_VAR] = 'tests/.env'
    os.environ['FLASK_APP'] = 'reg_server:create_app()'
    test_app = reg_server.create_app()

    with test_app.test_client() as client:
        with test_app.app_context():
            process = run_shell('flask gen:database')
            test_app.logger.debug(process.stdout)
            test_app.logger.error(process.stderr)
            yield client

            # remove test database
            db_path = test_app.get_db_path()
            run_shell(f'rm {db_path}')