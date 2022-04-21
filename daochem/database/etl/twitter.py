import os
import logging
import tweepy
from pprint import pprint
from dateutil.parser import isoparse
from django.db import transaction
from django.db.models import Q

from daochem.database.models.daos import Dao
from daochem.database.models.twitter import TwitterAccount, Tweet

class TwitterHandler():
    KEYWORDS = ['dao', 'daos', 'proposal', 'proposals', 'snapshot', 'boardroom', 'vote', 'votes', 'voter', 'voting', 'govern', 'governance', 'governing']

    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_API_BEARER_TOKEN'), 
            wait_on_rate_limit=True,
            return_type=dict
        )

    def upsert_dao_user_info(self, dao):
        """Given Dao model object, insert or update its Twitter user information (description, metrics, etc.)"""
        
        response = self._get_dao_user_info(dao)
        transformed = self._transform_user_info(response)
        id = self._upsert_user(transformed)
        if dao.twitter is None:
            dao.twitter = id
            dao.save()

    def upsert_dao_tweets(self, dao):
        """Given Dao model object, insert or update its Twitter user information (description, metrics, etc.)"""
        
        response = self._get_dao_tweets(dao)
        transformed = self._transform_tweets(response)
        pprint(transformed)
        self._upsert_tweets(transformed)

    def _get_dao_user_info(self, dao):
        """Given Dao model object, get its user information (description, metrics, etc.)"""

        if dao.twitter is None:
            if dao.twitter_url is None:
                return {}
            else:
                username = dao.twitter_url.split('twitter.com/')[-1]
        else:
            username = dao.twitter.username
        
        return self._get_user_info(username)

    def _get_dao_tweets(self, dao, since_id=None):
        """Given Dao model object, get its tweets"""

        if dao.twitter is None:
            return {}
        id = dao.twitter.id

        return self._get_tweets(id, since_id=since_id)

    def _get_user_info(self, username):
        """Get user information (description, metrics, etc.) given username"""
        
        user_fields = ['id', 'name', 'username', 'created_at', 'description', 'public_metrics', 'url']
        user_info = self.client.get_user(username=username, user_fields=user_fields)
        
        return user_info

    def _get_tweets(self, id, since_id=None):
        """Get tweets given user id"""

        kwargs = {
            'exclude': ['retweets', 'replies'], 
            'tweet_fields': ['id', 'text', 'created_at', 'entities', 'public_metrics']
        }
        if since_id is not None:
            kwargs['since_id'] = since_id

        tweets = self.client.get_users_tweets(id, **kwargs)

        return tweets

    def _transform_user_info(self, response):
        """Transform data to match TwitterAccount model"""

        if response.get('data') is None:
            return {}

        transformed = {}        
        data = response['data']

        for key in ['id', 'name', 'username', 'description', 'url']:
            transformed[key] = data.get(key)

        transformed['created_at'] = isoparse(data.get('created_at')).date()

        for metric in ['tweet_count', 'followers_count']:
            transformed[metric] = data['public_metrics'][metric]

        return transformed

    def _transform_tweets(self, response, author_id=None):
        """Transform data (containing list of tweets) to match Tweet model"""

        transformedList = []   
        for data in response.get('data', []):
            transformed = {}
            for key in ['id', 'text', 'created_at']:
                transformed[key] = data.get(key)

            transformed['created_at'] = isoparse(data.get('created_at'))

            for metric in ['like_count', 'reply_count', 'retweet_count']:
                transformed[metric] = data['public_metrics'][metric]

            urls = []
            for url in data.get('entities',{}).get('urls',[]):
                urls.append(url['expanded_url'])
            urls = list(set(urls)) # Sloppy mitigation of a tweepy (or twitter API?) bug where a single image URL is repeated when multiple images are embedded
            transformed['urls'] = " ".join(urls)

            if data.get('author_id') is None:
                transformed['author'] = author_id
            else:
                transformed['author'] = data['author_id']

            transformedList.append(transformed)
            
        return transformedList

    def _upsert_user(self, userDict):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            user = TwitterAccount.objects.update_or_create(**userDict)[0]
            user.save()

        return user

    def _upsert_tweets(self, tweets):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for t in tweets:
                self._upsert_tweet(t)

    def _upsert_tweet(self, recordDict):
        """Create new transaction from dictionary of model parameters"""

        if recordDict is None or recordDict == {}:
            return
        
        try:
            tweet = Tweet.objects.get(pk=recordDict.pop('id'))
            for key, value in recordDict.items():
                setattr(tweet, key, value)
            tweet.save()
        except Tweet.DoesNotExist:
            tweet = Tweet.objects.create(**recordDict)
            tweet.save()

        return tweet