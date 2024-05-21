import argparse
import socket
import threading

class TestMiner():
    def __init__(self, port):
        self.close = False
        self.port = port
    
    def clientSock(self):
        HOST = "127.0.0.1"  # The server's hostname or IP address
        PORT = self.port  # The port used by the server

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            s.connect((HOST, PORT))
            print('connected to tracker')
            while True:
                if self.close == True:
                    s.sendall('close'.encode())
                    break
                try:
                    data = s.recv(1024)
                    print(f'received: {data.decode()}')
                except:
                    pass


if __name__ == "__main__":
    # accepts commandline arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('trackerPort', type=int)
    args = parser.parse_args()
    
    testMiner = TestMiner(args.trackerPort)

    thread = threading.Thread(target=testMiner.clientSock)
    thread.start()

    data = input("\nPress enter at any time to terminate connection to network\n\n")
    testMiner.close = True

    thread.join()
