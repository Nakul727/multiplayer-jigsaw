<h4 align="center">
    Multiplayer Jigsaw Puzzle <br>
    CMPT 371: Data Communication / Networking
    <div align="center">
</h4>

<p align="center">
  <a href="#overview">Overview</a> •
  <a href="#gameplay">Gameplay</a> •
  <a href="#team-member">Team Members</a> •
  <a href="#setting-up">Setup</a> •
  <a href="#running-the-game">Running</a> •
  <a href="#contribution">Contribution</a>
</p>

## Gameplay

<!-- [Game Demo](https://www.youtube.com/your-demo-link) -->

### Team member

- name (student id)
- name (student id)
- name (student id)
- name (student id)

### Framework

- Python 3.11+
- Pygame for the frontend UI and rendering

## Overview

A real-time online multiplayer jigsaw puzzle where players collaboratively solve a puzzle. The server coordinates piece locking (mutex) and broadcasts movements so all clients stay in sync. When any player completes the puzzle, all clients see the completion screen.

## Gameplay Mechanics

- Drag-and-drop puzzle pieces on a shared board
- Piece locking: only one player can hold (move) a piece at a time
- Smart snapping when a piece is near its correct location
- Real-time synchronization of piece positions across all clients
- Shared completion celebration when the puzzle is solved

## Winning Condition

- The puzzle is considered complete when all pieces are placed correctly.
- When any player completes the puzzle, the server broadcasts completion and all clients show the win screen.

## Technical Details

- Client-Server Model
  - Server manages rooms, players, and mutex-locked pieces.
  - Clients render the game (Pygame) and send input (lock/release/move).
- Raw Sockets (TCP)
  - Custom JSON protocol for host/join/lock/release/move/solve.
- Simple 2D Graphics
  - Pygame-based rendering focused on functionality.

## Setting up

### Prerequisites

- Python 3.11+
- Pygame

### Installation (Windows PowerShell recommended)

```powershell
# Install dependencies
pip install -r requirements.txt

# Or install only pygame if needed
pip install pygame
```

### Running the Game

```powershell
# Start the server
python server\main.py

# Start a client (host or join from UI/CLI flow)
python client\main.py
```

Project structure:

```
shared/
  ├─ protocol.py      # Message types and serialization
  └─ constants.py     # Ports, colors, sizes, difficulty presets
server/
  ├─ main.py          # Server entry point
  ├─ server.py        # Socket accept loop and message routing
  └─ game_room.py     # Room state (players, locks, piece positions)
client/
  ├─ main.py          # Client entry/launcher
  ├─ game_gui.py      # Pygame GUI and game logic
  ├─ network_manager.py  # TCP client and handlers
  └─ puzzle.py        # Puzzle image slicing and piece metadata
```

## Code Snippets

Includes socket opening/closing and handling of mutex-locked object.

#### Server Socket Management (`server/server.py`)

class Server:

```python

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        print(f"Server listening on {self.host}:{self.port}")
        self.is_running = True
        try:
            while self.is_running:
                conn, addr = self.server_socket.accept()
                t = threading.Thread(target=self.handle_client_connection, args=(conn, addr), daemon=True)
                t.start()
        finally:
            self.shutdown()

    def shutdown(self):
        self.is_running = False
        try:
            self.server_socket.close()
        except Exception:
            pass
```

#### Client Socket Management (`client/network_manager.py`)

```python

    def connect(self, ip, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            self.connected = True
            threading.Thread(target=self._listener_loop, daemon=True).start()
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.close()
            return False

    def close(self):
        self.connected = False
        if self.sock:
            try:
                self.sock.close()
            finally:
                self.sock = None
```

#### Mutex-Locked Object Handling (`server/game_room.py`)

```python
class GameRoom:

    def lock_object(self, object_id, player_addr):
        if not object_id:
            return False, {"error": "missing object_id"}
        if object_id in self.locked_objects:
            return False, {"error": "already_locked"}
        self.locked_objects[object_id] = player_addr
        return True, {}

    def release_object(self, object_id, player_addr, position):
        owner = self.locked_objects.get(object_id)
        if owner != player_addr:
            return False, {"error": "not_owner"}
        self.locked_objects.pop(object_id, None)
        # Persist the final position for new joiners/sync
        if isinstance(position, dict) and "x" in position and "y" in position:
            self.piece_positions[object_id] = {"x": int(position["x"]), "y": int(position["y"])}
        return True, {}
```

### Contribution

Every group member contributed to client-server communication and synchronization.

- name (25%)
  - …
- name (25%)
  - …
- name (25%)
  - …
- name (25%)
  - …
