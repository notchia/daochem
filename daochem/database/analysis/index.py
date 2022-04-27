import os

from daochem.database.analysis.base import RESULTS_DIR, save_json
from daochem.database.models.blockchain import BlockchainTransaction, DaoFactory
from daochem.database.models.daos import Dao

RESULTS_FILE = os.path.join(RESULTS_DIR, 'index.json')

# Get overall database stats for index.html
fac_txn_count = 0
for fac in DaoFactory.objects.all():
    fac_txn_count += fac.related_transactions.count()

stats = {
    'factory_count': DaoFactory.objects.all().count(),
    'factory_transaction_count': fac_txn_count,
    'dao_transaction_count': BlockchainTransaction.objects.all().count() - fac_txn_count,
    'dao_count': Dao.objects.all().count(),
}

save_json(stats, RESULTS_FILE)