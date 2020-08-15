from vpngate.util import crypto
from vpngate.blockchain import Blocks
import pytest


@pytest.mark.asyncio
async def test_new_object_contains_the_genesis_block():
    blocks = await Blocks.create(name='foo', difficulty=1)
    assert_is_genesis_block(blocks.last_block)


@pytest.mark.asyncio
async def test_an_empty_chain_is_valid():
    blocks = await Blocks.create(name='foo', difficulty=1)
    assert blocks.is_valid_chain(blocks.chain)


@pytest.mark.asyncio
async def test_genesis_block_is_not_created_with_non_empty_chain():
    chain = ['something']

    blocks = await Blocks.create(name='foo', difficulty=1, chain=chain)
    assert blocks.chain == chain


@pytest.mark.asyncio
async def test_get_last_info_returns_the_newest_proof():
    expected_proof = 321
    
    blocks = await Blocks.create(name='foo', difficulty=1)
    await blocks.new_block(expected_proof, 'bar')

    proof, _ = await blocks.get_last_info()

    assert proof == expected_proof


@pytest.mark.asyncio
async def test_last_info_of_new_blockchain_returns_a_hashsum_of_the_genesis(monkeypatch):
    expected_hash = 'baz'
    
    async def my_hashsum(block, **kwargs):
        assert_is_genesis_block(block)
        return expected_hash

    monkeypatch.setattr(crypto, 'block_hashsum', my_hashsum)

    blocks = await Blocks.create(name='foo', difficulty=1)
    _, last_hash = await blocks.get_last_info()

    assert last_hash == expected_hash


def assert_is_genesis_block(block):
    assert block['previous_hash'] == '1'
    assert block['proof'] == 100
    assert block['index'] == 1
    assert block['timestamp'] == -1