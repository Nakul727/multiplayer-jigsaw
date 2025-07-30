import socket
import sys
import os

# importing from the 'shared' directory.
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from protocol import *

class NetworkClient:
    # Initializes the network client, but using own computer for now
    def __init__(self, host="127.0.0.1", port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (host, port)

    # Connect
    def connect(self):
        try:
            self.client.connect(self.addr)
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None
        
    # send stuff to server
    def send(self, msg_type, payload):
        try:
            # Serialize the message using the protocol
            message = serialize(msg_type, payload)
            self.client.send(message)

            # Wait for a reply from the server
            response = self.client.recv(4096)
            if response:
                # Deserialize the response
                return deserialize(response)
            return None
        except socket.error as e:
            print(f"Send/Receive Error: {e}")
            return None
        except Exception as e:
            print(f"An error occurred during communication: {e}")
            return None
        
    # close connection to server
    def close(self):
        self.client.close()
