# CMPT 371 Group Project

## Game - Undecided

## Overview

- A single server application acts as the central hub. Players do not connect directly to a game; 
  they connect to this main server. It can be hosted on either local, LAN, or the internet. 
  It binds to a IP address and a port.
- The server's job is to manage a Lobby, where players can choose to Host a new game or Join an existing one.
- Each game runs in a self-contained Game Room instance on the server. 
- The Client Application is responsible for two things: rendering the visuals and sending user 
  input to the server. The client is "dumb"—it only draws what the server tells it to and 
  trusts the server's game state completely.


## File Structure

This is going to be the file structure for the base 'sandbox' implementation of the architecture. The game can be adapted on top of it but just simply defining game logic (different entities), maps, game specific constants etc.

```
game/
├── shared/
│   └── protocol.py
│
├── server/
│   ├── server_main.py
│   ├── server.py
│   ├── game_room.py 
│   └── game_logic/
│       ├── world.py
│       ├── entities.py
│       └── grid.py
│
└── client/
    ├── client_main.py
    ├── network_client.py
    └── game_gui.py
```

Server-Side (server/): 

- Server: The "doorman." Manages connections and directs players to GameRooms.
- GameRoom: Manages one game session. Contains a World and the players in that game.
- World (in game_logic): The "game board." Holds all Player objects and the Grid.
- Player (in game_logic): Represents a single player's state and actions.
- Grid (in game_logic): Represents the map and handles collision rules.

Client-Side (client/):

- GameGUI: Manages all visuals, scenes (menu, game), and user input.
- NetworkClient: The bridge to the server. Sends player inputs and receives game state updates.

Shared (shared/):

- protocol.py: Defines the message formats that the NetworkClient and Server use to communicate, ensuring they understand each other (like JSON)