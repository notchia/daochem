from django.db import models

from daochem.database.models.blockchain import BlockchainAddress
from daochem.database.models.twitter import TwitterAccount
from utils.strings import clean_dao_name

_STR_KWARGS = {'max_length': 200, 'null': True}


class DeepdaoAddress(models.Model):
    id = models.CharField(primary_key=True, max_length=200, default="")
    type = models.CharField(max_length=50, null=True)
    url = models.URLField(**_STR_KWARGS)
    organization_name = models.CharField(max_length=50, default="")
    description = models.CharField(max_length=50, null=True)
    address = models.ForeignKey(
        BlockchainAddress,
        on_delete=models.CASCADE,
        null=True,
        related_name='deepdao_info'
    )

    @property
    def name_cleaned(self):
        return clean_dao_name(self.organization_name)

    class Meta:
        db_table = "deepdao_addresses"

    def __str__(self):
        return self.id


class Dao(models.Model):
    id = models.CharField(primary_key=True, max_length=25, default="")
    name = models.CharField(**_STR_KWARGS)
    website = models.URLField(**_STR_KWARGS)
    twitter = models.ForeignKey(
        TwitterAccount,
        on_delete=models.CASCADE,
        null=True,
        related_name='dao'
    )
    twitter_url = models.URLField(**_STR_KWARGS)
    deepdao = models.URLField(**_STR_KWARGS)
    boardroom = models.URLField(**_STR_KWARGS)
    governance_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to_dao'
    )
    deepdao_addresses = models.ManyToManyField(
        DeepdaoAddress,
        related_name='belongs_to_dao'
    )

    class Meta:
        db_table = "daos"

    def __str__(self):
        return self.name

    def normalized_name(self):
        return self.name.lower().replace(" ", "")
