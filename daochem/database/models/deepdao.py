from django.db import models

from utils.strings import clean_dao_name
from daochem.database.models.blockchain import BlockchainAddress


class DeepdaoCategory(models.Model):
    name = models.CharField(max_length=50, unique=True)
    deepdao_id = models.CharField(max_length=36, unique=True)

    class Meta:
        db_table = "deepdao_categories"

    def __str__(self):
        return self.name


class DeepdaoGovPlatform(models.Model):
    name = models.CharField(max_length=50, unique=True)
    deepdao_id = models.CharField(max_length=36, unique=True)

    class Meta:
        db_table = "deepdao_gov_platforms"

    def __str__(self):
        return self.name


class DeepdaoDao(models.Model):
    name = models.TextField()
    description = models.TextField()
    url = models.URLField(null=True)
    category = models.CharField(max_length=50, null=True)
    deepdao_id = models.CharField(max_length=36, unique=True)

    class Meta:
        db_table = "deepdao_daos"

    def __str__(self):
        return self.name


class DeepdaoAddress(models.Model):
    name = models.CharField(max_length=50)
    address = models.URLField()
    type = models.CharField(max_length=50) # TODO: add models.TextChoices class to populate this based on the available options 
    blockchain_address = models.ForeignKey(
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
    deepdao_id = models.CharField(max_length=36, unique=True)

    class Meta:
        db_table = "deepdao_addresses"

        unique_together = ('address', 'type',)

    def __str__(self):
        return self.deepdao_address