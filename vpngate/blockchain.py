from .util import crypto

from typing import List
from dataclasses import dataclass, field
import hashlib
import time


@dataclass
class Blocks:
    """
    The base blockchain class that handles running and verifying blocks of data.
    """
    
    name: str
    difficulty: int

    transactions: List = field(default_factory=list)
    chain: List = field(default_factory=list)

    @classmethod
    async def create(cls, **config):
        """Default factory for creating a full-featured blockchain"""

        blocks = cls(**config)
        if not len(blocks.chain):
            await blocks.create_genesis()
        return blocks

    @property
    def last_block(self):
        """
        Get the last block on the chain.

        :return: <dict>
        """
        
        return self.chain[-1]

    async def create_genesis(self):
        """Create the default first block of the chain"""

        await self.new_block(previous_hash='1', timestamp=-1, proof=100)

    async def get_last_info(self):
        """
        Get the last proof of work and the hash of the last
        block on the chain.

        :return: Proof of work and the hash
        """

        last_block = self.last_block
        last_block_sum = await crypto.block_hashsum(last_block) 
        return last_block['proof'], last_block_sum

    async def accept_chain(self, chain: list):
        """
        Compare the received chain with our chain and replace it
        when necessary.

        :param chain: A remote chain
        :return: Wheter our chain was replaced
        """

        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Check if the length is longer and the chain is valid
        if len(chain) > max_length and await self.is_valid_chain(chain):
            self.chain = chain
            return True

        return False

    async def new_block(self, proof: int, previous_hash: str, timestamp: time.time=None):
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        :return: New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': timestamp or time.time(),
            'transactions': self.transactions,
            'proof': proof,
            'previous_hash': previous_hash or (await self.get_last_info())[1],
        }

        # Reset the current transactions
        self.transactions = []

        self.chain.append(block)
        return block

    async def new_transaction(self, content):
        """
        Creates a new transaction to go into the next mined Block

        :param content: Content of new transaction
        :return: <int> The index of the Block that will hold this transaction
        """
        
        self.transactions.append(content) 
        return self.last_block['index'] + 1

    async def proof_of_work(self, last_block: dict=None):
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: last Block
        :return: <int> A valid proof of work
        """

        last_block = last_block or self.last_block
        last_proof = last_block['proof']
        
        last_hash = await crypto.block_hashsum(last_block)

        proof = 0
        while not await self.is_valid_proof(proof, last_proof, last_hash):
            proof += 1

        return proof

    async def is_valid_chain(self, chain: list):
        """
        Determine if a given blockchain is valid

        :param chain: A blockchain
        :return <bool>
        """

        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]

            # Check that the hash of the block is correct
            last_block_hash = await crypto.block_hashsum(last_block)
            
            if block['previous_hash'] != last_block_hash:
                return False

            is_valid = await self.is_valid_proof(block['proof'], 
                                                 last_block['proof'], 
                                                 last_block_hash)

            # Check that the Proof of Work is correct
            if not is_valid:
                return False

            last_block = block
            current_index += 1

        return True


    async def is_valid_proof(self, 
                             proof: int, 
                             last_proof: int, 
                             last_hash: str):
        """
        Determine wheter the proof of work is valid 
 
        :param last_proof: Previous Proof
        :param proof: Current Proof
        :param last_hash: The hash of the Previous Block
        :return: <bool>
        """

        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()

        return guess_hash[-self.difficulty:] == "0" * self.difficulty

    async def has_valid_proof(self, proof: int):
        """
        Determine wheter the proof of work is valid against this blockchain 
 
        :param proof: Current Proof
        :return: <bool>
        """

        return await self.is_valid_proof(proof, *await self.get_last_info())

