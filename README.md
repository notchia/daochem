# daochem-backend

**DAOchem** is a solution in which on- and off-chain governance data sources react to produce a holistic view of DAO governance. We integrate data on **smart contract parameters**, **voting activity**, **Twitter activity**, and **contributor sentiment** to help DAO creators and contributors understand the governance landscape.

## Overarching questions driving our work
Are (on-chain) DAOs working right now? Are they achieving their stated goals, and how do members feel about their experience in the DAO?
- What governance systems are DAO members choosing to implement, with what "laws"?
- In what ways are DAO members participating (in measureable ways)? Does DAO member activity relate to the chosen systems?
- How satisfied are DAO members with their own experiences in the DAO and with the health/success of the DAO overall? How do these experiences relate to the chosen systems?

## Where are we getting the data?
### New datasets
#### Governance-related smart contract parameters
DAOs that have an on-chain component to their governance process often deploy their smart contracts through a platform like Arargon or DAOHaus. In these cases, the contract is created by the platform's factory contract. We are accessing the entire transaction history of these factory contracts using [TrueBlocks](https://trueblocks.io/) and an archive node (generously provided by [ArchiveNode.io](https://archivenode.io/), to pull out the parameters set at the time of deployment for each set of DAO governance smart contracts.
#### Twitter engagement with governance-related tweets
Twitter is a common way for a DAO to engage with its membership. We are using the Twitter API to acquire the follower counts and the contents and engagement of up to the 200 most recent tweets for DAOs with Twitter accounts. From these, we select those related to governance (based on keyword searchs) to guage how frequently the DAO communicates about its governance process and how engaged the DAO's followers are with these.
#### Contributor sentiment survey
Quantitative data on DAO governance is useful, but ignores an important component of a DAO's operations: its contributors. Similar to how GlassDoor provides some context about what it's like to actually work at a company, we are deploying a short survey to understand how DAO contributors feel about, for example, whether the governance process is legitimate, or whether their contribution is valued.
### Sourced datasets
#### DeepDAO
[DeepDAO](https://archivenode.io/) generously provided us with a mapping of DAOs to their governance-related addresses, which we are using for data linking.
#### Boardroom
Through the [Boardroom](https://www.boardroom.info/) API, we obtained the proposal creation and voting activity of DAOs that used an on-chain voting mechanism or Snapshot. We also used this to assign categories to DAOs.
#### DAOHQ
We referenced [DAOHQ](https://www.daohq.co/) to assign categories to DAOs.

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
