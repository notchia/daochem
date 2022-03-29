import os
import json
from daochem.database.etl import trueblocks


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

    tb = trueblocks.TrueblocksHandler()
    for i, q in enumerate(testQueries):
        assert tb._build_chifra_command(q['args']) == q['result']
        print(f"Passed test build_chifra_command {i}")


def test_run_chifra():

    testQuery = {
        'function': 'list', 
        'value': '0x7378ad1ba8f3c8e64bbb2a04473edd35846360f1', 
        'postprocess': "| cut -f2,3 | tr '\t' '.' | grep -v blockNumber"
    }
    
    tb = trueblocks.TrueblocksHandler()
    cmd = tb._build_chifra_command(testQuery)
    result = tb._run_chifra(cmd, parse_as='lines')

    assert result is not None, "No result returned; error encountered"
    assert isinstance(result, list), f"Expected list, not {type(result)}"
    assert len(result) > 148, f"Fewer results found than expected... what gives?"

    print("Passed test run_chifra")


def test_parse_chifra_trace_result():

    tb = trueblocks.TrueblocksHandler()

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


if __name__ == "__main__":
    #test_build_chifra_command()
    #test_run_chifra()
    test_parse_chifra_trace_result()