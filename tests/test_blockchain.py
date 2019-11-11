import pytest
from blueprints.landing import get_node_chain
from .util import mock_proof


def test_append_node(reg_client):
    node_chain = get_node_chain()
    node_chain.node.is_secure = True

    mock_proof()
    bootstrap = node_chain.append_node('321', '1.2.3.4')
    node_chain.boot_storage.save(bootstrap)

    payload = dict(proof='123', token=bootstrap.token, id=bootstrap.identifier)
    res = reg_client.post('/bootstrap', data=payload)
    
    assert res.status_code == 201
    assert not bootstrap.token in node_chain.pending_tokens 
    assert res.json['access_token'] in node_chain.tokens


def test_fails_to_append_address_twice(reg_client):
    test_append_node(reg_client)
    with pytest.raises(LookupError):
        test_append_node(reg_client)


def test_exchange_chains(reg_get_clients):
    first_app = reg_get_clients.pop().app
    second_app = reg_get_clients.pop().app

    node_chain = first_app.node_storage.current
    node_chain.node.is_secure = True

    with first_app.test_client() as client:
        mock_proof(blocks=node_chain)
        token, identifier = node_chain.append_node('321', '1.2.3.4')
        payload = dict(proof='123', token=token, id=identifier)
        res = client.post('/bootstrap', data=payload)
        access_token = res.json['access_token']

    with second_app.test_client() as client:
        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Node-Id': second_app.node_storage.current.node.identifier
        }


