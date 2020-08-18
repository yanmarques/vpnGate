from dataclasses import dataclass, field, asdict
import time


@dataclass
class Block:
    """
    This class represents each component in the chain. It holds data
    about:
        - the index number of the current block
        - hash of the last block in chain
        - the actual content in the transactions
        - when the block was assigned
    """

    index: int
    transactions: list
    previous_hash: str
    timestamp: time.time = field(default_factory=time.time)

    @classmethod
    def genesis(cls, **kwargs):
        """Create the default first block in the chain"""

        defaults = dict(index=0,
                        transactions=[],
                        previous_hash='1',
                        timestamp=-1)

        defaults.update(**kwargs)

        return cls(**defaults)

    def to_dict(self) -> dict:
        """Return a dict representing this dataclass."""

        return asdict(self)


@dataclass
class PoWBlock(Block):
    proof: int = field(default=100)
