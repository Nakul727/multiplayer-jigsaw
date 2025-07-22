"""
Basic TCP client for testing the server
"""

import socket

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
            # Get message from user
            message = input("Enter message to send (or 'quit' to exit): ")
            if message.lower() == 'quit':
                break
            
            # Send message to server
            client_socket.send(message.encode('utf-8'))
            print(f"Sent: {message}")
            
            # Receive response from server
            response = client_socket.recv(4096)
            print(f"Received: {response.decode('utf-8')}")
            
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