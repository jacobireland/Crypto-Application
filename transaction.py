import json
import time
import hashlib

class Transaction:
    def __init__(self, sender, recipient, amount):
        """
        create a transaction dataect
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = time.time()
        self.trans_id = self.generate_id()

    def generate_id(self):
        """
        Generate a unique ID for each transaction with SHA-256
        """
        transaction_string = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}"
        transaction_hash = hashlib.sha256(transaction_string.encode()).hexdigest()
        return transaction_hash
    
    def serialize(self):
        """
        Serialize the transaction for transmission
        """
        return json.dumps({
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'id': self.trans_id
        })
    
    @classmethod
    def deserialize(cls, block_data):
        """
        Deserialize JSON string to a Transaction instance.

        arguments:
        block_data: JSON string representing a transaction.
        """
        data = json.loads(block_data)
        transaction = Transaction(data['sender'], data['recipient'], data['amount'])
        transaction.timestamp = data['timestamp']
        transaction.id = data['id']
        return transaction

