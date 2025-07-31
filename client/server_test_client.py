import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from network_manager import NetworkManager
from protocol import *

def main():
    """
    Interactive client for manual testing
    """
    network = NetworkManager()
    
    # Connect to server
    server_ip = input("Enter server IP (default: localhost): ") or "localhost"
    server_port = int(input("Enter server port (default: 5555): ") or "5555")
    
    if not network.connect(server_ip, server_port):
        print("Failed to connect to server")
        return
    
    print("Connected to server!")
    print("Commands:")
    print("  host <game_name> <max_players> - Host a new game")
    print("  join <game_id> - Join an existing game")
    print("  leave - Leave current game")
    print("  quit - Exit")
    
    try:
        while True:
            command = input("\n> ").strip().split()
            
            if not command:
                continue
                
            if command[0] == "host":
                game_name = command[1] if len(command) > 1 else "Test Game"
                max_players = int(command[2]) if len(command) > 2 else 4
                
                network.send_message(MSG_HOST_GAME, {
                    'game_name': game_name,
                    'max_players': max_players
                })
                
            elif command[0] == "join":
                if len(command) < 2:
                    print("Usage: join <game_id>")
                    continue
                    
                game_id = command[1]
                network.send_message(MSG_JOIN_GAME, {
                    'game_id': game_id
                })
                
            elif command[0] == "leave":
                network.send_message(MSG_LEAVE_GAME, {})
                
            elif command[0] == "quit":
                break
                
            else:
                print("Unknown command")
                
    except KeyboardInterrupt:
        pass
    finally:
        network.disconnect()
        print("\nDisconnected from server")

if __name__ == "__main__":
    main()