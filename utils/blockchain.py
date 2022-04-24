import os
from datetime import datetime
from web3 import Web3, HTTPProvider


def load_txid(blockNumber, txIndex):
    return f"{blockNumber}.{txIndex}"


def unpack_txid(txId):
    blockNumber, txIndex = txId.split('.')
    return {'blockNumber': blockNumber, 'transactionIndex': txIndex}


def unpack_compressed_call(s):
    """Unpack compressed_trace or compressed_log"""

    s = s.strip().strip(';')
    name, paramsString = s.split('(')
    paramsList = [s.strip(p).split() for p in paramsString[:-1].split(', ')]
    paramsDict = {p[1]: p[0].strip('/').strip('*') for p in paramsList}

    return {'name': name, 'input': paramsDict}


def get_timestamp(block):
    try:
        w3 = Web3(HTTPProvider(os.getenv('RPC_KEY')))
        timestamp_unix = w3.eth.get_block(block).timestamp
        timestamp = datetime.fromtimestamp(timestamp_unix)
    except Exception as e:
        print(e)
        timestamp = None

    return timestamp
