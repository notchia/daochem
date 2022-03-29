from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import BlockchainAddress, BlockchainTransaction

class Dao(models.Model):
    name = models.CharField()
    website = models.URLField()
    governance_addresses = models.ManyToManyField(BlockchainAddress) # TODO: figure out if through and through_fields kwargs are useful here


class GovernanceFramework(models.Model):
    factory_name = models.CharField(**_STR_KWARGS)

    class Meta:
        abstract = True
        db_table = "factory_contract"