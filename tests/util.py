from vpngate.util.building import Block
from vpngate.blockchain import BlocksManager, PoWBlockChain
from vpngate.p2p import Peer


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


def get_blocks_manager(**kwargs) -> BlocksManager:
    kwargs.setdefault('name', 'foo')
    kwargs.setdefault('peer', get_peer())
    return BlocksManager(**kwargs)


def get_peer(**kwargs) -> Peer:
    kwargs.setdefault('address', 'http://127.0.0.1')
    return Peer(**kwargs)


def get_pow_blockchain(**kwargs) -> PoWBlockChain:
    kwargs.setdefault('name', 'foo')
    kwargs.setdefault('peer', get_peer())
    return PoWBlockChain(**kwargs)