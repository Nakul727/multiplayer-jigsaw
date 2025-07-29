"""
Basic TCP client for testing the server
"""

import socket
import sys
import os

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from protocol import *

def test_client():
    server_ip = input("Enter server IP (or 'localhost' for local): ").strip()
    if server_ip.lower() == 'localhost':
        server_ip = '127.0.0.1'
    
    server_port = 5555
    
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print(f"Connecting to {server_ip}:{server_port}...")
        client_socket.connect((server_ip, server_port))
        print("Connected successfully!")
        
        while True:
            print("\nOptions:")
            print("1. Send text message (legacy)")
            print("2. Host a game")
            print("3. Lock object")
            print("4. Release object")
            print("5. Wait for server messages")
            print("6. Quit")

            choice = input("Choose an option (1-6): ").strip()

            if choice == '1':
                # Legacy text message
                message = input("Enter message to send: ")
                client_socket.send(message.encode('utf-8'))
                print(f"Sent: {message}")
                response = client_socket.recv(4096)
                print(f"Received: {response.decode('utf-8')}")

            elif choice == '2':
                # Host game using protocol
                game_name = input("Enter game name: ").strip() or "Test Game"
                max_players = input("Enter max players (default 4): ").strip() or "4"
                try:
                    max_players = int(max_players)
                except ValueError:
                    max_players = 4
                payload = {
                    'game_name': game_name,
                    'max_players': max_players
                }
                message = serialize(MSG_CREATE_ROOM, payload)
                client_socket.send(message)
                print(f"Sent HOST_GAME request for '{game_name}'")
                response = client_socket.recv(4096)
                try:
                    response_msg = deserialize(response)
                    if response_msg['type'] == MSG_CREATE_ROOM_ACK:
                        payload = response_msg['payload']
                        if payload['success']:
                            print(f"{payload['message']}")
                            print(f"Game ID: {payload['game_id']}")
                        else:
                            print(f"Failed to host game: {payload.get('message', 'Unknown error')}")
                    else:
                        print(f"Unexpected response: {response_msg}")
                except:
                    print(f"Raw response: {response.decode('utf-8')}")

            elif choice == '3':
                # Lock object
                object_id = input("Enter object ID to lock: ").strip()
                payload = {'action': INPUT_ACTION_LOCK_OBJECT, 'object_id': object_id}
                message = serialize(MSG_PLAYER_INPUT, payload)
                client_socket.send(message)
                # Wait for server response (error or confirmation)
                try:
                    response = client_socket.recv(4096)
                    response_msg = deserialize(response)
                    if response_msg['type'] == MSG_ERROR:
                        print(f"Error: {response_msg['payload']['message']}")
                    else:
                        print(f"Response: {response_msg}")
                except Exception:
                    print("Error: Failed to receive server response.")

            elif choice == '4':
                # Release object
                object_id = input("Enter object ID to release: ").strip()
                payload = {'action': INPUT_ACTION_RELEASE_OBJECT, 'object_id': object_id}
                message = serialize(MSG_PLAYER_INPUT, payload)
                client_socket.send(message)
                print(f"Sent release request for object {object_id}")
                # Wait for server response (error or confirmation)
                try:
                    response = client_socket.recv(4096)
                    response_msg = deserialize(response)
                    print(f"Received response for release request: {response_msg}")
                    if response_msg['type'] == MSG_ERROR:
                        print(f"Error: {response_msg['payload']['message']}")
                    else:
                        print(f"Response: {response_msg}")
                except Exception:
                    print("Error: Failed to receive server response.")

            elif choice == '5':
                print("Waiting for server broadcast (lock/release notifications)... Press Ctrl+C to stop.")
                try:
                    while True:
                        response = client_socket.recv(4096)
                        try:
                            response_msg = deserialize(response)
                            if response_msg['type'] == MSG_OBJECT_LOCKED:
                                obj = response_msg['payload']['object_id']
                                locker = response_msg['payload']['locked_by']
                                print(f"Object {obj} was locked by {locker}")
                            elif response_msg['type'] == MSG_OBJECT_RELEASED:
                                obj = response_msg['payload']['object_id']
                                rel = response_msg['payload']['released_by']
                                print(f"Object {obj} was released by {rel}")
                            else:
                                print(f"Server message: {response_msg}")
                        except Exception:
                            print(f"Raw server message: {response.decode('utf-8')}")
                except KeyboardInterrupt:
                    print("Stopped waiting for server messages.")

            elif choice == '6':
                break
            else:
                print("Invalid choice. Please try again.")
            
    except ConnectionRefusedError:
        print(f"Error: Could not connect to server at {server_ip}:{server_port}")
        print("Make sure the server is running and the IP address is correct.")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()
        print("Connection closed.")

if __name__ == "__main__":
    test_client()