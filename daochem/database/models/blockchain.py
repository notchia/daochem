from django.db import models

_STR_KWARGS = {'max_length': 200, 'null': True}


class BlockchainAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=42, default="0x0")
    ens = models.CharField(**_STR_KWARGS)
    contract_name = models.CharField(**_STR_KWARGS)
    contract_abi = models.JSONField(default=dict, null=True)

    class Meta:
        db_table = "blockchain_addresses"

    def __str__(self):
        name = self.ens if self.ens is not None else self.address
        #if self.contract_name is not None:
        #    name += f" ({self.contract_name})"
        return name

    def etherscan_url(self):
        return "https://etherscan.io/address/" + self.address


class BlockchainTransaction(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=20, default="0.0")
    transaction_hash = models.CharField(max_length=66, null=True)
    block_number = models.PositiveIntegerField()
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE, 
        related_name="transactions_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.CASCADE,
        related_name="transactions_to"
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


class DaoFramework(models.Model):
    name = models.CharField(max_length=200, default='not specified')
    website = models.URLField(**_STR_KWARGS)
    github = models.URLField(**_STR_KWARGS)

    class Meta:
        db_table = "dao_frameworks"
    
    def __str__(self):
        return self.name


class DaoFactory(models.Model):
    dao_framework = models.ForeignKey(
        DaoFramework, 
        on_delete=models.CASCADE,
        related_name='factories'
    )
    version = models.CharField(max_length=200, default='not specified')
    contract = models.ForeignKey(
        BlockchainAddress,
        on_delete=models.CASCADE,
        related_name="related_to_factory",
    )
    related_transactions = models.ManyToManyField(
        BlockchainTransaction,
        related_name='related_to_factory'
    )

    class Meta:
        db_table = "dao_factories"

    def __str__(self):
        return f"{self.dao_framework.name}, version {self.version}"

