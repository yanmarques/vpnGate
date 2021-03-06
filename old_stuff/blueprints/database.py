import sqlite3
import os


DATABASE_ATTR = '_database'


def register(app):
    """
    Parses flask database configuration to valid format, also adding 
    database functions to app object.
    """
    
    def _parse_db_config(name, full=True):
        preffix = get_db_dir() if full else ''
        return preffix + app.config[name].lstrip('/')

    def get_db_path(**kwargs):
        return _parse_db_config('DB_PATH', **kwargs)

    def get_db_dir():
        return app.config['DB_DIR'].rstrip('/') + '/'

    def get_db_schema(**kwargs):
        return _parse_db_config('DB_SCHEMA', **kwargs)

    def get_db():
        db = getattr(app, DATABASE_ATTR, None)
        if db is None:
            database = get_db_path()
            app.logger.info('connecting to database: %s', database)
            db = sqlite3.connect(database)
            db.row_factory = sqlite3.Row
            setattr(app, DATABASE_ATTR, db)
        return db
    
    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(app, DATABASE_ATTR, None)
        if db is not None:
            try:
                app.logger.debug('closing database connection...')
                db.close()
            except Exception as exception:
                app.logger.error(str(exception))
            delattr(app, DATABASE_ATTR)

    # patch app object with monkey functions
    monkeys = [get_db, get_db_path, get_db_schema]
    for mnk in monkeys:
        setattr(app, mnk.__name__, mnk)