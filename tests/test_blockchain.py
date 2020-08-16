from .util import get_blocks_manager, assert_is_genesis_block
from vpngate.util import crypto


def test_new_object_contains_the_genesis_block():
    blocks = get_blocks_manager()
    assert_is_genesis_block(blocks.last_block)


def test_genesis_block_is_not_created_with_non_empty_chain():
    chain = ['something']

    blocks = get_blocks_manager(chain=chain)
    assert blocks.chain == chain


def test_get_last_info_returns_the_newest_proof():
    expected_proof = 321
    
    blocks = get_blocks_manager()
    blocks.new_block(expected_proof, 'bar')

    proof, _ = blocks.get_info()

    assert proof == expected_proof


def test_last_info_of_new_blockchain_returns_a_hashsum_of_the_genesis(monkeypatch):
    expected_hash = 'baz'
    
    def my_hashsum(block, **kwargs):
        assert_is_genesis_block(block)
        return expected_hash

    monkeypatch.setattr(crypto, 'block_hashsum', my_hashsum)

    blocks = get_blocks_manager()
    _, last_hash = blocks.get_info()

    assert last_hash == expected_hash