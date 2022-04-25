import os

from daochem.database.analysis.base import RESULTS_DIR, save_json
from daochem.database.models.blockchain import DaoFactory
from daochem.database.models.daos import Dao

RESULTS_FILE = os.path.join(RESULTS_DIR, 'index.json')

# Get overall database stats for index.html
stats = {
    'factory_count': DaoFactory.objects.all().count(),
    'dao_count': Dao.objects.all().count(),
}

save_json(stats, RESULTS_FILE)