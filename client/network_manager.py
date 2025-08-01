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
        pass

    def _handle_release_object_ack(self, payload):
        pass

    def _handle_puzzle_solved_ack(self, payload):
        pass

    # Broadcast Handlers

    def _handle_player_joined_brod(self, payload):
        pass

    def _handle_player_left_brod(self, payload):
        pass

    def _handle_lock_object_brod(self, payload):
        pass

    def _handle_release_object_brod(self, payload):
        pass

    def _handle_move_locked_object_brod(self, payload):
        pass

    def _handle_puzzle_solved_brod(self, payload):
        pass

    # Error

    def _handle_error(self, payload):
        error_message = payload.get('message', 'Unknown error')
        print(f"[ACK] Server error: {error_message}")

    # -------------------------------------------------------------------------
    # Client to Server Helpers

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