from django.db import models

from daochem.database.models.blockchain import BlockchainAddress

class ContractSurface(models.Model):
    """Root entity for the objects and parameters defined within a smart contract"""
    contract_name = models.CharField(max_length=100, default="")
    contract_address = models.ForeignKey(
        BlockchainAddress, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="contract_surface"
    )
    contract_url = models.CharField(max_length=200, null=True)
 
    class Meta:
        db_table = "contract_surfaces"
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_address_or_contract_url",
                check=~models.Q(address__isnull=True, contract_url__isnull=True)
            )
        ]

    def __str__(self):
        address_name = str(self.address)
        return f"{self.name} at {address_name}"


class ContractObject(models.Model):
    
    class Category(models.TextChoices):
        CONTRACT = 'C', 'ContractDefinition'
        FUNCTION = 'F', 'FunctionDefinition'
        MODIFIER = 'M', 'ModifierDefinition'
        EVENT = 'E', 'EventDefinition'
        ENUM = 'N', 'EnumDefinition'
        STRUCT = 'S', 'StructDefinition'

    class Visibility(models.TextChoices):
        EXTERNAL = 'X', 'external'
        PUBLIC = 'U', 'public'
        INTERNAL = 'I', 'internal'
        PRIVATE = 'R', 'private'
        DEFAULT = 'D', 'default'
    
    contract_surface = models.ForeignKey(
        ContractSurface, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="contract_objects"
    )
    name = models.CharField(max_length=100, default="")
    category = models.CharField(
        max_length=1,
        choices=Category.choices,
        null=True
    )
    inheritance = models.CharField(max_length=100, default="")
    modifiers = models.CharField(max_length=100, default="")
    values = models.CharField(max_length=100, default="")
    visibility = models.CharField(
        max_length=1,
        choices=Visibility.choices,
        null=True
    )
    line_numbers = models.CharField(max_length=100, default="")
    description = models.CharField(max_length=200, default="")


    class Meta:
        db_table = "contract_objects"

    def __str__(self):
        return self.name


class ContractParameter(models.Model):
    
    class TypeCategory(models.TextChoices):
        ADDRESS = 'AD', 'address'
        ARRAY = 'AR', 'array'
        BOOL = 'B', 'boolean'
        BYTES = 'BY', 'bytes'
        INT = 'I', 'int'
        MAP = 'M', 'MAP'        
        STRING = 'S', 'string'
        UINT = 'UI', 'uint'
        USERDEFINED = 'UD', 'user-defined'
        PARSE_ERROR = 'PE', 'could not parse'

    class Visibility(models.TextChoices):
        EXTERNAL = 'X', 'external'
        PUBLIC = 'U', 'public'
        INTERNAL = 'I', 'internal'
        PRIVATE = 'R', 'private'
        DEFAULT = 'D', 'default'
    
    contract_object = models.ForeignKey(
        ContractObject, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="contract_parameters"
    )
    name = models.CharField(max_length=100, default="")
    type_category = models.CharField(
        max_length=2,
        choices=TypeCategory.choices,
        null=True
    )
    inheritance = models.CharField(max_length=100, default="")
    modifiers = models.CharField(max_length=100, default="")
    values = models.CharField(max_length=100, default="")
    visibility = models.CharField(
        max_length=1,
        choices=Visibility.choices,
        null=True
    )
    line_numbers = models.CharField(max_length=100, default="")
    description = models.CharField(max_length=200, default="")

    class Meta:
        db_table = "contract_parameters"

    def __str__(self):
        return self.name