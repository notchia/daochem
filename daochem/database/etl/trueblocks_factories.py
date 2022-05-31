import logging
from django.db import transaction

from daochem.database.models.blockchain import BlockchainTransaction, DaoFactory, EtlMonitor
from daochem.database.etl.trueblocks import TrueblocksHandler


def scrape_factory(factory, tb=None):
    """Scrape factory transactions given factory id or DaoFactory object"""

    if tb is None:
        tb = TrueblocksHandler()

    if isinstance(factory, int):
        factory = DaoFactory.objects.get(pk=factory)

    addressObj = factory.contract_address
    tb.add_or_update_transaction_count(addressObj)
    tb.add_or_update_address_traces(addressObj)    


def scrape_factories():
    """Query trueblocks and extract, transform, and load factory address transaction data
    
    If no factory_address provided, scrapes all in database. 
    If no since_block provided, finds most recent block for which a transaction appears
    and uses that (or, if no transactions found, from the beginning)
    """
    
    tb = TrueblocksHandler()
    #indexStatus = tb.get_index_status()

    for factory in DaoFactory.objects.all():
        if factory.version in ['0.6', '0.8', '0.8.1', 'openlaw_tribute', '2019-05-27']: # go back to '0.7' and 'v2.1' 
            continue
        logging.info(f"Processing {factory}...")
        scrape_factory(factory, tb=tb)

    #monitor = EtlMonitor.objects.get(pk='trueblocks')
    #monitor.last_scrape_time = datetime.now()
    #monitor.last_pinned_time = indexStatus['last_pinned_time']
    #monitor.last_scrape_block = indexStatus['last_pinned_block']


def get_txn_counts_contract_created(txnSet, tb=None):
    """Given a list of (factory) contract transactions, get txn count for each contract created"""

    if tb is None:
        tb = TrueblocksHandler()
    
    for txn in txnSet:
        with transaction.atomic():
            contracts = txn.contracts_created.all()
            max_count = 0
            for contract in contracts:
                count = tb.add_or_update_transaction_count(contract)
                if count > max_count:
                    max_count = count
            logging.info(f"Found {max_count} transactions for the DAO created by txn {txn.pk}")


def get_address_counts():
    tb = TrueblocksHandler()
    for factory in DaoFactory.objects.all():
        print(factory)
        transactions = factory.related_transactions.all()
        txnCount = 0
        for txn in transactions:
            print(txnCount)
            with transaction.atomic():
                contracts = txn.contracts_created.all()
                max_count = 0
                for contract in contracts:
                    count = tb.add_or_update_transaction_count(contract)
                    if count > max_count:
                        max_count = count
                print(f"Found {max_count} transactions")
            txnCount += 1



if __name__ == "__main__":
    #get_address_counts()
    factoryId = 5 # DAOhaus
    scrape_factory(factoryId)
    txnSet = DaoFactory.objects.get(pk=factoryId).related_transactions.all()
    get_txn_counts_contract_created(txnSet)
    