import hashlib
import json
import logging
from time import time
from traceback import print_tb
from dataclasses import dataclass, field
from typing import Any, List, Dict

import requests
import blueprints
from .node import Node, ClassStorage, simple_node_factory, filter_node_payload
from .tokens import JWTRegistry
from .timers import Scheduler
from flask import url_for


# Maximum time for http connection
DEFAULT_TIMEOUT = 10

DEFAULT_CONFIG = {
    'difficulty': 4, 
    'validation_time': 30,
    'spreading_time': 60,
    'token_pending_time': 120,
    'token_renew_time': (60 * 60) * 2 
}


def send_to_nodes(target, node_list, method='post'):
    payload = dict(nodes=target)
    caller = getattr(requests, method)
    assert caller is not None, 'Invalid method'
    relative_url = url_for('requsts.node') 
    for node in node_list:
        try:
            response = caller(f'{node}{relative_url}', 
                            data=payload,
                            timeout=DEFAULT_TIMEOUT)

            if response.status_code != 201:
                print(response.text)
        except Exception as exc:
            print_exception(exc)


def get_json(url):
    response = http_get(url)
    if response is not None:
        print(f'received response for {url}: {response}')
        if response.status_code == 200:
            return response.json()


def hash_http_response(url, default=''):
    response = http_get(url, default=default)
    if response != default:
        return hashlib.sha256(response.content).hexdigest()
    return default


def http_get(url, default=None):
    try:
        return requests.get(url, timeout=DEFAULT_TIMEOUT)
    except Exception as exc:
        print_exception(exc)
    return default


def url_wihout_csrf(url):
    return f'{url}?no_token=true'


def print_exception(exception):
    print_tb(exception.__traceback__)
    print(str(exception))


def simple_blockchain_factory(jwt, class_factory, data: dict):
    data['node'] = simple_node_factory(data['node'])
    
    return class_factory(jwt=jwt, **data)


def filter_blockchain_payload(payload: dict):
    payload['node'] = filter_node_payload(payload['node'])
    del payload['jwt']
    del payload['schedule']
    del payload['predicate']
    return payload


@dataclass
class BlockchainStorage(ClassStorage):
    output_filter: callable = filter_blockchain_payload


@dataclass
class Blockchain:
    """
    The blockchain where the server will run the transactions.
    """
    
    node: Node
    jwt: JWTRegistry
    
    name: str

    config: Dict = None
    tokens: List = field(default_factory=list)
    pending_tokens: List = field(default_factory=list)
    
    transactions: List = field(default_factory=list)
    chain: List = field(default_factory=list)
    predicate: Any = None

    revokeds: List = field(default_factory=list)
    schedule: Scheduler = field(default_factory=Scheduler)

    access_token: str = None

    def __post_init__(self):
        self.logger = logging.getLogger('blockchain')

        if self.predicate is None:
            self.predicate = NodePredicate(self)

        if self.config is None:
            self.config = DEFAULT_CONFIG
        else:
            # merge with default configuration
            cfg_keys = self.config.keys()
            for key, value in DEFAULT_CONFIG.items():
                if not key in cfg_keys:
                    self.config[key] = value
        
        self.schedule.configure('validation', self.config['validation_time'])
        self.schedule.configure('spread', self.config['spreading_time'])
        self.assign_jwt_issuer()

        self.logger.debug('blockchain config: %s', self.config)

        # Create the genesis block
        if not len(self.chain):
            self.new_block(previous_hash='1', timestamp=1, proof=100)    

    def request_with_auth(self, url, method='get'):
        assert self.access_token, 'Any access token available.'
        kwargs = dict()
        kwargs['headers'] = {
            'Authorization': f'Bearer {self.access_token}',
            'X-Node-Id': self.node.identifier
        }
        kwargs['timeout'] = 10
        return getattr(requests, method)(url, **kwargs)
    
    def check_proof_or_fail(self, proof):
        if not self.valid_proof(proof, *self.get_last_info()):
            raise RuntimeError('Invalid POW.')

    def assign_jwt_issuer(self):
        self.jwt.issuer = self.node.identifier

    def get_last_info(self):
        """
        Get the last proof of work and the hash of the last
        block on the chain.

        :return: Proof of work and the hash
        """

        last_block = self.last_block
        return last_block['proof'], self.hash(last_block)

    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return: Wheter is valid
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            self.logger.debug('last block on chain: %s', last_block)
            self.logger.debug('current block: %s', block)

            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(block['proof'], last_block['proof'], last_block_hash):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        self.validate_neighbors()
        self.spread_neighbors()
        return self.exchange_chains()
        
    def exchange_chains(self):
        """
        This is our consensus algorithm, it resolves conflicts
        by replacing our chain with the longest one in the network.

        :return: Wheter current chain was replaced
        """

        if not self.node.is_root:
            path = url_for('requests.chain', name=self.name)

            # Grab and verify the chains from all the nodes in our network
            response = self.request_with_auth(f'{self.node.parent.host}{path}')
            data = response.json()
            if response.status_code == 200 and data:
                if self.accept_chain(data['chain']):
                    return True
                self.logger.debug('our chain is longer')
                self.logger.debug('preparing to sync parent')
        return False

    def accept_chain(self, chain):
        """
        Compare the received chain with our chain and replace it
        when necessary.

        :param chain: A remote chain
        :return: Wheter our chain was replaced
        """

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Check if the length is longer and the chain is valid
        if len(chain) > max_length and self.valid_chain(chain):
            self.chain = chain
            return True
        return False

    def new_block(self, proof, previous_hash, timestamp=None):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': timestamp or time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.get_last_info()[1],
        }

        # Reset the current transactions
        self.transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, content):
        """
        Creates a new transaction to go into the next mined Block

        :param content: Content of new transaction
        :return: The index of the Block that will hold this transaction
        """
        
        self.transactions.append(content)
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        """
        Get the last block on the chain.

        :return: A block
        """
        
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Creates a SHA-256 hash of a Block

        :param block: Block
        """

        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_block=None):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: A valid proof of work
        """


        last_block = last_block or self.last_block
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(proof, last_proof, last_hash) is False:
            proof += 1

        return proof

    def valid_proof(self, proof, last_proof, last_hash):
        """
        Validates the Proof

        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :param last_hash: <str> The hash of the Previous Block
        :return: <bool>
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        difficulty = self.config['difficulty']

        return guess_hash[-difficulty:] == "0" * difficulty

    def is_remote(self, node: Node):
        """
        Defines wheter the given node is not the current server.

        :param node: <str> Node's url to check  
        :return: <bool>
        """
        
        return self.node.identifier != node.identifier

    def spread_neighbors(self):
        if self.schedule.check('spread'):
            self._do_spread()

    def validate_neighbors(self):
        if self.schedule.check('validation'):
            self._do_validation()

    def _has_own_server(self, nodes):
        """
        Defines wheter the current node is inside
        the given list of nodes.

        :param nodes: <list> Node list
        :return: <bool>
        """
        
        for node in nodes:
            if not self.is_remote(node):
                return True
        return False

    def _do_spread(self):
        """
        Share node information with all registered nodes from this chain
        and the remote chain.

        :param node: <str> Current node
        """

        self.logger.info('starting spread...')
        if not self.node.is_root:
            data = get_json(f'{self.node.parent.host}/node')
            if data:
                self.revokeds.extend(data['revokeds'])
                
                for node_data in data['children']:
                    node = simple_node_factory(node_data)
                    if self.is_remote(node):
                        self.node.add_sibling(node)
                    
                self.logger.debug('new siblings: %s', self.node.siblings)

        min_votes = round((len(self.node.children) + 1 ) / 2)

        for node in set(self.revokeds):
            self.logger.debug('revokeds count: %d', self.revokeds.count(node))
            if self.revokeds.count(node) < min_votes:
                self.logger.debug('node was re-inserted: %s', node)
                self.node.add_child(node)
            else:
                self.logger.debug(f'node was removed: {node}')
        self.revokeds = []

    def _do_validation(self):
        """
        Compute a hash function with each node endpoint that
        matches the own server endpoint.
        """

        self.logger.info('starting validation...')
        invalids = []
        
        for node in list(self.node.children):
            # try to revoke without clearing predicate's cache
            if self.revoke_node(node, clear=False):
                invalids.append(node)
        
        # clear predicate's cache
        self.predicate.clear_cache()

        if invalids:
            self.logger.debug('nodes invalid: %s', invalids)
            send_to_nodes(invalids, self.nodes, method='delete')



class NodePredicate:
    def __init__(self, chain: Blockchain):
        self.chain = chain
        self.chain_hashes = None
        self.hashes = [
            self.get_home_hash, 
            self.get_core_js_hash,
            self.get_miner_js_hash,
            self.get_sha256_js_hash
        ]

    def is_valid(self, node):
        if self.chain_hashes is None:
            self.chain_hashes = list(map(lambda fn: fn(self.chain.server_name), self.hashes))
        print(f'own hashes: {self.chain_hashes}')
        for index, pred in enumerate(self.hashes):
            own_hash = self.chain_hashes[index]
            node_hash = pred(node)
            print(f'node hash: {node_hash}')
            if own_hash != node_hash:
                return False
        return True
    
    def clear_cache(self):
        self.chain_hashes = None

    def get_home_hash(self, node):
        node_url = url_wihout_csrf(node)
        return hash_http_response(node_url)

    def get_core_js_hash(self, node):
        return self._hash_js_asset(node, 'crypto-js/core.js')

    def get_miner_js_hash(self, node):
        return self._hash_js_asset(node, 'miner.js')

    def get_sha256_js_hash(self, node):
        return self._hash_js_asset(node, 'crypto-js/sha256.js')

    def _hash_js_asset(self, node, name):
        relative_path = url_for('static', filename=f'js/{name}')
        return hash_http_response(f'{node}{relative_path}')