import socket
import threading
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from protocol import *
from game_room import GameRoom

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

        self.clients = []           # (client_socket, client_address)
        self.game_rooms = {}        # game_id -> GameRoom
        self.client_rooms = {}      # client_address -> game_id

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
                self.clients.append((client_socket, client_address))

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

    # -------------------------------------------------------------------------

    def handle_client_connection(self, client_socket, client_address):
        """
        Main thread function to handle communication with a single client
        """
        print(f"New connection established from {client_address}")

        try:
            while self.is_running:
                received_data = client_socket.recv(BUFFER_SIZE)
                if not received_data:
                    break
                
                try:
                    # Deserialize message JSON data 
                    message = deserialize(received_data)

                    # Pass it to handler to that returns response to send back
                    # and broadcast to send to other connected clients
                    response, broadcast = self.handle_message(message, client_address)
                    if response:
                        client_socket.send(response)
                    if broadcast:
                        self.broadcast_to_clients(broadcast, client_address, exclude=client_socket)

                except json.JSONDecodeError:
                    message_str = received_data.decode('utf-8')
                    print(f"Legacy message from {client_address}: {message_str}")
                    client_socket.send(received_data)
                    
        except ConnectionResetError:
            print(f"Client {client_address} disconnected unexpectedly")
        except Exception as error:
            print(f"Error handling client {client_address}: {error}")
        finally:
            self.handle_cleanup_client(client_socket, client_address)

    def handle_message(self, message, client_address):
        """
        Central handler function for each message type
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        print(f"Received {msg_type} from {client_address}")

        response = None
        broadcast = None

        if msg_type == MSG_HOST_GAME:
            response = self.handle_host_game(payload, client_address)
        elif msg_type == MSG_JOIN_GAME:
            response, broadcast = self.handle_join_game(payload, client_address)
        elif msg_type == MSG_LEAVE_GAME:
            response, broadcast = self.handle_leave_game(client_address)
        else:
            response = serialize(MSG_ERROR, {'message': f'Unknown message type: {msg_type}'})

        return response, broadcast

    def broadcast_to_clients(self, message_bytes, exclude=None):
        """
        Broadcase the message_bytes to all other clients
        This will later change to broadcast to all client in the game room
        """
        for sock, _ in self.clients:
            if sock != exclude:
                try:
                    sock.send(message_bytes)
                except Exception:
                    pass

    def handle_cleanup_client(self, client_socket, client_address):
        """
        Post cleanup for client after disconnection from server
        Later this will involve removing the client from game room alongside.
        """
        self.clients = [(sock, addr) for sock, addr in self.clients if sock != client_socket]
        client_socket.close()
        print(f"Connection with {client_address} closed")

    # -------------------------------------------------------------------------

    def handle_host_game(self, payload, client_address):
        """
        Payload must contain the game_name and max_players
        Creates a new game room and returns MSG_HOST_GAME_ACK with game room data
        """

        game_name = payload.get('game_name', 'Unnamed Room')
        max_players = payload.get('max_players', 4)
        
        # Client must not be in any existing game rooms
        if client_address in self.client_rooms:
            return serialize(MSG_ERROR, {'message': 'Already in a game room'})
        
        # Generate a random 6-character alphanumeric game ID
        import random
        import string
        def generate_game_id():
            chars = string.ascii_uppercase + string.digits
            return ''.join(random.choice(chars) for _ in range(6))
        game_id = generate_game_id()
        while game_id in self.game_rooms:
            game_id = generate_game_id()

        # Create a new GameRoom
        room = GameRoom(game_id, game_name, max_players, client_address)
        self.game_rooms[game_id] = room
        self.client_rooms[client_address] = game_id
        print(f"Client {client_address} hosted game: '{game_name}' (ID: {game_id})")

        # Return GameRoom info to client 
        response_payload = {
            'success': True,
            'game_id': game_id,
            'game_name': game_name,
            'max_players': max_players,
            'current_players': room.get_player_count(),
            'players': room.get_players_info(),
            'host': room.get_host_info(),
            'message': f'Successfully hosted game: {game_name}'
        }
        
        return serialize(MSG_HOST_GAME_ACK, response_payload)
    
    def handle_join_game(self, payload, client_address):
        """
        Handle client request to join an existing game room.
        Payload should contain game_id to join.
        """
        pass

    def handle_leave_game(self, client_address):
        """
        Handle client request to leave their current game room.
        Remove client from room and notify other players.
        """
        pass