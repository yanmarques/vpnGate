import hashlib
import json
from time import time
from urllib.parse import urlparse
from traceback import print_tb

import requests
from flask import url_for


# Maximum time for http connection
DEFAULT_TIMEOUT = 3.5

DEFAULT_CONFIG = {
    'difficulty': 4, 
    'validation_time': 30,
    'spreading_time': 60
}


def send_to_nodes(target, node_list, method='post'):
    payload = dict(nodes=target)
    caller = getattr(requests, method)
    assert caller is not None, 'Invalid method'
    for node in node_list:
        try:
            response = caller(f'{node}/node', 
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


def parse_host(address):
    parsed_url = urlparse(address.rstrip('/'))

    if parsed_url.netloc:
        return f'{parsed_url.scheme}://{parsed_url.netloc}'
    
    if parsed_url.path:
        # Accepts an URL without scheme
        return f'http://{parsed_url.path}'
    
    raise ValueError('Invalid URL')


def print_exception(exception):
    print_tb(exception.__traceback__)
    print(str(exception))


class Blockchain:
    """
    The blockchain where the server will run the transactions.
    """

    def __init__(self, server_name, config: dict=None):
        self.set_name(server_name)
        self.current_transactions, self.chain = [], []
        self.nodes, self.revokeds, self.timers = set(), [], [0, 0]
        self.predicate = NodePredicate(self)

        if config is None:
            config = DEFAULT_CONFIG
        else:
            # merge with default configuration
            cfg_keys = config.keys()
            for key, value in DEFAULT_CONFIG.items():
                if not key in cfg_keys:
                    config[key] = value
            
        self.config = config
        print(f'configuration: {config}')
        # Create the genesis block
        self.new_block(previous_hash='1', timestamp=1, proof=100)

    def set_name(self, address):
        self.server_name = parse_host(address)

    def register_node(self, address, spread=True):
        """
        Add a new node to the list of nodes

        :param address: Address of node
        """

        node_url = parse_host(address)
        print(f'to register: {node_url}')
        if self.is_remote(node_url):
            self.nodes.add(node_url)

    def revoke_node(self, node, clear=True):
        """
        Remove a node from neighborhood and return wheter was revoked.

        :param node: <str> Address of node
        :param clear: <bool> Indicates wheter to clear predicate cache
        :return: <bool> 
        """

        status = False
        if node in self.nodes and not self.predicate.is_valid(node):
            print(f'node revoked: {node}')
            self.nodes.remove(node)
            self.revokeds.append(node)
            status = True
        if clear:
            self.predicate.clear_cache()
        return status

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
            print(f'{last_block}')
            print(f'{block}')
            # Check that the hash of the block is correct
            last_block_hash = self.hash(last_block)
            if block['previous_hash'] != last_block_hash:
                return False

            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof'], last_block_hash):
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

        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        new_chain = None

        # Grab and verify the chains from all the nodes in our network
        for node in list(self.nodes):
            data = get_json(f'{node}/chain')
            if data:
                length, chain = data['length'], data['chain']

                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
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
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, content):
        """
        Creates a new transaction to go into the next mined Block

        :param content: Content of new transaction
        :return: The index of the Block that will hold this transaction
        """
        
        self.current_transactions.append(content)
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

    def proof_of_work(self, last_block):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: <dict> last Block
        :return: A valid proof of work
        """

        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    def valid_proof(self, last_proof, proof, last_hash):
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

    def is_remote(self, node):
        """
        Defines wheter the given node is not the current server.

        :param node: <str> Node's url to check  
        :return: <bool>
        """
        
        return not node.endswith(self.server_name)

    def spread_neighbors(self):
        """
        Share node information with all registered nodes from this chain
        and the remote chain.

        :param node: <str> Current node
        """

        if self.check_timer(0, 'spreading_time') is False:
            return

        for node in list(self.nodes):
            data = get_json(f'{node}/node')
            if not data:
                self.revokeds.append(node)
                continue

            self.revokeds.extend(data['revokeds'])
            new_neighbours = set(data['nodes'])
            diff = list(new_neighbours - self.nodes)
    
            print('starting spread...')        
            if diff:
                print(f'has differences: {diff}')
                remote_needs_local = not self._has_own_server(new_neighbours) 

                if len(self.nodes) > len(new_neighbours):
                    if remote_needs_local:
                        diff.add(self.server_name)
                    print('sending current configuration to this node')
                    send_to_nodes(diff, [node])
                else:
                    print('registering the difference with us')
                    list(map(self.register_node, diff))
                    if remote_needs_local:
                        print(f'sending local name: {node}')
                        send_to_nodes([self.server_name], [node])

        min_votes = round(len(self.nodes) / 2)
        for node in set(self.revokeds):
            if self.revokeds.count(node) < min_votes:
                self.nodes.add(node)
            else:
                print(f'node was removed: {node}')
        self.revokeds = []
    
    def validate_neighbors(self):
        """
        Compute a hash function with each node endpoint that
        matches the own server endpoint.
        """

        if self.check_timer(1, 'validation_time') is False:
            return

        invalids = []
        
        for node in list(self.nodes):
            # try to revoke without clearing predicate's cache
            if self.revoke_node(node, clear=False):
                invalids.append(node)
        
        # clear predicate's cache
        self.predicate.clear_cache()

        if invalids:
            print(f'nodes invalid: {invalids}')
            send_to_nodes(invalids, self.nodes, method='delete')

    def check_timer(self, index, max_time):
        if index < len(self.timers) and \
                    (time() - self.timers[index]) <= self.config[max_time]:
            return False

        # initialize timer
        self.timers[index] = time()
        return True

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