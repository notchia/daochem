import os
import json
from daochem.database.etl.trueblocks import TrueblocksHandler
from daochem.database.models.blockchain import BlockchainAddress, DaoFactory


def test_build_chifra_command():
    
    testQueries = [
        {'args': {
            'function': 'list', 
            'value': ['0x01', 
                      '0x02']
            },
         'result': "chifra list 0x01 0x02"
        },
        {'args': {
            'function': 'export', 
            'value': '0x01', 
            'format': 'csv',
            'filepath': 'tmp/test.json'
            },
         'result': "chifra export --fmt csv 0x01 > tmp/test.json"
        }
    ]

    tb = TrueblocksHandler()
    for i, q in enumerate(testQueries):
        assert tb._build_chifra_command(q['args']) == q['result']
        print(f"Passed test build_chifra_command {i}")


def test_run_chifra():

    testQuery = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    
    tb = TrueblocksHandler()
    cmd = tb._build_chifra_command(testQuery)
    result = tb._run_chifra(cmd, parse_as='lines')

    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, list), f"Expected list, not {type(result)}"
    assert len(result) > 148, f"Fewer results found than expected... what gives?"

    print("Passed test run_chifra")


def test_parse_chifra_trace_result():

    tb = TrueblocksHandler()

    testQuery_list = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    cmd = tb._build_chifra_command(testQuery_list)
    txIds = tb._run_chifra(cmd, parse_as='lines')
    testQuery_trace = {
        'function': 'traces', 
        'value': txIds, 
        'format': 'json',
        'args': ['articulate']
    }    
    cmd = tb._build_chifra_command(testQuery_trace)
    result = tb._run_chifra(cmd, parse_as='json')
    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, dict), f"Expected list, not {type(result)}"
    
    parsed = tb._transform_chifra_trace_result(result)
    assert len(parsed) == len(txIds), "Did not get traces of all transactions"

    with open(os.path.join(os.getcwd(), 'tmp/test_parse_chifra_trace_result.json'), 'w') as f:
        json.dump(parsed, f, indent=4)

    print("Passed test parse_chifra_trace_result")


def test_save_chifra_trace_result():
    tb = TrueblocksHandler()

    testQuery_list = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    cmd = tb._build_chifra_command(testQuery_list)
    txIds = tb._run_chifra(cmd, parse_as='lines')
    testQuery_trace = {
        'function': 'traces', 
        'value': txIds, 
        'format': 'json',
        'args': ['articulate']
    }    
    cmd = tb._build_chifra_command(testQuery_trace)
    result = tb._run_chifra(cmd, parse_as='json')
    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, dict), f"Expected list, not {type(result)}"
    
    parsed = tb._transform_chifra_trace_result(result, factory=testQuery_list['value'])
    assert len(parsed) == len(txIds), "Did not get traces of all transactions"

    tb._insert_transactions(parsed)    
    print("Passed test save_chifra_trace_result")


def test_add_or_update_address_traces():
    # Test w/Aragon v0.6 address (has factory object attached)
    tb = TrueblocksHandler()
    addressObj = BlockchainAddress.objects.get(pk='0x595b34c93aa2c2ba0a38daeede629a0dfbdcc559')
    tb.add_or_update_address_traces(addressObj)


def test_add_or_update_address_transactions():
    # Test w/some random Aragon AppProxyUpgradeable address
    tb = TrueblocksHandler()
    try:
        addressObj = BlockchainAddress.objects.get(pk='0x93CF86a83bAA323407857C0A25e768869E12C721')
    except BlockchainAddress.DoesNotExist:
        addressObj = BlockchainAddress(address='0x93CF86a83bAA323407857C0A25e768869E12C721')
        addressObj.save()
    tb.add_or_update_address_transactions(addressObj, local_only=True)


def test_add_or_update_contract_abi():
    tb = TrueblocksHandler()
    addressObj = BlockchainAddress.objects.get(pk='0x38064F40B20347d58b326E767791A6f79cdEddCe')
    tb.add_or_update_contract_abi(addressObj)    


if __name__ == "__main__":
    #test_build_chifra_command()
    #test_run_chifra()
    #test_parse_chifra_trace_result()
    #test_save_chifra_trace_result()
    #test_add_or_update_address_traces()
    #test_add_or_update_address_transactions()
    test_add_or_update_contract_abi()
