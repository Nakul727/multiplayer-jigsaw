import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from network_manager import NetworkManager
from protocol import *

def main():
    # argument parsing 
    # need at least 4 argumnts
    if len(sys.argv) < 4:
        print("Invalid number of arguments. Please provide all required parameters.")
        print("     WTF R U DOING?!?!?!")
        print("U need to do <server_ip> <port> <command> [whatever it is]")
        print("\nSuggesstion for you:")
        print("   python test.py 127.0.0.1 5555 host game_name 4 https://image.png")
        sys.exit(1) # exit if arguments are incorrect

    # 1. 127.0.0.1 
    server_ip = sys.argv[1]
    # 2. 5555
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("gang the port must be an integer")
        sys.exit(1)
    # 3. host / join / leave
    command = sys.argv[3].lower() # gotta make the command case-insensitive (just incase??)
    # 4. whatever it is
    command_args = sys.argv[4:]

    network = NetworkManager()
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
                if len(command_args) < 3:
                    print("Usage: host <game_name> <max_players> <image_url>")
                    return
                game_name = command_args[0]
                image_url = command_args[2]
                try:
                    max_players = int(command_args[1])
                except ValueError:
                    print("Error!!!: <max_players> must be an integer.")
                    return
                network.send_message(MSG_HOST_GAME, {
                    'game_name': game_name,
                    'max_players': max_players,
                    'image_url': image_url # added this
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