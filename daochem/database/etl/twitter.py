import os
import json
import subprocess
import logging
import tweepy
from django.db import transaction
from django.db.models import Q
from json import JSONDecodeError

from daochem.database.models.daos import Dao


class TwitterHandler():
    KEYWORDS = ['dao', 'daos', 'proposal', 'proposals', 'snapshot', 'boardroom', 'vote', 'votes', 'voter', 'voting', 'govern', 'governance', 'governing']

    def __init__(self):
        self.client = tweepy.Client(
            bearer_token=os.getenv('TWITTER_API_BEARER_TOKEN'), 
            wait_on_rate_limit=True,
            return_type=dict
        )

    def get_dao_user_info(self, dao):
        """Given Dao model object, get its user information (description, metrics, etc.)"""

        if dao.twitter is None:
            if dao.twitter_url is None:
                return {}
            else:
                username = dao.twitter_url.split('twitter.com/')[-1]
        else:
            username = dao.twitter.username
        
        return self._get_user_info(username)

    def get_dao_tweets(self, dao, since_id=None):
        """Given Dao model object, get its tweets"""

        if dao.twitter is None:
            return {}
        id = Dao.twitter.id

        return self._get_tweets(self, id, since_id=since_id)

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

        for key in ['id', 'name', 'username', 'created_at', 'description', 'url']:
            transformed[key] = data.get(key)

        for metric in ['tweet_count', 'followers_count']:
            transformed[metric] = data['public_metrics'][metric]

        return transformed

    def _transform_tweets(self, response):
        """Transform data (containing list of tweets) to match Tweet model"""

        transformedList = []   
        for data in response.get('data', []):
            transformed = {}
            for key in ['id', 'text', 'created_at']:
                transformed[key] = data.get(key)

            for metric in ['like_count', 'reply_count', 'retweet_count']:
                transformed[metric] = data['public_metrics'][metric]

            urls = []
            for url in data.get('entities',{}).get('urls',[]):
                urls.append(url['expanded_url'])
            urls = list(set(urls)) # Sloppy mitigation of a tweepy (or twitter API?) bug where a single image URL is repeated when multiple images are embedded
            transformed['urls'] = " ".join(urls)

            transformedList.append(transformed)
            
        return transformedList

