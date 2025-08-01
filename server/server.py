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

                    # Temporary
                    print(json.dumps(message, indent=2))

                    # Pass it to handler to that returns response to send back
                    # and broadcast to send to other connected clients
                    response, broadcast = self.handle_message(message, client_address)
                    if response:
                        client_socket.send(response)
                    if broadcast:
                        # Determine the type of broadcast and send to the correct room
                        broadcast_data = json.loads(broadcast.decode('utf-8'))
                        brod_type = broadcast_data['type']
                        # For leave game, use the game_id in the payload
                        if brod_type == MSG_PLAYER_LEFT_BROD:
                            game_id = broadcast_data['payload']['game_id']
                            self.broadcast_to_room(broadcast, game_id, exclude=client_socket)
                        # For all *_BROD messages, broadcast to the sender's room
                        elif brod_type.endswith('_BROD'):
                            if client_address in self.client_rooms:
                                game_id = self.client_rooms[client_address]
                                self.broadcast_to_room(broadcast, game_id, exclude=client_socket)
                        else:
                            # Fallback: broadcast to all clients in the same room
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
        Central handler function for each message type.
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        print(f"Received {msg_type} from {client_address}")

        response = None
        broadcast = None

        if msg_type == MSG_HOST_GAME:
            # Only ACK
            response, broadcast = self.handle_host_game(payload, client_address)
        elif msg_type == MSG_JOIN_GAME:
            response, broadcast = self.handle_join_game(payload, client_address)
        elif msg_type == MSG_LEAVE_GAME:
            response, broadcast = self.handle_leave_game(client_address)
        elif msg_type == MSG_LOCK_OBJECT:
            response, broadcast = self.handle_lock_object(payload, client_address)
        elif msg_type == MSG_RELEASE_OBJECT:
            response, broadcast = self.handle_release_object(payload, client_address)
        else:
            response = serialize(MSG_ERROR, {'message': f'Unknown message type: {msg_type}'})

        return response, broadcast

    def broadcast_to_room(self, message_bytes, game_id, exclude=None):
        """
        Broadcast message to all clients in a specific game room 
        except the excluded client.
        """
        if game_id not in self.game_rooms:
            return
        
        room = self.game_rooms[game_id]
        
        # Find client sockets for players in this room
        for sock, addr in self.clients:
            if addr in room.players and sock != exclude:
                try:
                    sock.send(message_bytes)
                except Exception as e:
                    print(f"Failed to send to {addr}: {e}")
    
    def broadcast_to_clients(self, message_bytes, client_address, exclude=None):
        """
        Broadcast message to all clients in the same room as the client_address.
        Updated to only broadcast to room members, not all connected clients.
        """
        # Find which room the client is in
        if client_address in self.client_rooms:
            game_id = self.client_rooms[client_address]
            self.broadcast_to_room(message_bytes, game_id, exclude)
        else:
            print(f"Client {client_address} is not in any room for broadcasting")

    def broadcast_to_room(self, message_bytes, game_id, exclude=None):
        """
        Broadcast message to all clients in a specific game room except the excluded client.
        """
        if game_id not in self.game_rooms:
            return
        
        room = self.game_rooms[game_id]
        
        # Find client sockets for players in this room
        for sock, addr in self.clients:
            if addr in room.players and sock != exclude:
                try:
                    sock.send(message_bytes)
                except Exception as e:
                    print(f"Failed to send to {addr}: {e}")

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
            response = serialize(MSG_ERROR, {'message': 'Already in a game room'})
            return response, None
        
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
        
        response = serialize(MSG_HOST_GAME_ACK, response_payload)
        return response, None

    def handle_join_game(self, payload, client_address):
        """
        Handle client request to join an existing game room.
        Payload should contain game_id to join.
        """
        game_id = payload.get('game_id')
        
        # Validate game_id is provided
        if not game_id:
            response = serialize(MSG_ERROR, {'message': 'Game ID is required'})
            broadcast = None
            return response, broadcast
        
        # Check if client is already in a game room
        if client_address in self.client_rooms:
            response = serialize(MSG_ERROR, {'message': 'Already in a game room'})
            broadcast = None
            return response, broadcast
        
        # Check if game room exists
        if game_id not in self.game_rooms:
            response = serialize(MSG_ERROR, {'message': 'Game room not found'})
            broadcast = None
            return response, broadcast
        
        room = self.game_rooms[game_id]
        
        # Check if room is full
        if room.is_full():
            response = serialize(MSG_ERROR, {'message': 'Game room is full'})
            broadcast = None
            return response, broadcast
        
        # Add player to the room
        if room.add_player(client_address):
            self.client_rooms[client_address] = game_id
            print(f"Client {client_address} joined game: '{room.game_name}' (ID: {game_id})")
            
            # Prepare response for the joining client
            response_payload = {
                'success': True,
                'game_id': game_id,
                'game_name': room.game_name,
                'max_players': room.max_players,
                'current_players': room.get_player_count(),
                'players': room.get_players_info(),
                'host': room.get_host_info(),
                'message': f'Successfully joined game: {room.game_name}'
            }
            
            # Prepare broadcast for other players in the room
            broadcast_payload = {
                'game_id': game_id,
                'player': {"ip": client_address[0], "port": client_address[1]},
                'current_players': room.get_player_count(),
                'players': room.get_players_info()
            }
            
            response = serialize(MSG_JOIN_GAME_ACK, response_payload)
            broadcast = serialize(MSG_PLAYER_JOINED_BROD, broadcast_payload)
            return response, broadcast
        else:
            response = serialize(MSG_ERROR, {'message': 'Failed to join game room'})
            broadcast = None
            return response, broadcast

    def handle_leave_game(self, client_address):
        """
        Handle client request to leave their current game room.
        Remove client from room and notify other players.
        """
        # Check if client is in any game room
        if client_address not in self.client_rooms:
            response = serialize(MSG_ERROR, {'message': 'Not in any game room'})
            broadcast = None
            return response, broadcast
        
        game_id = self.client_rooms[client_address]
        room = self.game_rooms[game_id]
        
        # Store original host info before removal
        was_host = (client_address == room.host_address)
        old_host = room.get_host_info()
        
        # Remove player from the room
        host_changed = room.remove_player(client_address)
        del self.client_rooms[client_address]
        
        print(f"Client {client_address} left game: '{room.game_name}' (ID: {game_id})")
        
        # Check if room is now empty and should be deleted
        if room.is_empty():
            del self.game_rooms[game_id]
            print(f"Game room '{room.game_name}' (ID: {game_id}) deleted - no players remaining")
            
            response_payload = {
                'success': True,
                'message': 'Successfully left game room'
            }
            response = serialize(MSG_LEAVE_GAME_ACK, response_payload)
            broadcast = None
            return response, broadcast
        
        # Prepare response for the leaving client
        response_payload = {
            'success': True,
            'message': 'Successfully left game room'
        }

        # Prepare broadcast for remaining players in the room
        broadcast_payload = {
            'game_id': game_id,
            'player': {"ip": client_address[0], "port": client_address[1]},
            'current_players': room.get_player_count(),
            'players': room.get_players_info()
        }
        
        # If host changed, include new host info in broadcast
        if host_changed:
            broadcast_payload['new_host'] = room.get_host_info()
            broadcast_payload['host_changed'] = True
            print(f"Host changed from {old_host} to {room.get_host_info()}")
        else:
            broadcast_payload['host_changed'] = False

        response = serialize(MSG_LEAVE_GAME_ACK, response_payload)
        broadcast = serialize(MSG_PLAYER_LEFT_BROD, broadcast_payload)
        return response, broadcast

    # -------------------------------------------------------------------------
    
    def handle_lock_object(self, payload, client_address):
        """
        Handle a request to lock an object.
        Returns (ACK, BROD)
        """
        if client_address not in self.client_rooms:
            response = serialize(MSG_ERROR, {'message': 'Not in any game room'})
            return response, None
    
        game_id = self.client_rooms[client_address]
        room = self.game_rooms[game_id]
        object_id = payload.get('object_id')
    
        success, info = room.lock_object(object_id, client_address)
        response_payload = {
            'success': success,
            'info': info,
            'object_id': object_id,
            'locked_objects': room.get_locked_objects()
        }
        response = serialize(MSG_LOCK_OBJECT_ACK, response_payload)
    
        # Only broadcast if successful
        broadcast = None
        if success:
            broadcast_payload = {
                'object_id': object_id,
                'player': {"ip": client_address[0], "port": client_address[1]},
                'info': info
            }
            broadcast = serialize(MSG_LOCK_OBJECT_BROD, broadcast_payload)
    
        return response, broadcast
    
    def handle_release_object(self, payload, client_address):
        """
        Handle a request to release an object.
        Returns (ACK, BROD)
        """
        if client_address not in self.client_rooms:
            response = serialize(MSG_ERROR, {'message': 'Not in any game room'})
            return response, None
    
        game_id = self.client_rooms[client_address]
        room = self.game_rooms[game_id]
        object_id = payload.get('object_id')
        position = payload.get('position')
    
        success, info = room.release_object(object_id, client_address, position)
        response_payload = {
            'success': success,
            'info': info,
            'object_id': object_id,
            'locked_objects': room.get_locked_objects()
        }
        response = serialize(MSG_RELEASE_OBJECT_ACK, response_payload)
    
        # Only broadcast if successful
        broadcast = None
        if success:
            broadcast_payload = {
                'object_id': object_id,
                'position': position,
                'player': {"ip": client_address[0], "port": client_address[1]},
                'info': info
            }
            broadcast = serialize(MSG_RELEASE_OBJECT_BROD, broadcast_payload)
    
        return response, broadcast