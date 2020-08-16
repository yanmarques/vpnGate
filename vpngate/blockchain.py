from .util import crypto
from .tree import Tree
from .p2p import Peer

from typing import List, Tuple
from dataclasses import dataclass, field
import hashlib
import time


@dataclass
class Block:
    """
    This class represents each component in the chain. It holds data
    about:
        - last block in chain 
        - the proof to create the block
        - the actual content in the transactions
        - when the block was assigned 
    """

    index: int
    transactions: List
    proof: int
    previous_hash: str
    timestamp: time.time = field(default_factory=time.time)

    @classmethod
    def genesis(cls):
        """Create the default first block in the chain"""

        return cls(index=1,
                   transactions=[],
                   proof=100,
                   previous_hash='1',
                   timestamp=-1)


@dataclass
class BlocksManager:
    """
    The base blockchain class that handles running and verifying blocks of data.
    """
    
    name: str
    difficulty: int

    peer: Peer

    transactions: List = field(default_factory=list)
    chain: Tree = field(default_factory=Tree)

    @property
    def last_block(self) -> Block:
        """
        Get the last block on the chain.

        :return: <dict>
        """
        
        return self.chain.get(self.peer)[-1]

    @property
    def next_index(self) -> int:
        """
        Get the index of the next block in the chain.
        """

        return self.last_block.index + 1

    async def get_info(self, block: Block=None) -> Tuple(int, str):
        """
        Get the last proof of work and the hash of the last
        block on the chain.

        :return: Proof of work and the hash
        """

        last_block = block or self.last_block
        last_block_sum = await crypto.block_hashsum(last_block) 
        return last_block.proof, last_block_sum

    async def new_block(self, 
                        proof: int, 
                        previous_hash: str=None, 
                        timestamp: time.time=None) -> Block:
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        """

        block = Block(index=self.next_index,
                      transactions=self.transactions,
                      proof=proof,
                      previous_hash=previous_hash or (await self.get_info())[1])

        # Reset the current transactions
        self.transactions = []

        self.chain.add(self.peer, block)
        return block

    def new_transaction(self, content) -> int:
        """
        Creates a new transaction to go into the next mined Block

        :param content: Content of new transaction
        :return: The index of the Block that will hold this transaction
        """
        
        self.transactions.append(content) 
        return self.next_index

    async def proof_of_work(self, last_block: Block=None) -> int:
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: last Block
        :return: A valid proof of work
        """

        last_proof, last_hash = await self.get_info(block=last_block)

        proof = 0
        while not await self.is_valid_proof(proof, last_proof, last_hash):
            proof += 1

        return proof

    def is_valid_proof(self, 
                       proof: int, 
                       last_proof: int, 
                       last_hash: str) -> bool:
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

    async def has_valid_proof(self, proof: int) -> bool:
        """
        Determine wheter the proof of work is valid against this blockchain 
 
        :param proof: Current Proof
        """

        return self.is_valid_proof(proof, *await self.get_info())

