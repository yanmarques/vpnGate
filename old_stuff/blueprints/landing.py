import sqlite3
import socket
import ipaddress
from urllib.parse import urlparse
from functools import wraps
from dataclasses import asdict

from lib.node import filter_node_payload
from flask import Blueprint, render_template, current_app, request
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email
from wtforms.fields import StringField, SubmitField, TextAreaField
from wtforms.fields.html5 import EmailField


LOCAL_NETWORK = ipaddress.IPv4Network('127.0.0.0/8')

web = Blueprint('requests', __name__, template_folder='templates')


class RequestForm(FlaskForm):
    """
    Represents the registration form.
    """
    
    email = EmailField('Email', validators=[DataRequired(), Email()])
    proof = StringField('Proof of work', validators=[DataRequired()])
    last_proof = StringField('Last POW')
    last_hash = StringField('Last block hash')


class NodeContext:
    def __init__(self):
        self.storage = current_app.node_storage

    @property
    def chain(self): 
        return self.storage.current

    def __enter__(self):
        self.storage.load()
        return self.chain

    def __exit__(self, *args):
        self.storage.save(self.chain)


def get_mail_chain():
    node_chain = get_node_chain()
    storage = current_app.mail_storage
    storage.load()
    if node_chain.access_token:
        storage.current.access_token = node_chain.access_token
        storage.save(storage.current)
    return storage.current


def get_node_chain():
    storage = current_app.node_storage
    storage.load()
    return storage.current


def save_node_chain():
    storage = current_app.node_storage
    storage.save(storage.current)


def get_remote_addr():
    return request.headers.get('X-Forwarded-For') or request.remote_addr


def has_node_address():
    """
    Defines wheter the chain contains the node of 
    the current request in the neighbour nodes.

    :return: <bool>
    """

    remote_addr = get_remote_addr()
    address = urlparse(remote_addr).path
    current_app.logger.debug('incoming address: %s', address)

    # allow localhost
    if address in DEFAULT_ALLOWEDS:
        return True

    for node in list(current_app.blocks.nodes):
        node_address = urlparse(node).netloc.split(':', 1)[0] 
        try:
            ipaddress.IPv4Address(node_address)
            # is an ip address, direct checking
            if node_address == address:
                current_app.logger.debug('node address found: %s', address)
                return True
        except ipaddress.AddressValueError:
            # it's a hostname, resolve to IP and check 
            node_addr_resolution = socket.gethostbyname_ex(node_address)[2]
            if address in node_addr_resolution:
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
        token_header = request.headers.get('authorization')
        node_id = request.headers.get('x-node-id')
        header_type = 'bearer'
        
        if token_header and node_id and token_header.lower().startswith(header_type):
            token = token_header[len(header_type):].strip()  
            if get_node_chain().is_valid_token(token, node_id):
                request.token = token
                request.node_id = node_id
                return fn(*args, **kwargs)

        return 'Access denied', 401
    return barrier


@web.route('/')
def index(form=None):
    with_token = request.args.get('no_token', '').lower() != 'true'
    
    current_app.logger.debug('token: %s', with_token)
    if with_token:
        get_mail_chain().resolve_conflicts()
    else:
        with NodeContext() as chain:
            chain.exchange_chains()
        
        get_mail_chain().exchange_chains()

    if form is None:
        form = RequestForm()

    last_proof, last_hash = get_mail_chain().get_last_info()

    return render_template('home.html.j2', 
                            form=form,
                            last_proof=last_proof,
                            last_hash=last_hash, 
                            with_token=with_token)


@web.route('/mirrors')
def mirrors():
    return render_template('mirrors.html.j2', nodes=get_mail_chain().nodes)


@web.route('/register', methods=['post'])
def register():
    logger = current_app.logger
    form = RequestForm()
    
    if form.validate():
        blocks = get_mail_chain()
        blocks.spread_neighbors()
        blocks.exchange_chains()
        blocks.validate_neighbors()

        last_proof, last_hash = blocks.get_last_info()
        email = form.data['email']
        proof = form.data['proof']

        if blocks.valid_proof(proof, last_proof, last_hash):
            if blocks.is_valid(email):
                blocks.new_transaction(email)
                blocks.new_block(proof, last_hash)
                replaced = blocks.exchange_chains()
                logger.debug('chain was replaced: %s', replaced)
                return render_template('success.html.j2')
            form.email.errors.append(f"This email {email} was already been registered.")
        else:
            form.proof.errors.append('Invalid proof of work!') 
            form.proof.errors.append('Maybe someone have mined faster than you. Try it again.')            
    logger.debug('errors: %s', form.errors)
    return index(form=form)


@web.route('/<name>/chain', methods=['get', 'put'])
@only_node_personal
def chain(name):
    if name == 'mail':
        blockchain = get_mail_chain()
    elif name == 'node':
        blockchain = get_node_chain()
    else:
        return 'Not found', 404

    if request.method == 'GET':
        response = {
            'chain': blockchain.chain
        }

        return response, 200
    
    if 'chain' in request.form:
        remote_chain = request.form.getlist('chain')
        if remote_chain:
            result = blockchain.accept_chain(remote_chain)
            current_app.logger.debug('chain was replaced: %s', result)
            return '', 200
    
    response = {
        'errors': 'Invalid arguments.'
    }

    return response, 400


@web.route('/node', methods=['get', 'delete'])
@only_node_personal
def node_action():
    logger = current_app.logger
    blockchain = get_node_chain()

    if request.method == 'GET':
        response = {
            'children': list(blockchain.node.children),
            'revokeds': list(blockchain.revokeds)
        }

        return response
    
    if 'nodes' in request.form:
        nodes = request.form.getlist('nodes')
        logger.debug('nodes size: %s', len(nodes))
                
        if nodes:
            list(map(blockchain.revoke_node, nodes))
            return '', 201

    response = {
        'nodes': 'Value is missing.'
    }

    return response, 400


@web.route('/bootstrap', methods=['post'])
def bootstrap_child():
    keys = list(request.form)
    if 'token' in keys and 'id' in keys and 'proof' in keys:
        token = request.form['token']
        node_id = request.form['id']
        proof = request.form['proof']
        
        current_app.logger.debug('recv token: %s', len(token) > 0)
        current_app.logger.debug('recv id: %s', node_id)
        current_app.logger.debug('recv proof: %s', proof)
        
        if token and node_id and proof:
            blockchain = get_node_chain()
            new_token = blockchain.register_child(proof, token, node_id)
            if new_token:
                payload = asdict(blockchain.node)
                response = dict(access_token=new_token, self=filter_node_payload(payload))
                return response, 201

    response = {
        'errors': 'Invalid arguments.'
    }

    return response, 400