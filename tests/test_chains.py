from vpngate.chains import Tree
from vpngate.p2p import Peer
from vpngate.util.building import Block
import pytest


@pytest.mark.asyncio
async def test_tree_returns_zero_when_empty():
    chain = Tree()
    assert chain.length == 0


@pytest.mark.asyncio
async def test_tree_returns_correct_length():
    expected_size = 3
    chain = Tree()

    for _ in range(expected_size):
        chain.add(Peer(), get_block())

    assert chain.length == expected_size


@pytest.mark.asyncio
async def test_tree_get_correct_block():
    chain = Tree()
    peer = Peer()
    expected_block = get_block()

    chain.add(peer, expected_block)

    assert chain.get(peer)[-1] == expected_block


@pytest.mark.asyncio
async def test_tree_get_genesis_block_when_peer_chain_is_empty():
    chain = Tree()
    assert chain.get(Peer()) == [Block.genesis()]


@pytest.mark.asyncio
async def test_tree_get_all_chains_of_the_peer():
    chain = Tree()
    peer = Peer()
    block = get_block()
    chain.add(peer, block)
    assert chain.get(peer) == [Block.genesis(), block]


@pytest.mark.asyncio
async def test_tree_items_let_us_loop_over_peer_and_chain():
    chain = Tree()
    peer = Peer()
    block = get_block()

    chain.add(peer, block)

    assert list(chain.items())[0] == (peer, [block])


@pytest.mark.asyncio
async def test_tree_returns_false_when_peer_has_no_chains():
    chain = Tree()
    assert not chain.has(Peer())


@pytest.mark.asyncio
async def test_tree_returns_true_when_peer_has_any_chains():
    chain = Tree()
    peer = Peer()
    chain.add(peer, get_block())
    assert chain.has(peer)


def get_block(**kwargs) -> Block:
    kwargs.setdefault('index', 1)
    kwargs.setdefault('transactions', [])
    kwargs.setdefault('proof', 123)
    kwargs.setdefault('previous_hash', '321')
    kwargs.setdefault('timestamp', None)
    return Block(**kwargs)