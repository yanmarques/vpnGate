import sqlite3

from flask import Blueprint, render_template, current_app


web = Blueprint('control', __name__, template_folder='templates')


@web.route('/')
def index():
    conn = current_app.get_db()
    generator = iter(conn.execute('select * from request'))
    return render_template('listing.html.j2', requests=generator)