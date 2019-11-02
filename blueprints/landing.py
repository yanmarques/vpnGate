import sqlite3

from flask import Blueprint, render_template, current_app
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import EmailField
from .models import Request


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
        req = Request(email=form.data['email'])
        if req.create() is True:
            current_app.logger.debug('request created: %s', req)
            return render_template('success.html.j2')
        form.email.errors.append(f"This email '{req['email']}' was already been registered.")

    return index(form=form)