from vpngate.util import building
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

import json
import uuid
import hashlib
import base64


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


class KeyPair:
    def __init__(self, private: ed25519.Ed25519PrivateKey=None):
        self.__private = private or ed25519.Ed25519PrivateKey.generate()
        self.public = self.__private.public_key()

    @classmethod
    def from_pem_private_bytes(cls, private: bytes):
        return cls(private=serialization.load_pem_private_key(private, 
                                                              None, 
                                                              backend=default_backend()))

    def private_to_pem(self) -> bytes:
        return self.__private.private_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.PKCS8,
                                            encryption_algorithm=serialization.NoEncryption())

    def public_to_base64(self) -> bytes:
        raw_bytes = self.public.public_bytes(encoding=serialization.Encoding.Raw,
                                             format=serialization.PublicFormat.Raw)
        return base64.b64encode(raw_bytes)

    def sign(self, data: bytes) -> bytes:
        return self.__private.sign(data)

    @staticmethod
    def was_signed_from_base64(public_b64: bytes, signature: bytes, data: bytes) -> bool:
        public_bytes = base64.b64decode(public_b64)
        pk = ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)
        return KeyPair.was_signed(pk, signature, data)

    @staticmethod
    def was_signed(public_key: ed25519.Ed25519PublicKey, 
                   signature: bytes, 
                   data: bytes) -> bool:
        try:
            public_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False

    def was_signed_by_me(self, signature: bytes, data: bytes) -> bool:
        return KeyPair.was_signed(self.public, signature, data)