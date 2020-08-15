from vpngate.util import crypto
import pytest

import uuid
import hashlib


@pytest.mark.asyncio
async def test_generate_valid_uuid_size():
    rand_uuid = await crypto.hex_uuid()
    assert len(rand_uuid) == 32


@pytest.mark.asyncio
async def test_hashsum_of_similar_objects_gives_the_same_sum():
    foo = dict(something=True)
    bar = dict(something=True)

    foo_hashsum = await crypto.block_hashsum(foo)
    bar_hashsum = await crypto.block_hashsum(bar)

    assert foo_hashsum == bar_hashsum


@pytest.mark.asyncio
async def test_hashsum_of_non_similar_objects_gives_different_sums():
    foo = dict(something=True)
    bar = dict(something=False)

    foo_hashsum = await crypto.block_hashsum(foo)
    bar_hashsum = await crypto.block_hashsum(bar)

    assert foo_hashsum != bar_hashsum


@pytest.mark.asyncio
async def test_hashsum_of_unsorted_keys_gives_the_same_sum():
    foo = dict(something=True, another='baz')
    bar = dict(another='baz', something=True)

    foo_hashsum = await crypto.block_hashsum(foo)
    bar_hashsum = await crypto.block_hashsum(bar)

    assert foo_hashsum == bar_hashsum


@pytest.mark.asyncio
async def test_hashsum_with_custom_hashing_implementation():
    foo = dict(something=True)

    foo_hashsum = await crypto.block_hashsum(foo, impl=hashlib.md5)

    # as MD5 generates a fixed 32 bytes string
    assert len(foo_hashsum) == 32