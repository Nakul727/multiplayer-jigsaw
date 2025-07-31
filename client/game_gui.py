import pygame
import random
from network_client import NetworkClient
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
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Multiplayer Jigsaw Puzzle") # should we change the name ?
        self.clock = pygame.time.Clock()

        # get the image, TODO: need to use arrry to add link for more random img. REMEMBER TO CHANGE
        image_url =  "https://i.pinimg.com/1200x/97/c3/e0/97c3e03d8bc65b3f277908c07289141f.jpg"
        self.puzzle = Puzzle(image_url, GRID_SIZE)
        self.pieces = self.puzzle.get_pieces()
        self.piece_rects = []
        
        # ----------drag & drop ----------
        self.selected_piece_index = None
        self.is_dragging =  False
        #track mouse 
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
            print("Failed to load puzzle pieces. game cannot start.")
            self.board_rect = pygame.Rect(0,0,0,0)

        # Networking
        self.network_client = NetworkClient()
        self.network_client.connect()

    # scxatter pieces 
    def _scatter_pieces(self):
        self.piece_rects = []
        for piece_data in self.pieces:
            piece_image = piece_data['image']
            random_x = random.randint (0, WINDOW_WIDTH - piece_image.get_width())
            random_y = random.randint(0, WINDOW_HEIGHT - piece_image.get_height())
            self.piece_rects.append (piece_image.get_rect(topleft=(random_x , random_y)))

# DA MAIN GAME LOOP 
    def run(self):
        running = True
        while running:
            # --- Event Handling ---
            # checking if anyones clicking, dragging, quitting, all that stuff
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    if self.network_client:
                        self.network_client.close()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1: # Left mouse button down
                        # we go backwards in list so topmost pieces get picked first
                        for i in range(len (self.piece_rects) - 1, -1, -1):
                            if self.piece_rects[i].collidepoint (mouse_pos):
                                self.is_dragging = True
                                self.selected_piece_index = i
                                
                                # get pieceid and send lock request (idk about lock)
                                piece_id = self.pieces[i]['id']
                                print(f"Attempting to lock {piece_id}")
                                payload = {
                                    'action': INPUT_ACTION_LOCK_OBJECT,
                                    'object_id': piece_id
                                }
                                response = self.network_client.send(MSG_PLAYER_INPUT , payload)
                                print(f"Server response to lock: {response}")
                                # need to check if lock was successful
                                
                                # meowouse math, so the piece sticks to our cursor nicely
                                self.mouse_offset_x = mouse_pos[0] - self.piece_rects[i].x
                                self.mouse_offset_y = mouse_pos[1] - self.piece_rects[i].y
                                
                                # if you select the pieces, bring piece to front
                                selected_p = self.pieces.pop(i)
                                selected_r = self.piece_rects.pop(i)
                                self.pieces.append(selected_p)
                                self.piece_rects.append (selected_r)
                                self.selected_piece_index = len(self.pieces) - 1
                                break

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.is_dragging:
                        # letting go of mouse
                        # get pieceid and send release req
                        if self.selected_piece_index is not None:
                            piece_id = self.pieces[self.selected_piece_index]['id']
                            print(f"Releasing {piece_id}")
                            payload = {
                                'action': INPUT_ACTION_RELEASE_OBJECT, 
                                'object_id': piece_id
                            }
                            response = self.network_client.send(MSG_PLAYER_INPUT , payload)
                            print(f"Server response to release: {response}")

                        # no longer dragging
                        self.is_dragging = False
                        self.selected_piece_index  = None

                elif event.type == pygame.MOUSEMOTION:
                    # Move the piece with mouse if holding
                    if self.is_dragging and self.selected_piece_index is not None:
                        self.piece_rects[self.selected_piece_index].x = mouse_pos[0] - self.mouse_offset_x
                        self.piece_rects[self.selected_piece_index].y = mouse_pos[1] - self.mouse_offset_y

            self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    # draw game and grid
    def draw_game(self):
        self.screen.fill(COLOR_BACKGROUND)
        self.draw_grid_lines()

        for i, piece_data in enumerate(self.pieces):
            self.screen.blit(piece_data['image'], self.piece_rects[i])

    def draw_grid_lines(self):
        if not self.pieces:
            return
        
        #how big each piece is
        piece_width, piece_height = self.puzzle.piece_size
        
        # draw vertical + horizontal lines 
        for i in range(GRID_SIZE + 1):
            start_pos_v = (self.board_rect.left + i * piece_width, self.board_rect.top)
            end_pos_v = (self.board_rect.left   + i * piece_width, self.board_rect.bottom)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos_v, end_pos_v, 2)
            
            start_pos_h = (self.board_rect.left, self.board_rect.top + i * piece_height)
            end_pos_h = (self.board_rect.right, self.board_rect.top  + i * piece_height)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos_h, end_pos_h, 2)