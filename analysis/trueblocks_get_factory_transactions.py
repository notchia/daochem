import os
import json
import pandas as pd

from modules.config import CWD, TMPDIR, DATADIR
import modules.trueblocks as tb
from modules.utils import load_json

os.chdir(CWD)

def get_matching_files(version, label):
    """Get files matching the framework version"""
    files = os.listdir(TMPDIR)
    matching = [f for f in files if ((version in f) and (label in f))]
    return matching


def combine_transaction_data(matching, fpath):
    """Given list of files containing individual transaction, group into single file"""
    transactions = {}
    matching.sort(key=lambda s: int(os.path.splitext(s)[0].split('_')[-1]))
    for f in matching:
        count = os.path.splitext(f)[0].split('_')[-1]
        t = load_json(os.path.join(TMPDIR, f))
        t_cut = tb.get_minimal_transaction_info(t)
        transactions[int(count)] = t_cut
        
    with open(fpath, 'w') as out:
        json.dump(transactions, out, indent=4)


def combine_trace_data(matching, fpath):
    """Given list of files containing individual transaction, group into single file"""
    transactions = {}
    matching.sort(key=lambda s: int(os.path.splitext(s)[0].split('_')[-1]))
    for f in matching:
        count = os.path.splitext(f)[0].split('_')[-1]
        t = load_json(os.path.join(TMPDIR, f))
        t_cut = tb.get_minimal_trace_info(t)
        transactions[int(count)] = t_cut
        
    with open(fpath, 'w') as out:
        json.dump(transactions, out, indent=4)


# Load factory contract addresses for each DAO framework
df_factories = pd.read_csv(os.path.join(DATADIR, 'framework_factory_contract_addresses.csv'), index_col=False)

# Run chifra list for all addresses to generate monitors
addresses = list(df_factories['factoryAddress'])
addresses_str = " ".join(addresses)
cmd = tb.chifra_list(addresses)
tb.pipe_chifra_call(cmd)

# Run chifra abi for all addresses to get ABIs
for i, row in df_factories.iterrows(): 
    cmd = tb.chifra_abi(row['factoryAddress'])
    tb.pipe_chifra_call(cmd, fpath=os.path.join(DATADIR, f"trueblocks_framework_abis_{row['version']}.json"))

# Run chifra export for each address
for i, row in df_factories.iterrows():
    version = row['version']
    addr = row['factoryAddress']
    print(version)

    label = 'factory'
    fpath = os.path.join(DATADIR, f'trueblocks_export_{version}.json')
    matching = get_matching_files(version, label)
    if not any(matching):
        try:
            # Export transactions if not previously exported
            cmd = tb.chifra_export(addr)
            tb.pipe_chifra_call_with_sleep(cmd, label=f"trueblocks_factory_{row['version']}_full")

            # Update matching file list
            matching = get_matching_files(version, label)
        except Exception as e:
            print(e)
    else:
        print(f"using {len(matching)} previous files")
    
    # Merge individual transactions into a single file for each address
    fpath = os.path.join(DATADIR, f'trueblocks_export_{version}.json')
    combine_transaction_data(matching, fpath)

# Run chifra trace for each address
for i, row in df_factories.iterrows():
    version = row['version']
    addr = row['factoryAddress']
    print(version)

    label = 'trace'
    matching = get_matching_files(version, label)
    if not any(matching):
        try:
            # Export transactions if not previously exported
            cmd = tb.chifra_trace(addr)
            tb.pipe_chifra_call_with_sleep(cmd, label=f"trueblocks_trace_{row['version']}")

            # Update matching file list
            matching = get_matching_files(version, label)
            print(f"found {len(matching)} traces")
        except Exception as e:
            print(e)
    else:
        print(f"using {len(matching)} previous files")
    
    # Merge individual transactions into a single file for each address
    fpath = os.path.join(DATADIR, f'trueblocks_trace_{version}.json')
    combine_trace_data(matching, fpath)
