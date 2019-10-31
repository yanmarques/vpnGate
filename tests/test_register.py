"""
This module provides basic test for registration functionality. 
"""


def test_register_action(client):
    payload = dict(email='foo@net.com')
    res = client.post('/register', data=payload)
    assert b'Suceeded' in res.data


def test_register_fails_with_duplicate_email(client):
    expected = b'Suceeded' 
    payload = dict(email='foo@net.com')
    res = client.post('/register', data=payload)
    assert expected in res.data
    failed_res = client.post('/register', data=payload)
    assert not expected in failed_res.data