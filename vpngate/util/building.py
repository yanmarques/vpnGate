from dataclasses import dataclass, field, asdict
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
    transactions: list
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
                
    def to_dict(self) -> dict:
        """Return a dict representing this dataclass."""

        return asdict(self)