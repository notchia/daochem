from django.db import models

_STR_KWARGS = {'max_length': 200, 'null': True}


class BlockchainAddress(models.Model):
    address = models.CharField(max_length=42, null=True)
    ens = models.CharField(_STR_KWARGS)
    contract = models.CharField(_STR_KWARGS)
    url = models.URLField() # TODO: write function that creates Etherscan address for it if not provided
    #chain = models.CharField(_STR_KWARGS) Add for multi-chain support

    #class Meta:
    # Don't create table for this
    #    abstract = True


class BlockchainTransaction(models.Model):
    from_address = models.ForeignKey(BlockchainAddress, on_delete=models.CASCADE)
    to_address = models.ForeignKey(BlockchainAddress, on_delete=models.CASCADE)
    function_call = models.JSONField()
    contracts_created = models.ManyToManyField(BlockchainAddress)

    #class Meta:
    # Don't create table for this
    #    abstract = True

