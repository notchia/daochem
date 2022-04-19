import os
import re
import json
import time
import subprocess
import logging
from datetime import datetime
from django.db import transaction
from json import JSONDecodeError

import utils.strings as s2s
import daochem.database.models.trueblocks as tbmodel
import daochem.database.models.base as basemodel
from utils.strings import camel_to_snake


class TrueblocksHandler:
    """Run chifra commands and extract, transform, and load the outputs of these
    e.g., `chifra traces --articulate --fmt json [addresses]` 
    """

    def get_factory_contracts(self, params, kwargs_run=None, kwargs_parse=None):
        """Build, run, and parse a chifra command from a query dictionary"""
        cmd = self._build_chifra_command(params)
        if kwargs_run is None:
            kwargs_run = {}
        result = self._run_chifra(cmd, **kwargs_run)
        if kwargs_parse is None:
            kwargs_parse = {}
        parsed = self._parse_chifra_result(result, **kwargs_parse)
        return result

    def _run_chifra(self, command, mode='w', parse_as='json', fpath=None):
        """Call chifra command and return the output as a JSON object

        command: chifra call as you would provide in command line
        parse_as: try to load the result as JSON or as a list of items, one on each line
        mode: overwrite or append to file
        fpath: save output to a specified filepath (otherwise, saves to default JSON file)
        """

        assert parse_as in ['json', 'lines']
        if fpath is None:
            fpath = os.path.join(os.getcwd(), 'tmp/trueblocks.log')

        try:
            # Run command and parse output as JSON
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            result_lines = [line.decode("utf-8") for line in process.stdout]

            if parse_as == 'json': 
                result_str = "".join(result_lines)
                try:
                    result = json.loads(result_str)
                    with open(fpath, mode) as f:
                        json.dump(result, f, indent=4)

                except json.decoder.JSONDecodeError:
                    logging.warning("could not parse chifra result as JSON")
                    result = result_str

            elif parse_as == 'lines':
                with open(fpath, mode) as f:
                    f.writelines(result_lines)
                result = [s.strip() for s in result_lines]

        except Exception as e:
            logging.error(e)
            result = None

        return result

    def _build_chifra_command(self, params):
        """Build a chifra command to run by subprocess
        
        params: dictionary with the following keys:
            function: e.g., list, export
            value: single value or list of values to provide to command (e.g., address(es), transaction(s))
            format: (optional) e.g., csv, json
            args: (optional) list of flags to provide
            kwargs: (optional) dictionary of other keyword:value pairs for chifra
            postprocess: (optional) string corresponding to command line postprocessing commands
            filepath: (optional) provide file path to pipe output to
        """

        # Get required arguments
        fcn = params['function']
        addresses = params['value']
        if isinstance(addresses, list):
            addresses = " ".join(addresses)

        # Set optional arguments
        postprocess = params.get('postprocess', None)

        # Set export format if provided
        if params.get('format', None) is not None:
            format = f"--fmt {params['format']}"
        else:
            format = None

        # Add flags
        if params.get('args', None) is not None:
            argsList = [f"--{f.strip('-')}" for f in params.get('args')]
        else:
            argsList = []

        # Add keyword arguments if provided
        if params.get('kwargs', None) is not None:
            kwargsList = [f"--{k.strip('-')} {v}" for k, v in params.get('kwargs').items()]
        else:
            kwargsList = []

        # Pipe output to file if filepath provided
        if params.get('filepath', None) is not None:
            pipeTo = f"> {params['filepath']}"
        else:
            pipeTo = None

        # Build list
        argList = ["chifra", fcn, *argsList, *kwargsList, addresses]
        if format:
            argList.insert(-1, format)
        if postprocess:
            argList.append(postprocess)
        if pipeTo:
            argList.append(pipeTo)
        
        # Return string to send to subprocess
        return " ".join(argList)

    def _load_result_from_file(self, fpath):
        """Placeholder for loading results from a file"""
        assert os.path.isfile(fpath), "Provide a valid filepath"
        try:
            with open(fpath, 'r') as f:
                result = json.load(f)
        except JSONDecodeError:
            result = None

        return result

    def _transform_chifra_result(self, call_type, result=None, fpath=None):
        """Run a chifra-call-specific transform function"""
        assert type in ['trace'], "Provide a valid chifra command to parse the output of"
        assert any([result, fpath]), "Provide exactly one of the result of a chifra call or a filepath from which to load the result"

        if fpath is not None:
            result = self._load_result_from_file(fpath)

        if call_type == 'trace':
            parsed = self._transform_chifra_trace_result(result)

        return parsed

    def _load_tx_id(self, trace):
        blockNumber = trace['blockNumber']
        txIndex = trace['transactionIndex']
        return f"{blockNumber}.{txIndex}"

    def _unload_tx_id(self, txId):
        blockNumber, txIndex = txId.split('.')
        return {'blockNumber': blockNumber, 'transactionIndex': txIndex}

    def _transform_chifra_trace_result(self, result):
        """Return list of nested dictionaries corresponding to unique transactions records"""
        txList = []
        data = result['data']
        data = [{**trace, 'transactionId': self._load_tx_id(trace)} for trace in data]

        # Group traces by transaction hash and extract relevant information
        uniqueTxs = list(set([trace['transactionId'] for trace in data]))
        for txId in uniqueTxs:
            txData = {'transaction_id': txId}
            traces = [t for t in data if t['transactionId'] == txId]

            # Get data on originating transaction
            _origin = [t for t in traces if t["traceAddress"] is None]
            if len(_origin) == 1:
                origin = _origin[0]
                for key in ['transactionHash', 'blockNumber', 'articulatedTrace']:
                    txData[camel_to_snake(key)] = origin.get(key)
                for key in ['from', 'to']:
                    txData[f"{key}_address"] = origin['action'][key]
                txData['value'] = origin['action']['value']
            else:
                logging.warning(f"Found {len(_origin)} traces with no traceAddress for txn {txId}; expected 1")

            # Get list of contracts created as a result of that transaction
            contractsCreated = []
            _creation = [t for t in traces if t.get('action', {}).get('callType', '') == 'creation']
            for trace in _creation:
                address = trace['result']['newContract']
                contractsCreated.append(address)
            txData['contracts_created'] = contractsCreated

            # Add transaction to list
            txList.append(txData)

        return txList

    def _upsert_transactions(self, dataDicts):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for d in dataDicts:
                self._upsert_transaction(d)

    def _upsert_transaction(self, recordDict):
        """Create new transaction from dictionary of model parameters"""

        if recordDict.get('factory') is not None:
            _model = tbmodel.DaoFactoryContractTransaction
        else:
            _model = basemodel.BlockchainTransaction

        if recordDict is not None and recordDict != {}:
            # Create smart contract record for from and to addresses if they doesn't already exist
            for addressType in ['from_address', 'to_address']:
                value = recordDict[addressType]
                addressObj = basemodel.BlockchainAddress.objects.update_or_create(address=value)[0]
                addressObj.save()
                recordDict[addressType] = basemodel.BlockchainAddress.objects.get(pk=value)

            # Create smart contract record for each created contract only if it doesn't already exist
            contractsCreated_orig = recordDict.pop('contracts_created', [])
            for c in contractsCreated_orig:
                contractObj = basemodel.SmartContract.objects.update_or_create(address=c)[0]
                contractObj.save()
            contractsCreated = [basemodel.SmartContract.objects.get(pk=c) for c in contractsCreated_orig]
            
            # Create smart contract 
            obj = _model.objects.update_or_create(**recordDict)[0]
            obj.save()
            obj.contracts_created.set(contractsCreated)