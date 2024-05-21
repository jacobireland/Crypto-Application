# CSEE 4119 Spring 2024, Class Project
## Team name: zaj
## Team members (name, GitHub username): Alush Benitez (Alush-Benitez), Jacob Ireland (jacobireland), Zachary Coeur (zjc2106)

# Description

In this project, we built a peer-to-peer blockchain with a simplified cryptocurrrency on top of it. In our implementation, there are miners and traders. Miners keep track of their own copy of the blockchain, receive and verify transactions, mine, verify, and add blocks to the chain, and send out their newly mined blocks to the other miners in the network. Traders take in transactions from the command line and send those transactions to the miners.

# Code Structure

**`miner.py`**: Contains the Miner class which creates and keeps track of one copy of the blockchain. Miners receive and verify transactions, mine, verify, and add blocks to the chain, and send out their newly mined blocks and entire blockchain to other miners in the network. 

**`trader.py`**: Contains the Trader class which is part of the cryptocurrency application. Takes in user input from the command line, creates transaction objects, and sends them to all miners in the network.

**`tracker.py`**: Contains the Tracker class which maintains a peer list of all connected miners and traders in the P2P network. Updates to the peer list are sent out to all miners and traders in the network so they know where to send information.

**`blockchain.py`**: Contains the Block and Blockchain classes which miners use to create and modify copies of the blockchain.

**`transaction.py`**: Contains the Transaction class that traders use to build transaction objects.

**`networking.py`**: Contains helper networking functions for sending packets using the protocol described in DESIGN.md.

# Code Compilation

To run the application, start by running tracker.py:

**python tracker.py [tracker_port]**

Then create as many miners as you want. Create one by running miner.py:

**python miner.py [tracker_ip] [tracker_port] [client_port]**

If you want a distributed blockchain, ensure there is more than one miner running. You can add another miner to the network at any time.

Then create as many traders as you want. Create one by running trader.py:

**python trader.py [tracker_ip] [tracker_port] [client_port] [username]**

Each trader instance will ask you to input a transaction by entering a receiver and amount. Each transaction will be sent to the miners to be added to the blockchain. 
