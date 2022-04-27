import os
import re
import pandas as pd
from datetime import datetime

from daochem.settings import BASE_DIR
from daochem.database.etl.twitter import TwitterHandler
from daochem.database.models.daos import Dao
from daochem.database.models.twitter import TwitterAccount
from utils.strings import clean_dao_name


def setup_daos():
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


def update_dao_twitters():
    """Check that I have the earliest available tweet"""
    tw = TwitterHandler()
    for account in TwitterAccount.objects.all():
        try:
            tweets = account.tweets.all()
            end_date = tweets.order_by('-created_at')[0].created_at
            kwargs = {'end_time': datetime(end_date.year, end_date.month, end_date.day)}
            print(f"Getting tweets for {account.username} up till {end_date}")
            tw.upsert_dao_tweets(account.dao.all()[0], kwargs=kwargs)
        except IndexError:
            pass

if __name__=="__main__":
    #setup_daos()
    update_dao_twitters()