from .util import crypto
from typing import Set, Any
from dataclasses import dataclass, field


@dataclass
class Peer:
    identifier: field(default_factory=crypto.hex_uuid)
    children: Set[Any]
    parent: Any