import os
import json
import subprocess
import logging
from datetime import datetime
from json import JSONDecodeError
from django.db import transaction
from django.db.models import Q

from daochem.database.models import blockchain
from utils.strings import camel_to_snake


class TrueblocksHandler:
    """Run chifra commands and extract, transform, and load the outputs of these
    e.g., `chifra traces --articulate --fmt json [addresses]` 
    """

    def get_index_status(self):
        """Check how up-to-date the index being used is"""
        query_pins = {
            'function': 'pins', 
            'value': '--list', 
            'postprocess': "| tail -n 1"
        }
        cmd = self._build_chifra_command(query_pins)
        pin = self._run_chifra(cmd, parse_as='lines')[0]
        lastPinnedBlock = pin.split()[0].split('-')[-1]

        query_when = {
            'function': 'when', 
            'format': 'json',
            'value': lastPinnedBlock, 
        }
        cmd = self._build_chifra_command(query_when)
        info = self._run_chifra(cmd, parse_as='json')
        lastPinnedTime = datetime.fromtimestamp(info['timestamp'])

        status = {
            'last_pinned_block': lastPinnedBlock,
            'last_pinned_time': lastPinnedTime
        }

        return status

    def add_or_update_address_transactions(self, addressObj, since_block=None, local_only=False):
        """Get list of all transaction ids from index, then export trace 
        
        since_block options: 
            - None: look for most recent appearance of block in |int block_number|False]
        """

        address = addressObj.address

        fpath = os.path.join(os.getcwd(), f"tmp/trueblocks_{address}.json")
        fpath_parsed = os.path.join(os.getcwd(), f"tmp/trueblocks_{address}_parsed.json")

        if not os.path.isfile(fpath):
            # Get list of all transaction IDs
            query_list = {
                'function': 'list', 
                'value': address, 
                'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
            }
            cmd = self._build_chifra_command(query_list)
            txIds = self._run_chifra(cmd, parse_as='lines')

            # Filter transaction IDs for those since most recent appearance in chain
            if since_block is not False:
                if since_block is None:
                    since_block = addressObj.most_recent_appearance()
                else:
                    since_block = str(since_block)

                txIds = list(filter(lambda id: int(id.split('.')[0]) > since_block, txIds))

            # Get all transaction traces
            logging.info("Running chifra traces for list of tx ids...")
            query_trace = {
                'function': 'traces', 
                'value': txIds, 
                'format': 'json',
                'args': ['articulate']
            }  
            cmd = self._build_chifra_command(query_trace)
            result = self._run_chifra(cmd, parse_as='json', fpath=fpath)
        else:
            result = json.loads(fpath)
        
        # Transform to model format, associating with factory if necessary
        factoryAddress = None
        if hasattr(addressObj, 'daofactory'):
            # TODO: check that this is actually catching this case!
            factoryAddress = address
        parsed = self._transform_chifra_trace_result(result, factory=factoryAddress)
        
        if local_only:
            with open(fpath_parsed, 'w') as f:
                json.dump(parsed, f, indent=4)
        if not local_only:
            # Insert transactions
            logging.info("Adding transactions to database...")
            self._insert_transactions(parsed)    

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

    def _transform_chifra_trace_result(self, result, factory=None):
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

            # Link to factory if provided
            if factory is not None:
                txData['factory'] = factory

            # Add transaction to list
            txList.append(txData)

        return txList

    def _insert_transactions(self, dataDicts):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for d in dataDicts:
                print(d['transaction_id'])
                self._insert_transaction(d)

        logging.info(f'Added {len(dataDicts.keys)} transactions to database')

    def _insert_transaction(self, recordDict):
        """Create new transaction from dictionary of model parameters"""

        if recordDict is None or recordDict == {}:
            return
        
        try:
            blockchain.BlockchainTransaction.objects.get(pk=recordDict['transaction_id'])
            logging.debug(f"Skipping transaction {recordDict['transaction_id']} already in database")
            return
        except blockchain.BlockchainTransaction.DoesNotExist:
            pass

        factory = None
        if recordDict.get('factory') is not None:
            factory = recordDict.pop('factory')
           
        # Create smart contract record for from and to addresses if they doesn't already exist
        for addressType in ['from_address', 'to_address']:
            value = recordDict.get(addressType, '0x0')
            addressObj = blockchain.BlockchainAddress.objects.update_or_create(address=value)[0]
            addressObj.save()
            recordDict[addressType] = blockchain.BlockchainAddress.objects.get(pk=value)

        # Create smart contract record for each created contract only if it doesn't already exist
        contractsCreated_orig = recordDict.pop('contracts_created', [])
        for c in contractsCreated_orig:
            contractObj = blockchain.BlockchainAddress.objects.update_or_create(address=c)[0]
            contractObj.save()
        contractsCreated = [blockchain.BlockchainAddress.objects.get(pk=c) for c in contractsCreated_orig]
        
        # Create smart contract 
        tx = blockchain.BlockchainTransaction.objects.create(**recordDict)
        tx.save()
        tx.contracts_created.set(contractsCreated)

        # Add transaction to factory contract list
        if factory is not None:
            fac = blockchain.DaoFactory.objects.get(Q(contract_address=factory))
            fac.related_transactions.add(tx)
    