import sys
import time
from game_gui import GameGUI
from network_manager import NetworkManager
from protocol import *

def main():

    if len(sys.argv) < 5:
        print("not gonna work try these:")
        print("  To host: python main.py <ip> <port> host <game_name> <max_players> <image_url>")
        print("  To join: python main.py <ip> <port> join <game_id>")
        sys.exit(1)

    # 1. 127.0.0.1 
    server_ip = sys.argv[1]
    # 2. 5555
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("gang the port must be an integer")
        sys.exit(1)
    # 3. host / join / leave + whatever it is
    command = sys.argv[3]

    network = NetworkManager()
    if not network.connect(server_ip, server_port):
        print(f"Failed to connect to server at {server_ip}:{server_port}\n")
        return

    image_url = ""

    # Handle hosting
    if command.lower() == 'host' and len(sys.argv) >= 7:
        game_name = sys.argv[4]
        try:
            max_players = int(sys.argv[5])
        except ValueError:
            print("Error: Max players must be an integer.")
            network.disconnect()
            sys.exit(1)
        image_url = sys.argv[6]
        
        print(f"Attempting to host game '{game_name}'...")
        network.host_game(game_name, max_players, image_url)

    # handle joining
    elif command.lower() == 'join' and len(sys.argv) == 5:
        game_id = sys.argv[4]
        print(f"Attempting to join game '{game_id}'...")
        network.join_game(game_id)
    else:
        print("Invalid arguments.")
        print("Usage:")
        print("  To host: python main.py <ip> <port> host <game_name> <max_players> <image_url>")
        print("  To join: python main.py <ip> <port> join <game_id>")
        network.disconnect()
        sys.exit(1)

    # lets wait for server ACK is nothign time out 
    print("Waiting for server response...")
    start_time = time.time()
    while network.game_id is None:
        time.sleep(0.1)
        if time.time() - start_time > 10: # 10 second timeout
            print("Error: No response from server. Timed out.")
            network.disconnect()
            sys.exit(1)

    print(f"Successfully joined game!!! Game ID: {network.game_id}")
    
    # Get game data from network manager
    image_url = network.image_url
    piece_positions = network.piece_positions
    if not image_url or not piece_positions:
        print("Error: Could not retrieve image_url or piece positions from server")
        network.disconnect()
        sys.exit(1)

    # launch game GUI (working dont touch)
    try:
        gui = GameGUI(network, image_url, piece_positions)
        gui.run()
    except Exception as e:
        print(f"An error occurred during the game: {e}")
    finally:
        print("\nDisconnected from server.")
        network.disconnect()


if __name__ == "__main__":
    main()