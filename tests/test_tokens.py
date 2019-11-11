import pytest
from lib.tokens import JWTRegistry
from jose.exceptions import ExpiredSignatureError, JWTClaimsError


def test_registry_with_an_issuer():
    expected_iss = 'foo'
    registry = JWTRegistry(lambda: 'secret', issuer=expected_iss)
    token = registry.encode(10)
    data = registry.decode(token)
    assert expected_iss == data['iss']


def test_fails_to_decode_token_with_different_issuer():
    registry = JWTRegistry(lambda: 'secret', issuer='foo')
    token = registry.encode(10)
    registry.issuer = 'bar'
    with pytest.raises(JWTClaimsError):
        registry.decode(token)


def test_decodes_token_without_checking_issuer():
    expected_iss = 'foo'
    registry = JWTRegistry(lambda: 'secret', issuer=expected_iss)
    token = registry.encode(10)
    registry.issuer = None
    data = registry.decode(token)
    assert expected_iss == data['iss']


def test_registry_with_an_audience():
    expected_aud = 'foo'
    registry = JWTRegistry(lambda: 'secret', audience=expected_aud)
    token = registry.encode(10)
    data = registry.decode(token)
    assert expected_aud == data['aud']


def test_fails_to_decode_token_with_different_audience():
    registry = JWTRegistry(lambda: 'secret', audience='foo')
    token = registry.encode(10)
    registry.audience = 'bar'
    with pytest.raises(JWTClaimsError):
        registry.decode(token)


def test_fails_to_decode_token_without_audience():
    registry = JWTRegistry(lambda: 'secret', audience='foo')
    token = registry.encode(10)
    registry.audience = None
    with pytest.raises(JWTClaimsError):
        registry.decode(token)

def test_token_expiration():
    registry = JWTRegistry(lambda: 'secret')
    token = registry.encode(-1)
    with pytest.raises(ExpiredSignatureError):
        registry.decode(token)