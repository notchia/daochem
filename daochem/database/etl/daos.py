import os
import logging
from threading import local
import pandas as pd
from numpy import nan
import web3
from django.db import transaction

from daochem.database.etl.trueblocks import TrueblocksHandler, update_or_create_address_record
from daochem.database.models.daos import Dao, DeepdaoAddress
from daochem.settings import BASE_DIR
from utils.strings import clean_dao_name


def load_deepdao_from_csv():

    DEEPDAO_CSV = os.path.join(BASE_DIR, 'tmp/deepdao.csv')
    df = pd.read_csv(DEEPDAO_CSV, index_col=None)

    w3 = web3.Web3(web3.HTTPProvider(os.getenv('RPC_KEY')))

    with transaction.atomic():
        for i, row in df.iterrows():
            name_clean = clean_dao_name(row['organization_name'])

            try:
                dao = Dao.objects.get(pk=name_clean)

                id = row.get('governance_address')
                if id is not None and id is not nan:
                    id = id.lower()
                    data = {
                        'id': id,
                        'type': row['type'],
                        'url': row['url'],
                        'organization_name': row['organization_name'],
                        'description': row['description'].split('Governance')[0].strip()
                    }

                    if w3.isAddress(id):
                        data['address'] = update_or_create_address_record(id)

                    deepdao = DeepdaoAddress.objects.create(**data)
                    deepdao.save()
                    logging.info(f"saved {name_clean}")

                    dao.deepdao_addresses.add(deepdao)
                    dao.save()

            except Dao.DoesNotExist:
                logging.info(f"skipping {name_clean}")
                pass


def get_deepdao_address_txns():
    tb = TrueblocksHandler()
    for deepdao in DeepdaoAddress.objects.filter(address__isnull=False):
        name = deepdao.organization_name.lower()
        print(name)
        if (name not in ['1up', 'bancor', 'barnbridge', 'brightid', 'compound', 'cura dao', 'dxdao', 'lexdao', 'piedao', 'uniswap']):# and not (
        #    any([name.startswith(letter) for letter in 'ab'])
        #    ) and (
        #        deepdao.address.appears_in().count() < 2
        #    ):
        #try:
            print(deepdao.address.address)
            tb.add_or_update_address_transactions(deepdao.address)
        #except Exception as e:
        #    print(e)
#        else:
#            print('skipping...')

if __name__ == "__main__":
    #load_deepdao_from_csv()
    get_deepdao_address_txns()