import hashlib
import json
from time import time
from urllib.parse import urlparse

import requests


def send_nodes(target, node_list):
    payload = dict(nodes=target)
    for node in node_list:
        try:
            response = requests.post(f'{node}/node', data=payload)
            if response.status_code != 201:
                print(response.text)
        except Exception as exc:
            print(str(exc))


def get_json(url):
    response = requests.get(url)
    print(f'received response for {url}: {response}')
    if response.status_code == 200:
        return response.json()


class Blockchain:
    """
    The blockchain where the server will run the transactions.
    """

    def __init__(self, server_name=None, dificulty=4):
        self.server_name = server_name
        self.dificulty = dificulty
        self.current_transactions = []
        self.chain = []
        self.nodes, self.queue = set(), set()

        # Create the genesis block
        self.new_block(previous_hash='1', proof=100)

    def register_node(self, address, spread=True):
        """
        Add a new node to the list of nodes

        :param address: Address of node
        """

        parsed_url = urlparse(address.rstrip('/'))

        if parsed_url.netloc:
            node_url = f'{parsed_url.scheme}://{parsed_url.netloc}'
        elif parsed_url.path:
            # Accepts an URL without scheme
            node_url = f'http://{parsed_url.path}'
        else:
            raise ValueError('Invalid URL')
        print(f'to register: {node_url}')
        if self.is_remote(node_url):
            self.nodes.add(node_url)

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
            print("\n-----------\n")
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
            self._spread(node)
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

    def new_block(self, proof, previous_hash):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }

        # Reset the current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def new_transaction(self, email):
        """
        Creates a new transaction to go into the next mined Block

        :param sender: Address of the Sender
        :return: The index of the Block that will hold this transaction
        """
        
        self.current_transactions.append(email)
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
        return guess_hash[-self.dificulty:] == "0" * self.dificulty

    def is_remote(self, node):
        """
        Defines wheter the given node is not the current server.

        :param node: <str> Node's url to check  
        :return: <bool>
        """
        
        return not node.endswith(self.server_name)

    def _spread(self, node):
        """
        Share node information with all registered nodes from this chain
        and the remote chain.

        :param node: <str> Current node
        """

        data = get_json(f'{node}/node')
        if not data:
            return

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
                send_nodes(diff, [node])
            else:
                print('registering the difference with us')
                list(map(self.register_node, diff))
                if remote_needs_local:
                    print(f'sending local name: {node}')
                    send_nodes([self.server_name], self.nodes)

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