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
COLOR_SNAP_ZONE = (0, 255, 255)  # Cyan for snap zones
COLOR_SNAPPED = (0, 255, 0)      # Green for correctly placed pieces
COLOR_DRAGGING = (255, 255, 0)   # Yellow for piece being dragged
COLOR_GRID = (100, 100, 100)     # Darker grey for grid lines

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
        
        # ----------snap functionality----------
        self.snap_threshold = 40  # pixels within which pieces will snap (increased for stronger snap)
        self.snapped_pieces = {}  # track which pieces are in correct positions
        
        # ----------win condition----------
        self.puzzle_completed = False
        self.win_time = None
        self.start_time = pygame.time.get_ticks()  # Track game start time
        
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

    def get_correct_position(self, piece_id):
        """Calculate the correct grid position for a piece based on its ID"""
        piece_index = int(piece_id.split('_')[1])  # Extract number from 'piece_X'
        row = piece_index // GRID_SIZE
        col = piece_index % GRID_SIZE
        
        piece_width, piece_height = self.puzzle.piece_size
        correct_x = self.board_rect.left + col * piece_width
        correct_y = self.board_rect.top + row * piece_height
        
        return (correct_x, correct_y)
    
    def get_nearest_grid_position_from_cursor(self, cursor_pos):
        """Find the nearest grid position to the cursor location"""
        piece_width, piece_height = self.puzzle.piece_size
        
        # Find nearest grid position within the board based on cursor
        relative_x = cursor_pos[0] - self.board_rect.left
        relative_y = cursor_pos[1] - self.board_rect.top
        
        # Simple grid calculation - which cell does the cursor fall into?
        grid_col = max(0, min(GRID_SIZE - 1, int(relative_x // piece_width)))
        grid_row = max(0, min(GRID_SIZE - 1, int(relative_y // piece_height)))
        
        # Always snap to the top-left corner of the grid cell the cursor is in
        snap_x = self.board_rect.left + grid_col * piece_width
        snap_y = self.board_rect.top + grid_row * piece_height
        
        return (snap_x, snap_y, grid_row, grid_col)
    
    def get_nearest_grid_position(self, piece_rect):
        """Find the nearest grid position to the piece's current location"""
        piece_width, piece_height = self.puzzle.piece_size
        
        # Calculate which grid cell the piece center is closest to
        piece_center_x = piece_rect.x + piece_rect.width // 2
        piece_center_y = piece_rect.y + piece_rect.height // 2
        
        # Find nearest grid position within the board
        relative_x = piece_center_x - self.board_rect.left
        relative_y = piece_center_y - self.board_rect.top
        
        # Simple grid calculation - which cell does the piece center fall into?
        grid_col = max(0, min(GRID_SIZE - 1, int(relative_x // piece_width)))
        grid_row = max(0, min(GRID_SIZE - 1, int(relative_y // piece_height)))
        
        snap_x = self.board_rect.left + grid_col * piece_width
        snap_y = self.board_rect.top + grid_row * piece_height
        
        return (snap_x, snap_y, grid_row, grid_col)
    
    def is_near_grid_position(self, piece_rect):
        """Check if a piece is within snap threshold of any grid position"""
        if not self.board_rect.colliderect(piece_rect.inflate(self.snap_threshold * 3, self.snap_threshold * 3)):
            return False
            
        snap_x, snap_y, _, _ = self.get_nearest_grid_position(piece_rect)
        # Use piece center for more accurate distance calculation
        piece_center_x = piece_rect.x + piece_rect.width // 2
        piece_center_y = piece_rect.y + piece_rect.height // 2
        snap_center_x = snap_x + piece_rect.width // 2
        snap_center_y = snap_y + piece_rect.height // 2
        
        # Calculate Manhattan distance for stronger snap behavior
        distance_x = abs(piece_center_x - snap_center_x)
        distance_y = abs(piece_center_y - snap_center_y)
        max_distance = max(distance_x, distance_y)
        
        return max_distance <= self.snap_threshold
    
    def snap_piece_to_position(self, piece_index):
        """Snap a piece to the nearest grid position if it's close enough"""
        piece_rect = self.piece_rects[piece_index]
        
        if self.is_near_grid_position(piece_rect):
            snap_x, snap_y, grid_row, grid_col = self.get_nearest_grid_position(piece_rect)
            self.piece_rects[piece_index].x = snap_x
            self.piece_rects[piece_index].y = snap_y
            
            # Check if this is the correct position for this piece
            piece_id = self.pieces[piece_index]['id']
            piece_index_id = int(piece_id.split('_')[1])
            correct_row = piece_index_id // GRID_SIZE
            correct_col = piece_index_id % GRID_SIZE
            
            if grid_row == correct_row and grid_col == correct_col:
                self.snapped_pieces[piece_id] = True
                print(f"Piece {piece_id} snapped into CORRECT position!")
            else:
                # Remove from snapped pieces if it was there before
                if piece_id in self.snapped_pieces:
                    del self.snapped_pieces[piece_id]
                print(f"Piece {piece_id} snapped to grid position ({grid_row}, {grid_col})")
            
            return True
        return False

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
                            
                            # Try to snap the piece to its correct position
                            snapped = self.snap_piece_to_position(self.selected_piece_index)
                            
                            # Check if puzzle is completed after snapping
                            if snapped:
                                self.check_puzzle_completion()
                            
                            payload = {
                                'action': INPUT_ACTION_RELEASE_OBJECT, 
                                'object_id': piece_id,
                                'snapped': snapped,
                                'position': {
                                    'x': self.piece_rects[self.selected_piece_index].x,
                                    'y': self.piece_rects[self.selected_piece_index].y
                                }
                            }
                            response = self.network_client.send(MSG_PLAYER_INPUT , payload)
                            print(f"Server response to release: {response}")

                        # no longer dragging
                        self.is_dragging = False
                        self.selected_piece_index  = None

                elif event.type == pygame.MOUSEMOTION:
                    # Move the piece with mouse if holding
                    if self.is_dragging and self.selected_piece_index is not None:
                        new_x = mouse_pos[0] - self.mouse_offset_x
                        new_y = mouse_pos[1] - self.mouse_offset_y
                        
                        # Apply magnetic snap effect when near grid positions
                        test_rect = pygame.Rect(new_x, new_y, 
                                              self.piece_rects[self.selected_piece_index].width,
                                              self.piece_rects[self.selected_piece_index].height)
                        
                        if self.is_near_grid_position(test_rect):
                            snap_x, snap_y, _, _ = self.get_nearest_grid_position(test_rect)
                            # Apply magnetic pull effect - pieces are drawn toward snap positions
                            pull_strength = 0.5  # Adjust between 0.1-0.5 for different pull strengths
                            new_x = new_x + (snap_x - new_x) * pull_strength
                            new_y = new_y + (snap_y - new_y) * pull_strength
                        
                        self.piece_rects[self.selected_piece_index].x = new_x
                        self.piece_rects[self.selected_piece_index].y = new_y

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r and self.puzzle_completed:
                        # Restart the game
                        self.restart_game()
                    elif event.key == pygame.K_ESCAPE:
                        # Quit the game
                        running = False
                        if self.network_client:
                            self.network_client.close()

            self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    # draw game and grid
    def draw_game(self):
        self.screen.fill(COLOR_BACKGROUND)
        self.draw_grid_lines()
        
        # Get current mouse position for snap zone calculation
        mouse_pos = pygame.mouse.get_pos()
        self.draw_snap_zones(mouse_pos)

        for i, piece_data in enumerate(self.pieces):
            piece_id = piece_data['id']
            piece_rect = self.piece_rects[i]
            
            # Highlight piece being dragged
            if self.is_dragging and i == self.selected_piece_index:
                pygame.draw.rect(self.screen, COLOR_DRAGGING, piece_rect, 2)
            
            self.screen.blit(piece_data['image'], piece_rect)
        
        # Draw UI elements
        self.draw_ui()
        
        # Draw win screen if puzzle is completed
        if self.puzzle_completed:
            self.draw_win_screen()

    def draw_snap_zones(self, mouse_pos):
        """Draw visual indicators for snap zones when dragging"""
        if not self.is_dragging or self.selected_piece_index is None:
            return
            
        # Use cursor position to determine snap zone for better alignment
        if self.board_rect.collidepoint(mouse_pos):
            snap_x, snap_y, grid_row, grid_col = self.get_nearest_grid_position_from_cursor(mouse_pos)
            piece_width, piece_height = self.puzzle.piece_size
            
            # Draw a larger, more visible snap zone
            snap_zone = pygame.Rect(snap_x - self.snap_threshold // 2, 
                                   snap_y - self.snap_threshold // 2,
                                   piece_width + self.snap_threshold, 
                                   piece_height + self.snap_threshold)
            
            # Create a surface for transparency with stronger visual feedback
            snap_surface = pygame.Surface((snap_zone.width, snap_zone.height))
            snap_surface.set_alpha(80)  # More visible
            snap_surface.fill(COLOR_SNAP_ZONE)  # Cyan color
            self.screen.blit(snap_surface, snap_zone.topleft)
            
            # Draw the exact snap position with a thicker, more visible outline
            snap_rect = pygame.Rect(snap_x, snap_y, piece_width, piece_height)
            pygame.draw.rect(self.screen, COLOR_SNAP_ZONE, snap_rect, 4)  # Thicker border
            
            # Draw crosshairs at cursor position for better alignment reference
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (mouse_pos[0] - 10, mouse_pos[1]), 
                           (mouse_pos[0] + 10, mouse_pos[1]), 2)
            pygame.draw.line(self.screen, (255, 255, 255), 
                           (mouse_pos[0], mouse_pos[1] - 10), 
                           (mouse_pos[0], mouse_pos[1] + 10), 2)

    def draw_ui(self):
        """Draw game UI elements like progress and timer"""
        # Initialize font if not already done
        if not hasattr(self, 'font'):
            pygame.font.init()
            self.font = pygame.font.Font(None, 36)
            self.small_font = pygame.font.Font(None, 24)
        
        # Calculate progress
        progress = len(self.snapped_pieces) / len(self.pieces) * 100
        
        # Calculate elapsed time - stop timer when puzzle is completed
        if self.puzzle_completed and self.win_time:
            elapsed_time = (self.win_time - self.start_time) / 1000
        else:
            current_time = pygame.time.get_ticks()
            elapsed_time = (current_time - self.start_time) / 1000
        
        # Draw progress text
        progress_text = self.font.render(f"Progress: {progress:.0f}%", True, COLOR_WHITE)
        self.screen.blit(progress_text, (10, 10))
        
        # Draw timer
        timer_text = self.small_font.render(f"Time: {elapsed_time:.1f}s", True, COLOR_WHITE)
        self.screen.blit(timer_text, (10, 50))
        
        # Draw pieces count
        pieces_text = self.small_font.render(f"Pieces: {len(self.snapped_pieces)}/{len(self.pieces)}", True, COLOR_WHITE)
        self.screen.blit(pieces_text, (10, 75))
        
        # Draw progress bar
        bar_width = 200
        bar_height = 20
        bar_x = 10
        bar_y = 100
        
        # Background bar
        pygame.draw.rect(self.screen, COLOR_GREY, (bar_x, bar_y, bar_width, bar_height))
        
        # Progress bar
        progress_width = int(bar_width * progress / 100)
        color = COLOR_SNAPPED if progress == 100 else COLOR_SNAP_ZONE
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, progress_width, bar_height))
        
        # Progress bar border
        pygame.draw.rect(self.screen, COLOR_WHITE, (bar_x, bar_y, bar_width, bar_height), 2)

    def draw_win_screen(self):
        """Draw celebration screen when puzzle is completed"""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))
        
        # Initialize fonts for win screen
        if not hasattr(self, 'big_font'):
            self.big_font = pygame.font.Font(None, 72)
            self.medium_font = pygame.font.Font(None, 48)
        
        # Calculate completion time
        completion_time = (self.win_time - self.start_time) / 1000
        
        # Draw celebration text
        win_text = self.big_font.render("🎉 PUZZLE COMPLETED! 🎉", True, COLOR_SNAPPED)
        win_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60))
        self.screen.blit(win_text, win_rect)
        
        # Draw completion time
        time_text = self.medium_font.render(f"Time: {completion_time:.1f} seconds", True, COLOR_WHITE)
        time_rect = time_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(time_text, time_rect)
        
        # Draw pieces info
        pieces_text = self.medium_font.render(f"Pieces: {len(self.pieces)}", True, COLOR_WHITE)
        pieces_rect = pieces_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        self.screen.blit(pieces_text, pieces_rect)
        
        # Draw restart instruction
        restart_text = self.font.render("Press R to restart or ESC to quit", True, COLOR_SNAP_ZONE)
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 100))
        self.screen.blit(restart_text, restart_rect)

    def restart_game(self):
        """Restart the puzzle game"""
        print("🔄 Restarting puzzle...")
        
        # Reset game state
        self.puzzle_completed = False
        self.win_time = None
        self.start_time = pygame.time.get_ticks()
        self.snapped_pieces = {}
        self.is_dragging = False
        self.selected_piece_index = None
        
        # Re-scatter pieces
        self._scatter_pieces()
        
        print("✅ Puzzle restarted!")

    def check_puzzle_completion(self):
        """Check if all pieces are in their correct positions"""
        if not self.puzzle_completed:
            # Count how many pieces are actually in their correct positions right now
            correctly_placed = 0
            
            for i, piece_data in enumerate(self.pieces):
                piece_id = piece_data['id']
                piece_rect = self.piece_rects[i]
                piece_index_id = int(piece_id.split('_')[1])
                
                # Calculate the correct position for this piece
                correct_row = piece_index_id // GRID_SIZE
                correct_col = piece_index_id % GRID_SIZE
                
                # Calculate which grid position this piece is currently in
                piece_width, piece_height = self.puzzle.piece_size
                piece_center_x = piece_rect.x + piece_rect.width // 2
                piece_center_y = piece_rect.y + piece_rect.height // 2
                
                # Check if piece is within the board area
                if self.board_rect.collidepoint(piece_center_x, piece_center_y):
                    relative_x = piece_center_x - self.board_rect.left
                    relative_y = piece_center_y - self.board_rect.top
                    
                    current_col = int(relative_x // piece_width)
                    current_row = int(relative_y // piece_height)
                    
                    # Check if piece is in correct position and properly snapped
                    if (current_row == correct_row and current_col == correct_col and
                        piece_rect.x == self.board_rect.left + correct_col * piece_width and
                        piece_rect.y == self.board_rect.top + correct_row * piece_height):
                        correctly_placed += 1
            
            # Only complete if ALL pieces are correctly placed
            if correctly_placed == len(self.pieces):
                self.puzzle_completed = True
                self.win_time = pygame.time.get_ticks()
                completion_time = (self.win_time - self.start_time) / 1000  # Convert to seconds
                
                print("🎉 PUZZLE COMPLETED! 🎉")
                print(f"⏱️  Completion time: {completion_time:.1f} seconds")
                print(f"🧩 Total pieces: {len(self.pieces)}")
                
                # Send completion notification to server
                if self.network_client:
                    payload = {
                        'action': 'PUZZLE_COMPLETED',
                        'completion_time': completion_time,
                        'total_pieces': len(self.pieces)
                    }
                    try:
                        response = self.network_client.send('MSG_GAME_EVENT', payload)
                        print(f"Server notified of completion: {response}")
                    except:
                        print("Could not notify server of completion")
                
                return True
        return False

    def draw_grid_lines(self):
        if not self.pieces:
            return
        
        #how big each piece is
        piece_width, piece_height = self.puzzle.piece_size
        
        # draw vertical + horizontal lines 
        for i in range(GRID_SIZE + 1):
            start_pos_v = (self.board_rect.left + i * piece_width, self.board_rect.top)
            end_pos_v = (self.board_rect.left   + i * piece_width, self.board_rect.bottom)
            pygame.draw.line(self.screen, COLOR_GRID, start_pos_v, end_pos_v, 2)
            
            start_pos_h = (self.board_rect.left, self.board_rect.top + i * piece_height)
            end_pos_h = (self.board_rect.right, self.board_rect.top  + i * piece_height)
            pygame.draw.line(self.screen, COLOR_GRID, start_pos_h, end_pos_h, 2)