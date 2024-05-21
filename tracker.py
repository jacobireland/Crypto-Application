import argparse
import socket
import threading
import sys
import networking


class Tracker:
    def __init__(self, port):
        """
        constructor for tracker class

        args:
        port number for tracker socket
        """
        self.peer_list = []
        self.trader_list = []
        self.wallet_list = []
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket.bind(('', port))
        self.peer_list_lock = threading.Lock()
        self.trader_list_lock = threading.Lock()
        print(f'Tracker IP: {socket.gethostbyname(socket.gethostname())}')

    def update_peers(self, type, peer):
        """
        update peer list and send updated list to all peers on network

        args:
        type of update
        peer that is joining/leaving
        """
        if peer[1] == '':
            return

        self.peer_list_lock.acquire()

        # add to peer list
        if type == 'add':
            self.peer_list.append(peer)
        else:
            try:
                self.peer_list.remove(peer)
            except:
                pass
        self.peer_list_lock.release()
        
        packet = self.format_peer_list_packet()

        self.peer_list_lock.acquire()
        # send updated list to all miners
        for p in self.peer_list:
            networking.send_custom(p[0], packet, 4)
        self.peer_list_lock.release()

        self.trader_list_lock.acquire()
        # send updated list to all traders
        for trader in self.trader_list:
            print(f'trader: {trader}')
            sys.stdout.flush()
            networking.send_custom(trader[0], packet, 4)
        self.trader_list_lock.release()

        if type == 'add':
            print(f'\nPeer joined network')
        else:
            print(f'\nPeer left network')
        print(f'Sending updated peer list to all peers: {self.peer_list}')
        sys.stdout.flush()

    def update_traders(self, type, trader):
        """
        add and remove trader from trader_list

        args:
        type of update
        the trader to be added/removed
        """

        trader_info = [trader[0].getpeername()[0], trader[1].split(',')[0]]

        print(f'trader info: {trader_info}')
        print(f'trader_list: {self.trader_list}')
        sys.stdout.flush()

        if type == 'remove':
            self.trader_list_lock.acquire()
            for t in self.trader_list:
                t_info = [t[0].getpeername()[0], t[1].split(',')[0]]
                if t_info == trader_info:
                    self.trader_list.remove(t)
            self.trader_list_lock.release()
        
        else:
            self.trader_list_lock.acquire()
            self.trader_list.append(trader)
            self.trader_list_lock.release()
        
        self.send_wallet_addresses()

    def send_wallet_addresses(self):
        """
        sends up-to-date wallet address list to peers
        """

        current_wallets = ''
        self.trader_list_lock.acquire()
        for t in self.trader_list:
            if current_wallets != '':
                current_wallets += (',')
            current_wallets += (t[1].split(',')[1])
            if t[1].split(',')[1] not in self.wallet_list:
                self.wallet_list.append(t[1].split(',')[1])
        self.trader_list_lock.release()

        all_wallets = ''
        for w in self.wallet_list:
            if all_wallets != '':
                all_wallets += ','
            all_wallets += w
        
        self.peer_list_lock.acquire()
        # send to all miners
        for p in self.peer_list:
            networking.send_custom(p[0], all_wallets+';'+current_wallets, 9)
        self.peer_list_lock.release()


    def handle_new_peer(self, client_socket):
        """
        target function for threads that are started upon a peer joining the
        network. Updates peer list when peers joins and leaves network

        args:
        the client socket information
        """

        client_info = None
        client_port = None
        while True:
            try:
                # receive from client
                msg, indicator = networking.recv_custom(client_socket)
                client_info = [client_socket, msg]
                print(f'client_info: {client_info}')
                print(f'indicator: {indicator}')
                sys.stdout.flush()
                if indicator == 5:
                    # New Miner connected
                    print(f'NEW PEER: {client_info}')
                    sys.stdout.flush()
                    self.update_peers('add', client_info)
                    client_port = msg
                    self.send_wallet_addresses()
                elif indicator == 8:
                    # New trader connected
                    print("TRADER CONNECTED")
                    print(f'client_info: {client_info}')
                    sys.stdout.flush()
                    self.update_traders('add', client_info)
                    # send out updated peer list
                    networking.send_custom(client_info[0], self.format_peer_list_packet(), 4)
                elif indicator == 9:
                    # Trader disconnecting
                    print("TRADER LEAVING")
                    print(f"client_info = {client_info}")
                    sys.stdout.flush()
                    self.update_traders('remove', client_info)
                elif indicator == 0:
                    # if client connection is forcibly closed (CTRL+C)
                    client_socket.close()
                    client_info[1] = client_port
                    self.update_peers('remove', client_info)
                    break
            except ConnectionResetError:
                # if client connection is forcibly closed (CTRL+C)
                client_socket.close()
                self.update_peers('remove', client_info)
                break

    def format_peer_list_packet(self):
        """
        format the peer info into packet

        returns:
        formatted packet ready to be sent
        """
        packet = ''
        self.peer_list_lock.acquire()
        for peer in self.peer_list:
            if packet != '':
                packet += ';'
            peer_info = (peer[0].getpeername()[0], peer[1])
            packet += f'{peer_info}'
        self.peer_list_lock.release()

        sys.stdout.flush()

        return packet

if __name__ == "__main__":
    # accepts commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('tracker_port', type=int)
    args = parser.parse_args()

    #initialize a tracker
    tracker = Tracker(args.tracker_port)

    #accept connections from peers, start handler thread for each connection
    tracker.socket.listen(15)
    while True:
        client, addr = tracker.socket.accept()
        peer_thread = threading.Thread(target=tracker.handle_new_peer, args=(client,))
        peer_thread.start()
