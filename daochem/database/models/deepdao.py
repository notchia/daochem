from django.db import models

from daochem.database.models.blockchain import BlockchainAddress


class DeepdaoCategory(models.Model):
    """Sourced from `organizations/categories` records"""

    name = models.CharField(max_length=50, unique=True)
    deepdao_id = models.CharField(max_length=36, unique=True) # category_id

    class Meta:
        db_table = "deepdao_categories"

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

    class Platforms(models.TextChoices):
        """Available options under governance>platform for an organization as of 08/30/2022 
        
        The first value in the tuple is what is returned by the API.
        Note that these are not directly connected to the values returned by the ecosystems/gov_platforms API call.
        """

        NONE = '', 'Not specified' 
        ARAGON = 'ARAGON', 'Aragon'
        COLONY = 'COLONY', 'Colony'
        COMPOUND = 'COMPOUND', 'Compound'
        DAOHAUS = 'DAOHAUS', 'DAOhaus'
        DAOSTACK = 'DAOSTACK', 'DAOstack'
        INDEPENDENT = 'INDEPENDENT', 'Independent'
        OPENLAW = 'OPENLAW', 'OpenLaw'
        REALMS = 'REALMS', 'Realms'
        SAFE = 'SAFE', 'Safe'
        SNAPSHOT = 'SNAPSHOT', 'Snapshot' 

    name = models.CharField(max_length=50)
    address = models.CharField(max_length=100)
    platform = models.CharField(
        max_length=11, 
        choices=Platforms.choices, 
        default=Platforms.NONE
    )
    blockchain_address = models.ForeignKey( 
        # Check if the "address" field is a valid blockchain or ENS address: if so, add a link to the corresponding database entry here.
        # Currently only supporting Ethereum addresses. Create this record if it doesn't yet exist. 
        # If ENS address, look up the current owner of the address and then do the above.
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

        unique_together = ('address', 'platform',)

    def __str__(self):
        return f"{self.platform}: {self.address}"


class DeepdaoAddressDeprecated(models.Model):
    """TODO: port over what's in this table to the new format, if it's not already in there"""

    id = models.CharField(primary_key=True, max_length=200, default="")
    type = models.CharField(max_length=50, null=True)
    url = models.URLField(max_length=200, null=True)
    organization_name = models.CharField(max_length=50, default="")
    description = models.CharField(max_length=50, null=True)
    address = models.ForeignKey(
        BlockchainAddress,
        on_delete=models.CASCADE,
        null=True,
        related_name='deepdao_info_deprecated'
    )

    class Meta:
        db_table = "deepdao_addresses_deprecated"

    def __str__(self):
        return self.id