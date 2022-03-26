# daochem-backend

## Install

### Basic install
1. Create a Python environment from `requirements.txt`. If you are using `pip`, make sure Python 3.9 is installed. If you are using `conda`, run the following commands:
```
conda create -n daochem python=3.9
conda activate daochem
pip install -r requirements.txt
```

### TrueBlocks install
This project uses [TrueBlocks](https://trueblocks.io/) and an [Ethereum archive node](https://ethereum.org/en/developers/docs/nodes-and-clients/#archive-node) to get on-chain data on DAOs (e.g., factory contract transactions identifying new DAO addresses, transactions for known DAO addresses). If you do not have access to an archive node, either by running one locally (requires >2TB free memory and ~1 week of time to sync) or via a service (may costs $$), you will not be able to run this part of the code. DAOchem uses [ArchiveNode.io](https://archivenode.io/), which offers free archive node access to Ethereum 

As described in their documentation: "These instructions assume you can navigate directories with the command line and edit configuration files." We recommend adding both Go and TrueBlocks to `PATH` by adding the following line at the end of `~/.profile`:
`export PATH=$PATH:/usr/local/go/bin:$HOME/trueblocks-core/bin`. We also recommend running running `chifra init --all` (or, if you are running your own node, `chifra scrape`). 