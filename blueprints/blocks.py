import os
import hashlib
from dataclasses import dataclass

import requests
import click
from . import landing
from lib.tokens import JWTRegistry
from lib.node import Node, ClassStorage, simple_node_factory
from lib.blockchain import (
    Blockchain,
    BlockchainStorage, 
    DEFAULT_CONFIG, 
    simple_blockchain_factory,
    filter_blockchain_payload
)
from flask import url_for


def register_app(app):
    mail_storage, node_storage = create_storages(app)
    setattr(app, 'mail_storage', mail_storage)
    setattr(app, 'node_storage', node_storage)
    
    @app.teardown_appcontext
    def save_storage(exception):
        mail_storage.save(mail_storage.current)
        node_storage.save(node_storage.current)

    @app.cli.command('gen:bootstrap')
    @click.argument('proof')
    @click.argument('address')
    @click.option('--dest-file', default='myboot.json')
    def generate_boot(proof, address, dest_file):
        boot = node_storage.current.append_node(proof, address)
        BootstrapStorage(dest_file).save(boot)
        click.echo(f'Bootstrap file saved at: {dest_file}')

    @app.cli.command('node:pow')
    @click.option('--last-block-file')
    def generate_proof(last_block_file):
        # last_block = None
        # if last_hash and last_proof:
        #     last_block = {
        #         'proof' = last_proof
        #     }
        proof = node_storage.current.proof_of_work()
        click.echo(proof)

    app.logger.info('running on: %s', node_storage.current.node.host)


def create_storages(app):
    mail_storage_path = get_config_or_environ(app, 'MAIL_CHAIN_STORAGE_PATH')
    assert mail_storage_path, 'Missing mail storage path configuration.'

    node_storage_path = get_config_or_environ(app, 'NODE_CHAIN_STORAGE_PATH')
    assert node_storage_path, 'Missing node storage path configuration.'

    bootstrap_storage_path = get_config_or_environ(app, 'BOOTSTRAP_STORAGE_PATH')
    
    if app.config['TESTING']:
        app.logger.debug('remove storage files when testing')
        try:
            os.unlink(mail_storage_path)
            os.unlink(node_storage_path)
        except FileNotFoundError as exc:
            app.logger.error(str(exc))

    algo = app.config.get('JWT_ALGO') or None
    jwt = JWTRegistry(lambda: app.config['SECRET_KEY'], algo=algo)
    
    def mail_factory(data: dict):
        return simple_blockchain_factory(jwt, MailBlockchain, data)

    def node_factory(data: dict):
        if 'boot_storage_path' in data:
            data['boot_storage'] = BootstrapStorage(data['boot_storage_path'])
            del data['boot_storage_path']
        
        block = simple_blockchain_factory(jwt, NodeBlockchain, data)

        if app.config.get('NODE_IGNORE_SECURE_HOST'):
            app.logger.info('Configured to ignore secure hosts check, use it carefully.')
            app.logger.info('You can add childs to your host even in plain HTTP.')
            block.node.is_secure = True
        return block
        
    mail_storage = BlockchainStorage(mail_storage_path, input_factory=mail_factory)    
    node_storage = BlockchainStorage(node_storage_path, 
                                    input_factory=node_factory,
                                    output_filter=filter_node_chain)

    host = who_am_i(app)
    config = parse_blockchain_config(app)
    current_node = None

    bootstrap = None
    if bootstrap_storage_path:
        bootstrap = BootstrapStorage(bootstrap_storage_path, 
                                    block_storage=node_storage)
    
    if node_storage.current is None:
        assert host, 'Missing node host configuration.'
        app.logger.info('Any mail chain storage available, building one...')

        current_node = Node(host)

        blocks = NodeBlockchain(node=current_node,
                                boot_storage=bootstrap, 
                                jwt=jwt, 
                                config=config)
        node_storage.save(blocks)
    else:
        current_node = node_storage.current.node 
        node_storage.current.boot_storage = bootstrap
        node_storage.current.bootstrap()

    if mail_storage.current is None:
        blocks = MailBlockchain(node=current_node, 
                                jwt=jwt, 
                                config=config)
        mail_storage.save(blocks)
    else:
        if current_node.host != mail_storage.current.node.host:
            app.logger.warn('Mail storage node has a different configure host.')
            app.logger.warn('Node storage configured host will be take.')
        mail_storage.current.node = current_node

    return mail_storage, node_storage  


def who_am_i(app):
    pre_built_name = f'{app.config["FLASK_RUN_HOST"]}:{app.config["FLASK_RUN_PORT"]}'
    return get_config_or_environ(app, 'NODE_HOST', default=pre_built_name)


def parse_blockchain_config(app):
    config = dict()
    
    for key in DEFAULT_CONFIG.keys():
        value = app.config.get(f'CHAIN_{key.upper()}')
        if value:
            config[key] = value

    return config


def get_config_or_environ(app, key, default=None):
    return (app.config.get(key) or os.getenv(key)) or default


def simple_bootstrap_factory(data: dict):
    return ChainBootstrap(**data)


def filter_node_chain(payload: dict):
    if payload['boot_storage'] and payload['boot_storage']['current']:
        storage_path = payload['boot_storage']['path']
        storage = simple_bootstrap_factory(payload['boot_storage']['current'])
        BootstrapStorage(storage_path).save(storage)
        payload['boot_storage_path'] = storage_path
    
    del payload['boot_storage']
    return filter_blockchain_payload(payload)


@dataclass
class MailBlockchain(Blockchain):
    name: str = 'mail'

    def new_transaction(self, email):
        return super().new_transaction(email)

    def email_exists(self, email):
        """
        Defines wheter an email is not used in the chain.

        :param email: <str> Email address
        :return: <bool>
        """

        for block in self.chain:
            if email in block['transactions']:
                return True
        return False


@dataclass
class ChainBootstrap:
    issuer_host: str
    host: str
    identifier: str
    token: str


@dataclass
class BootstrapStorage(ClassStorage):
    block_storage: BlockchainStorage = None
    input_factory: callable = simple_bootstrap_factory


@dataclass
class NodeBlockchain(Blockchain):
    name: str = 'node'

    bootstraped: bool = False
    boot_storage: BootstrapStorage = None

    def __post_init__(self):
        super().__post_init__()
        self.bootstrap()

    def bootstrap(self):
        if not self.bootstraped and self.boot_storage and self.boot_storage.current:
            bootstraper = self.boot_storage.current
            self.node = Node(bootstraper.host, identifier=bootstraper.identifier)
            self.assign_jwt_issuer()
            self.logger.debug('bootstraping: %s', self.boot_storage)

            payload = dict(token=bootstraper.token,
                        id=self.node.identifier,
                        proof=self.proof_of_work())

            url = f'{bootstraper.issuer_host}/bootstrap'
            res = requests.post(url, data=payload)
            assert res.status_code == 201, 'Failed to bootstrap.'
            data = res.json()
            assert data and 'access_token' in data and 'self' in data, \
                            'Invalid bootstrap information returned from issuer.' 

            self.access_token = data['access_token']
            self.bootstraped = True

            self.node.parent = simple_node_factory(data['self'])

            # grab block storage, use it and throw away
            block_storage = self.boot_storage.block_storage
            self.boot_storage.block_storage = None
            block_storage.save(self)
        if self.boot_storage:
            self.boot_storage.block_storage = None

    def revoke_node(self, node, clear=True):
        """
        Remove a node from neighborhood and return wheter was revoked.

        :param node: <str> Address of node
        :param clear: <bool> Indicates wheter to clear predicate cache
        :return: <bool> 
        """

        status = False
        if (node in self.node.children or node in self.revokeds) and \
                        not self.predicate.is_valid(node):
            print(f'node revoked: {node}')
            self.node.remove_child(node)
            self.revokeds.append(node)
            status = True
        if clear:
            self.predicate.clear_cache()
        return status

    def register_child(self, proof, token, identifier):
        """
        Add a new child of current node from registered 
        JWT token and an UUID string.

        :param token: Generated token
        :param identifier: A 128 bits UUID
        """

        self.check_proof_or_fail(proof)
        self.jwt.audience = identifier
        data = self.jwt.decode(token)

        if token in self.pending_tokens:
            assert 'hst' in data, 'Invalid token.'
            self.pending_tokens.remove(token)

            new_node = Node(data['hst'], identifier=identifier)            

            if self.node_exists(new_node):
                raise LookupError('Node already exists in the chain.')

            self.node.add_child(new_node)
            self.logger.debug('new node config: %s', self.node)

            self.jwt.audience = None
            new_token = self.jwt.encode(self.config['token_renew_time'])
            self.tokens.append(new_token)

            self.new_transaction(new_node)
            self.new_block(proof, self.get_last_info()[1])
            return new_token

    def is_valid_token(self, token, identifier):
        try:
            self.jwt.audience = identifier
            self.jwt.decode(token)
            return token in self.tokens
        except Exception:
            return False

    def append_node(self, proof, address):
        self.check_proof_or_fail(proof)
        new_node = Node(address)
        self.jwt.audience = new_node.identifier

        token = self.jwt.encode(self.config['token_pending_time'],
                                hst=new_node.host)
        
        self.pending_tokens.append(token)
        return ChainBootstrap(host=new_node.host,
                            issuer_host=self.node.host,
                            identifier=new_node.identifier,
                            token=token)

    def node_exists(self, node):
        hash_host = hashlib.sha256(node.host.encode()).hexdigest()        
        for block in self.chain:
            for transaction in block['transactions']:
                if hash_host == transaction['hsh']:
                    return True
        return False


    def new_transaction(self, dest_node):
        return super().new_transaction({
            'snd': self.node.identifier,
            'dst': dest_node.identifier,
            'hsh': hashlib.sha256(dest_node.host.encode()).hexdigest()
        })