from .util.crypto import KeyPair

from typing import Set, Any
from dataclasses import dataclass, field


@dataclass
class Peer:
    address: str
    keys: KeyPair = field(default_factory=KeyPair)
    children: Set[Any] = field(default_factory=set)
    siblings: Set[Any] = field(default_factory=set)
    parent: Any = None

    @property
    def identifier(self) -> str:
        return self.keys.public_to_base64().decode('utf-8')

    def __eq__(self, another_peer) -> bool:
        return self.identifier == another_peer.identifier

    def __hash__(self) -> int:
        return int.from_bytes(self.keys.public_to_bytes(), 'little')