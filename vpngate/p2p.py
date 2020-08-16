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
        """
        Get a nice representation of the public key.
        """

        return self.keys.public_to_base64().decode('utf-8')

    def __eq__(self, another_obj) -> bool:
        """
        Determines wheter the given peer equals the local peer.
        The peers identifier is used to make suck comparison.

        :param another_obj: Some object to compare 
        """

        return self.identifier == another_peer.identifier

    def __hash__(self) -> int:
        """
        Returns an integer representing uniquely this object. The public
        key bytes are used as an integer.
        """

        return int.from_bytes(self.keys.public_to_bytes(), 'little')