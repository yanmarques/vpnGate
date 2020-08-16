from .util import crypto

from typing import Set, Any
from dataclasses import dataclass, field


@dataclass
class Peer:
    address: str
    identifier: str = field(default_factory=crypto.hex_uuid)
    children: Set[Any] = field(default_factory=set)
    siblings: Set[Any] = field(default_factory=set)
    parent: Any = None

    def __eq__(self, another_peer):
        return self.identifier == another_peer.identifier

    def __hash__(self):
        return int(self.identifier, 16)