import argparse
import socket
import json
import threading
import time
import networking
import sys
from transaction import Transaction

class Trader:
    def __init__(self, wallet_address):
        self.running = False
        self.wallet_address = wallet_address
        self.miners = []
        self.miner_list_lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.miner_response = None
    
    def register(self, tracker_ip, tracker_port, client_port):
        """
        registers new trader by connecting to tracker

        arguments:
        tracker_ip -- ip of tracker
        tracker_port -- port of tracker
        client_port -- port of client (trader)
        """
        self.running = True
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_socket.bind(('', 0))
        self.tracker_socket.connect((tracker_ip, tracker_port))
        networking.send_custom(self.tracker_socket, str(client_port) + f',{self.wallet_address}', 8)
    
    def unregister(self, tracker_ip, tracker_port, client_port):
        """
        unregisters new trader by sending packet to tracker

        arguments:
        tracker_ip -- ip of tracker
        tracker_port -- port of tracker
        client_port -- port of client (trader)
        """
        self.tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.tracker_socket.bind(('', 0))
        self.tracker_socket.connect((tracker_ip, tracker_port))
        networking.send_custom(self.tracker_socket, str(client_port) + f',{self.wallet_address}', 9)
    
    def tracker_thread(self):
        """
        receives initial miner list from tracker
        """
        while self.running:
            payload, _ = networking.recv_custom(self.tracker_socket) 
            print(f"New miner list received")
            sys.stdout.flush()

            # if trader.py is run before any miners are running
            # receives empty miner list
            if len(payload) == 0:
                continue

            self.miner_list_lock.acquire()
            self.miners = []
            self.miner_list_lock.release()

            miner_list = payload.split(';')
            # add each miner to miner list
            miner_list = payload.split(';')
            for miner in miner_list:
                miner_ip = miner.split(',')[0][2:-1]
                miner_port = miner.split(',')[1][1:-1].strip("'")
                miner_addr = (miner_ip, int(miner_port))
                self.miner_list_lock.acquire()
                self.miners.append(miner_addr)
                self.miner_list_lock.release()

    def handle_connection(self, conn):
        """
        target function for thread that handles connected peers
        """
        data, indicator = networking.recv_custom(conn)
        if indicator == 4:
            print("\nNew miner list received")
            # NEW MINER LIST RECIEVED
            self.miner_list_lock.acquire()
            self.miners = []
            self.miner_list_lock.release()
            # add each to miner list
            miner_list = data.split(';')
            for miner in miner_list:
                miner_ip = miner.split(',')[0][2:-1]
                miner_port = miner.split(',')[1][1:-1].strip("'")
                miner_addr = (miner_ip, int(miner_port))
                self.miner_list_lock.acquire()
                self.miners.append(miner_addr)
                self.miner_list_lock.release()
            print(self.miners)
        elif indicator == 7:
            # MINER RESPONSE TO TRANSACTION REQUEST RECIEVED
            self.miner_response = data
        else:
            print("unknown indicator: " + str(indicator))
        sys.stdout.flush()




    # -------- not sure if we need this func anymore, handle_connection() thread gets started -----
    # -------- from within accept_transactions() function and connects to miners ------------------
    def listen_for_updates(self, client_port):
        """
        target function for thread that listens for peers requesting a
        connection and accepts
        """
        self.socket.bind(('', client_port))
        # sys.stdout.flush()
        self.socket.listen(15)

        while self.running:
            s, peer_addr = self.socket.accept()
            threading.Thread(target=self.handle_connection, args=(s,)).start()
            print('Accepted connection from peer')
            sys.stdout.flush()
    # --------------------------------------------------------------------------------------------

    

    def accept_transactions(self):
        """
        function that takes in transactions from the command line, checks to see if 
        they are valid, and if so, sends them to miners
        """
        while self.running:
            if self.miners:
                # get transaction from command line
                recipient = input("Enter recipient's wallet address: ")
                if recipient == "EXIT":
                    self.running = False
                    continue
                # check inputs
                amount = input("Enter amount to send: ")
                if amount == "":
                    print("Invalid input. Please try again.")
                    continue
                amount = float(amount)
                if recipient and amount > 0:
                    # create transaction
                    transaction = Transaction(self.wallet_address, recipient, amount)
                    self.miner_response = None
                    # iterate through all miners in peer list
                    for miner_ip, miner_port in self.miners:
                        try:
                            # connect to miner
                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            s.connect((miner_ip, miner_port))
                            # send transaction to miner
                            networking.send_custom(s, transaction.serialize(), 3)
                            threading.Thread(target=self.handle_connection, args=(s,)).start()
                        except Exception as e:
                            print(f"Failed to send transaction to {miner_ip}:{miner_port}: {e}")
                    while self.miner_response == None:
                        continue
                    print(self.miner_response)
                    self.miner_response = None
                else:
                    print("Invalid input. Please try again.")
            else:
                print("No miners available, waiting for updates...")
            
            time.sleep(0.5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('tracker_ip', type=str)
    parser.add_argument('tracker_port', type=int)
    parser.add_argument('client_port', type=int)
    parser.add_argument('username', type=str)
    args = parser.parse_args()
    
    trader = Trader(args.username)

    trader.register(args.tracker_ip, args.tracker_port, args.client_port)

    #start thread to accept incomding connections from the tracker or miners
    tracker_thread = threading.Thread(target=trader.tracker_thread)
    tracker_thread.start()

    #start thread to accept incomding connections from the tracker or miners
    listen_thread = threading.Thread(target=trader.listen_for_updates, args=(args.client_port,))
    listen_thread.start()

    #start thread to accept inputs for new transactions
    transaction_thread = threading.Thread(target=trader.accept_transactions)
    transaction_thread.start()

    while trader.running:
        pass

    trader.unregister(args.tracker_ip, args.tracker_port, args.client_port)