from django.db import models

from utils.strings import clean_dao_name
from daochem.database.models.blockchain import BlockchainAddress


class DeepdaoCategory(models.Model):
    """Sourced from `organizations/categories` records"""

    name = models.CharField(max_length=50, unique=True)
    deepdao_id = models.CharField(max_length=36, unique=True) # category_id

    class Meta:
        db_table = "deepdao_categories"

    def __str__(self):
        return self.name


class DeepdaoGovPlatform(models.Model):
    """Sourced from `ecosystem/gov_platforms` records"""

    name = models.CharField(max_length=50, unique=True) # platformTitle
    deepdao_id = models.CharField(max_length=36, unique=True) # platformId

    class Meta:
        db_table = "deepdao_gov_platforms"

    def __str__(self):
        return self.name


class DeepdaoDao(models.Model):
    """Sourced from `organizations` records"""

    name = models.TextField()
    description = models.TextField()
    category = models.CharField(max_length=50, null=True) # populate based on category search
    deepdao_id = models.CharField(max_length=36, unique=True) # organizationId

    class Meta:
        db_table = "deepdao_daos"

    def __str__(self):
        return self.name


class DeepdaoAddress(models.Model):
    """Sourced from `governance` field in each `organization` record"""

    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    platform = models.CharField(max_length=50) # e.g., "SNAPSHOT". TODO: add models.TextChoices class to populate this based on the available options 
    blockchain_address = models.ForeignKey( # If the address is on Ethereum specifically, create this record if it doesn't yet exist. If ENS address, look up the current owner of the address.
        BlockchainAddress,
        on_delete=models.CASCADE,
        null=True,
        related_name='deepdao_info'
    )
    deepdao_record = models.ForeignKey(
        DeepdaoDao,
        on_delete=models.CASCADE,
        null=False,
        related_name='deepdao_info'
    )
    deepdao_id = models.CharField(max_length=36, unique=True) # id

    class Meta:
        db_table = "deepdao_addresses"

        unique_together = ('address', 'type',)

    def __str__(self):
        return f"{self.platform}: {self.address}"