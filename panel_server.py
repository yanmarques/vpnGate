"""
Main module to panel.
"""

import reg_server
import blueprints


def create_app():
    app = reg_server._make_flask_app(__name__, '.panel.env')
    blueprints.register_panel_app(app)
    return app


def main():
    app = create_app()
    app.logger.debug('starting panel server...')
    app.run(port=app.config.get('FLASK_RUN_PORT'))


if __name__ == '__main__':
    main()