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

        # get the image, TODO: need to use array to add link for more random img. REMEMBER TO CHANGE
        image_url =  "https://i.pinimg.com/1200x/97/c3/e0/97c3e03d8bc65b3f277908c07289141f.jpg"
        self.puzzle = Puzzle(image_url, GRID_SIZE)
        self.pieces = self.puzzle.get_pieces()
        self.piece_rects = []
        
        # ----------Grid State Management----------
        # 2D grid to track which piece is in each position (None = empty, piece_id = occupied)
        self.grid_state = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        # Track which pieces are correctly placed
        self.correctly_placed_pieces = set()
        
        # ----------drag & drop ----------
        self.selected_piece_index = None
        self.is_dragging = False
        # track mouse 
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        
        # ----------snap functionality----------
        self.snap_threshold = 40  # pixels within which pieces will snap (increased for stronger snap)
        
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
        self.network_client = NetworkManager()
        self.network_client.connect("localhost", 8888)  # Default values, should be configurable

    # scatter pieces 
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
    
    def get_piece_grid_coordinates(self, piece_id):
        """Get the correct grid coordinates (row, col) for a piece"""
        piece_index = int(piece_id.split('_')[1])
        return (piece_index // GRID_SIZE, piece_index % GRID_SIZE)
    
    def update_grid_state(self, piece_id, new_grid_row, new_grid_col, old_grid_row=None, old_grid_col=None):
        """Update the grid state when a piece moves"""
        # Clear old position if provided
        if old_grid_row is not None and old_grid_col is not None:
            if (0 <= old_grid_row < GRID_SIZE and 0 <= old_grid_col < GRID_SIZE):
                self.grid_state[old_grid_row][old_grid_col] = None
        
        # Set new position if valid
        if (0 <= new_grid_row < GRID_SIZE and 0 <= new_grid_col < GRID_SIZE):
            self.grid_state[new_grid_row][new_grid_col] = piece_id
            
            # Check if piece is in correct position
            correct_row, correct_col = self.get_piece_grid_coordinates(piece_id)
            if new_grid_row == correct_row and new_grid_col == correct_col:
                self.correctly_placed_pieces.add(piece_id)
            else:
                self.correctly_placed_pieces.discard(piece_id)
        else:
            # Piece is off the grid
            self.correctly_placed_pieces.discard(piece_id)
    
    def get_grid_state_for_server(self):
        """Get a serializable grid state for server communication"""
        return {
            'grid': self.grid_state,
            'correctly_placed': list(self.correctly_placed_pieces),
            'completion_percentage': len(self.correctly_placed_pieces) / len(self.pieces) * 100,
            'is_completed': len(self.correctly_placed_pieces) == len(self.pieces)
        }
    
    def is_puzzle_completed(self):
        """Simple check if puzzle is completed"""
        return len(self.correctly_placed_pieces) == len(self.pieces)
    
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
            # Get old grid position if piece was already on grid
            piece_id = self.pieces[piece_index]['id']
            old_grid_pos = self.find_piece_in_grid(piece_id)
            
            # Get new grid position
            snap_x, snap_y, grid_row, grid_col = self.get_nearest_grid_position(piece_rect)
            self.piece_rects[piece_index].x = snap_x
            self.piece_rects[piece_index].y = snap_y
            
            # Update grid state
            old_row, old_col = old_grid_pos if old_grid_pos else (None, None)
            self.update_grid_state(piece_id, grid_row, grid_col, old_row, old_col)
            
            # Check if piece is correctly placed
            if piece_id in self.correctly_placed_pieces:
                print(f"Piece {piece_id} snapped into CORRECT position!")
            else:
                print(f"Piece {piece_id} snapped to grid position ({grid_row}, {grid_col})")
            
            return True
        else:
            # Piece moved off grid - remove from grid state
            piece_id = self.pieces[piece_index]['id']
            old_grid_pos = self.find_piece_in_grid(piece_id)
            if old_grid_pos:
                old_row, old_col = old_grid_pos
                self.update_grid_state(piece_id, -1, -1, old_row, old_col)  # -1 indicates off-grid
        
        return False
    
    def find_piece_in_grid(self, piece_id):
        """Find the current grid position of a piece, returns (row, col) or None"""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if self.grid_state[row][col] == piece_id:
                    return (row, col)
        return None

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
                        self.network_client.disconnect()

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
                                success = self.network_client.send_message(MSG_PLAYER_INPUT, payload)
                                print(f"Server response to lock: {success}")
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
                            if snapped and self.is_puzzle_completed():
                                self.puzzle_completed = True
                                self.win_time = pygame.time.get_ticks()
                                completion_time = (self.win_time - self.start_time) / 1000
                                print("🎉 PUZZLE COMPLETED! 🎉")
                                print(f"⏱️  Completion time: {completion_time:.1f} seconds")
                                self.send_completion_notification()
                            
                            # Send comprehensive state to server
                            grid_state = self.get_grid_state_for_server()
                            payload = {
                                'action': INPUT_ACTION_RELEASE_OBJECT, 
                                'object_id': piece_id,
                                'snapped': snapped,
                                'position': {
                                    'x': self.piece_rects[self.selected_piece_index].x,
                                    'y': self.piece_rects[self.selected_piece_index].y
                                },
                                'grid_state': grid_state
                            }
                            success = self.network_client.send_message(MSG_PLAYER_INPUT, payload)
                            print(f"Server response to release: {success}")

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
                            self.network_client.disconnect()

            self.draw_game()
            pygame.display.flip()
            self.clock.tick(60)

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
        progress = len(self.correctly_placed_pieces) / len(self.pieces) * 100
        
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
        pieces_text = self.small_font.render(f"Pieces: {len(self.correctly_placed_pieces)}/{len(self.pieces)}", True, COLOR_WHITE)
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
        
        # Reset grid state
        self.grid_state = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.correctly_placed_pieces = set()
        
        # Reset drag state
        self.is_dragging = False
        self.selected_piece_index = None
        
        # Re-scatter pieces
        self._scatter_pieces()
        
        print("✅ Puzzle restarted!")

    def send_completion_notification(self):
        """Send puzzle completion notification to server"""
        if self.network_client and self.puzzle_completed:
            completion_time = (self.win_time - self.start_time) / 1000
            grid_state = self.get_grid_state_for_server()
            
            payload = {
                'action': 'PUZZLE_COMPLETED',
                'completion_time': completion_time,
                'total_pieces': len(self.pieces),
                'grid_state': grid_state
            }
            try:
                success = self.network_client.send_message('MSG_GAME_EVENT', payload)
                print(f"Server notified of completion: {success}")
            except:
                print("Could not notify server of completion")
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