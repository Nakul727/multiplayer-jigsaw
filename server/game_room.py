import random
import string
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from constants import * 

class GameRoom:
    def __init__(self, game_name, max_players, host_address, image_url, difficulty='easy'):
        """
        Initialize a new game room with the specified parameters.
        The host is automatically added as the first player.
        """
        # Game config
        self.game_id = self._generate_game_id()
        self.game_name = game_name
        self.max_players = max_players
        self.host_address = host_address
        self.players = [host_address]

        # Puzzle config
        self.image_url = image_url
        self.difficulty = difficulty
        self.difficulty_settings = DIFFICULTY_SETTINGS[difficulty]
        self.piece_positions = self._generate_initial_piece_positions()

        # Game state
        self.locked_objects = {}
        self.puzzle_solved_flag = False

    def _generate_game_id(self):
        """
        Generate a random 6-character alphanumeric game ID
        """
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choice(chars) for _ in range(6))

    def _generate_initial_piece_positions(self):
        """
        Generate a dictionary mapping piece_id to random x,y coordinates, 
        based on the difficulty settings
        """
        total_pieces = self.difficulty_settings['pieces']
        
        # Screen dimensions
        window_width = WINDOW_WIDTH
        window_height = WINDOW_HEIGHT
        avg_piece_size = self.difficulty_settings['target_piece_size']
        margin = 80 
        
        piece_positions = {}
        
        for i in range(total_pieces):
            piece_id = f'piece_{i}'
            
            # x,y boundaries (with small margin)
            max_x = max(margin, window_width - avg_piece_size - margin)
            max_y = max(margin, window_height - avg_piece_size - margin)
            
            # generate x,y coordinates
            x = random.randint(margin, max_x)
            y = random.randint(margin, max_y)
            piece_positions[piece_id] = {'x': x, 'y': y}
        
        return piece_positions
    
    # -------------------------------------------------------------------------
    # Player Management

    def add_player(self, client_address):
        """
        Add a new player to the game room if there's space available.
        Returns True if player was added successfully, otherwise False.
        """
        if client_address in self.players:
            return False
        if len(self.players) >= self.max_players:
            return False
        self.players.append(client_address)
        return True

    def remove_player(self, client_address):
        """
        Remove a player from the game room.
        If the host leaves and other players remain, the first player becomes the new host.
        Returns True if host changed, otherwise False.
        """
        if client_address in self.players:
            # Remove from players array
            self.players.remove(client_address)

            # Remove any locks held by this player
            to_remove = [obj for obj, addr in self.locked_objects.items() if addr == client_address]
            for obj in to_remove:
                del self.locked_objects[obj]

            # If host left, assign new host if possible
            host_changed = False
            if client_address == self.host_address:
                if self.players:
                    self.host_address = self.players[0]
                    print(f"New host for room {self.game_id}: {self.host_address}")
                    host_changed = True
                else:
                    self.host_address = None
            return host_changed
        return False

    def is_full(self):
        return len(self.players) >= self.max_players

    def is_empty(self):
        return len(self.players) == 0

    def get_player_count(self):
        return len(self.players)

    def get_players_info(self):
        return [{"ip": addr[0], "port": addr[1]} for addr in self.players]

    def get_host_info(self):
        if self.host_address:
            return {"ip": self.host_address[0], "port": self.host_address[1]}
        return None

    # -------------------------------------------------------------------------
    # Piece Position

    def update_piece_position(self, piece_id, position):
        """
        Update the position of a piece in the server's game state.
        """
        if piece_id in self.piece_positions:
            self.piece_positions[piece_id] = position
            return True
        return False

    def get_piece_positions(self):
        """
        Get all current piece positions.
        """
        return self.piece_positions.copy()

    def get_piece_position(self, piece_id):
        """
        Get the current position of a specific piece.
        """
        return self.piece_positions.get(piece_id)
    
    # -------------------------------------------------------------------------
    # Object Locking

    def lock_object(self, object_id, client_address):
        """
        Attempt to lock an object for a player.
        Returns (success: bool, info: dict).
        """
        if not object_id:
            return False, {'error': 'Missing object_id'}
        if object_id in self.locked_objects:
            return False, {'error': f'Object {object_id} is already locked'}
        
        self.locked_objects[object_id] = client_address
        return True, {'message': f'Object {object_id} locked'}

    def release_object(self, object_id, client_address, position):
        """
        Release a locked object and update its position in the server
        Returns (success: bool, info: dict).
        """
        if not object_id or position is None:
            return False, {'error': 'Missing object_id or position'}
        if self.locked_objects.get(object_id) != client_address:
            return False, {'error': f'Object {object_id} not locked by you'}
    
        # Remove from locked objects
        del self.locked_objects[object_id]
        
        # Update piece position in server state
        self.update_piece_position(object_id, position)
        return True, {'message': f'Object {object_id} released'}


    def move_locked_object(self, object_id, client_address, position):
        """
        Move a locked object to a new position.
        Returns (success: bool, info: dict).
        """
        if not object_id or position is None:
            return False, {'error': 'Missing object_id or position'}
        if self.locked_objects.get(object_id) != client_address:
            return False, {'error': f'Object {object_id} not locked by you'}
        
        # Update piece position in server state
        self.update_piece_position(object_id, position)

        return True, {'message': f'Object {object_id} moved', 'position': position}

    def get_locked_objects(self):
        return {
            obj: {"ip": addr[0], "port": addr[1]}
            for obj, addr in self.locked_objects.items()
        }

    # -------------------------------------------------------------------------
    # Puzzle Config

    def get_puzzle_info(self):
        """
        Get puzzle configuration for sharing with joining clients.
        """
        return {
            'image_url': self.image_url,
            'difficulty': self.difficulty,
        }
    
    def set_puzzle_info(self, image_url, difficulty='easy'):
        """
        Update puzzle configuration.
        """
        self.image_url = image_url
        self.difficulty = difficulty

    def puzzle_solved(self, client_address):
        """
        Mark the puzzle as solved.
        Returns (success: bool, info: dict).
        """
        if self.puzzle_solved_flag:
            return False, {'error': 'Puzzle already solved'}
        
        self.puzzle_solved_flag = True
        return True, {'message': 'Puzzle solved!'}

    # -------------------------------------------------------------------------
    # Game Room State
    
    def get_game_room_state(self):
        """
        Get complete game room state for client communication.
        This is the primary method for retrieving room information.
        """
        return {
            'game_id': self.game_id,
            'game_name': self.game_name,
            'max_players': self.max_players,
            'current_players': self.get_player_count(),
            'host': self.get_host_info(),
            'players': self.get_players_info(),
            'is_full': self.is_full(),
            'is_empty': self.is_empty(),
            'image_url': self.image_url,
            'difficulty': self.difficulty,
            'piece_positions': self.get_piece_positions(),
            'locked_objects': self.get_locked_objects(),
            'puzzle_solved': self.puzzle_solved_flag
        }