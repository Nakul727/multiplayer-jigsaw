import pygame
import random
from network_manager import NetworkManager
from protocol import *
from puzzle import Puzzle

# Size
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800
GRID_SIZE = 3

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (200, 200, 200)
COLOR_BLACK = (0, 0, 0)
COLOR_BACKGROUND = (30, 30, 30)

class GameGUI:
    def __init__(self, network_manager: NetworkManager, image_url: str):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Multiplayer Jigsaw Puzzle")
        self.clock = pygame.time.Clock()

        # Use the provided image_url to create the puzzle
        self.puzzle = Puzzle(image_url, GRID_SIZE)
        self.pieces = self.puzzle.get_pieces()
        self.piece_rects = []
        
        # --- Drag & Drop State ---
        self.selected_piece_index = None
        self.is_dragging =  False
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        if self.pieces:
            piece_width, piece_height = self.pieces[0]['image'].get_size()
            board_width  = piece_width * GRID_SIZE
            board_height = piece_height * GRID_SIZE
            self.board_rect = pygame.Rect(
                (WINDOW_WIDTH  - board_width) // 2,
                (WINDOW_HEIGHT -  board_height) // 2,
                board_width,
                board_height
            )
            self._scatter_pieces()
        else:
            print("Failed to load puzzle pieces. Game cannot start.")
            self.board_rect = pygame.Rect(0,0,0,0)

        # Use the network_manager passed from main.py
        self.network_manager = network_manager

    def _scatter_pieces(self):
        """Randomly places pieces on the screen."""
        self.piece_rects = []
        for piece_data in self.pieces:
            piece_image = piece_data['image']
            random_x = random.randint(0, WINDOW_WIDTH - piece_image.get_width())
            random_y = random.randint(0, WINDOW_HEIGHT - piece_image.get_height())
            self.piece_rects.append(piece_image.get_rect(topleft=(random_x, random_y)))

    def run(self):
        """The main game loop."""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.network_manager.leave_game()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse button
                        for i in range(len(self.piece_rects) - 1, -1, -1):
                            if self.piece_rects[i].collidepoint(mouse_pos):
                                self.is_dragging = True
                                self.selected_piece_index = i
                                
                                piece_id = self.pieces[i]['id']
                                print(f"Attempting to lock piece: {piece_id}")
                                self.network_manager.lock_object(piece_id)
                                
                                self.mouse_offset_x = mouse_pos[0] - self.piece_rects[i].x
                                self.mouse_offset_y = mouse_pos[1] - self.piece_rects[i].y
                                
                                # Bring the selected piece to the front for rendering
                                selected_p = self.pieces.pop(i)
                                selected_r = self.piece_rects.pop(i)
                                self.pieces.append(selected_p)
                                self.piece_rects.append(selected_r)
                                self.selected_piece_index = len(self.pieces) - 1
                                break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.is_dragging and self.selected_piece_index is not None:
                        piece_id = self.pieces[self.selected_piece_index]['id']
                        final_pos = self.piece_rects[self.selected_piece_index].topleft
                        print(f"Releasing piece {piece_id} at {final_pos}")
                        self.network_manager.release_object(piece_id, {"x": final_pos[0], "y": final_pos[1]})
                        
                        self.is_dragging = False
                        self.selected_piece_index = None

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging and self.selected_piece_index is not None:
                        # Update position locally
                        new_x = mouse_pos[0] - self.mouse_offset_x
                        new_y = mouse_pos[1] - self.mouse_offset_y
                        self.piece_rects[self.selected_piece_index].x = new_x
                        self.piece_rects[self.selected_piece_index].y = new_y
                        
                        # Send move update to server
                        piece_id = self.pieces[self.selected_piece_index]['id']
                        self.network_manager.move_locked_object(piece_id, {"x": new_x, "y": new_y})

            self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def draw_game(self):
        """Renders the game state to the screen."""
        self.screen.fill(COLOR_BACKGROUND)
        self.draw_grid_lines()

        for i, piece_data in enumerate(self.pieces):
            self.screen.blit(piece_data['image'], self.piece_rects[i])

    def draw_grid_lines(self):
        """Draws the puzzle board grid."""
        if not self.pieces:
            return
        
        piece_width, piece_height = self.puzzle.piece_size
        
        for i in range(GRID_SIZE + 1):
            # Vertical lines
            start_pos_v = (self.board_rect.left + i * piece_width, self.board_rect.top)
            end_pos_v = (self.board_rect.left   + i * piece_width, self.board_rect.bottom)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos_v, end_pos_v, 2)
            
            # Horizontal lines
            start_pos_h = (self.board_rect.left, self.board_rect.top + i * piece_height)
            end_pos_h = (self.board_rect.right, self.board_rect.top  + i * piece_height)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos_h, end_pos_h, 2)