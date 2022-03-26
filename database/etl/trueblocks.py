import os
import re
import json
from django.db import transaction
from json import JSONDecodeError

import utils.strings as s2s
import database.models.trueblocks as tb

#os.environ.setdefault("DJANGO_SETTINGS_MODULE", "database.settings")
#import django
#django.setup()


class TrueblocksETL:
    """Extract, transform, and load the output of the TrueBlocks function call:
    `chifra traces --articulate --fmt json` 
    """

    def __init__(self, datafile):
        assert os.path.isfile(datafile), "Provide an existing JSON file to load"
        try:
            with open(datafile, 'r') as f:
                self.rawData = json.load(f)
        except JSONDecodeError:
            raise

    def upload_to_db(self):
        """Upload all blockchain transactions in file 
        TODO: check if transaction.atomic() is the right function here..."""

        dataDicts = self._transform_data()
        for d in dataDicts:
            with transaction.atomic():    
                self._upload_record(d)

    def _upload_record(self, record):
        """Upload single transaction in file
        TODO: Upload supplementary records (e.g., addresses) if they're not yet in the db"""
    
        # tb.FactoryContractTransaction.objects.update_or_create(record)
        pass

    def _transform_data(self):
        """Return list of nested dictionaries corresponding to unique transactions records"""
        txList = []
        # TODO:
        # Group by unique blockHash; for each of these:
        # Get trace with traceAddress is None, and:
        # Grab blockNumber+transactionIndex, transactionHash, type, articulatedTrace 
        # Get other traces with action[callType] == "creation", and:
        # Grab the super-trace of that trace to get articulatedTrace, and
        # Add that and the newContract address to the list of traces for the transaction
        return txList

