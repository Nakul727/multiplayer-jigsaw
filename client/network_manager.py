import socket
import threading
import sys
import os
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
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
        
        # Game state
        self.game_id = None
        self.game_name = None
        self.current_players = 0
        self.max_players = 0
        self.image_url = None
        self.host_info = None 
        self.is_host = False
        self.difficulty = 'easy'
        self.difficulty_settings = None

        # Piece state
        self.piece_positions = {}
        self.locked_by_others = {} 

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
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = deserialize(data)
                    # Temporary
                    print(json.dumps(message, indent=2))
                    
                    self._handle_received_message(message)
                except json.JSONDecodeError:
                    print(f"Received non-JSON message: {data.decode('utf-8', errors='ignore')}")
                    
            except Exception as e:
                if self.listening:
                    print(f"Error in network listener: {e}")
                break
        
        self.connected = False
        print("Network listener stopped")

    # -------------------------------------------------------------------------
    # Server to Client Message Handlers

    def _handle_received_message(self, message):
        """
        Process incoming messages using direct handler methods.
        Routes messages to specific handler methods based on message type.
        """
        msg_type = message.get('type')
        payload = message.get('payload', {})
        
        if msg_type == MSG_HOST_GAME_ACK:
            self._handle_host_game_ack(payload)
        elif msg_type == MSG_JOIN_GAME_ACK:
            self._handle_join_game_ack(payload)
        elif msg_type == MSG_LEAVE_GAME_ACK:
            self._handle_leave_game_ack(payload)
        elif msg_type == MSG_LOCK_OBJECT_ACK:
            self._handle_lock_object_ack(payload)
        elif msg_type == MSG_RELEASE_OBJECT_ACK:
            self._handle_release_object_ack(payload)
        elif msg_type == MSG_PUZZLE_SOLVED_ACK:
            self._handle_puzzle_solved_ack(payload)
        elif msg_type == MSG_PLAYER_JOINED_BROD:
            self._handle_player_joined_brod(payload)
        elif msg_type == MSG_PLAYER_LEFT_BROD:
            self._handle_player_left_brod(payload)
        elif msg_type == MSG_LOCK_OBJECT_BROD:
            self._handle_lock_object_brod(payload)
        elif msg_type == MSG_RELEASE_OBJECT_BROD:
            self._handle_release_object_brod(payload)
        elif msg_type == MSG_MOVE_LOCKED_OBJECT_BROD:
            self._handle_move_locked_object_brod(payload)
        elif msg_type == MSG_PUZZLE_SOLVED_BROD:
            self._handle_puzzle_solved_brod(payload)
        elif msg_type == MSG_ERROR:
            self._handle_error(payload)
        else:
            print(f"Unknown message type received: {msg_type}")
    
    # Ack Handlers

    def _handle_host_game_ack(self, payload):
        if payload.get('success'):
            self.game_id = payload.get('game_id')
            self.game_name = payload.get('game_name')
            self.current_players = payload.get('current_players')
            self.max_players = payload.get('max_players')
            self.image_url = payload.get('image_url')
            self.host_info = payload.get('host')
            self.is_host = True
            self.difficulty = payload.get('difficulty', 'easy')
            self.difficulty_settings = payload.get('difficulty_settings')

            self.piece_positions = payload.get('piece_positions', {})

            print(f"[ACK] Game hosted successfully: {self.game_id}")
            print(f"[ACK] Room: {self.game_name} ({self.current_players}/{self.max_players})")
            print(f"[ACK] Difficulty: {self.difficulty}")
            print(f"[ACK] Piece positions: {len(self.piece_positions)} pieces")
        else:
            print(f"[ACK] Failed to host game: {payload.get('message')}")

    def _handle_join_game_ack(self, payload):
        if payload.get('success'):
            self.game_id = payload.get('game_id')
            self.game_name = payload.get('game_name')
            self.current_players = payload.get('current_players')
            self.max_players = payload.get('max_players')
            self.image_url = payload.get('image_url')
            self.host_info = payload.get('host')
            self.is_host = False
            self.difficulty = payload.get('difficulty', 'easy')
            self.difficulty_settings = payload.get('difficulty_settings')
            
            self.piece_positions = payload.get('piece_positions', {})

            print(f"[ACK] Joined game: {self.game_name}")
            print(f"[ACK] Players: {self.current_players}/{self.max_players}")
            print(f"[ACK] Image URL: {self.image_url}")
            print(f"[ACK] Difficulty: {self.difficulty}")
            print(f"[ACK] Piece positions: {len(self.piece_positions)} pieces")
        else:
            print(f"[ACK] Failed to join game: {payload.get('message')}")

    def _handle_leave_game_ack(self, payload):
        if payload.get('success'):
            self.game_id = None
            self.game_name = None
            self.current_players = 0
            self.max_players = 0
            self.image_url = None
            self.host_info = None
            self.is_host = False
            self.difficulty = 'easy'
            self.difficulty_settings = None

            self.piece_positions = {}
            self.locked_by_others = {}

            print("[ACK] Left game successfully")
        else:
            print(f"[ACK] Failed to leave game: {payload.get('message')}")

    def _handle_lock_object_ack(self, payload):
        if payload.get('success'):
            print(f"[ACK] Object locked: {payload.get('object_id')}")
        else:
            print(f"[ACK] Failed to lock object: {payload.get('info', {}).get('error', '')}")
        if 'locked_objects' in payload:
            print(f"[ACK] Locked objects: {payload['locked_objects']}")

    def _handle_release_object_ack(self, payload):
        if payload.get('success'):
            print(f"[ACK] Object released: {payload.get('object_id')}")
        else:
            print(f"[ACK] Failed to release object: {payload.get('info', {}).get('error', '')}")
        if 'locked_objects' in payload:
            print(f"[ACK] Locked objects: {payload['locked_objects']}")

    def _handle_puzzle_solved_ack(self, payload):
        if payload.get('success'):
            print("[ACK] Puzzle solved!")
        else:
            print(f"[ACK] Failed to solve puzzle: {payload.get('info', {}).get('error', '')}")

    # Broadcast Handlers

    def _handle_player_joined_brod(self, payload):
        player_info = payload.get('player')
        self.current_players = payload.get('current_players', self.current_players)

        print(f"[BROD] Player joined: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"[BROD] Room now has {self.current_players} players")
    
    def _handle_player_left_brod(self, payload):
        player_info = payload.get('player')
        self.current_players = payload.get('current_players', self.current_players)
        
        # Handle host change if it occurred
        if payload.get('host_changed', False):
            new_host = payload.get('host')
            if new_host:
                self.host_info = new_host
                print(f"[BROD] Host changed to: {new_host.get('ip')}:{new_host.get('port')}")
            
            # Update players list
            if 'players' in payload:
                players_list = payload.get('players', [])
                print(f"[BROD] Updated players list: {players_list}")
        
        print(f"[BROD] Player left: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"[BROD] Room now has {self.current_players} players")


    def _handle_lock_object_brod(self, payload):
        player_info = payload.get('player')
        object_id = payload.get('object_id') 

        # Add to locked list     
        self.locked_by_others[object_id] = player_info

        print(f"[BROD] Object locked: {object_id} by {player_info}")
  

    def _handle_release_object_brod(self, payload):
        object_id = payload.get('object_id')
        position = payload.get('position')
        player_info = payload.get('player')

        # Remove from locked list and update position
        if object_id in self.locked_by_others:
            del self.locked_by_others[object_id]
        
        # Update piece position
        if object_id in self.piece_positions:
            self.piece_positions[object_id] = position

        print(f"[BROD] Object released: {object_id} at {position} by {player_info}")
        
    def _handle_move_locked_object_brod(self, payload):
        object_id = payload.get('object_id')
        position = payload.get('position')
        player_info = payload.get('player')
  
        # Update piece position
        if object_id in self.piece_positions:
            self.piece_positions[object_id] = position

        print(f"[BROD] Object moved: {object_id} to {position} by {player_info}")
      
    def _handle_puzzle_solved_brod(self, payload):
        player_info = payload.get('player')
        print(f"[BROD] Puzzle solved by {player_info}")

    # Error

    def _handle_error(self, payload):
        error_message = payload.get('message', 'Unknown error')
        print(f"[ERROR] Server error: {error_message}")

    # -------------------------------------------------------------------------
    # State Query Methods for GUI

    def is_piece_locked_by_others(self, piece_id):
        """Check if a piece is locked by another player."""
        return piece_id in self.locked_by_others

    def get_piece_locker_info(self, piece_id):
        """Get information about who locked a piece."""
        return self.locked_by_others.get(piece_id)

    def get_current_piece_positions(self):
        """Get current piece positions from network manager."""
        return self.piece_positions.copy()

    def update_local_piece_position(self, piece_id, position):
        """Update local piece position tracking."""
        self.piece_positions[piece_id] = position

    # -------------------------------------------------------------------------
    # Client to Server Helpers

    def host_game(self, game_name, max_players, image_url, difficulty='easy'):
        """
        Send a request to host a new game
        """
        payload = {
            'game_name': game_name,
            'max_players': max_players,
            'image_url': image_url,
            'difficulty': difficulty,
        }
        return self.send_message(MSG_HOST_GAME, payload)

    def join_game(self, game_id):
        """
        Send a request to join an existing game
        """
        payload = {'game_id': game_id}
        return self.send_message(MSG_JOIN_GAME, payload)
    
    def leave_game(self):
        """
        Send a request to leave the current game
        """
        return self.send_message(MSG_LEAVE_GAME, {})

    def lock_object(self, object_id):
        """
        Request to lock an object.
        """
        payload = self._make_payload(object_id=object_id)
        return self.send_message(MSG_LOCK_OBJECT, payload)

    def move_locked_object(self, object_id, position):
        """
        Send a request to move a locked object to a new position.
        """
        payload = self._make_payload(object_id=object_id, position=position)
        return self.send_message(MSG_MOVE_LOCKED_OBJECT, payload)

    def release_object(self, object_id, position):
        """
        Request to release an object with its position.
        """
        payload = self._make_payload(object_id=object_id, position=position)
        return self.send_message(MSG_RELEASE_OBJECT, payload)

    def puzzle_solved(self, completion_time=None, total_pieces=None):
        """
        Notify the server that the puzzle is completed.
        """
        payload = self._make_payload(completion_time=completion_time, total_pieces=total_pieces)
        return self.send_message(MSG_PUZZLE_SOLVED, payload)

    def _make_payload(self, **kwargs):
        """
        Build a payload dictionary, excluding keys with None values.
        Usage: self._make_payload(object_id=..., position=...)
        """
        return {k: v for k, v in kwargs.items() if v is not None}
    
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