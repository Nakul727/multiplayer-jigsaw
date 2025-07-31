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
        # Track locked tiles: {tile_id: client_address}
        self.locked_tiles = {}
        # Track released tiles: {tile_id: coordinates}
        self.released_tiles = {}
    def lock_tile(self, tile_id, client_address):
        """
        Attempt to lock a tile for a player. Returns True if successful, False if already locked.
        """
        if tile_id in self.locked_tiles:
            return False  # Already locked
        self.locked_tiles[tile_id] = client_address
        return True

    def release_tile(self, tile_id, client_address, coordinates):
        """
        Release a locked tile and record its coordinates. Only the locking player can release.
        Returns True if successful, False otherwise.
        """
        if self.locked_tiles.get(tile_id) == client_address:
            del self.locked_tiles[tile_id]
            self.released_tiles[tile_id] = coordinates  # e.g., (x, y)
            return True
        return False

    def get_locked_tiles(self):
        """
        Return a dict of currently locked tiles and their owners.
        """
        return self.locked_tiles.copy()

    def get_released_tiles(self):
        """
        Return a dict of released tiles and their coordinates.
        """
        return self.released_tiles.copy()
    
    def add_player(self, client_address):
        """
        Add a new player to the game room if there's space available.
        Returns True if player was added successfully, False if room is full.
        """
        if len(self.players) < self.max_players:
            self.players.append(client_address)
            return True
        return False
    
    def remove_player(self, client_address):
        """
        Remove a player from the game room.
        If the host leaves and other players remain, the first player becomes the new host.
        """
        if client_address in self.players:
            self.players.remove(client_address)
            if client_address == self.host_address and len(self.players) > 0:
                self.host_address = self.players[0]
                print(f"New host for room {self.game_id}: {self.host_address}")
                return True
        return False
    
    def is_full(self):
        """
        Check if the game room has reached its maximum player capacity.
        """
        return len(self.players) >= self.max_players
    
    def is_empty(self):
        """
        Check if the game room has no players.
        """
        return len(self.players) == 0
    
    def is_host(self, client_address):
        """
        Check if the given client address is the host of this room.
        """
        return client_address == self.host_address
    
    def has_player(self, client_address):
        """
        Check if a specific player is in this game room.
        """
        return client_address in self.players
    
    def get_player_count(self):
        """
        Return the current number of players in the game room.
        """
        return len(self.players)
    
    def get_players_info(self):
        """
        Return a list of player information dictionaries containing IP and port.
        """
        return [{"ip": addr[0], "port": addr[1]} for addr in self.players]
    
    def get_host_info(self):
        """
        Return the host's information as a dictionary with IP and port.
        """
        return {"ip": self.host_address[0], "port": self.host_address[1]}
    
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
            'is_empty': self.is_empty()
        }