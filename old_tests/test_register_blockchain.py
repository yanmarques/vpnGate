import pytest
import requests
from flask import current_app
from .util import (bootstrap_on_lan, 
                mock_node_predicate, 
                fake_node_list, 
                mock_http_get,
                mock_http_post)


@pytest.fixture
def started_client(reg_client):
    bootstrap_on_lan()
    mock_node_predicate()
    yield reg_client


@pytest.fixture
def started_mash(reg_get_clients):
    cmd_ctrl = reg_get_clients.pop().app
    bootstaper = reg_get_clients.pop().app
    last = reg_get_clients.pop().app

    cmd_name = cmd_ctrl.blocks.server_name
    bootstraper_name = bootstaper.blocks.server_name
    last_name = last.blocks.server_name 
    
    cmd_ctrl.blocks.register_node(bootstraper_name)
    last.blocks.register_node(bootstraper_name)
    bootstaper.blocks.register_node(cmd_name)    
    bootstaper.blocks.register_node(last_name)    

    with cmd_ctrl.test_client() as cmd_client:
        with last.test_client() as last_client: 
            with bootstaper.test_client() as bootstrap_client:
                mock_http_mappings(
                    (cmd_name, cmd_client),
                    (last_name, last_client),
                    (bootstraper_name, bootstrap_client)
                )

                mock_node_predicate(blocks=bootstaper.blocks)
                bootstrap_client.get('/')

                mock_node_predicate(blocks=cmd_ctrl.blocks)
                cmd_client.get('/')

                mock_node_predicate(blocks=last.blocks)
                last_client.get('/')

                yield [
                    (last_name, last_client, last),
                    (bootstraper_name, bootstrap_client, bootstaper), 
                    (cmd_name, cmd_client, cmd_ctrl), 
                ]


def test_block_by_ip(reg_client):
    endpoints = ['/node', '/chain']
    for url in endpoints:
        res = reg_client.get(url)
        assert res.status_code == 401


def test_get_chain_list(started_client):
    res = started_client.get('/chain')
    assert res.status_code == 200
    assert res.json['chain'] == current_app.blocks.chain


def test_get_node_list(reg_client):
    expected_nodes = fake_node_list()
    expected_revoked = fake_node_list(myself=False)[-1]
    
    blocks = current_app.blocks 
    list(map(blocks.register_node, expected_nodes))

    mock_node_predicate(return_value=False)
    blocks.revoke_node(expected_revoked)
    expected_nodes = set(expected_nodes) - set([expected_revoked])
    
    assert_nodes(expected_nodes, reg_client, revokeds=[expected_revoked])


def test_register_node(started_client):
    expected_nodes = fake_node_list()
    
    payload = dict(nodes=expected_nodes)
    res = started_client.post('/node', data=payload)
    assert res.status_code == 201
    assert set(expected_nodes) == current_app.blocks.nodes


def test_revoke_with_unknow_nodes_will_register_bootstraper(started_client):
    expected_nodes = fake_node_list()
    payload = dict(nodes=expected_nodes)

    # force revoking
    mock_node_predicate(return_value=False)
    res = started_client.delete('/node', data=payload)
    assert res.status_code == 201
    assert expected_nodes[-1:] == current_app.blocks.revokeds


def test_revoke_all_nodes(started_client):
    expected_nodes = fake_node_list()
    payload = dict(nodes=expected_nodes)

    mock_node_predicate(return_value=False)
    started_client.post('/node', data=payload)
    res = started_client.delete('/node', data=payload)
    assert res.status_code == 201
    assert expected_nodes == current_app.blocks.revokeds


def test_spreading_with_multi_nodes(started_mash):
    cmd_ctrl = started_mash.pop()
    bootstrap = started_mash.pop()
    last = started_mash.pop()

    nodes_cmd = set([last[0], bootstrap[0]])
    nodes_bootstrap = set([last[0], cmd_ctrl[0]])
    nodes_last = set([cmd_ctrl[0], bootstrap[0]])

    assert_nodes(nodes_cmd, cmd_ctrl[1])
    assert_nodes(nodes_bootstrap, bootstrap[1])
    assert_nodes(nodes_last, last[1])


def test_node_not_revoked_with_alone_voting(started_mash):
    cmd_ctrl = started_mash.pop()
    bootstrap = started_mash.pop()
    last = started_mash.pop()

    # allow us to run spreading
    last[2].blocks.config['spreading_time'] = 0

    mock_node_predicate(blocks=last[2].blocks, return_value=False)
    last[1].delete('/node', data=dict(nodes=cmd_ctrl[0]))
    last[1].get('/')

    nodes_cmd = set([last[0], bootstrap[0]])
    nodes_bootstrap = set([last[0], cmd_ctrl[0]])
    nodes_last = set([cmd_ctrl[0], bootstrap[0]])

    assert_nodes(nodes_cmd, cmd_ctrl[1])
    assert_nodes(nodes_bootstrap, bootstrap[1])
    assert_nodes(nodes_last, last[1])


def test_node_revoked_with_valid_voting(started_mash):
    cmd_ctrl = started_mash.pop()
    bootstrap = started_mash.pop()
    last = started_mash.pop()

    # allow us to run spreading
    last[2].blocks.config['spreading_time'] = 0

    revoke_payload = dict(nodes=cmd_ctrl[0])

    mock_node_predicate(blocks=last[2].blocks, return_value=False)
    last[1].delete('/node', data=revoke_payload)

    mock_node_predicate(blocks=bootstrap[2].blocks, return_value=False)
    bootstrap[1].delete('/node', data=revoke_payload)
    bootstrap[1].get('/')

    assert_nodes(set([last[0]]), bootstrap[1])
    assert_nodes(set([bootstrap[0]]), last[1])


def assert_nodes(expected, client, revokeds=None):
    res = client.get('/node')
    assert res.status_code == 200
    assert expected == set(res.json['nodes'])
    if revokeds:
        assert revokeds == res.json['revokeds'] 


def mock_http_mappings(cmd_ctrl: list, last: list, bootstraper: list):
    cmd_name, cmd_ctr_client = cmd_ctrl[0], cmd_ctrl[1]
    last_name, last_client = last[0], last[1]
    bootstraper_name, bootstraper_client = bootstraper[0], bootstraper[1]

    mapping = [
        (f'{cmd_name}/node', cmd_ctr_client),
        (f'{cmd_name}/chain', cmd_ctr_client),
        (f'{last_name}/node', last_client),
        (f'{last_name}/chain', last_client),
        (f'{bootstraper_name}/node', bootstraper_client),
        (f'{bootstraper_name}/chain', bootstraper_client),
    ]

    mock_http_get(mapping)
    mock_http_post(mapping)