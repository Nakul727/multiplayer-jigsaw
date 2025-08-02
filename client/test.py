import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from network_manager import NetworkManager
from protocol import *

def main():
    network = NetworkManager()
    
    server_ip = input("Enter server IP (default: localhost): ") or "localhost"
    server_port = int(input("Enter server port (default: 5555): ") or "5555")
    
    if not network.connect(server_ip, server_port):
        print("Failed to connect to server\n")
        return
    
    print("Connected to server!")
    print("Commands:")
    print("  host <game_name> <max_players> - Host a new game")
    print("  join <game_id> - Join an existing game")
    print("  leave - Leave current game")
    print("  lock <object_id> - Lock an object")
    print("  move <object_id> <x> <y> - Move a locked object to (x, y)")
    print("  release <object_id> <x> <y> - Release an object at position (x, y)")
    print("  quit - Exit\n")
    
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
                print()
                
            elif command[0] == "join":
                if len(command) < 2:
                    print("Usage: join <game_id>\n")
                    continue
                game_id = command[1]
                network.send_message(MSG_JOIN_GAME, {'game_id': game_id})
                print()
                
            elif command[0] == "leave":
                network.send_message(MSG_LEAVE_GAME, {})
                print()

            elif command[0] == "lock":
                if len(command) < 2:
                    print("Usage: lock <object_id>\n")
                    continue
                object_id = command[1]
                network.lock_object(object_id)
                print()

            elif command[0] == "move":
                if len(command) < 4:
                    print("Usage: move <object_id> <x> <y>\n")
                    continue
                object_id = command[1]
                try:
                    x = int(command[2])
                    y = int(command[3])
                except ValueError:
                    print("x and y must be integers\n")
                    continue
                network.move_locked_object(object_id, {"x": x, "y": y})
                print()

            elif command[0] == "release":
                if len(command) < 4:
                    print("Usage: release <object_id> <x> <y>\n")
                    continue
                object_id = command[1]
                try:
                    x = int(command[2])
                    y = int(command[3])
                except ValueError:
                    print("x and y must be integers\n")
                    continue
                network.release_object(object_id, {"x": x, "y": y})
                print()

            elif command[0] == "quit":
                print()
                break
                
            else:
                print("Unknown command\n")
                
    except KeyboardInterrupt:
        pass
    finally:
        network.disconnect()
        print("\nDisconnected from server")

main()