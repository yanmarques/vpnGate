from .util import get_peer


def test_peer_recognizes_itself_using_its_identifier():
    me = get_peer()
    other_me = get_peer(identifier=me.identifier)
    assert me == other_me


def test_peer_assert_different_peers():
    peer = get_peer()
    other_peer = get_peer()
    assert peer != other_peer


def test_peer_does_not_duplicate_childs():
    peer = get_peer()
    child_peer = get_peer()

    peer.children.add(child_peer)
    peer.children.add(get_peer(identifier=child_peer.identifier))

    assert len(peer.children) == 1


def test_peer_does_not_duplicate_siblings():
    peer = get_peer()
    sibling_peer = get_peer()

    peer.siblings.add(sibling_peer)
    peer.siblings.add(get_peer(identifier=sibling_peer.identifier))

    assert len(peer.siblings) == 1


def test_peer_is_hashable():
    list_of_peers = [get_peer() for _ in range(3)]
    assert get_peer() not in list_of_peers