import logging

from daochem.database.models.blockchain import DaoFactory, EtlMonitor
from daochem.database.etl.trueblocks import TrueblocksHandler


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
        addressObj = factory.contract_address
        tb.add_or_update_address_traces(addressObj)

    #monitor = EtlMonitor.objects.get(pk='trueblocks')
    #monitor.last_scrape_time = datetime.now()
    #monitor.last_pinned_time = indexStatus['last_pinned_time']
    #monitor.last_scrape_block = indexStatus['last_pinned_block']


if __name__ == "__main__":
    scrape_factories()
    