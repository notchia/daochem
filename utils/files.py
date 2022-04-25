import os
import json


def load_json(fpath):
    """Load JSON file"""

    r = {}
    try:
        with open(fpath, 'r', encoding='utf-8', errors='replace') as f:
            r = json.load(f)
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