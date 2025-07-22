"""
server_main.py
"""

from server import Server

SERVER_IP = "127.0.0.1"
SERVER_PORT = 5555

def main():
    server = Server(SERVER_IP, SERVER_PORT)
    server.run()

if __name__ == "__main__":
    main()