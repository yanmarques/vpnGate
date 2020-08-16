from .util import get_peer, get_block, assert_is_genesis_block
from vpngate.chains import Tree
from vpngate.util.building import Block


def test_tree_returns_zero_when_empty():
    chain = Tree()
    assert chain.length == 0


def test_tree_returns_correct_length():
    expected_size = 3
    chain = Tree()

    for _ in range(expected_size):
        chain.add(get_peer(), get_block())

    assert chain.length == expected_size


def test_tree_get_correct_block():
    chain = Tree()
    peer = get_peer()
    expected_block = get_block()

    chain.add(peer, expected_block)

    assert chain.get(peer)[-1] == expected_block


def test_tree_get_genesis_block_when_peer_chain_is_empty():
    chain = Tree()
    blocks = chain.get(get_peer())
    assert_is_genesis_block(blocks[0])


def test_tree_get_all_chains_of_the_peer():
    chain = Tree()
    peer = get_peer()
    block = get_block()
    chain.add(peer, block)
    assert chain.get(peer) == [Block.genesis(), block]


def test_tree_items_let_us_loop_over_peer_and_chain():
    chain = Tree()
    peer = get_peer()
    block = get_block()

    chain.add(peer, block)

    assert list(chain.items())[0] == (peer, [block])


def test_tree_returns_false_when_peer_has_no_chains():
    chain = Tree()
    assert not chain.has(get_peer())


def test_tree_returns_true_when_peer_has_any_chains():
    chain = Tree()
    peer = get_peer()
    chain.add(peer, get_block())
    assert chain.has(peer)