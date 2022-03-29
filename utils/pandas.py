import pandas as pd


def print_groupby(gb):
    """Print pandas groupby object"""
    for key, item in gb:
        print(gb.get_group(key), "\n")
