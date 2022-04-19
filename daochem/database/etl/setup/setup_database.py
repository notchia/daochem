import os
import pandas as pd
from django.db import transaction
from django.db.models import Q

import daochem.database.models.trueblocks as tb


SETUP_DIR = os.path.dirname(os.path.abspath(__file__))
FRAMEWORK_DICT = {
    'table': "dao_frameworks",
    'model': tb.DaoFramework,
    'filepath': os.path.join(SETUP_DIR, "dao_frameworks.csv"),
}
FACTORY_DICT = {
    'table': "dao_factory_contracts",
    'model': tb.DaoFactoryContract,
    'filepath': os.path.join(SETUP_DIR, "dao_factories.csv"),
}


@transaction.atomic
def setup_dao_frameworks():
    """Populate each table in the dictionary with csv-format data from the provided file"""

    # Populate frameworks first
    with transaction.atomic():
        table = FRAMEWORK_DICT['table']
        model = FRAMEWORK_DICT['model']
        filepath = FRAMEWORK_DICT['filepath']
        assert os.path.isfile(filepath), f"Provide a csv file from which to populate {table}"
        df = pd.read_csv(filepath, index_col=None)
        for index, row in df.iterrows():
            data = row.to_dict()
            obj = model.objects.create(**data)
            print(obj)
            obj.save()


@transaction.atomic
def setup_dao_factories():
    """Populate each table in the dictionary with csv-format data from the provided file"""

    # Populate frameworks first
    with transaction.atomic():
        table = FACTORY_DICT['table']
        model = FACTORY_DICT['model']
        filepath = FACTORY_DICT['filepath']
        assert os.path.isfile(filepath), f"Provide a csv file from which to populate {table}"
        df = pd.read_csv(filepath, index_col=None)
        for index, row in df.iterrows():
            data = row.to_dict()
            data['dao_framework_id'] = tb.DaoFramework.objects.get(Q(name=data.pop('framework'))).id
            print(data)
            obj = model.objects.create(**data)
            print(obj)
            obj.save()


if __name__ == "__main__":
    #setup_dao_frameworks()
    setup_dao_factories()