"""
TCP Server for handling multiple client connections
"""

import socket
import threading
import sys
import os

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from net_protocol import *

HOST = '0.0.0.0'
PORT = 5555
BUFFER_SIZE = 4096

class Server:
    def __init__(self):
        """
        Initialize the TCP server
        """
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((HOST, PORT))
        self.server_socket.listen(5)
        self.is_running = False

    def start(self):
        """
        Start the server and begin accepting client connections
        """
        print(f"Server listening on port {PORT}")
        print(f"Local connection: localhost:{PORT}")
        print(f"LAN connection: {self.get_local_ip_address()}:{PORT}")
        print("Waiting for client connections...")

        self.is_running = True

        try:
            while self.is_running:
                client_socket, client_address = self.server_socket.accept()
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=self.handle_client_connection, 
                    args=(client_socket, client_address)
                )
                client_thread.daemon = True
                client_thread.start()

        except KeyboardInterrupt:
            print("\nReceived shutdown signal...")
        finally:
            self.shutdown()

    def shutdown(self):
        """
        Gracefully shutdown the server
        """
        self.is_running = False
        self.server_socket.close()
        print("Server successfully shutdown")

    def get_local_ip_address(self):
        """
        Get the local IP address for LAN connections
        Connect to external DNS and get ip (doesn't send any data)
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as temp_socket:
                temp_socket.connect(("8.8.8.8", 80))
                local_ip = temp_socket.getsockname()[0]
                return local_ip
        except Exception:
            return "127.0.0.1"

    def handle_client_connection(self, client_socket, client_address):
        """
        Handle communication with a single client
        """

        print(f"New connection established from {client_address}")

        try:
            while self.is_running:
                # Receive data from client
                received_data = client_socket.recv(BUFFER_SIZE)
                if not received_data:
                    break
                
                try:
                    # Try to deserialize as protocol message
                    message = deserialize(received_data)
                    response = self.handle_message(message, client_address)
                    if response:
                        client_socket.send(response)
                except json.JSONDecodeError:
                    # If it's not a protocol message, echo it back (legacy behavior)
                    client_socket.send(received_data)
                
        except ConnectionResetError:
            print(f"Client {client_address} disconnected unexpectedly")
        except Exception as error:
            print(f"Error handling client {client_address}: {error}")
        finally:
            client_socket.close()
            print(f"Connection with {client_address} closed")

    def handle_message(self, message, client_address):
        """
        Handle protocol messages from clients
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        
        print(f"Received {msg_type} from {client_address}")
        
        if msg_type == MSG_CREATE_ROOM:
            return self.handle_host_game(payload, client_address)
        else:
            # Unknown message type
            error_response = serialize(MSG_ERROR, {'message': f'Unknown message type: {msg_type}'})
            return error_response

    def handle_host_game(self, payload, client_address):
        """
        Handle MSG_CREATE_ROOM request
        """
        game_name = payload.get('game_name', 'Unnamed Game')
        max_players = payload.get('max_players', 4)
        
        print(f"Client {client_address} wants to host game: '{game_name}' (max {max_players} players)")
        
        # For now, just acknowledge the request, create create a game room otherwise
        # Just return a game id using the address, later maybe like a 6 digit game room code
        response_payload = {
            'success': True,
            'game_id': f'game_{id(client_address)}', 
            'game_name': game_name,
            'max_players': max_players,
            'message': f'Successfully created game room: {game_name}'
        }
        
        return serialize(MSG_CREATE_ROOM_ACK, response_payload)