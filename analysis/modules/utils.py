import json
import requests
import pandas as pd
import numpy as np


def load_json(fpath):
    """Load JSON or JSONL files"""
    try:
        with open(fpath, 'r') as f:
            r = json.load(f)
    except json.decoder.JSONDecodeError:
        try:
            with open(fpath, 'r') as f:
                r = json.loads(f.read())
        except json.decoder.JSONDecodeError:
            r = {}

    return r


def print_groupby(gb):
    """Print pandas groupby object"""
    for key, item in gb:
        print(gb.get_group(key), "\n")


def normalize_name(s):
    s_norm = s.strip().lower()
    s_norm = s_norm.replace(" ", "")
    s_norm = s_norm.removesuffix('dao')
    return s_norm
