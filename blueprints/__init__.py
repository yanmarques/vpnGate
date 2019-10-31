from .landing import web
from . import database


def register_all(app):
    # register each application blueprint
    blueprints = [web]
    list(map(app.register_blueprint, blueprints))
    database.register(app)
