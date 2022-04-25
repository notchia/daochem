import os

from daochem.database.analysis.base import RESULTS_DIR, save_json
from daochem.database.models.blockchain import DaoFactory

RESULTS_FILE = os.path.join(RESULTS_DIR, 'factories.json')

# Get factory stats for factories.html
factories = []
for factoryObj in DaoFactory.objects.all().order_by('dao_framework__name', 'version'):
    factoryDict = {
        'name': str(factoryObj),
        'address': factoryObj.contract_address.address,
        'address_url': factoryObj.contract_address.etherscan_url,
    }
    relatedTxSet = factoryObj.related_transactions.filter(call_name__in=factoryObj.dao_creation_functions)
    creationCount = relatedTxSet.count()
    factoryDict['daos_created_count'] = creationCount

    """
    # TODO: Figure out how to aggregate over JSONfield keys
    for fcn in factoryObj.dao_creation_functions:
        aggDict = {}
        abi = ContractAbi.objects.get(
            Q(address=factoryObj.contract_address) &
            Q(name=fcn)
        )
        params = abi.get('params', {})
        for key, value in params:
            agg = None
            if value.endswith('[]'):
                relatedTxSet.agg.count()
                agg = relatedTxSet.annotate(val=KeyTextTransform('createdDate','jdata')).count()
    """

    factories.append(factoryDict)

save_json(factories, RESULTS_FILE)