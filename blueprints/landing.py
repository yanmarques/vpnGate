import sqlite3
from urllib.parse import urlparse
from functools import wraps

from flask import Blueprint, render_template, current_app, request
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms.fields import StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField


web = Blueprint('requests', __name__, template_folder='templates')


class RequestForm(FlaskForm):
    """
    Represents the registration form.
    """
    
    email = EmailField('Email', validators=[DataRequired(), Email()])
    proof = StringField('Proof of work', validators=[DataRequired()])
    last_proof = StringField('Last POW')
    last_hash = StringField('Last block hash')


def get_last_info():
    """
    Get the last proof of work and the hash of the last
    block on the chain.

    :return: Proof of work and the hash
    """

    last_block = web.blocks.last_block
    return last_block['proof'], web.blocks.hash(last_block)


def valid_email(email):
    """
    Defines wheter an email is not used in the chain.

    :param email: <str> Email address
    :return: <bool>
    """

    for block in web.blocks.chain:
        if email in block['transactions']:
            return False
    return True


def has_node_address():
    """
    Defines wheter the chain contains the node of 
    the current request in the neighbour nodes.

    :return: <bool>
    """

    address = urlparse(request.remote_addr).path
    current_app.logger.debug('incoming address: %s', address)
    for node in list(web.blocks.nodes):
        if urlparse(node).netloc.split(':', 1)[0] == address:
            current_app.logger.debug('node address found: %s', address)
            return True
    return False


def only_node_personal(fn):
    """
    Decorator to block access based on IP address.

    :param fn: <function> Function to decorate
    """

    @wraps(fn)
    def barrier(*args, **kwargs):
        if not has_node_address():
            return 'Access denied', 401
        return fn(*args, **kwargs)
    return barrier


@web.route('/')
def index(form=None):
    with_token = request.args.get('no_token', '').lower() != 'true'
    
    print(f'token: {with_token}')
    if with_token:
        web.blocks.resolve_conflicts()
    else:
        web.blocks.exchange_chains()

    if form is None:
        form = RequestForm()

    last_proof, last_hash = get_last_info()

    return render_template('home.html.j2', 
                            form=form,
                            last_proof=last_proof,
                            last_hash=last_hash, 
                            with_token=with_token)


@web.route('/register', methods=['post'])
def register():
    logger = current_app.logger
    form = RequestForm()
    
    if form.validate():
        web.blocks.spread_neighbors()
        web.blocks.exchange_chains()
        web.blocks.validate_neighbors()

        last_proof, last_hash = get_last_info()
        email = form.data['email']
        proof = form.data['proof']

        if web.blocks.valid_proof(last_proof, proof, last_hash):
            if valid_email(email):
                web.blocks.new_transaction(email)
                web.blocks.new_block(proof, last_hash)
                replaced = web.blocks.exchange_chains()
                logger.debug('chain was replaced: %s', replaced)
                return render_template('success.html.j2')
            form.email.errors.append(f"This email '{email}' was already been registered.")            
        else:
            form.proof.errors.append('Invalid proof of work!') 
            form.proof.errors.append('Maybe someone have mined faster than you. Try it again.')            
    logger.debug('errors: %s', form.errors)
    return index(form=form)


@web.route('/chain', methods=['get'])
@only_node_personal
def chain():
    response = {
        'chain': web.blocks.chain,
        'length': len(web.blocks.chain)
    }
    
    return response, 200


@web.route('/node', methods=['get', 'post', 'delete'])
@only_node_personal
def node_action():
    logger = current_app.logger
    if request.method == 'GET':
        response = {
            'nodes': list(web.blocks.nodes),
            'revokeds': list(web.blocks.revokeds)
        }

        return response

    values = request.form
    if 'nodes' in values and values['nodes']:
        content = values['nodes']
        if not type(content) is list:
            content = [content]

        if request.method == 'POST':
            function = web.blocks.register_node
        else:
            function = web.blocks.revoke_node

        list(map(function, content))
        return '', 201

    response = {
        'nodes': 'Value is missing.'
    }

    return response, 400