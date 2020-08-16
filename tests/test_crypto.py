from . import util
from vpngate.util import crypto

import uuid
import hashlib


def test_generate_valid_uuid_size():
    rand_uuid = crypto.hex_uuid()
    assert len(rand_uuid) == 32


def test_generate_valid_hexadecimal_value():
    rand_uuid = crypto.hex_uuid()
    int(rand_uuid, 16)


def test_hashsum_of_similar_objects_gives_the_same_sum():
    foo = util.get_block()
    bar = util.get_block()

    foo_hashsum = crypto.block_hashsum(foo)
    bar_hashsum = crypto.block_hashsum(bar)

    assert foo_hashsum == bar_hashsum


def test_hashsum_of_non_similar_objects_gives_different_sums():
    foo = util.get_block(index=1)
    bar = util.get_block(index=2)

    foo_hashsum = crypto.block_hashsum(foo)
    bar_hashsum = crypto.block_hashsum(bar)

    assert foo_hashsum != bar_hashsum


def test_hashsum_of_unsorted_keys_gives_the_same_sum():
    class fake_block:
        items_to_ret = [
            dict(something=True, another='baz'),
            dict(another='baz', something=True)
        ]
        
        @staticmethod
        def to_dict():
            return fake_block.items_to_ret.pop()

    foo_hashsum = crypto.block_hashsum(fake_block)
    bar_hashsum = crypto.block_hashsum(fake_block)

    assert foo_hashsum == bar_hashsum


def test_hashsum_with_custom_hashing_implementation():
    foo_hashsum = crypto.block_hashsum(util.get_block(), impl=hashlib.md5)

    # as MD5 generates a fixed 32 bytes string
    assert len(foo_hashsum) == 32


def test_key_pair_verifies_the_signed_data():
    data = b'some random data'
    pair = crypto.KeyPair()

    signature = pair.sign(data)
    assert pair.was_signed_by_me(signature, data)


def test_key_pair_loaded_private_key_is_the_same_generated_earlier():
    old_pair = crypto.KeyPair()
    old_pk = old_pair.public_to_base64()

    private_bytes = old_pair.private_to_pem()
    new_pair = crypto.KeyPair.from_pem_private_bytes(private_bytes)
    assert old_pk == new_pair.public_to_base64()


def test_key_pair_can_verify_a_signature_from_other_key():
    data = b'some random data'
    pair = crypto.KeyPair()

    pair_pk = pair.public_to_base64()
    signature = pair.sign(data)

    assert crypto.KeyPair.was_signed_from_base64(pair_pk, signature, data)