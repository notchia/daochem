import os
import time
import json
import subprocess
import argh
import numpy as np
from datetime import datetime

from config import TMPDIR, DATADIR
from utils import load_json

RPS_LIMIT = 10 # requests per second rate limit from ArchiveNode.io
SLEEP = 1 # second

CACHE = "--cache"
JSON = "--fmt json"


def pipe_chifra_call(command, mode='w', fpath=None):
    """Call chifra command and save to JSON file"""
    if fpath is None:
        fpath = os.path.join(TMPDIR, 'trueblocks.json')

    try:
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)

        with open(fpath, mode) as f:
            lines = [line.decode("utf-8") for line in process.stdout]
            if 'w' in mode:
                f.writelines(lines)
            elif 'a' in mode:
                line = " ".join(lines)
                f.write(line)
    except Exception as e:
        print(e)

    return fpath


def pipe_chifra_call_with_sleep(cmd, label=None):
    """Batch the chifra call to (hopefully) prevent the archive node rate limit from being exceeded"""

    dir = TMPDIR
    if label is None:
        label = 'trueblocks'

    flags = {'max': 1}
    r_all = []
    r = {'data': {}}
    totalCount = 0
    batchCount = 0
    t0 = datetime.now()
    while len(r) > 0:
        # Get API response and save to file/append to list
        flags['first'] = totalCount
        cmd_items = cmd.split(' ')
        cmd_items.insert(2, f"--first_record={flags['first']}")
        cmd_items.insert(3, f"--max_records={flags['max']}")
        _cmd = " ".join(cmd_items)
        fpath = os.path.join(dir, f"{label}_{totalCount}.json")
        pipe_chifra_call(_cmd, fpath=fpath)
        r = load_json(fpath)
        if len(r) == 0:
            # Retry once after an extra-long sleep if there was no response
            time.sleep(2*SLEEP)
            pipe_chifra_call(_cmd, fpath=fpath)
            r = load_json(fpath)
        data = get_minimal_transaction_info(r)
        print(data)
        r_all.append(data)

        # Pause if RPS_LIMIT is about to be exceeded
        batchCount += 1
        totalCount += 1
        if (batchCount > RPS_LIMIT - 1):
            time.sleep(SLEEP)
        t1 = datetime.now()
        if (t1 - t0).total_seconds() > 1:
            t0 = t1
            batchCount = 0
        print(batchCount)

    return r_all


def get_minimal_transaction_info(transaction):
    keys = ['hash', 'blockNumber', 'date', 'from', 'to', 'articulatedTx']
    try:
        data = transaction['data'][0]
        t = {k: v for k, v in data.items() if k in keys}
        t['contractAddress'] = data['receipt']['contractAddress']
    except (KeyError, TypeError, IndexError):
        t = {}
    return t


def get_minimal_trace_info(fullTrace):
    trace = fullTrace.get('data', [])
    contractsCreated = [t.get('result', {}).get('newContract') for t in trace if t.get('action', {}).get('callType') == "creation"]

    return {'contractsCreated': contractsCreated}


def chifra_list(address):
    """Retrieve a smart contract's ABI file
    https://trueblocks.io/docs/chifra/accounts/#chifra-abis
    """    
    if isinstance(address, list):
       address = " ".join(address)
    return " ".join(["chifra", "list", JSON, address])


def chifra_blocks(block):
    """Retrieve a smart contract's ABI file
    https://trueblocks.io/docs/chifra/accounts/#chifra-abis
    """
    if isinstance(address, list):
       address = " ".join(address)
    return " ".join(["chifra", "blocks", JSON, CACHE, block])


def chifra_abi(address):
    """Retrieve a smart contract's ABI file
    https://trueblocks.io/docs/chifra/accounts/#chifra-abis
    """
    if isinstance(address, list):
       address = " ".join(address)
    return " ".join(["chifra", "abis", JSON, address])


def chifra_export(address):
    """Export all transactions involving this account:
    command line: chifra export --fmt json <address>
    https://trueblocks.io/docs/chifra/accounts/#chifra-export
    """

    return " ".join(["chifra", "export", "--articulate", CACHE, JSON, address])


def chifra_trace(address):
    return " ".join(["chifra", "export", "--traces", "--articulate", CACHE, JSON, address])


def chifra_export_logs(address):
    """Export all transactions involving this account:
    command line: chifra export --fmt json <address>
    https://trueblocks.io/docs/chifra/accounts/#chifra-export
    """

    return " ".join(["chifra", "export", "--factory",  "--logs", "--articulate", "--relevant", JSON, address])


def chifra_trace(address):
    """Export all transactions involving this account:
    command line: chifra export --fmt json <address>
    https://trueblocks.io/docs/chifra/accounts/#chifra-export
    """

    return " ".join(["chifra", "export", "--trace", "--articulate", JSON, address])


def test_address_export(address):
    # Create monitor
    cmd = chifra_list(address)
    fpath = os.path.join(TMPDIR, 'trueblocks_test_list.json')
    pipe_chifra_call(cmd, fpath=fpath)
    r = load_json(fpath)
    print("successfully loaded `chifra list` results")

    # Export transaction history
    cmd = chifra_export(address)
    label = 'trueblocks_test_export'
    r = pipe_chifra_call_with_sleep(cmd, label=label)  
    print(f"successfully got {len(r)} `chifra export` results")


if __name__ == "__main__":
    argh.dispatch_command(test_address_export)
