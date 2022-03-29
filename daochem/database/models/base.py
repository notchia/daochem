from django.db import models

_STR_KWARGS = {'max_length': 200, 'null': True}


class BlockchainAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=200, default="0x0")
    ens = models.CharField(**_STR_KWARGS)
    url = models.URLField(**_STR_KWARGS) # TODO: write function that creates Etherscan address for it if not provided
    #chain = models.CharField(_STR_KWARGS) Add for multi-chain support

    class Meta:
        db_table = "blockchain_addresses"


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
    articulated_trace = models.JSONField(default=dict)
    #chain = models.CharField(_STR_KWARGS) Add for multi-chain support

    class Meta:
        abstract = True

