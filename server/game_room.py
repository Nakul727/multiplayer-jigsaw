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