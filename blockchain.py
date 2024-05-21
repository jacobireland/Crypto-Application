import json
import hashlib
import time
import random
from transaction import Transaction
import sys

BLOCK_DIFFICULTY = 4  # Number of leading zeroes for a valid block
STARTING_WALLET_AMOUNT = 100.0 # amount of money that new traders begin with


class Block:
    def __init__(self, index, nonce, transaction, prev_hash, hash=None):
        """
        Constructor for Block class

        Args:
            index (int): Index of the block in the blockchain
            nonce (int): Nonce used in mining to satisfy the proof-of-work condition
            transaction (str): Transaction data stored in the block
            prev_hash (str): Hash of the previous block in the blockchain
            hash (str): Hash of the block
        """
        self.index = index 
        self.nonce = nonce
        self.transaction = transaction
        self.prev_hash = prev_hash
        self.hash = hash
        if self.hash is None:
            self.hash = self.calculate_hash()


    def calculate_hash(self):
        """
        Calculate the hash of the block

        Returns:
            str: Hash of the block
        """
        block_string = json.dumps({
            'index': self.index,
            'nonce': self.nonce,
            'transaction': self.transaction,
            'prev_hash': self.prev_hash,
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def is_valid_block(self):
        """
        Check if the block is valid

        Returns:
            bool: True if the block is valid, False otherwise
        """
        return (self.hash[:BLOCK_DIFFICULTY] == '0' * BLOCK_DIFFICULTY and
                self.hash == self.calculate_hash())
    
    def serialize(self):
        """
        Serialize the block for transmission
        """
        return json.dumps({
            'index': self.index,
            'nonce': self.nonce,
            'transaction': self.transaction,
            'prev_hash': self.prev_hash,
            'hash': self.hash,
        })
    
    @classmethod
    def deserialize(cls, block_data):
        """
        Deserialize JSON string to a Block instance.

        arguments:
        block_data: JSON string representing block.
        """
        data = json.loads(block_data)
        # Create a new Block object using the data extracted from the JSON
        return Block(data['index'], data['nonce'], data['transaction'], data['prev_hash'], data['hash'])

    def print_block(self):
        """
        Prints block information
        """
        print(f"INDEX: {self.index}")
        print(f"NONCE: {self.nonce}")
        print(f"TRANSACTION: {self.transaction}")
        print(f"PREV HASH: {self.prev_hash}")
        print(f"HASH: {self.hash}")


class Blockchain:
    def __init__(self, chain=None):
        """
        Constructor for Blockchain class

        Initializes the blockchain with a genesis block.
        """
        if chain is not None:
            self.blockchain = chain
        else:
            self.blockchain = []
            block = Block(0, 0, 'GENESIS', '')
            while not block.is_valid_block():
                block.nonce = random.randint(0, 2**32)
                block.hash = block.calculate_hash()
            self.blockchain.append(block)

    def verify_transaction(self, data, wallets):
        """
        verifies if a transaction is valid

        args:
        data -- the transaction
        wallets -- the known wallets

        returns:
        0 if valid
        else returns statement describing error
        """
        transaction = Transaction.deserialize(data)
        # check for duplicates
        if self.transaction_exists(transaction.id):
            return 'TRANSACTION FAILED: transaction already on chain'
        # check to ensure recepient is in known wallets
        if transaction.recipient in wallets[0]:
            if transaction.recipient in wallets[1]:
                # iterate through chain, check to see if sender has enough money
                money = STARTING_WALLET_AMOUNT
                for i in range(1, len(self.blockchain)):
                    t = Transaction.deserialize(self.blockchain[i].transaction)
                    if t.sender == transaction.sender:
                        money -= t.amount
                    if t.recipient == transaction.sender:
                        money += t.amount
                if transaction.amount > money:
                    return f'TRANSACTION FAILED: {transaction.sender} only has ${money} in their account.\n'
                else:
                    money -= transaction.amount
                    return f'Transaction complete\nAccount balance: ${money}\n'
            else:
                return f'TRANSACTION FAILED: {transaction.recipient} is not currently active.\n'
        else:
            return f'TRANSACTION FAILED: {transaction.recipient} is not a valid wallet address.\n'   
        
    def transaction_exists(self, trans_id):
        """
        Check if a transaction with ID already exists in the blockchain

        arguments:
        trans_id -- ID of the transaction to check.
        """
        for block in self.blockchain:
            if block.transaction == "GENESIS":
                continue
            if Transaction.deserialize(block.transaction).id == trans_id:
                return True
        return False
    

    def mine(self, data):
        """
        Mine a new block with the provided data

        Args:
            data (str): Data to be stored in the new block

        Returns:
            block and boolean describing if mined block was added
        """
        index = len(self.blockchain)
        prev_hash = self.blockchain[-1].hash if self.blockchain else ''
        nonce = 0
        # create block
        block = Block(index, nonce, data, prev_hash)
        # check diff nonces to find valid block
        while not block.is_valid_block():
            block.nonce = random.randint(0, 2**32)
            block.hash = block.calculate_hash()
        added = self.add_block(block)
        return block, added

    def is_valid_chain(self):
        """
        Check if the blockchain is valid

        Returns:
            bool: True if the blockchain is valid, False otherwise
        """
        # iterate over chain, checking to see if indexes or hashes are off
        for i in range(1, len(self.blockchain)):
            if not self.blockchain[i].is_valid_block() or self.blockchain[i].prev_hash != self.blockchain[i - 1].hash or self.blockchain[i].index != self.blockchain[i-1].index + 1:
                return False
        return True    

    def add_block(self, block):
        """
        Add block to the end of the chain IF it is valid

        arguments:
        block -- block to add
        """
        if block.prev_hash == self.blockchain[-1].hash and block.is_valid_block():
            self.blockchain.append(block)
            return True
        return False
    
    def print_chain(self):
        """
        prints out each block in the chain
        """
        for block in self.blockchain:
            block.print_block()
