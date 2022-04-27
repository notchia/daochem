import os
import re
import json


def load_json(fpath):
    """Load JSON file"""

    r = {}
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
            lines = [re.sub(r'\\{1}', r'\\\\', l) for l in lines] # to prevent invalid \escape JSONDecodeError
            r = json.loads("\n".join(lines))
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError:
        raise

    return r


def save_json(data, fpath):
    """Save JSON file"""

    with open(fpath, 'w') as f:
        json.dump(data, f, indent=4)

    return fpath


if __name__=="__main__":
    from daochem.settings import BASE_DIR
    load_json(os.path.join(BASE_DIR, "tmp/trueblocks_txns_0xafdd1eb2511cd891acf2bff82dabf47e0c914d24.json"))