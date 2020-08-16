from .util import get_peer
from vpngate.util import crypto


def test_peer_recognizes_itself_using_its_identifier():
    me = get_peer()
    other_me = get_peer(keys=me.keys)
    assert me == other_me


def test_peer_assert_different_peers():
    peer = get_peer()
    other_peer = get_peer()
    assert peer != other_peer


def test_peer_does_not_duplicate_childs():
    peer = get_peer()
    child_peer = get_peer()

    peer.children.add(child_peer)
    peer.children.add(get_peer(keys=child_peer.keys))

    assert len(peer.children) == 1


def test_peer_does_not_duplicate_siblings():
    peer = get_peer()
    sibling_peer = get_peer()

    peer.siblings.add(sibling_peer)
    peer.siblings.add(get_peer(keys=sibling_peer.keys))

    assert len(peer.siblings) == 1


def test_peer_is_comparable():
    list_of_peers = [get_peer() for _ in range(3)]
    assert get_peer() not in list_of_peers


def test_peer_identifier_can_be_used_to_verify_a_signature():
    data = b'foo bar baz'
    peer = get_peer()
    
    signature = peer.keys.sign(data)

    assert crypto.KeyPair.was_signed_from_base64(peer.identifier, signature, data)