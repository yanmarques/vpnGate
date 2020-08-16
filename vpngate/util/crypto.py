from vpngate.util import building
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.exceptions import InvalidSignature

import json
import hashlib
import base64


def block_hashsum(block: building.Block, impl=hashlib.sha256):
    """Calculates the hash from the string representation of the object."""

    # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
    block_bytes = json.dumps(block.to_dict(), sort_keys=True).encode()
    
    hashsum = impl(block_bytes)
    return hashsum.hexdigest() 


class AsymmetricVerifier:
    """
    Holds a the asymmetric public key, used to verify signatures. It also contains 
    methods to dump and load public keys.

    Usage:
        >>> from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        >>> sk = Ed25519PrivateKey.generate()
        >>> pk = AsymmetricVerifier(sk.public_key())
        >>> pk.public_to_b64()
        b'RuTGMuR+93aIVQLsa0bZzJOR7QUXNCyPDpx6qAUMB6g='
    """

    def __init__(self, pubkey: ed25519.Ed25519PublicKey):
        self.pubkey = pubkey

    @classmethod
    def from_public_b64(cls, public_b64: bytes):
        """
        Instantiate using the public key as base64 format.
        """

        return cls(AsymmetricVerifier.b64_to_public_key(public_b64))

    def public_to_bytes(self) -> bytes:
        """
        Get the public key as UTF-8 bytes.
        """

        return self.pubkey.public_bytes(encoding=serialization.Encoding.Raw,
                                        format=serialization.PublicFormat.Raw)

    def public_to_b64(self) -> bytes:
        """
        Get the public key encoded as base64 format. Usefull when saving it using
        text format, or sending over the network.
        """

        return base64.b64encode(self.public_to_bytes())

    @staticmethod
    def b64_to_public_key(data: bytes) -> ed25519.Ed25519PublicKey:
        """
        Get a public key from the base64 encoded data.

        :param data: Public key as base64
        """

        public_bytes = base64.b64decode(data)
        return ed25519.Ed25519PublicKey.from_public_bytes(public_bytes)

    @staticmethod
    def was_signed(public_key: ed25519.Ed25519PublicKey, 
                   signature: bytes, 
                   data: bytes) -> bool:
        """
        Determine wheter the given signature is valid for the given data. The assigner's 
        public key is used to verify such thing.

        :param public_b64: The public of the assigner
        :param signature: Signature generated by some private key
        :param data: Data to check against the signature
        """

        try:
            public_key.verify(signature, data)
            return True
        except InvalidSignature:
            return False

    def was_signed_by_me(self, signature: bytes, data: bytes) -> bool:
        """
        Calls AsymmetricKeyPair.was_signed() using the class publick key.

        :param signature: Signature generated by some private key
        :param data: Data to check against the signature
        """

        return AsymmetricKeyPair.was_signed(self.pubkey, signature, data)


class AsymmetricKeyPair(AsymmetricVerifier):
    """
    Holds a pair of asymetric cryptographic keys. These are used to both sign
    and verify signatures. It also contains methods to dump and load keys.

    Default algorithm: ed25519
    Usage:
        >>> keys = AsymmetricKeyPair()
        >>> signature = keys.sign(b'thanks cryptography')
        >>> keys.was_assigned_by_me(signature, b'thanks cryptography')
        True

    """

    def __init__(self, private: ed25519.Ed25519PrivateKey=None):
        self.__privkey = private or ed25519.Ed25519PrivateKey.generate()

        # the public key is always generated from the private key
        super().__init__(self.__privkey.public_key())

    @classmethod
    def from_pem_private_bytes(cls, private: bytes):
        """
        Instantiate using the private keys bytes data.

        :param private: The data of the private key
        """

        return cls(private=serialization.load_pem_private_key(private, 
                                                              None, 
                                                              backend=default_backend()))

    def private_to_pem(self) -> bytes:
        """
        Get the private key in the PEM encoding, using the PKCS8 format in plain text.
        """

        return self.__privkey.private_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.PKCS8,
                                            encryption_algorithm=serialization.NoEncryption())

    def sign(self, data: bytes) -> bytes:
        """
        Create a signature of the given data and return the signature as UTF-8 bytes.

        :param data: The data to sign
        """

        return self.__privkey.sign(data)