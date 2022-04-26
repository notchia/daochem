import os
import re
import pandas as pd

from daochem.settings import BASE_DIR
from daochem.database.etl.twitter import TwitterHandler
from daochem.database.models.daos import Dao
from utils.strings import clean_dao_name


DAOS_FILE = os.path.join(BASE_DIR, 'tmp/daos.csv')

df = pd.read_csv(DAOS_FILE, index_col=None)

tw = TwitterHandler()
for i, row in df.iterrows():
    daoDict = {
        'id': clean_dao_name(row['id']),
        'name': row['name'],
        'twitter_url': row['twitter_url']
    }
    print(daoDict['id'])

    try:
        dao = Dao.objects.get(pk=daoDict['id'])
    except Dao.DoesNotExist:
        dao = Dao.objects.create(**daoDict)
        dao.save()
        tw.upsert_dao_user_info(dao)
        tw.upsert_dao_tweets(dao)
