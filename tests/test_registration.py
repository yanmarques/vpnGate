"""
This module provides basic test for registration functionality. 
"""
from .util import mock_proof


def test_register_action(reg_client):
    mock_proof()
    res = reg_client.post('/register', data=fake_payload())
    assert b'Suceeded' in res.data


def test_register_fails_with_duplicate_email(reg_client):
    expected = b'Suceeded'
    mock_proof()
    payload = fake_payload()
    res = reg_client.post('/register', data=payload)
    assert expected in res.data
    failed_res = reg_client.post('/register', data=payload)
    assert not expected in failed_res.data


def test_email_requirement(reg_client):
    payload = dict(proof='123')
    res = reg_client.post('/register', data=payload)
    assert b'This field is required' in res.data


def fake_payload(email='foo@net.com', proof='123'):
    return dict(email=email, proof=proof)
