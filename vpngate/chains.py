from .util import building
from .p2p import Peer

from typing import Dict, List
from dataclasses import dataclass, field


@dataclass
class RootNode:
    """
    The RootNode is the first block in the tree chain. By default the block
    is the genesis block and it does not have a parent related with, but may
    have a bunch of children, also called chains.

    Each chain is independent and is associated with a Peer.
    """

    block: building.Block = field(default_factory=building.Block.genesis)
    chains: Dict[Peer, List[building.Block]] = field(default_factory=dict)


@dataclass
class Tree:
    root: RootNode = field(default_factory=RootNode)

    @property
    def length(self) -> int:
        """Determine the length of chains of the root node."""

        return len(self.root.chains)

    def items(self) -> list:
        """Get a list of (peer, chain) for looping over."""

        return self.root.chains.items()

    def add(self, peer: Peer, block: building.Block):
        """
        Add a new block at the peer chain, taking care when a new chain
        should be created.

        :param peer: A peer responsable of the block
        :param block: The next block with data
        """

        if not self.has(peer):
            self.root.chains[peer] = []

        chain = self.root.chains[peer]
        chain.append(block)

    def get(self, peer: Peer) -> list:
        """
        Return the full chain of the given peer

        :param peer: The peer of the chains
        """

        stock_chain = self.root.chains.get(peer, [])
        return [self.root.block] + stock_chain

    def has(self, peer: Peer) -> bool:
        """
        Determine wheter the peer already has a chain registered.

        :param peer: The peer to check against
        """

        return peer in self.root.chains
