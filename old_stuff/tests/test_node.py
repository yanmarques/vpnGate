from dataclasses import asdict

import pytest
from lib.node import Node, NodeStorage


def test_create_empty_node():
    node = fake_node()
    assert node.identifier is not None
    assert len(node.children) == 0
    assert node.is_leaf is True


def test_secured_node_with_children():
    node = fake_node(depth=1, host='https://1.2.3.4')
    assert node.is_leaf is False


def test_http_node_has_no_children():
    node = fake_node()
    with pytest.raises(Exception):
        node.add_child(fake_node())


def test_save_empty_node(temp_file):
    node = fake_node()
    storage = NodeStorage(path=temp_file)
    storage.save(node)
    assert asdict(node) == asdict(storage.current)


def test_save_node_with_inner_nodes(temp_file):
    node = fake_node(depth=3, host='https://1.2.3.4')
    storage = NodeStorage(path=temp_file)
    storage.save(node)
    assert asdict(node) == asdict(storage.current)


def test_load_node_equals_saved_node(temp_file):
    node = fake_node(depth=1)
    storage = NodeStorage(path=temp_file)
    storage.save(node)
    storage.load()
    assert asdict(node) == asdict(storage.current)


def fake_node(depth=0, host='1.2.3.4'):
    children = []
    for _ in range(depth):
        children.append(Node(host))
    return Node(host, children=children)