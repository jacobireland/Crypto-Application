from blockchain import Blockchain, Block
import networking
import argparse
import socket
import sys
import threading
import json
import time

class Miner:
    def __init__(self, client_port):
        """
        Constructor for Miner class

        Initializes a miner node, waits to create blockchain
        until after it checks peer list
        """
        self.blockchain = None
        self.peer_list = []
        self.peer_list_lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connections = []
        self.wallets = [[None],[None]]
        
    def handle_connection(self, conn):
        """
        target function for thread that handles connected peers
        """
        while True:
            sys.stdout.flush()
            # receive from socket connection
            data, indicator = networking.recv_custom(conn)
            if indicator == 0:
                # CLOSED CONNECTION ACK
                if conn in self.connections:
                    self.connections.remove(conn)
                conn.close()
                break
            elif indicator == 1:
                # INCOMING BLOCK
                block = Block.deserialize(data)
                if self.blockchain.add_block(block):
                    # broadcast it to all peers
                    self.broadcast_block(block)
                else:
                    self.request_chain()
            elif indicator == 2:
                #INCOMING CHAIN
                self.handle_chain(data)
            elif indicator == 3:
                # INCOMING TRANSACTION
                valid = miner.blockchain.verify_transaction(data, self.wallets)
                if 'TRANSACTION FAILED' not in valid:
                    print('Received transaction')
                    new_block, added = miner.blockchain.mine(data)
                    if added:
                        print("New block mined")
                    else:
                        print("Block received from peer")
                    miner.broadcast_block(new_block)
                # if the error was a duplicate transaction, don't send a failed notice
                if 'transaction already on chain' not in valid:
                    networking.send_custom(conn, valid, 7)
            elif indicator == 6:
                # CHAIN REQUEST
                if self.blockchain is not None:
                    self.broadcast_chain(self.blockchain.blockchain)
            else:
                print("unknown indicator: " + str(indicator))
            sys.stdout.flush()
            # no data, connection was closed
            if not data:
                if conn in self.connections:
                    self.connections.remove(conn)
                conn.close()
                break


    def connect_to_peers(self):
        """
        use the peer list sent from the tracker to create a TCP connection
        to each peer
        """
        self.peer_list_lock.acquire()
        for peer in self.peer_list:
            sys.stdout.flush()
            duplicate = False
            for conn in self.connections:
                if conn.getpeername() == (peer[0],peer[1]):
                    duplicate = True
                    break
            if duplicate:
                continue
            try:
                # connect to peer
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.connect(peer)
                self.connections.append(peer_socket)
                threading.Thread(target=self.handle_connection, args=(peer_socket,)).start()
                print('Connected to peer')
                # immediately request peer's chain
                self.request_chain()
                sys.stdout.flush()
            except:
                print(f'Error connecting to peer: {peer}')
                sys.stdout.flush()

        self.peer_list_lock.release()

    def listen_for_peers(self, client_port):
        """
        target function for thread that listens for peers requesting a
        connection and accepts

        arguments:
        client_port -- port to bind
        """
        self.socket.bind(('', client_port))
        sys.stdout.flush()
        self.socket.listen(15)

        while True:
            peer_socket, peer_addr = self.socket.accept()
            # start thread for each connected peer
            threading.Thread(target=self.handle_connection, args=(peer_socket,)).start()
    
    def update_wallets(self, wallet_addreses):
        """
        uses wallet list sent from tracker to update wallets

        args:
        list of wallets
        """
        all_wallets, cur_wallets = wallet_addreses.split(';')

        self.wallets[1] = []
        for wallet in cur_wallets.split(','):
            if wallet != '':
                self.wallets[1].append(wallet)

        self.wallets[0] = []
        for wallet in all_wallets.split(','):
            if wallet != '':
                self.wallets[0].append(wallet)
    
    def handle_tracker(self, tracker_ip, tracker_port, client_port):
        """
        connects to tracker and handles all receives and peer list updating

        args:
        tracker port
        client port
        """
        # connect to tracker
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_socket.bind(('', 0))
        self.tracker_socket.connect((tracker_ip, tracker_port))
        # send port number
        networking.send_custom(self.tracker_socket, str(client_port), 5)

        while True:
            # receive from tracker
            payload, indicator = networking.recv_custom(self.tracker_socket)

            if indicator == 9:
                # TRACKER SENT WALLET ADDRESSES
                # print('INCOMING WALLET ADDRESSES')
                sys.stdout.flush()
                self.update_wallets(payload)

            elif indicator == 4:
                # TRACKER SENT PEER LIST
                peer_list = payload.split(';')

                # check to see if we need to create the chain
                # we only need to if the peer list only contains
                # ourself and the blockchain hasn't been created
                if len(peer_list) == 1 and self.blockchain is None:
                    self.blockchain = Blockchain()
                    print("No peers. Blockchain created.")

                # reset peer_list
                self.peer_list_lock.acquire()
                self.peer_list = []
                self.peer_list_lock.release()

                # add all peers besides yourself to peerList
                for peer in peer_list:
                    my_info = (self.tracker_socket.getsockname()[0], str(client_port))
                    sys.stdout.flush()
                    if peer != str(my_info):
                        peer_ip = peer.split(',')[0][2:-1]
                        peer_port = peer.split(',')[1][1:-1].strip("'")
                        peer_addr = (peer_ip, int(peer_port))
                        self.peer_list_lock.acquire()
                        self.peer_list.append(peer_addr)
                        self.peer_list_lock.release()

                # connect to peers using updated peer list
                self.connect_to_peers()

    def handle_chain(self, data):
        """
        Deserialize blockchain and check if it should overwrite current chain

        arguments:
        data -- data received over socket
        """

        new_chain = Blockchain([Block.deserialize(block) for block in json.loads(data)])

        # if the chain is none, it is the first chain received from a peer
        if self.blockchain is None:
            print("Initial chain received from peer")
            self.blockchain = new_chain
            self.broadcast_chain(new_chain.blockchain)

        # if new chain is longer, overwrite it
        elif len(new_chain.blockchain) > len(self.blockchain.blockchain) and new_chain.is_valid_chain():
            print("Chain overwritten")
            self.blockchain = new_chain
            self.broadcast_chain(new_chain.blockchain)

        # if blockchain and new_chain are same lengths, take one with lower hash
        elif (self.blockchain.blockchain[-1].hash != new_chain.blockchain[-1].hash and
              len(new_chain.blockchain) == len(self.blockchain.blockchain) and new_chain.is_valid_chain()):
            if self.blockchain.blockchain[-1].hash < new_chain.blockchain[-1].hash:
                self.broadcast_chain(self.blockchain.blockchain)
            else:
                self.blockchain = new_chain
                self.broadcast_chain(new_chain.blockchain)
                print("Chain overwritten")
        sys.stdout.flush()

    def broadcast_block(self, block):
        """
        broadcasts block to all peers

        arguments:
        block -- chain to broadcast
        """
        for conn in self.connections:
            networking.send_custom(conn, block.serialize(), 1)

    def broadcast_chain(self, chain):
        """
        broadcasts chain to all peers

        arguments:
        chain -- chain to broadcast
        """
        serialized_chain = json.dumps([block.serialize() for block in chain])
        for conn in self.connections:
            networking.send_custom(conn, serialized_chain, 2)


    def request_chain(self):
        """
        Request all peers' blockchains
        """
        for conn in self.connections:
            networking.send_custom(conn, "request", 6)

if __name__ == "__main__":
    # accepts commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('tracker_ip', type=str)
    parser.add_argument('tracker_port', type=int)
    parser.add_argument('client_port', type=int)
    args = parser.parse_args()

    # initialize Miner class
    miner = Miner(args.client_port)

    #start thread to communicate with tracker
    tracker_thread = threading.Thread(target=miner.handle_tracker, args=(args.tracker_ip, args.tracker_port, args.client_port))
    tracker_thread.start()

    #start thread to accept incomding connections from other peers
    peer_thread = threading.Thread(target=miner.listen_for_peers, args=(args.client_port,))
    peer_thread.start()

    time.sleep(1)
    while True:
        input("\nPress Enter to Print Blockchain\n")
        miner.blockchain.print_chain()