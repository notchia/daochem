import os
import numpy as np
from pprint import pprint
from datetime import datetime
import pandas as pd

from utils.files import save_json, load_json
from daochem.database.analysis.base import RESULTS_DIR
from daochem.database.models.twitter import TwitterAccount, Tweet, KEYWORDS_DICT

RESULTS_FILE = os.path.join(RESULTS_DIR, 'twitter.json')
MIN_TOTAL_TWEETS = 100 # Only include accounts with *at least* this many total tweets

if not os.path.isfile(RESULTS_FILE):

    accounts = TwitterAccount.objects.all()
    tweets = Tweet.objects.all()

    # Get per-account stats for accounts that meet the tweet threshold
    accountsDict = {}
    accounts_count = 0
    tweets_count = 0
    for account in TwitterAccount.objects.all():
        tweets = account.tweets.all()
        tweet_count = tweets.count()

        if (tweet_count > MIN_TOTAL_TWEETS):
            accounts_count += 1
            tweets_count += tweet_count
            # Get tweet rate info
            birthday = account.created_at
            earliest = tweets.order_by('created_at')[0].created_at
            latest = tweets.order_by('-created_at')[0].created_at
            days_alive = (datetime.now() - datetime(birthday.year, birthday.month, birthday.day)).days
            available_tweet_days = (datetime.now() - datetime(earliest.year, earliest.month, earliest.day)).days
            tweet_rate = 365*tweet_count/available_tweet_days

            # Get governance tweet info
            govtweets = tweets.filter(is_governance_related=True)
            govtweet_count = govtweets.count()
            topics = {topic: 0 for topic in KEYWORDS_DICT.keys()}
            for tweet in govtweets:
                for topic in tweet.governance_topics:
                    topics[topic] += 1

            print(f"{account.name}")
            print(f"  governance: {govtweet_count} ({100*govtweet_count/tweet_count:.1f}%)")
            accountsDict[account.dao.all()[0].id] = {
                'twitter_username': account.username,
                'twitter_url': account.url,
                'account_birthday': account.created_at.strftime("%m/%d/%Y"),
                'account_days_alive': days_alive,
                'account_followers_count': account.followers_count,
                'account_tweet_count': account.tweet_count,
                'available_earliest_tweet_date': earliest.strftime("%m/%d/%Y"),
                'available_latest_tweet_date': latest.strftime("%m/%d/%Y"),
                'available_tweet_days': available_tweet_days,
                'tweet_count': tweet_count,
                'yearly_tweet_rate': float(f"{tweet_rate:.2f}"),
                'gov_tweet_count': govtweet_count,
                'gov_tweet_pct': float(f"{100*govtweet_count/tweet_count:.1f}"),
                'gov_tweet_keywords': topics,
            }
        else:
            print(f"                           EXCLUDING {account.name}")

    # Get overall twitter stats for twitter.html
    stats = {
        'meta': {
            'MIN_TOTAL_TWEETS': MIN_TOTAL_TWEETS,
            'dao_count': accounts_count,
            'tweet_count': tweets_count,
            'governance_tweet_count': tweets.filter(is_governance_related=True).count()
        },
    }

    stats['accounts'] = accountsDict

    df = pd.DataFrame.from_dict(accountsDict,orient='index')

    stats['governance_tweet_stats'] = {
        'mean': df['gov_tweet_pct'].agg('mean'),
        'median': df['gov_tweet_pct'].agg('median'),
        'min': df['gov_tweet_pct'].agg('min'),
        'max': df['gov_tweet_pct'].agg('max'),
    }

    save_json(stats, RESULTS_FILE)

else:
    # Get percentage of governance-related tweets that were about each topic for each dao
    data = load_json(RESULTS_FILE)
    df = pd.DataFrame.from_dict(data['accounts'],orient='index')
    df_cols = pd.DataFrame(columns=KEYWORDS_DICT.keys())
    for i, row in df.iterrows():
        gov_tweets = row['gov_tweet_count']
        topic_pcts = {col: float(f"{100*val/gov_tweets:.1f}") for col, val in row['gov_tweet_keywords'].items()}
        df_cols = df_cols.append(pd.Series(topic_pcts, name=i))

    print(len(df.index))
    print(df['tweet_count'].agg('sum'))

    # Get stats on topic frequency (%) across all daos
    topic_stats = {}
    for topic in df_cols.columns:
        topic_stats[topic] = {
            'mean': float(f"{df_cols[topic].agg('mean'):.1f}"),
            'median': df_cols[topic].agg('median'),
            'min': df_cols[topic].agg('min'),
            'max': df_cols[topic].agg('max'),
        }        

    print(df_cols[KEYWORDS_DICT.keys()])
    pprint(topic_stats)