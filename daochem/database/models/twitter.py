from django.db import models
from utils.strings import tokenize

_STR_KWARGS = {'max_length': 200, 'null': True}


class TwitterAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=30, default="0")
    name = models.CharField(max_length=50, default="")
    username = models.CharField(max_length=15, default="")
    created_at = models.DateField()
    description = models.CharField(max_length=500, default="")
    metrics_tweet_count = models.PositiveIntegerField()
    metrics_followers_count = models.PositiveIntegerField()
    url = models.URLField(**_STR_KWARGS)

    @property
    def description_tokenized(self):
        return tokenize(self.description)

    def description_clean(self):
        return " ".join(self.description_tokenized) # Not stored as property to reduce redundancy

    class Meta:
        db_table = "twitter_accounts"

    def __str__(self):
        name = self.ens if self.ens is not None else self.address
        if self.contract_name is not None:
            name += f" ({self.contract_name})"
        return name


class Tweet(models.Model):
    id = models.CharField(primary_key=True, max_length=30, default="0")
    text = models.CharField(max_length=280, default="")
    created_at = models.DateField()
    metrics_impression_count = models.PositiveSmallIntegerField()
    metrics_like_count = models.PositiveSmallIntegerField()
    metrics_reply_count = models.PositiveSmallIntegerField()
    metrics_retweet_count = models.PositiveSmallIntegerField()
    metrics_url_link_clicks = models.PositiveSmallIntegerField()

    @property
    def description_tokenized(self):
        return tokenize(self.text)

    def description_clean(self):
        return " ".join(self.text_tokenized) # Not stored as property to reduce redundancy

    class Meta:
        db_table = "tweets"

    def __str__(self):
        return self.text_clean()

