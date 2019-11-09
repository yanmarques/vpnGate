from unittest.mock import MagicMock, Mock

import requests
from flask import current_app


def mock_proof(return_value=True):
    return mock_blockchain('valid_proof', return_value=return_value)


def mock_blockchain(name, impl=MagicMock, **kwargs):
    setattr(current_app.blocks, name, impl(**kwargs))
    return current_app.blocks


def bootstrap_on_lan():
    """
    Add a node on the same loopback interface.
    """

    my_other_self = fake_node_list()[-1]
    current_app.blocks.register_node(my_other_self)


def mock_node_predicate(blocks=None, **kwargs):
    blocks = blocks or current_app.blocks
    blocks.predicate.is_valid = MagicMock(**kwargs)


def fake_node_list(myself=True):
    nodes = ['http://1.2.3.4', 
            'http://4.3.2.1', 
            'http://7.4.3.1']
    if myself:
        # pick a localhost address
        # this simulate two nodes on the same LAN
        port = 9999
        candidate = f'http://127.0.0.1:{port}'
        while not current_app.blocks.is_remote(candidate):
            port += 1
            candidate = f'http://127.0.0.1:{port}'
        nodes.append(candidate)
    return nodes


def mock_http_get(url_mapping):
    response = Mock()

    def handle_req(req_url, **kwargs):
        for url, client in url_mapping:
            if req_url.endswith(url):
                recv_res = client.get(req_url)
                response.status_code = recv_res.status_code
                response.json = lambda: recv_res.json
                return response

    requests.get = MagicMock(side_effect=handle_req)
    return requests.get


def mock_http_post(url_mapping):
    response = Mock()

    def handle_req(req_url, **kwargs):
        print(req_url)
        for url, client in url_mapping:
            if req_url.endswith(url):
                data = kwargs['data']
                recv_res = client.post(req_url, data=data)
                response.status_code = recv_res.status_code
                response.content = response.data
                return response

    requests.post = MagicMock(side_effect=handle_req)
    return requests.post