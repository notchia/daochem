from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import BlockchainAddress, BlockchainTransaction
from daochem.database.models.daos import DaoFramework

_STR_KWARGS = {'max_length': 200, 'null': True}


class FactoryContract(BlockchainAddress):
    name = models.CharField(**_STR_KWARGS)
    dao_framework = models.ForeignKey(
        DaoFramework, 
        on_delete=models.CASCADE,
        related_name='contracts'
    )

    class Meta:
        db_table = "factory_contracts"


class FactoryContractTransaction(BlockchainTransaction):
    factory_contract = models.ForeignKey(
        FactoryContract, 
        on_delete=models.CASCADE,
        related_name='transactions')
    contracts_created = models.ManyToManyField(
        BlockchainAddress,
        related_name='created_by_transaction')

    class Meta:
        db_table = "factory_contract_transactions"