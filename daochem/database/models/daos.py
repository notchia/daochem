from django.db import models

from daochem.database.models.blockchain import BlockchainAddress
from daochem.database.models.twitter import TwitterAccount
from utils.strings import clean_dao_name

_STR_KWARGS = {'max_length': 200, 'null': True}

SURVEY_QUESTIONS = {
    'q1': "do you feel a sense of agency in the decision-making process?", 
    'q2': "do you trust the decision-making process?", 
    'q3': "does the DAO effectively accomplish its mission?", 
    'q4': "do you feel wanted and/or needed by the DAO?", 
    'q5': "does contributing to this DAO bring you a sense of fulfillment?", 
}

class DeepdaoAddress(models.Model):
    id = models.CharField(primary_key=True, max_length=200, default="")
    type = models.CharField(max_length=50, null=True)
    url = models.URLField(**_STR_KWARGS)
    organization_name = models.CharField(max_length=50, default="")
    description = models.CharField(max_length=50, null=True)
    address = models.ForeignKey(
        BlockchainAddress,
        on_delete=models.CASCADE,
        null=True,
        related_name='deepdao_info'
    )

    @property
    def name_cleaned(self):
        return clean_dao_name(self.organization_name)

    class Meta:
        db_table = "deepdao_addresses"

    def __str__(self):
        return self.id


class Dao(models.Model):
    id = models.CharField(primary_key=True, max_length=25, default="")
    name = models.CharField(**_STR_KWARGS)
    website = models.URLField(**_STR_KWARGS)
    twitter = models.ForeignKey(
        TwitterAccount,
        on_delete=models.CASCADE,
        null=True,
        related_name='dao'
    )
    twitter_url = models.URLField(**_STR_KWARGS)
    deepdao = models.URLField(**_STR_KWARGS)
    boardroom = models.URLField(**_STR_KWARGS)
    governance_addresses = models.ManyToManyField(
        BlockchainAddress,
        related_name='belongs_to_dao'
    )
    deepdao_addresses = models.ManyToManyField(
        DeepdaoAddress,
        related_name='belongs_to_dao'
    )

    class Meta:
        db_table = "daos"

    def __str__(self):
        return self.name

    def normalized_name(self):
        return self.name.lower().replace(" ", "")


class DaoSurveyResponse(models.Model):
    timestamp = models.CharField(max_length=50, null=True)
    dao_name_raw = models.CharField(max_length=50, null=True)
    dao_name_clean = models.CharField(max_length=50, null=True)
    dao = models.ForeignKey(
        Dao,
        on_delete=models.CASCADE,
        null=True,
        related_name='survey_responses'
    )
    q1 = models.PositiveSmallIntegerField()
    q2 = models.PositiveSmallIntegerField()
    q3 = models.PositiveSmallIntegerField()
    q4 = models.PositiveSmallIntegerField()
    q5 = models.PositiveSmallIntegerField()
    comments = models.TextField(null=True)

    class Meta:
        db_table = "survey_responses"
        unique_together = ('timestamp', 'dao_name_clean',)

    def __str__(self):
        return f"{self.dao_name_raw} on {self.timestamp}"