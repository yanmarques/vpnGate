from .util import *
from vpngate.util import crypto, exceptions
import pytest

from unittest.mock import Mock
import time
import hashlib


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


def test_last_info_of_new_blocksmngr_returns_a_hashsum_of_the_genesis(monkeypatch):
    expected_hash = 'baz'
    
    def my_hashsum(block, **kwargs):
        assert_is_genesis_block(block)
        return expected_hash

    monkeypatch.setattr(crypto, 'block_hashsum', my_hashsum)

    blocks = get_blocks_manager()
    _, last_hash = blocks.get_info()

    assert last_hash == expected_hash


def test_newly_created_block_returns_a_valid_first_block():
    blocks = get_blocks_manager()
    block = blocks.new_block()
    assert block.index == 1
    assert block.previous_hash == crypto.block_hashsum(Block.genesis())
    assert block.transactions == []
    assert isinstance(block.timestamp, float)


def test_new_transactions_are_provided_in_the_new_created_block():
    expected_transactions = ['foo', 'bar', dict(baz=1)]
    blocks = get_blocks_manager()

    list(map(blocks.new_transaction, expected_transactions))
    
    assert blocks.new_block().transactions == expected_transactions


def test_new_transaction_returns_the_index_of_the_next_block():
    blocks = get_blocks_manager()
    for i in range(1, 3):
        assert blocks.new_transaction('foo') == i
        blocks.new_block()


def test_pow_blockchain_uses_a_pow_block():
    blockchain = get_pow_blockchain()
    assert_is_genesis_block(blockchain.last_block)
    assert blockchain.last_block.proof == 100


def test_pow_blockchain_using_a_proof_to_create_a_new_block(monkeypatch):
    expected_proof = 'something_that_is_not_a_proof'
    blockchain = get_pow_blockchain()

    monkeypatch.setattr(blockchain, 'has_valid_proof', lambda *args: True)
    block = blockchain.new_block(proof=expected_proof)

    assert block.proof == expected_proof


def test_pow_blockchain_fails_creating_a_new_block_without_a_proof():
    blochain = get_pow_blockchain()
    with pytest.raises(TypeError):
        blochain.new_block()


def test_pow_blockchain_fails_creating_a_new_block_with_an_invalid_a_proof():
    blochain = get_pow_blockchain()
    with pytest.raises(exceptions.InvalidProofOfWork):
        blochain.new_block(proof='abosolutely_wrong_proof')


def test_pow_blockchain_returns_a_pair_with_proof_and_hash(monkeypatch):
    expected_proof = 'bar'
    blockchain = get_pow_blockchain()

    monkeypatch.setattr(blockchain, 'has_valid_proof', lambda *args: True)
    newly_block = blockchain.new_block(proof=expected_proof)

    last_proof, last_hash = blockchain.get_info()
    assert last_proof == expected_proof
    assert last_hash == crypto.block_hashsum(newly_block)


def test_pow_block_calculates_a_valid_proof(monkeypatch):
    blocks = get_pow_blockchain(difficulty=2)

    shamock = Mock()

    # force the result of hexdigest be a string ending with 0 * difficulty(2)
    shamock.hexdigest = lambda: 'foobar00'

    monkeypatch.setattr(hashlib, 'sha256', lambda *args: shamock)

    # in the first hit we got it right
    assert blocks.proof_of_work() == 0