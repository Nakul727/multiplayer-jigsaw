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
        self.game_gui = None  # Reference to the game GUI for callbacks
    
    def set_game_gui(self, game_gui):
        """Set the game GUI reference for network event callbacks"""
        self.game_gui = game_gui

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
            print(f"[ACK] Game hosted successfully: {payload.get('game_id')}")
            print(f"[ACK] Room: {payload.get('game_name')} ({payload.get('current_players')}/{payload.get('max_players')})")
        else:
            print(f"[ACK] Failed to host game: {payload.get('message')}")

    def _handle_join_game_ack(self, payload):
        if payload.get('success'):
            print(f"[ACK] Joined game: {payload.get('game_name')}")
            print(f"[ACK] Players: {payload.get('current_players')}/{payload.get('max_players')}")
        else:
            print(f"[ACK] Failed to join game: {payload.get('message')}")

    def _handle_leave_game_ack(self, payload):
        if payload.get('success'):
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
        current_players = payload.get('current_players')
        print(f"[BROD] Player joined: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"[BROD] Room now has {current_players} players")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_player_joined'):
            self.game_gui.on_player_joined(player_info, current_players)

    def _handle_player_left_brod(self, payload):
        player_info = payload.get('player')
        current_players = payload.get('current_players')
        print(f"[BROD] Player left: {player_info.get('ip')}:{player_info.get('port')}")
        print(f"[BROD] Room now has {current_players} players")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_player_left'):
            self.game_gui.on_player_left(player_info, current_players)

    def _handle_lock_object_brod(self, payload):
        object_id = payload.get('object_id')
        player = payload.get('player')
        print(f"[BROD] Object locked: {object_id} by {player}")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_object_locked'):
            self.game_gui.on_object_locked(object_id, player)

    def _handle_release_object_brod(self, payload):
        object_id = payload.get('object_id')
        position = payload.get('position')
        player = payload.get('player')
        print(f"[BROD] Object released: {object_id} at {position} by {player}")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_object_released'):
            self.game_gui.on_object_released(object_id, position, player)

    def _handle_move_locked_object_brod(self, payload):
        object_id = payload.get('object_id')
        position = payload.get('position')
        player = payload.get('player')
        print(f"[BROD] Object moved: {object_id} to {position} by {player}")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_object_moved'):
            self.game_gui.on_object_moved(object_id, position, player)

    def _handle_puzzle_solved_brod(self, payload):
        player = payload.get('player')
        completion_time = payload.get('completion_time')
        total_pieces = payload.get('total_pieces')
        print(f"[BROD] Puzzle solved by {player}")
        print(f"[BROD] Completion time: {completion_time:.1f}s, Pieces: {total_pieces}")
        
        # Notify game GUI if available
        if self.game_gui and hasattr(self.game_gui, 'on_puzzle_solved'):
            self.game_gui.on_puzzle_solved(player, completion_time, total_pieces)

    # Error

    def _handle_error(self, payload):
        error_message = payload.get('message', 'Unknown error')
        print(f"[ACK] Server error: {error_message}")

    # -------------------------------------------------------------------------
    # Client to Server Helpers

    def host_game(self, game_name, max_players=4):
        """
        Request to host a new game.
        """
        payload = self._make_payload(game_name=game_name, max_players=max_players)
        return self.send_message(MSG_HOST_GAME, payload)

    def join_game(self, game_id):
        """
        Request to join an existing game.
        """
        payload = self._make_payload(game_id=game_id)
        return self.send_message(MSG_JOIN_GAME, payload)

    def leave_game(self):
        """
        Request to leave the current game.
        """
        payload = {}
        return self.send_message(MSG_LEAVE_GAME, payload)

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