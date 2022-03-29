import os
import time
import requests
import pandas as pd

import modules.trueblocks as tb
from modules.config import CWD, TMPDIR, DATADIR

os.chdir(CWD)


# Load proposer-block pairs for each DAO found on boardroom
df_lookup = pd.read_csv(os.path.join(DATADIR, 'boardroom_address_lookup.csv'), index_col=False)

df_lookup['contractAddress'] = None
sesh = requests.Session
for i, row in df_lookup.iterrows():
    # Get all transactions in the block
    print(f"Processing {row['protocol']}...")
    cmd = tb.chifra_blocks(row['blockNumber'])
    fpath = tb.pipe_chifra_call(cmd)
    r = tb.load_json(fpath)

    try:
        transactions = r['data'][0]['transactions']

        # Find transaction(s) with proposer as 'from' address and get corresponding 'to' address, if any
        to_addresses = [t['to'] for t in transactions if str(t['from']) == str(row['proposer'])]
        if len(to_addresses) > 1:
            print(f"Warning: found more than one address for {row['protocol']}")
        try:
            to_address = to_addresses[0]
        except IndexError:
            print(f"No contract address found for {row['protocol']}")
            to_address = None
    except KeyError:
        print(f"No contract address found for {row['protocol']}")
        to_address = None        

    # Add to df
    print(to_address)
    df_lookup.at[i, 'contractAddress'] = to_address

    time.sleep(2)

# Save to new file
df_lookup.drop(columns=['blockNumber', 'proposer'])
df_lookup.to_csv('boardroom_contract_addresses.csv')
