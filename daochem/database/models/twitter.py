from django.db import models
from django.contrib.postgres.fields import ArrayField
from utils.strings import tokenize

_STR_KWARGS = {'max_length': 200, 'null': True}


class TwitterAccount(models.Model):
    id = models.CharField(primary_key=True, max_length=30, default="0")
    name = models.CharField(max_length=50, default="")
    username = models.CharField(max_length=15, default="")
    created_at = models.DateField()
    description = models.CharField(max_length=500, default="")
    tweet_count = models.PositiveIntegerField()
    followers_count = models.PositiveIntegerField()
    url = models.URLField(**_STR_KWARGS)
    last_updated = models.DateField(auto_now=True)

    @property
    def description_tokenized(self):
        return tokenize(self.description)

    def description_clean(self):
        return " ".join(self.description_tokenized) # Not stored as property to reduce redundancy

    def __str__(self):
        name = self.ens if self.ens is not None else self.address
        if self.contract_name is not None:
            name += f" ({self.contract_name})"
        return name

    class Meta:
        db_table = "twitter_accounts"


class Tweet(models.Model):
    id = models.CharField(primary_key=True, max_length=30, default="0")
    author = models.ForeignKey(
        TwitterAccount,
        on_delete=models.SET_NULL,
        null=True,
        related_name="tweets"
    )
    text = models.CharField(max_length=400, default="")
    created_at = models.DateField()
    like_count = models.PositiveIntegerField() # For tweet, not row
    reply_count = models.PositiveIntegerField()
    retweet_count = models.PositiveIntegerField()
    urls = models.CharField(max_length=300, default="") # Space-separated urls, if multiple
    last_updated = models.DateTimeField(auto_now=True)
    governance_topics = ArrayField(models.CharField(max_length=15, blank=True), null=True)
    is_governance_related = models.BooleanField(default=False)

    @property
    def text_tokenized(self):
        return tokenize(self.text) # Not stored to reduce redundancy

    @property
    def text_clean(self):
        return " ".join(self.text_tokenized) # Not stored to reduce redundancy

    def __str__(self):
        return self.text_clean()

    class Meta:
        db_table = "tweets"


def is_governance_related(governance_topics):
    if len(governance_topics) > 0:
        return True
    return False


def governance_topics(text, names):
    """Find topics in tokenized text"""

    text_tokenized = tokenize(text)

    KEYWORDS_DICT = {
        'propose': ['proposal', 'proposals'],
        'vote': ['vote', 'votes', 'voter', 'voters', 'voting'],
        'decide': ['decide', 'decision', 'decisionmaking', 'decision-making'],
        'discuss': ['forum'],
        'governance': ['governance'],
        'treasury': ['treasury', 'budget']
    }

    keywords = [
        topic for topic, keywords in KEYWORDS_DICT.items() if 
        any([k for k in keywords if k in text_tokenized])
    ]
    keywords.sort()

    return keywords