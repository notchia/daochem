import logging
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import ast
import numpy as np

from daochem.database.models.blockchain import BlockchainAddress, DaoFactory

KWARGS_FIG = {'format': 'png', 'bbox_inches': 'tight', 'dpi': 600}
SAVEDIR = 'tmp'

def format_call_input(value, description):
    if description == 'int':
        return int(value)
    elif description.startswith('list'):
        value = ast.literal_eval(value)
        if description.endswith('int'):
            return [int(v) for v in value]
    else:
        return value


def _len(value):
    try:
        return len(value)
    except TypeError:
        return 0


def get_factory_transactions(factoryId, threshold=5):
    """Analyze transactions with at least threshold txns"""

    txns = DaoFactory.objects.get(pk=factoryId).related_transactions.all()
    filteredTxns = txns.filter(contracts_created__chifra_list_count__gte=threshold) # Does this work if more than one contract is created?

    series = []
    for txn in txns:
        txnDict = {
            k: v for k, v in txn.__dict__.items() 
            if k in ['transaction_id', 'call_name', 'call_inputs']
        }

        try:
            mainContract = txn.contracts_created.order_by('-chifra_list_count')[0]
            contractDict = {
                k: v for k, v in mainContract.__dict__.items() 
                if k in ['address', 'chifra_list_count']
            }
        except IndexError:
            contractDict = {'address': None, 'chifra_list_count': None}

        series.append(pd.Series({**txnDict, **contractDict}))

    df = pd.concat(series, axis=1, ignore_index=True).transpose()

    print(df['call_name'].value_counts())
    df_creation = df[df['call_name'] == 'summonMoloch'] # TODO: add summonMolochLLC
    df_filtered = df_creation[df_creation['chifra_list_count'] > threshold].reset_index()

    sns.histplot(df_creation['chifra_list_count'], discrete=True)
    fname = f"{SAVEDIR}/histplot_chifra_list_count"
    plt.savefig(f'{fname}.png', **KWARGS_FIG)

    logging.info(f"Selecting {len(df_filtered.index)} txns out of {len(df_creation.index)} that match chifra_list_count >= {threshold}")

    # TODO: reference dao_creation_functions in DaoFactory
    # TODO: add ABI/dao_creation_fields to DaoFactory, so that this can be drawn from database for any factory
    # TODO: store call input data types somewhere (if it's not already in ABI)
    inputs = {
        '_summoner': 'list', 
        '_dilutionBound': 'int', 
        '_approvedTokens': 'list', 
        '_periodDuration': 'int', 
        '_summonerShares': 'list_int',
        '_proposalDeposit': 'int', 
        '_processingReward': 'int', 
        '_gracePeriodLength': 'int', 
        '_votingPeriodLength': 'int',
    }

    for input, description in inputs.items():
        df_filtered[input] = df_filtered['call_inputs'].apply(
            lambda x: format_call_input(x[input], description)
        )

    # TODO: function to automatically generate counts of call data that are lists
    df_filtered['shareholder_count'] = df_filtered['_summoner'].apply(lambda x: _len(x))

    # TODO: create generic mapping between data types and aggregation functions
    for input in ['_proposalDeposit', '_processingReward', '_gracePeriodLength', '_votingPeriodLength', '_periodDuration', '_dilutionBound', 'shareholder_count']:
        print(input)
        data = df_filtered[input]
        print(f"  Min:    {min(data):.2e}")
        print(f"  Max:    {max(data):.2e}")
        print(f"  Median: {np.median(data):.2e}")
        plt.figure()
        if min(data) == 0:
            data_to_plot = [x for x in data if x != 0]
            print(f"not plotting {len(data)-len(data_to_plot)} points with value 0")
        else:
            data_to_plot = data
        ax = sns.histplot(data_to_plot, discrete=True, bins=len(df_filtered.index), log_scale=True)
        fname = f"{SAVEDIR}/histplot_{input}"
        plt.savefig(f'{fname}.png', **KWARGS_FIG)




def get_creation_parameters(address):
    tx = BlockchainAddress.objects.get(pk=address)
    print(tx.created_by_transaction)


if __name__ == "__main__":
    get_factory_transactions(5)
    #get_creation_parameters('0x4570b4faf71e23942b8b9f934b47ccedf7540162')