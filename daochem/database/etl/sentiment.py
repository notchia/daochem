import os
import pandas as pd
from django.db import transaction

from daochem.settings import BASE_DIR
from daochem.database.models.daos import Dao, DaoSurveyResponse
from utils.strings import clean_dao_name


def load_responses_from_csv():
    CSV = os.path.join(BASE_DIR, 'tmp/sentiment.csv')
    df = pd.read_csv(CSV, index_col=None)

    cols = df.columns
    with transaction.atomic():
        for i, row in df.iterrows():
            rDict = {c: row[c] for c in cols}
            rDict['dao_name_clean'] = clean_dao_name(rDict['dao_name_raw'])
            try:
                rDict['dao'] = Dao.objects.get(pk=rDict['dao_name_clean'])
            except:
                pass
            rObj = DaoSurveyResponse.objects.create(**rDict)
            rObj.save()  


if __name__=="__main__":
    load_responses_from_csv()