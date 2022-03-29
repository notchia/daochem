import os
import json


def load_json(path):
    """Load JSON file"""

    r = {}

    try:
        with open(path, 'r') as f:
            r = json.load(f)
    except FileNotFoundError:
        raise
    except json.decoder.JSONDecodeError:
        raise

    return r

