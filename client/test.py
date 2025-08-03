import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from network_manager import NetworkManager
from protocol import *

def handle_command(network, command_parts):

    if not command_parts:
        return True # continue if input is empty

    command = command_parts[0].lower()
    args = command_parts[1:]

    if command == "host":
        if len(args) < 3:
            print("Usage: host <game_name> <max_players> <image_url>")
            return True
        game_name = args[0]
        image_url = args[2]
        try:
            max_players = int(args[1])
        except ValueError:
            print("Error: <max_players> must be an integer.")
            return True
        
        print(f"Sending HOST request for game '{game_name}'...")
        network.send_message(MSG_HOST_GAME, {
            'game_name': game_name,
            'max_players': max_players,
            'image_url': image_url
        })

    elif command == "join":
        if len(args) < 1:
            print("Usage: join <game_id>")
            return True
        game_id = args[0]
        network.send_message(MSG_JOIN_GAME, {'game_id': game_id})

    elif command == "leave":
        network.send_message(MSG_LEAVE_GAME, {})

    elif command == "lock":
        if len(args) < 1:
            print("Usage: lock <object_id>")
            return True
        object_id = args[0]
        network.lock_object(object_id)

    elif command == "move":
        if len(args) < 3:
            print("Usage: move <object_id> <x> <y>")
            return True
        object_id = args[0]
        try:
            x = int(args[1])
            y = int(args[2])
            network.move_locked_object(object_id, {"x": x, "y": y})
        except ValueError:
            print("Error: x and y must be integers.")

    elif command == "release":
        if len(args) < 3:
            print("Usage: release <object_id> <x> <y>")
            return True
        object_id = args[0]
        try:
            x = int(args[1])
            y = int(args[2])
            network.release_object(object_id, {"x": x, "y": y})
        except ValueError:
            print("Error: x and y must be integers.")

    elif command == "quit":
        return False 

    else:
        print(f"Unknown command: {command}")
    
    return True



def main():
    # argument parsing 
    # need at least 4 argumnts
    if len(sys.argv) < 4:
        print("Invalid number of arguments. Please provide all required parameters.")
        print("     WTF R U DOING?!?!?!")
        print("U need to do <server_ip> <port> <command> [whatever it is]")
        print("\nSuggesstion for you:")
        print("  python test.py 127.0.0.1 5555 host game_name 4 https://image.png")
        print("   python test.py 127.0.0.1 5555 join ROOMCODE")
        sys.exit(1) # exit if arguments are incorrect

    # 1. 127.0.0.1 
    server_ip = sys.argv[1]
    # 2. 5555
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("gang the port must be an integer")
        sys.exit(1)
    # 3. host / join / leave + whatever it is
    initial_command_parts = sys.argv[3:]

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
    
    handle_command(network, initial_command_parts)

    # Interactive Loop
    print("\nEntering interactive mode. Type 'quit' to exit.")
    print("Commands: host, join, leave, lock, move, release, quit")
    
    try:
        while True:
            # Get command from user input
            input_line = input("\n> ").strip()
            command_parts = input_line.split()
            
            # Process the command and check if we should quit
            if not handle_command(network, command_parts):
                break
                
    except KeyboardInterrupt:
        print("\nExiting due to KeyboardInterrupt.")
    finally:
        network.disconnect()
        print("Disconnected from server.")
main()