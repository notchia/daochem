from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import BlockchainAddress
from daochem.database.models.trueblocks import DaoFactoryContractTransaction


class Dao(models.Model):
    name = models.CharField(**_STR_KWARGS)
    website = models.URLField(**_STR_KWARGS)
    twitter = models.URLField(**_STR_KWARGS)
    deepdao = models.URLField(**_STR_KWARGS)
    governance_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to') # TODO: figure out if through and through_fields kwargs are useful here
    created_by_transaction = models.ForeignKey(
        DaoFactoryContractTransaction,
        on_delete=models.CASCADE,
        null=True,
        related_name="%(app_label)s_%(class)s_created",
        related_query_name="%(app_label)s_%(class)ss_created"
    )

    class Meta:
        db_table = "daos"

    def __str__(self):
        return self.name

