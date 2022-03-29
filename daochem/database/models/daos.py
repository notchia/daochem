from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import BlockchainAddress


class Dao(models.Model):
    name = models.CharField(**_STR_KWARGS)
    website = models.URLField()
    twitter = models.URLField()
    governance_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to') # TODO: figure out if through and through_fields kwargs are useful here

    class Meta:
        db_table = "daos"

    def __str__(self):
        return self.name


class DaoFramework(models.Model):
    name = models.CharField(**_STR_KWARGS)

    class Meta:
        db_table = "dao_frameworks"
    
    def __str__(self):
        return self.name