"""
Basic TCP client for testing the server
"""

import socket
import sys
import os

# Add the shared directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from net_protocol import *

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
            print("3. Quit")
            
            choice = input("Choose an option (1-3): ").strip()
            
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