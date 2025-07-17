## How to install Pygame
``` 
pip install pygame
```

## Once in the client directory, run :
```
python game_gui.py
```
click, drag, and release your mouse in the windoe to see output messages(coordinate) in terminal

## 1. The Network Client (network_client.py)
Contain class that manages the socket connection. so it:
- Connect to the server's IP address and port (need to change this)
- Send data to the server
- Receive data from the server (idk about this yet)

## 2. The GUI (game_gui):
Create a window, draws a 3x3 grid and made it so it prints mouse actions to the console

Integrated NetworkClient so it can send information over the network