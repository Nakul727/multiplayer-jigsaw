import pygame
from network_client import NetworkClient

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
        
        # connect to network client (hope this works)
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

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.is_scribbling = True
                        pos = pygame.mouse.get_pos()
                        grid_coords = (pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE)
                        
                        # --- SEND DATA TO SERVER ---
                        message = f"mouse down on: {grid_coords[0]};{grid_coords[1]}"
                        print(f"Sending: {message}")
                        self.network_client.send(message)

                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.is_scribbling = False
                        pos = pygame.mouse.get_pos()
                        grid_coords = (pos[0] // SQUARE_SIZE, pos[1] // SQUARE_SIZE)
                        
                        # --- SEND DATA TO SERVER ---
                        message = f"mouse up on: {grid_coords[0]};{grid_coords[1]}"
                        print(f"Sending: {message}")
                        self.network_client.send(message)
            
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

if __name__ == '__main__':
    gui = GameGUI()
    gui.run()