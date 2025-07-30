import pygame
from network_client import NetworkClient
from protocol import *

# Size
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
GRID_SIZE = 3
SQUARE_SIZE = WINDOW_WIDTH // GRID_SIZE

#color
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (200, 200, 200)
COLOR_BLACK = (0, 0, 0)

class GameGUI:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("GAME NAME")
        self.clock = pygame.time.Clock() # need to control frame rate
        self.is_scribbling = False
        
        self.network_client = NetworkClient()
        initial_message = self.network_client.connect()
        if not initial_message:
            print("Failed to connect to server. Exiting.")
            # need to add error msg on screen later on, maybe ?
        else:
            print(f"Connected to server: {initial_message}")

    def run(self):
        running = True
        while running:
            # --- Event Handling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                    self.network_client.close() # Close the connection when quitting

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse button down
                        pos = pygame.mouse.get_pos()
                        grid_x, grid_y = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
                        object_id = f"square_{grid_x}_{grid_y}" # Create a unique ID for the square

                        # --- SEND DATA ---
                        # 1. Create the payload dictionary
                        payload = {
                            'action': INPUT_ACTION_LOCK_OBJECT,
                            'object_id': object_id
                        }
                        # 2. Call send() with the message type and payload
                        print(f"Sending LOCK request for {object_id}")
                        response = self.network_client.send(MSG_PLAYER_INPUT, payload)
                        print(f"Server response: {response}")

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1: # Left mouse button up
                        pos = pygame.mouse.get_pos()
                        grid_x, grid_y = pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE
                        object_id = f"square_{grid_x}_{grid_y}"

                        # --- SEND DATA ---
                        payload = {
                            'action': INPUT_ACTION_RELEASE_OBJECT,
                            'object_id': object_id
                        }
                        print(f"Sending RELEASE request for {object_id}")
                        response = self.network_client.send(MSG_PLAYER_INPUT, payload)
                        print(f"Server response: {response}")
            
            # draw and update
            self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    # draw game and grid
    def draw_game(self):
        self.screen.fill(COLOR_WHITE)
        self.draw_grid_lines()

    def draw_grid_lines(self):
        for x in range(GRID_SIZE + 1):
            pygame.draw.line(self.screen, COLOR_GREY, (x * SQUARE_SIZE, 0), (x * SQUARE_SIZE, WINDOW_HEIGHT))
        for y in range(GRID_SIZE + 1):
            pygame.draw.line(self.screen, COLOR_GREY, (0, y * SQUARE_SIZE), (WINDOW_WIDTH, y * SQUARE_SIZE))