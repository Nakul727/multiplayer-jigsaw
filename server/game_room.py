class GameRoom:
    def __init__(self, game_id, game_name, max_players, host_address):
        """
        Initialize a new game room with the specified parameters.
        The host is automatically added as the first player.
        """
        self.game_id = game_id
        self.game_name = game_name
        self.max_players = max_players
        self.host_address = host_address
        self.players = [host_address]
        self.locked_objects = {}
        self.released_objects = {}
        self.puzzle_solved_flag = False

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
        Release a locked object and record its coordinates.
        Returns (success: bool, info: dict).
        """
        if not object_id or position is None:
            return False, {'error': 'Missing object_id or position'}
        if self.locked_objects.get(object_id) != client_address:
            return False, {'error': f'Object {object_id} not locked by you'}
    
        del self.locked_objects[object_id]
        self.released_objects[object_id] = position
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
        
        # Add game logic here like (objectid, x, y) etc.
        # Update the local server game room instance with that as well

        return True, {'message': f'Object {object_id} moved', 'position': position}

    def get_locked_objects(self):
        return {
            obj: {"ip": addr[0], "port": addr[1]}
            for obj, addr in self.locked_objects.items()
        }

    def get_released_objects(self):
        return self.released_objects.copy()

    # -------------------------------------------------------------------------
    # Puzzle State

    def puzzle_solved(self, client_address, completion_time=None, total_pieces=None):
        """
        Mark the puzzle as solved.
        Returns (success: bool, info: dict).
        """
        if self.puzzle_solved_flag:
            return False, {'error': 'Puzzle already solved'}
        
        self.puzzle_solved_flag = True
        
        # Include completion details in the info
        info = {
            'message': 'Puzzle solved!',
            'completion_time': completion_time,
            'total_pieces': total_pieces,
            'solver': client_address
        }
        
        return True, info

    # -------------------------------------------------------------------------
    # Room Info

    def get_room_info(self):
        """
        Return complete room information as a dictionary.
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
            'locked_objects': self.get_locked_objects(),
            'released_objects': self.get_released_objects()
        }