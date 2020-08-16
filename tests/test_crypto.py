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