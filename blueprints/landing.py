import sqlite3
from urllib.parse import urlparse

from flask import Blueprint, render_template, current_app, request
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms.fields import StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField
from lib.models import Request
from lib.blockchain import Blockchain


web = Blueprint('requests', __name__, template_folder='templates')
noob_chain = Blockchain(dificulty=1)


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

    last_block = noob_chain.last_block
    return last_block['proof'], noob_chain.hash(last_block)


def valid_email(email):
    """
    Defines wheter an email is not used in the chain.

    :param email: <str> Email address
    :return: <bool>
    """

    for block in noob_chain.chain:
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
    for node in list(noob_chain.nodes):
        if urlparse(node).netloc.split(':', 1)[0] == address:
            current_app.logger.debug('node address found: %s', address)
            return True
    return False


@web.route('/')
def index(form=None):
    noob_chain.resolve_conflicts()

    if form is None:
        form = RequestForm()

    last_proof, last_hash = get_last_info()

    return render_template('home.html.j2', 
                            form=form,
                            last_proof=last_proof,
                            last_hash=last_hash)


@web.route('/register', methods=['post'])
def register():
    noob_chain.resolve_conflicts()
    logger = current_app.logger

    form = RequestForm()
    
    if form.validate():
        last_proof, last_hash = get_last_info()
        email = form.data['email']
        proof = form.data['proof']

        if noob_chain.valid_proof(last_proof, proof, last_hash):
            if not email in all_emails():
                noob_chain.new_transaction(email)
                noob_chain.new_block(proof, last_hash)
                replaced = noob_chain.resolve_conflicts()
                logger.debug('chain was replaced: %s', replaced)
                return render_template('success.html.j2')
            form.email.errors.append(f"This email '{email}' was already been registered.")            
        else:
            form.proof.errors.append('Invalid proof of work. Try it again.')            
    current_app.logger.debug('errors: %s', form.errors)
    return index(form=form)


@web.route('/chain', methods=['get'])
def chain():
    if not has_node_address():
        return 'Access denied', 401

    response = {
        'chain': noob_chain.chain,
        'length': len(noob_chain.chain)
    }
    
    return response, 200


@web.route('/node', methods=['get', 'post'])
def add_node():
    if not has_node_address():
        return 'Access denied', 401
    logger = current_app.logger
    if request.method == 'GET':
        response = dict(nodes=list(noob_chain.nodes))
        return response

    values = request.form
    if 'nodes' in values and values['nodes']:
        content = values['nodes']
        if not type(content) is list:
            content = [content]
        list(map(noob_chain.register_node, content))
        return '', 201

    response = {
        'nodes': 'Value is missing.'
    }

    return response, 400