from django.db import models

from utils.blockchain import get_timestamp, unpack_compressed_call

_STR_KWARGS = {'max_length': 200, 'null': True}


class BlockchainAddress(models.Model):
    address = models.CharField(primary_key=True, max_length=42, default="0x0")
    ens = models.CharField(**_STR_KWARGS)
    contract_name = models.CharField(**_STR_KWARGS)
    chifra_list_count = models.PositiveIntegerField(null=True)
    record_modified_date = models.DateField(auto_now=True, null=True)

    @property
    def etherscan_url(self):
        return "https://etherscan.io/address/" + self.address

    def appears_in(self):
        """ Return QuerySet of all transactions in which the address appears
        Uses related_names defined in BlockchainTransaction
        """

        txns = self.transactions_from.all()
        txns = txns.union(self.transactions_to.all())
        txns = txns.union(self.created_by_transaction.all())
        txns = txns.union(self.transactions_involving.all())

        return txns

    class Meta:
        db_table = "blockchain_addresses"

    def __str__(self):
        name = self.ens if self.ens is not None else self.address
        if self.contract_name is not None:
            name += f" ({self.contract_name})"
        return name


class BlockchainTransactionLog(models.Model):
    id = models.CharField(primary_key=True, max_length=50, default="0.0.0") # transactionId.logIndex
    address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="logs_from"
    )
    topics = models.CharField(max_length=267, null=True) # up to 4 space-separated 32-bit words
    event = models.CharField(max_length=200, null=True)
    compressed_log = models.TextField(null=True)

    @property
    def log_dict(self):
        return unpack_compressed_call(self.compressed_log) if self.compressed_log is not None else {}

    class Meta:
        db_table = "blockchain_logs"


class BlockchainTransactionTrace(models.Model):
    id = models.CharField(primary_key=True, max_length=50, default="0.0.0") # transactionId.traceAddress
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="traces_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="traces_to"
    )
    value = models.FloatField()
    compressed_trace = models.TextField(max_length=1000, null=True)
    error = models.CharField(max_length=20, null=True)
    outputs = models.CharField(max_length=1000, null=True) # List of values concatenated with spaces
    delegate = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL,
        null=True,
        related_name="delegate_for_trace"
    )

    @property
    def trace_dict(self):
        return unpack_compressed_call(self.compressed_trace) if self.compressed_trace is not None else {}

    class Meta:
        db_table = "blockchain_traces"


class BlockchainTransaction(models.Model):
    transaction_id = models.CharField(primary_key=True, max_length=20, default="0.0")
    transaction_hash = models.CharField(max_length=66, null=True)
    block_number = models.PositiveIntegerField()
    from_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="transactions_from"
    )
    to_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="transactions_to"
    )
    value = models.FloatField()
    error = models.CharField(max_length=20, null=True)
    call_name = models.CharField(max_length=200, null=True)
    call_inputs = models.JSONField(default=dict, null=True)
    call_outputs = models.CharField(max_length=200, null=True) # List of values concatenated with spaces
    contracts_created = models.ManyToManyField(
        BlockchainAddress,
        related_name='created_by_transaction'
    )
    traces = models.ManyToManyField(
        BlockchainTransactionTrace,
        related_name='originating_from_transaction'
    )
    logs = models.ManyToManyField(
        BlockchainTransactionLog,
        related_name='originating_from_transaction'
    )
    addresses_involved = models.ManyToManyField(
        BlockchainAddress,
        related_name="transactions_involving"
    )

    @property
    def timestamp(self):
        return get_timestamp(self.block_number)

    def contains_address(self, address):
        """Check if an address (string) appears anywhere in the transaction"""

        addresFound = (
            self.to_address.address == address or
            self.from_address.address == address or
            address in [c.address for c in self.contracts_created]
        )

        return addresFound

    class Meta:
        db_table = "blockchain_transactions"

    def __str__(self):
        return self.transaction_id


class ContractAbi(models.Model):
    address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="abis"
    )
    contract_url = models.CharField(max_length=200, null=True)
    name = models.CharField(max_length=100, default="")
    type = models.CharField(max_length=20, default="")
    inputs = models.JSONField(default=dict, null=True) # dictionary of param:type pairs

    class Meta:
        db_table = "contract_abis"
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_address_or_contract_url",
                check=~models.Q(address__isnull=True, contract_url__isnull=True)
            )
        ]

    def __str__(self):
        address_name = str(self.address)
        return f"{self.name} at {address_name}"


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
        on_delete=models.SET_NULL,
        null=True,
        related_name='factories'
    )
    version = models.CharField(max_length=200, default='not specified')
    contract_address = models.OneToOneField(
        BlockchainAddress,
        on_delete=models.SET_NULL,
        null=True
    )
    related_transactions = models.ManyToManyField(
        BlockchainTransaction,
        related_name='related_to_factory'
    )
    is_active = models.BooleanField(default=True)
    dao_creation_functions_str = models.CharField(max_length=50, default="") # List of values concatenated with spaces

    @property
    def dao_creation_functions(self):
        return self.dao_creation_functions_str.split()

    class Meta:
        db_table = "dao_factories"

    def __str__(self):
        return f"{self.dao_framework.name}, version {self.version}"


class EtlMonitor(models.Model):
    name = models.CharField(primary_key=True, max_length=20, default="test")
    last_scrape_time = models.DateTimeField(null=True)
    last_scrape_block = models.PositiveIntegerField(default=0) # TrueBlocks only

    class Meta:
        db_table = "etl_monitors"

    def __str__(self):
        return self.name