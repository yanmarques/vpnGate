from vpngate.util.building import Block


def assert_is_genesis_block(block):
    assert block.previous_hash == '1'
    assert block.proof == 100
    assert block.index == 0
    assert block.timestamp == -1


def get_block(**kwargs) -> Block:
    kwargs.setdefault('index', 1)
    kwargs.setdefault('transactions', [])
    kwargs.setdefault('proof', 123)
    kwargs.setdefault('previous_hash', '321')
    kwargs.setdefault('timestamp', None)
    return Block(**kwargs)