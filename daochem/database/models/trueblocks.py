from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import SmartContract, BlockchainTransaction


class DaoFramework(models.Model):
    name = models.CharField(max_length=200, default='not specified')
    website = models.URLField(**_STR_KWARGS)
    github = models.URLField(**_STR_KWARGS)

    class Meta:
        db_table = "dao_frameworks"
    
    def __str__(self):
        return self.name


class DaoFactoryContract(SmartContract):
    dao_framework = models.ForeignKey(
        DaoFramework, 
        on_delete=models.CASCADE,
        related_name='factories'
    )
    version = models.CharField(max_length=200, default='not specified')

    class Meta:
        db_table = "dao_factory_contracts"

    def __str__(self):
        return f"{self.dao_framework.name}, version {self.version}"


class DaoFactoryContractTransaction(BlockchainTransaction):
    factory_contract = models.ForeignKey(
        DaoFactoryContract, 
        on_delete=models.CASCADE,
        related_name='transactions'
    )

    class Meta:
        db_table = "dao_factory_transactions"

    def __str__(self):
        return f"{self.transaction_id} ({self.factory_contract.name})"