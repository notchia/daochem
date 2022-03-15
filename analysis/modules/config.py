import os
import sys

# Directories
CWD = os.path.dirname(os.path.abspath(__file__))
CWD = os.sep.join(CWD.split(os.sep)[:-2])
TMPDIR = os.path.join(CWD, 'tmp')
DATADIR = os.path.join(CWD, 'data')

sys.path.append('code/modules')

# Archive node API key
with open(os.path.join(CWD, "archivenode_api_key.txt"), 'r') as f:
    API_KEY = f.read()
