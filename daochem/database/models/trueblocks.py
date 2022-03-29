from django.db import models

from daochem.database.models.base import _STR_KWARGS
from daochem.database.models.base import BlockchainAddress, BlockchainTransaction

_STR_KWARGS = {'max_length': 200, 'null': True}


class FactoryContract(BlockchainAddress):
    name = models.CharField(**_STR_KWARGS)

    class Meta:
        db_table = "factory_contracts"


class FactoryContractTransaction(BlockchainTransaction):
    factory_contract = models.ForeignKey(FactoryContract, on_delete=models.CASCADE)

    "factory_contract_transactions"