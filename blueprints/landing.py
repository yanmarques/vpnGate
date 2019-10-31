import sqlite3

from flask import Blueprint, render_template, current_app
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import EmailField


web = Blueprint('requests', __name__, template_folder='templates')


class RequestForm(FlaskForm):
    """
    Represents the registration form.
    """
    email = EmailField('Email', validators=[DataRequired(), Email()])


@web.route('/')
def index(form=None):
    if form is None:
        form = RequestForm()
    return render_template('home.html.j2', form=form)


@web.route('/register', methods=['post'])
def register():
    form = RequestForm()

    if form.validate():
        email = form.data['email']
        conn = current_app.get_db()
        
        # retrieve last ID from db
        cr_last_id = conn.cursor()
        last_id = cr_last_id.lastrowid or 0
        cr_last_id.close()
        
        try:
            conn.execute('insert into request (id,email) values (?,?)', (last_id + 1, email))
            conn.commit()
            return render_template('success.html.j2') 
        except sqlite3.IntegrityError as exception:
            if 'email' in str(exception):
                form.email.errors.append(f"This email '{email}' was already been registered.")

    return index(form=form)