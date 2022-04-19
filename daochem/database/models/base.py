from django.db import models

_STR_KWARGS = {'max_length': 200, 'null': True}


class BlockchainAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=200, default="0x0")
    ens = models.CharField(**_STR_KWARGS)
    url = models.URLField(**_STR_KWARGS) # TODO: write function that creates Etherscan address for it if not provided

    class Meta:
        db_table = "blockchain_addresses"

    def __str__(self):
        name = self.ens if self.ens is not None else self.address
        return name


class SmartContract(BlockchainAddress):
    name = models.CharField(**_STR_KWARGS)
    abi = models.JSONField(default=dict, null=True)

    class Meta:
        db_table = "blockchain_contracts"

    def __str__(self):
        name = super().__str__
        if self.name is not None:
            name = f"{name} ({self.name})"
        else:
            name = f"{name} (contract)"
        return name


class BlockchainTransaction(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=200, default="0.0")
    transaction_hash = models.CharField(**_STR_KWARGS)
    block = models.PositiveIntegerField()
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        related_name="%(app_label)s_%(class)s_from",
        related_query_name="%(app_label)s_%(class)ss_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_to",
        related_query_name="%(app_label)s_%(class)ss_to"
    )
    value = models.FloatField()
    articulated_trace = models.JSONField(default=dict, null=True)
    contracts_created = models.ManyToManyField(
        BlockchainAddress,
        related_name='created_by_transaction'
    )

    class Meta:
        db_table = "blockchain_transactions"

    def __str__(self):
        return self.transaction_id
