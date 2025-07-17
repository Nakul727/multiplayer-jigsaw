import socket

class NetworkClient:
    # Initializes the network client, but using own computer for now
    def __init__(self, host="127.0.0.1", port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = (host, port)

    # Connect
    def connect(self):
        try:
            self.client.connect(self.addr)
            # if connect, wait to receive a message server
            return self.client.recv(2048).decode()
        except socket.error as e:
            print(f"Connection Error: {e}")
            return None
    # send stuff to server
    def send(self, data):
        try:
            self.client.send(str.encode(data))
            # Wait for a reply from the server
            reply = self.client.recv(2048).decode()
            return reply
        except socket.error as e:
            print(f"Send/Receive Error: {e}")
            return None