import socket
import threading
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))
from protocol import *

class NetworkManager:
    def __init__(self):
        """
        Initialize the network manager with default values.
        Sets up socket, connection status, and message handling.
        """
        self.client_socket = None
        self.connected = False
        self.listening = False
        self.listen_thread = None

    def connect(self, ip, port):
        """
        Establish a connection to the server at the specified IP and port.
        Returns True on successful connection, False otherwise.
        """
        try:
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket.connect((ip, port))
            self.connected = True
            self._start_listener()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """
        Close the connection to the server and stop all network activity.
        Cleans up socket and listener thread resources.
        """
        self.connected = False
        self.listening = False
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
        
        if self.listen_thread and self.listen_thread.is_alive():
            self.listen_thread.join(timeout=1.0)

    # -------------------------------------------------------------------------

    def _start_listener(self):
        """
        Start a background thread to listen for incoming messages from the server.
        Only starts if not already listening.
        """
        if not self.listening:
            self.listening = True
            self.listen_thread = threading.Thread(target=self._listen_for_messages)
            self.listen_thread.daemon = True
            self.listen_thread.start()

    def _listen_for_messages(self):
        """
        Main loop for receiving and processing messages from the server.
        Runs in a separate thread until connection is closed.
        """
        while self.listening and self.connected:
            try:
                data = self.client_socket.recv(2048)
                if not data:
                    break
                
                try:
                    message = deserialize(data)
                    self._handle_received_message(message)
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {data.decode('utf-8', errors='ignore')}")
                    
            except Exception as e:
                if self.listening:
                    print(f"Error in network listener: {e}")
                break
        
        self.connected = False
        print("Network listener stopped")

    def _handle_received_message(self, message):
        """
        Process incoming messages using direct handler methods.
        Routes messages to specific handler methods based on message type.
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        
        if msg_type == MSG_HOST_GAME_ACK:
            self._handle_host_game_response(payload)
        elif msg_type == MSG_JOIN_GAME_ACK:
            self._handle_join_game_response(payload)
        elif msg_type == MSG_LEAVE_GAME_ACK:
            self._handle_leave_game_response(payload)
        elif msg_type == MSG_PLAYER_JOINED:
            self._handle_player_joined(payload)
        elif msg_type == MSG_PLAYER_LEFT:
            self._handle_player_left(payload)
        elif msg_type == MSG_ERROR:
            self._handle_error(payload)
        elif msg_type == "TILE_LOCKED":
            self._handle_tile_locked(payload)
        elif msg_type == "TILE_RELEASED":
            self._handle_tile_released(payload)
        else:
            print(f"Unknown message type received: {msg_type}")


    # -------------------------------------------------------------------------

    def _handle_host_game_response(self, payload):
        """
        Handle server response to hosting a game.
        Process game creation confirmation and room details.
        """
        if payload.get('success'):
            print(f"Game hosted successfully: {payload.get('game_id')}")
            print(f"Room: {payload.get('game_name')} ({payload.get('current_players')}/{payload.get('max_players')})")
        else:
            print(f"Failed to host game: {payload.get('message')}")

    def _handle_join_game_response(self, payload):
        """
        Handle server response to joining a game.
        Process join confirmation and updated room information.
        """
        if payload.get('success'):
            print(f"Joined game: {payload.get('game_name')}")
            print(f"Players: {payload.get('current_players')}/{payload.get('max_players')}")
        else:
            print(f"Failed to join game: {payload.get('message')}")

    def _handle_leave_game_response(self, payload):
        """
        Handle server response to leaving a game.
        Process leave confirmation and cleanup.
        """
        if payload.get('success'):
            print("Left game successfully")
        else:
            print(f"Failed to leave game: {payload.get('message')}")

    def _handle_player_joined(self, payload):
        """
        Handle notification that another player joined the game.
        Update local player list and UI.
        """
        player_info = payload.get('player')
        print(f"Player joined: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"Room now has {payload.get('current_players')} players")

    def _handle_player_left(self, payload):
        """
        Handle notification that another player left the game.
        Update local player list and UI.
        """
        player_info = payload.get('player')
        print(f"Player left: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"Room now has {payload.get('current_players')} players")

    def _handle_error(self, payload):
        """
        Handle error messages from the server.
        Display error information to user.
        """
        error_message = payload.get('message', 'Unknown error')
        print(f"Server error: {error_message}")

    # -------------------------------------------------------------------------

    def send_message(self, msg_type, payload):
        """
        Send a message to the server with the specified type and payload.
        Returns True if sent successfully, False if connection is unavailable.
        """
        if not self.connected or not self.client_socket:
            return False
        try:
            message = serialize(msg_type, payload)
            self.client_socket.send(message)
            return True
        except Exception as e:
            print(f"Failed to send message: {e}")
            return False
        
 # -------------------------------------------------------------------------

    def lock_tile(self, tile_id):
        """
        Request to lock a tile. Sends message to server.
        """
        payload = {"tile_id": tile_id}
        return self.send_message("LOCK_TILE", payload)

    def release_tile(self, tile_id, coordinates):
        """
        Request to release a tile with its coordinates. Sends message to server.
        """
        payload = {"tile_id": tile_id, "coordinates": coordinates}
        return self.send_message("RELEASE_TILE", payload)

    def _handle_tile_locked(self, payload):
        """
        Handle notification that a tile has been locked by a player.
        Update local state/UI as needed.
        """
        tile_id = payload.get("tile_id")
        locker = payload.get("player")
        print(f"Tile {tile_id} locked by {locker}")

    def _handle_tile_released(self, payload):
        """
        Handle notification that a tile has been released and placed on the board.
        Update local state/UI as needed.
        """
        tile_id = payload.get("tile_id")
        coordinates = payload.get("coordinates")
        releaser = payload.get("player")
        print(f"Tile {tile_id} released by {releaser} at {coordinates}")