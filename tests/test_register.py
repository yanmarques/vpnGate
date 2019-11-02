"""
This module provides basic test for registration functionality. 
"""


def test_register_action(reg_client):
    payload = dict(email='foo@net.com')
    res = reg_client.post('/register', data=payload)
    assert b'Suceeded' in res.data


def test_register_fails_with_duplicate_email(reg_client):
    expected = b'Suceeded' 
    payload = dict(email='foo@net.com')
    res = reg_client.post('/register', data=payload)
    assert expected in res.data
    failed_res = reg_client.post('/register', data=payload)
    assert not expected in failed_res.data