from vpngate.util import building

import json
import secrets
import uuid
import hashlib


def hex_uuid():
    """Returns an hexadecimal representation of an random UUID."""

    unique_id = uuid.uuid4()
    return unique_id.hex


def block_hashsum(block: building.Block, impl=hashlib.sha256):
    """Calculates the hash from the string representation of the object."""

    # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
    block_bytes = json.dumps(block.to_dict(), sort_keys=True).encode()
    
    hashsum = impl(block_bytes)
    return hashsum.hexdigest() 
