from .util import crypto, building
from .chains import Tree, RootNode
from .p2p import Peer

from typing import Tuple, Callable
from dataclasses import dataclass, field
import hashlib
import time


@dataclass
class BlocksManager:
    """
    The base blockchain class that handles running and verifying blocks of data.
    """
    
    name: str
    peer: Peer

    transactions: list = field(default_factory=list)
    chain: Tree = field(default_factory=Tree)

    block_factory: Callable = building.Block

    @property
    def last_block(self) -> building.Block:
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


    def new_block(self, **kwargs) -> building.Block:
        """
        Create a new Block in the Blockchain

        :param proof: The proof given by the Proof of Work algorithm
        :param previous_hash: Hash of previous Block
        """

        if 'previous_hash' in kwargs:
            kwargs.setdefault('previous_hash', 
                              crypto.block_hashsum(self.last_block))

        # this are overwritten
        kwargs.update(index=self.next_index, transactions=self.transactions)

        block = self.block_factory(**kwargs)

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


def pow_chain():
    root = RootNode(block=building.PoWBlock.genesis())
    return Tree(root=root)


@dataclass
class PoWBlockChain(BlocksManager):
    difficulty: int
    block_factory: Callable = building.PoWBlock
    chain: Tree = field(default_factory=pow_chain)

    def new_block(self, **kwargs) -> building.Block:
        """
        Rewrite new_block function to allow using a proof_of_work
        """

        if 'proof' not in kwargs:
            kwargs.update(proof=self.proof_of_work())
        return super().new_block(**kwargs)

    def get_info(self, block: building.PoWBlock=None) -> Tuple[int, str]:
        """
        Get the last proof of work and the hash of the last
        block on the chain.

        :return: Proof of work and the hash
        """

        last_block = block or self.last_block
        last_block_sum = crypto.block_hashsum(last_block) 
        return last_block.proof, last_block_sum

    def proof_of_work(self, last_block: building.PoWBlock=None) -> int:
        """
        Simple Proof of Work Algorithm:

         - Find a number p' such that hash(pp') contains leading 4 zeroes
         - Where p is the previous proof, and p' is the new proof
         
        :param last_block: last Block
        :return: A valid proof of work
        """

        last_proof, last_hash = self.get_info(block=last_block)

        proof = 0
        while not PoWBlockChain.is_valid_proof(self.difficulty, proof, last_proof, last_hash):
            proof += 1

        return proof

    @staticmethod
    def is_valid_proof(difficulty: int, 
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

        return guess_hash[-difficulty:] == "0" * difficulty

    def has_valid_proof(self, proof: int) -> bool:
        """
        Determine wheter the proof of work is valid against this blockchain 
 
        :param proof: Current Proof
        """

        return PoWBlockChain.is_valid_proof(self.difficulty, proof, *self.get_info())
