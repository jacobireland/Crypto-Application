# Final Project Design

## Team Members

- Alush Benitez
- Jacob Ireland
- Zachary Coeur

## Overview

The following design document lays out how we implemented a distributed blockchain with a cryptocurrency application built on top of it.

## System Components

### 1. Blockchain

The blockchain implementation is similar to the one found [here](http://blockchain.mit.edu/how-blockchain-works) from MIT. The blockchain itself is a linked list of blocks, each connected by the hash of the previous block. If any part of any block structure is modified, the hash changes, voiding the validity of the blockchain. The hash function used is SHA-256. The proof of work algorithm is finding a Nonce value that results in a hash output starting with four zeros (the input will be the block structure).
    
#### Block Structure
    
-   Block Number (iterative)
-   Nonce
-   Transaction -- structure shown in section 3
-   Previous Hash
-   Current Block Hash
    
#### Blockchain Functions

-   mine() - mine a new block using the data

-   is_valid_chain() - check if blockchain is valid

-   add_block() - add block to end of chain if chain is valid

-   print_chain() - print the data of each block in the blockchain

#### Block Functions

-   calulate_hash() - calulate the hash for a given block

-   is_valid_block()- validate a block by computing the hash and ensuring it follows the protocol

-   serialize() - serialize the block for transmission

-   deserialize() - deserialize JSON string to a Block instance

-   print_block() - print the data of a block


### 2. Peer to peer Protocol
    
The P2P Protocol connects all of the nodes’ local blockchains together, forming a distributed blockchain. To make sure that all nodes know where to send their packets, a tracker program is used to maintain a list of peers that updates when a peer joins or leaves the network. 
  
#### Packet Structure
    
Each packet header between the nodes of the network follows this format:
    
-  Type Indicator (1 byte): An integer value specifying the type of data being transmitted or requested.
-   Data Size (4 bytes): The total size of the accompanying data payload
    
The possible integers are:

- 0: Connection closed, no data
    
-   1: Singular block (miner to miner)
    
-   2: Entire blockchain (miner to miner)
    
-   3: Transaction (trader to miner)

-   4: Peer list update (tracker to peers)

-   5: Initial Miner connection to tracker (miner to tracker)

-   6: Request blockchain (miner to miner)

-   7: Transaction Response (miner to trader)

-   8: Register trader (trader to tracker)

-   9: Unregister trader (trader to tracker)
    
 Using these headers allows each node in the network to make the necessary requests and receptions of the blockchain and cryptocurrency data.

#### Tracker Functions:

-   format_peer_list_packet() - formats the peer list to be sent to peers using the packet structure described above

-   update_peers() - update peer list and send updated list to all peers on network

-   handle_new_peer() - receives messages from peer, updates peer list when peer leaves or joins network
    - target function for thread. New thread gets created when a peer joins the network.

#### Networking Functions

-    recv_custom() - receives message header, parses header, reads data in chunks

-   send_custom() - formats data into packet using packet structure defined above, sends data


### 3. Cryptocurrency Application

The cryptocurrency application is built on top of the distributed blockchain and allows traders to make transactions which are verified and recorded on the distributed blockchain.

#### Miners

Miners make up the nodes of the network. They take incoming transactions from traders and verify the validity of the transaction. They then 'mine' by performing the proof of work algorithm with the valid transaction. They verify transacton validity by working backwards through the blockchain to compare incoming and outgoing transactions, ensuring user has enough funds to send. These are multithreaded: one thread mines while the other waits for a new block or transaction. Competition between miners will be simulated by having miners use random numbers for nonces insead of starting at 0. 

If a new block is received that matches the transaction the miner is working on, the proof of work thread is killed. 

**Assumption/Simplification**: The miners are not be wallet owners in our implementation. This means they do not make transactions or gain anything by creating blocks.

#### Miner Functions:

-   handle_connection() - receives messages from peers, parses message, handles data accordingly
    - target function for thread. New thread gets created whenever a new peer is connected

-   connect_to_peers() - use the peer list sent from the tracker to create a TCP connection with each peer

-   listen_for_peers() - listen for and accept incoming requests from peers who want to start a connection
    - target function for thread that is created upon running miner.py

-   handle_tracker() - connects to tracker and handles all receives and peer list updating
    - target function for thread that is created upon running miner.py

-   handle_chain() - deserialize blockchain and check if it should overwrite current chain

-   broadcast_block() - broadcast block to all peers

-   broadcast_chain() - broadcast chain to all peers

-   request_chain() - request all peers to send their blockchain

#### Traders

Traders interact with the cryptocurrency by making transactions. To simplify the simulation of the market, each trader begins with 100 coins in their wallet. These traders are identified by their usernames inputted by the user in the command line. Transactions are requested by inputting destination address and coin amount. Transactions are sent to all nodes in the network, which are then mined by a miner and added to the blockchain. Once the transaction has been added to the blockchain, the trader receives a confirmation (failure of transaction is also possible). They can also see their coin balance.

#### Transaction Structure

- Sender
- Recipient
- Amount
- Timestamp
- Unique ID (hash of above inputs)

### 4. Technologies Used

All code is implemented in Python. We use Google Cloud VMs to simulate our network, with multiple VMs for both miners and traders. 

### 5. Possible Extensions

Future enhancements could include:

-   RSA signatures to validate transactions
    
-   Group multiple transactions in one block
    
-   Verify transaction using Merkle tree

