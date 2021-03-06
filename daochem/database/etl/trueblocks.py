import os
import json
import subprocess
import logging
from datetime import datetime
from pprint import pformat
from django.db import transaction
from django.db.models import Q

from daochem.database.models import blockchain
from utils.strings import camel_to_snake, could_be_address
from utils.files import load_json, save_json
from utils.blockchain import load_txid

# TODO: handle all addresses in lowercase only!


def update_or_create_address_record(address):
    try:
        addressObj = blockchain.BlockchainAddress.objects.get(pk=address)
    except blockchain.BlockchainAddress.DoesNotExist:
        addressObj = blockchain.BlockchainAddress.objects.create(address=address)
        addressObj.save()

    return addressObj


def update_or_create_trace_record(traceDict):
    for addressType in ['from_address', 'to_address', 'delegate']:
        value = traceDict.get(addressType)
        if value is not None:
            traceDict[addressType] = update_or_create_address_record(value)
    traceObj = blockchain.BlockchainTransactionTrace.objects.update_or_create(**traceDict)[0]
    traceObj.save()

    return traceObj


def update_or_create_log_record(logDict):
    value = logDict.get('address', '0x0')
    logDict['address'] = update_or_create_address_record(value)
    logObj = blockchain.BlockchainTransactionLog.objects.update_or_create(**logDict)[0]
    logObj.save()

    return logObj


def update_or_create_transaction_record(recordDict, only_create=False, includeTraces=False):
    """Create new transaction from dictionary of model parameters"""

    if recordDict is None or recordDict == {}:
        return

    factory = None
    if recordDict.get('factory') is not None:
        factory = recordDict.pop('factory')
    
    # Create BlockchainAddress record for from and to addresses if they doesn't already exist
    for addressType in ['from_address', 'to_address']:
        value = recordDict.get(addressType, '0x0')
        recordDict[addressType] = update_or_create_address_record(value)

    # Create BlockchainAddress record for each created contract, if any
    contractsCreated_orig = recordDict.pop('contracts_created', [])
    contractsCreated = []
    for c in contractsCreated_orig:
        contractsCreated.append(update_or_create_address_record(c))

    # Create BlockchainAddress record for each involved address, if any
    addressesInvolved_orig = recordDict.pop('addresses_involved', [])
    addressesInvolved = []
    for c in addressesInvolved_orig:
        if (c not in contractsCreated) and not (
            c == recordDict.get('from_address') or c == recordDict.get('from_address')
        ):
            addressesInvolved.append(update_or_create_address_record(c))

    # Create log record for each log, if any
    logs_orig = recordDict.pop('logs', [])
    logs = []
    for l in logs_orig:
        logs.append(update_or_create_log_record(l))

    # Create trace record for each trace, if any
    if includeTraces:
        traces_orig = recordDict.pop('traces', [])
        traces = []
        for t in traces_orig:
            traces.append(update_or_create_trace_record(t))
    else:
        recordDict.pop('traces', None)

    # Update or create BlockchainTransaction record
    try:
        txn = blockchain.BlockchainTransaction.objects.get(pk=recordDict['transaction_id'])
        for key, value in recordDict.items():
            if key not in ['contracts_created', 'logs', 'traces']:
                setattr(txn, key, value)
            else:
                if key == 'contracts_created':
                    txn.contracts_created.add(*value)
                if key == 'addresses_involved':
                    txn.addresses_involved.add(*value)
                if key == 'logs':
                    txn.logs.add(*value)
                if key == 'traces':
                    txn.traces.add(*value)
        txn.save()
        logging.debug(f"Updated transaction already in database")
        
    except blockchain.BlockchainTransaction.DoesNotExist:
        txn = blockchain.BlockchainTransaction.objects.create(**recordDict)
        txn.save()
        txn.contracts_created.set(contractsCreated)
        txn.addresses_involved.set(addressesInvolved)
        txn.logs.set(logs)
        if includeTraces:
            txn.traces.set(traces)
        logging.debug("Added new transaction to database...")

    # Add transaction to factory contract list
    if factory is not None:
        fac = blockchain.DaoFactory.objects.get(Q(contract_address=factory))
        fac.related_transactions.add(txn)

    return txn


def update_or_create_abi(item, address=None, contract_url=None):
    assert (address is not None) or (contract_url is not None), "Specify at least one"
    abiDict = {
        'address': address,
        'contract_url': contract_url,
        'name': item.get('name'),
        'type': item.get('type'),
    }
    inputs = {i['name']: i['type'] for i in item.get('inputs', [])}
    abiDict['inputs'] = inputs if len(inputs) > 0 else None
    abi = blockchain.ContractAbi.objects.update_or_create(**abiDict)[0]
    abi.save()

    return abi


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

        status = {
            'last_pinned_block': lastPinnedBlock,
            'last_pinned_timestamp': info['timestamp'],
            'last_pinned_datetime': datetime.fromtimestamp(info['timestamp'])
        }

        return status

    def add_or_update_transaction_count(self, addressObj):
        """Get list of transactions found for an address, then update chifra_list_count
        Log shows whether this value was changed
        """

        address = addressObj.address
        txIds = self._get_txids(address)
        try:
            count = len(txIds)
        except:
            count = 0
        
        originalCount = addressObj.chifra_list_count
        if originalCount is None:
            originalCount = 0
        if count > originalCount:
            logging.info(f"Found {count-originalCount} new transactions")
            addressObj.chifra_list_count = count 
            addressObj.save()
        else:
            logging.info(f"No new transactions since {addressObj.record_modified_date} ({originalCount})")

        return count

    def add_or_update_address_traces(self, addressObj, since_block=None, local_only=False, reuseList=False):
        """Get list of all transaction ids from index, then export trace 
        
        since_block options: 
            - None: look for most recent appearance of block in |int block_number|False]
        """

        address = addressObj.address

        fpath = os.path.join(os.getcwd(), f"tmp/trueblocks_traces_{address}.json")
        fpath_parsed = os.path.join(os.getcwd(), f"tmp/trueblocks_{address}_parsed.json")

        if not os.path.isfile(fpath) or not reuseList:
            # Get list of all transaction IDs
            txIds = self._get_txids(address)

            # Filter transaction IDs for those not yet in database
            existingTxIds = blockchain.BlockchainTransaction.objects.filter(pk__in=txIds).values_list('pk', flat=True)
            newTxIds = list(filter(lambda id: id not in existingTxIds, txIds))
            logging.info(f"Processing {len(newTxIds)} transactions (of {len(txIds)} total transactions found)")

            # Get all transaction traces
            logging.info("Running chifra traces for the list of tx ids...")
            query_trace = {
                'function': 'traces', 
                'value': newTxIds, 
                'format': 'json',
                'args': ['articulate']
            }  
            
            cmd = self._build_chifra_command(query_trace)
            result, _ = self._run_chifra(cmd, parse_as='json', fpath=fpath)
        else:
            logging.info(f"Using existing trace list from file for {address}")
            result = load_json(fpath)
        
        # Transform to model format, associating with factory if necessary
        factoryAddress = None
        if hasattr(addressObj, 'daofactory'):
            # TODO: check that this is actually catching this case!
            factoryAddress = address
        parsed = self._transform_chifra_trace_result(result, factory=factoryAddress)
        
        if local_only:
            save_json(parsed, fpath_parsed)
        if not local_only:
            # Insert transactions
            logging.info(f"Adding {len(parsed)} transactions to database...")
            self._insert_transactions(parsed)    

    def add_or_update_address_transactions(self, addressObj, since_block=None, local_only=False):
        """Get list of all transaction ids from index, then export logs
        
        since_block options: 
            - None: look for most recent appearance of block in |int block_number|False]

        TODO: Test!!
        """

        address = addressObj.address

        fpath = os.path.join(os.getcwd(), f"tmp/trueblocks_txns_{address}.json")
        fpath_parsed = os.path.join(os.getcwd(), f"tmp/trueblocks_{address}_parsed.json")

        if not os.path.isfile(fpath):
            # Get list of all transaction IDs
            txIds = self._get_txids(address)

            # Filter transaction IDs for those since most recent appearance in chain
            if since_block is not False:
                if since_block is None:
                    since_block = addressObj.most_recent_appearance()
                else:
                    since_block = str(since_block)

                txIds = list(filter(lambda id: int(id.split('.')[0]) > since_block, txIds))

            # Get all transaction traces
            logging.info("Running chifra transactions for the list of tx ids...")
            query_txn = {
                'function': 'transactions', 
                'value': txIds, 
                'format': 'json',
                'args': ['articulate']
            }  
            
            cmd = self._build_chifra_command(query_txn)
            result, _ = self._run_chifra(cmd, parse_as='json', fpath=fpath)
        else:
            result = load_json(fpath)
        
        # Transform to model format, associating with factory if necessary
        factoryAddress = None
        if hasattr(addressObj, 'daofactory'):
            # TODO: check that this is actually catching this case!
            factoryAddress = address
        parsed = self._transform_chifra_transaction_result(result, factory=factoryAddress)
        
        if local_only:
            save_json(parsed, fpath_parsed)
        if not local_only:
            # Insert transactions
            print(addressObj.appears_in().count())
            logging.info(f"Adding {len(parsed)} transactions to database...")
            self._insert_transactions(parsed)    

    def add_or_update_contract_abi(self, addressObj):
        """Get contract abi and add to address record"""

        # Get ABI
        address = addressObj.address
        query = {
            'function': 'abis',
            'value': address,
            'format': 'json'
        }
        cmd = self._build_chifra_command(query)
        abiDict, _ = self._run_chifra(cmd, parse_as='json')

        # Create ABI records
        data = abiDict.get('data', [])
        for item in data:
            update_or_create_abi(item, address=addressObj)
        logging.info(f"Added {len(data)} ABI records for {address}")


    def _get_txids(self, address):
        """Get list of all transaction IDs for an address from the index"""

        query_list = {
            'function': 'list', 
            'value': address, 
            'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
        }
        
        cmd = self._build_chifra_command(query_list)
        txIds, _ = self._run_chifra(cmd, parse_as='lines')

        return txIds

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

        # Redirect output to fpath using pipe 
        if '>' not in command:
            if 'w' in mode:
                m = ''
            elif 'a' in mode:
                m = ' -a'
            command = command + f"| tee{m} {fpath}"
        else:
            fpath = command.split('>')[-1]
            logging.warning(f"Command already pipes output to {fpath}: will not change this")

        try:
            # Run command and parse output as either JSON or a list of lines
            # NOTE: excapes all backslashes to prevent invalid \escape JSONDecoderError
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
            result_lines = [line.decode('utf-8', errors='replace').replace('\\','\\\\') for line in process.stdout]

            if parse_as == 'json': 
                result_str = "".join(result_lines)
                try:
                    result = json.loads(result_str)
                except json.decoder.JSONDecodeError:
                    logging.warning("Could not parse chifra result as JSON")
                    result = None

            elif parse_as == 'lines':
                result = [s.strip() for s in result_lines]

        except Exception as e:
            logging.error(e)
            result = None

        return result, fpath

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

    def _transform_chifra_result(self, call_type, result=None, fpath=None):
        """Run a chifra-call-specific transform function"""
        assert call_type == 'trace', "Haven't yet supported other call types"
        assert any([result, fpath]), "Provide exactly one of the result of a chifra call or a filepath from which to load the result"

        if fpath is not None:
            result = load_json(fpath)

        if call_type == 'trace':
            parsed = self._transform_chifra_trace_result(result)

        return parsed

    def _transform_chifra_trace_result(self, result, factory=None):
        """From result of chifra traces, return list of nested dictionaries corresponding to unique transactions records"""
        txList = []
        data = result['data']
        data = [{**trace, 'transactionId': load_txid(trace['blockNumber'], trace['transactionIndex'])} for trace in data]

        # Group traces by transaction hash and extract relevant information
        uniqueTxs = list(set([trace['transactionId'] for trace in data]))
        for txId in uniqueTxs:
            txData = {'transaction_id': txId}
            traces = [t for t in data if t['transactionId'] == txId]

            # Get data on originating transaction
            _origin = [t for t in traces if t["traceAddress"] is None]
            if len(_origin) == 0:
                # I hope this never happens...
                logging.warning(f"Could not find a trace without a traceAddress for txn {txId}; expected 1. Skipping...")
                continue            
            elif len(_origin) > 1:
                # Not sure why this happens - don't see anything odd upon inspection of Trueblocks output.
                # When it finds two, it repeats the same one twice, so okay to proceed
                logging.warning(f"Found {len(_origin)} traces with no traceAddress for txn {txId}; expected 1. Using the first one found...")
            origin = _origin[0]
            for key in ['transactionHash', 'blockNumber']:
                txData[camel_to_snake(key)] = origin.get(key)
            for key in ['from', 'to']:
                txData[f"{key}_address"] = origin['action'][key]
            txData['value'] = origin['action']['value']

            aT = origin.get('articulatedTrace', {})
            txData['call_name'] = aT.get('name')
            txData['call_inputs'] = aT.get('inputs')
            outputs = " ".join([v for k,v in aT.get('outputs', {}).items()])
            txData['call_outputs'] = outputs if len(outputs) > 0 else None

            # Get list of contracts created as a result of that transaction
            contractsCreated = []
            _creations = [t for t in traces if t.get('action', {}).get('callType', '') == 'creation']
            for trace in _creations:
                address = trace['result']['newContract']
                contractsCreated.append(address)
            txData['contracts_created'] = contractsCreated

            # BlockchainTransactionTrace model: Lump together remaining compressedTrace + output information, tacking on delegation if found
            # Note: only captures one iteration of delegation (not a deeper callstack)
            _calls = [t for t in traces if t.get('action', {}).get('callType', '') == 'call' and t["traceAddress"] is not None]
            _delegatecalls = [t for t in traces if t.get('action', {}).get('callType', '') == 'delegatecall' and t["traceAddress"] is not None]
            calls = []
            for trace in _calls:
                try:
                    call = {'id': f"{txId}.{trace['traceAddress']}"}
                    action = trace.get('action', {})
                    for key in ['from', 'to']:
                        call[f"{key}_address"] = action.get(key)
                    call['compressed_trace'] = trace.get('compressedTrace', "")
                    call['value'] = action.get('value')
                    call['error'] = trace.get('error')
                    call['outputs'] = trace.get('result', {}).get('output', "")
                    delegates = [
                        d['action']['to'] for d in _delegatecalls if 
                        d['action']['from'] == action.get('to') and
                        d.get('compressedTrace', "") == trace.get('compressedTrace', "") and
                        d['traceAddress'].startswith(trace['traceAddress'])
                    ]
                    call['delegate'] = delegates[0] if len(delegates) > 0 else None
                    calls.append(call)
                except KeyError as e:
                    logging.warning(e)
                    logging.debug(pformat(trace))
                    
            txData['traces'] = calls

            # Link to factory if provided. In some cases (e.g., Aragon 0.8.1) the factory address is actually a delegate for another call...
            if factory is not None:
                txData['factory'] = factory

            # Add transaction to list
            txList.append(txData)

        return txList

    def _transform_chifra_transaction_result(self, result, factory=None):
        """From result of chifra transactions, return list of nested dictionaries corresponding to unique transactions records
        Does not get contracts_created or traces!"""

        txList = []
        data = result.get('data')
        if data is None:
            logging.warning("'data' not found in transaction result")
            return []

        for tx in data:
            txId = load_txid(tx['blockNumber'], tx['transactionIndex'])
            txData = {
                'transaction_id': txId,
                'block_number': tx.get('blockNumber'),
                'transaction_hash': tx.get('hash'),
                'value': tx.get('value'),
            }
            for key in ['from', 'to']:
                txData[f"{key}_address"] = tx[key]

            # Get articulated trace data
            aT = tx.get('articulatedTx', {})
            txData['call_name'] = aT.get('name')
            txData['call_inputs'] = aT.get('inputs')
            outputs = " ".join([v for k,v in aT.get('outputs', {}).items()])
            txData['call_outputs'] = outputs if len(outputs) > 0 else None

            # Get contract created
            contractCreated = tx.get('receipt', {}).get('contractAddress')
            if contractCreated is not None and contractCreated != '0x0':
                txData['contracts_created'] = [contractCreated]

            # Get events emitted by the 'to' address
            logs = []
            addresses_involved = [txData['from_address'], txData['to_address']] + txData.get('contracts_created', [])
            for log in tx.get('receipt', {}).get('logs', []):
                #if log['address'] == txData['to_address']:
                logData = {}
                logData['id'] = f"{txId}.{log['logIndex']}"
                logData['address'] = log['address']
                #topics = " ".join([t for t in log.get('topics', [])])
                #logData['topics'] = topics if len(topics) > 0 else None
                #logData['data'] = log.get('data)
                articulatedLog = log.get('articulatedLog', {})
                logData['event'] = articulatedLog.get('name')
                logData['compressed_log'] = log.get('compressedLog')
                logs.append(logData)
                # Add addresses to list
                addresses_involved.append(logData['address'])
                for value in articulatedLog.get('inputs', {}).values():
                    if could_be_address(value):
                        addresses_involved.append(value)
            if len(logs) > 0:
                txData['logs'] = logs

            txData['addresses_involved'] = list(set(addresses_involved))

            # Add transaction to list
            txList.append(txData)

        return txList

    def _insert_transactions(self, dataDicts, includeTraces=False):
        """Upload all blockchain transactions in file"""

        with transaction.atomic():
            for d in dataDicts:
                logging.debug(f"Updating/creating BlockchainTransaction for {d['transaction_id']}...")
                update_or_create_transaction_record(d, includeTraces)

        logging.info(f'Added {len(dataDicts)} transactions to database')
