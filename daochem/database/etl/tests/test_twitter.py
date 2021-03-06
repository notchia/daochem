import os
import tweepy
from pprint import pprint
from django.db.models import Q

from daochem.database.etl.twitter import TwitterHandler
from daochem.database.models.daos import Dao


def test_twitter_credentials():
    client = tweepy.Client(
        bearer_token=os.getenv('TWITTER_API_BEARER_TOKEN'), 
        wait_on_rate_limit=True,
        return_type=dict
    )

    username = "LuciaKorpas"
    user_fields = ['id', 'name', 'username', 'created_at', 'description', 'public_metrics', 'url']
    user_info = client.get_user(username=username, user_fields=user_fields)
    
    assert user_info.get('data') is not None
    pprint(user_info['data'])

    kwargs = {
        'exclude': ['retweets', 'replies'], 
        'tweet_fields': ['id', 'text', 'created_at', 'entities', 'public_metrics', 'attachments'],
        'since_id': '1265747554815422471',
        'until_id': '1497450378815758337'
    }

    tweets = client.get_users_tweets(user_info['data']['id'], **kwargs)
    pprint(tweets)
    assert tweets.get('errors') is None
    assert tweets['meta'].get('result_count', 0) == 8

def test_transforms():

    tw = TwitterHandler()

    response = tw._get_user_info("LuciaKorpas")
    transformed = tw._transform_user_info(response)
    pprint(transformed)

    response = tw._get_tweets(transformed['id'])
    transformed = tw._transform_tweets(response)
    pprint(transformed)


def test_twitter_account_add():

    tw = TwitterHandler()
    dao = Dao.objects.get(Q(name='MolochDAO'))
    data = tw.get_dao_user_info(dao)
    transformed = tw._transform_user_info(data)
    tw._insert_user(transformed)


def test_tweet_add():
    tw = TwitterHandler()
    dao = Dao.objects.get(Q(name='MolochDAO'))
    data = tw.get_dao_tweets(dao.twitter.username)
    transformed = tw._transform_tweets(data)
    tw._insert_tweets(transformed)    


if __name__ == "__main__":
    #test_twitter_credentials()
    #test_transforms()
    #test_twitter_account_add()
    test_tweet_add()

