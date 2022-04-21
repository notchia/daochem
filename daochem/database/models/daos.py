from django.db import models

from daochem.database.models.blockchain import BlockchainAddress
from daochem.database.models.twitter import TwitterAccount


_STR_KWARGS = {'max_length': 200, 'null': True}


class Dao(models.Model):
    name = models.CharField(**_STR_KWARGS)
    website = models.URLField(**_STR_KWARGS)
    twitter = models.ForeignKey(
        TwitterAccount,
        on_delete=models.CASCADE,
        null=True,
        related_name='+'
    )
    twitter_url = models.URLField(**_STR_KWARGS)
    deepdao = models.URLField(**_STR_KWARGS)
    boardroom = models.URLField(**_STR_KWARGS)
    governance_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to_dao'
    )

    class Meta:
        db_table = "daos"

    def __str__(self):
        return self.name

    def normalized_name(self):
        return self.name.lower().replace(" ", "")