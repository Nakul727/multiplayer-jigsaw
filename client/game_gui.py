import pygame
import sys
import os

from puzzle import Puzzle

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from protocol import *
from constants import *

class GameGUI:
    def __init__(self, network_manager, image_url, piece_positions, difficulty='easy'):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Multiplayer Jigsaw Puzzle - {difficulty.title()}")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
    
        # Network manager
        self.network_manager = network_manager
        
        # Difficulty settings
        self.difficulty = difficulty
        self.difficulty_settings = DIFFICULTY_SETTINGS[difficulty]
        
        # Game state
        self.selected_piece_index = None
        self.is_dragging = False
        self.mouse_offset_x = 0
        self.mouse_offset_y = 0
        self.game_won = False
        self.snap_tolerance = 30
        
        # Create puzzle with difficulty
        self.puzzle = Puzzle(image_url, difficulty)
        self.pieces = self.puzzle.get_pieces()
        self.piece_rects = []
        
        # Calculate board dimensions using ACTUAL puzzle piece sizes
        if self.pieces:
            grid_cols, grid_rows = self.puzzle.get_grid_dimensions()
            piece_width, piece_height = self.puzzle.get_piece_size()
            
            # Use the actual puzzle dimensions
            board_width = piece_width * grid_cols
            board_height = piece_height * grid_rows
            
            # Center the board on screen
            board_x = (WINDOW_WIDTH - board_width) // 2
            board_y = (WINDOW_HEIGHT - board_height) // 2
            
            self.board_rect = pygame.Rect(board_x, board_y, board_width, board_height)
            
            # Use the ACTUAL piece sizes from puzzle
            self.piece_display_width = piece_width
            self.piece_display_height = piece_height
            
            # Set piece positions from server data
            self._set_piece_positions(piece_positions)
            
            # print(f"Board size: {board_width}x{board_height}")
            # print(f"Board position: ({board_x}, {board_y})")
            # print(f"Piece display size: {self.piece_display_width}x{self.piece_display_height}")
            # print(f"Total pieces: {len(self.pieces)}")
            # print(f"Difficulty: {difficulty}")
        else:
            print("Failed to load puzzle pieces. Game cannot start.")
            self.board_rect = pygame.Rect(0, 0, 0, 0)
            self.piece_display_width = 0
            self.piece_display_height = 0
        
        # Track piece positions for win condition
        self.piece_positions = {}
        for i, piece in enumerate(self.pieces):
            if i < len(self.piece_rects):
                pos = self.piece_rects[i].topleft
                self.piece_positions[piece['id']] = pos

    def _set_piece_positions(self, server_positions):
        """
        Set piece positions from server data - pieces can be anywhere on screen.
        """
        self.piece_rects = []
        
        if server_positions:
            # print(f"Using server-provided piece positions for {len(server_positions)} pieces")
            
            # Position pieces according to server data
            for piece_data in self.pieces:
                piece_id = piece_data['id']
                piece_image = piece_data['image']
                
                # Get position from server data
                if piece_id in server_positions:
                    server_pos = server_positions[piece_id]
                    x, y = server_pos['x'], server_pos['y']
                else:
                    # Fallback position if server data missing
                    print(f"Warning: No server position for piece {piece_id}, using fallback")
                    x, y = 50, 50
                
                self.piece_rects.append(piece_image.get_rect(topleft=(x, y)))
        else:
            print("No server positions provided, using fallback scatter")
            self._fallback_scatter_pieces()

    def _fallback_scatter_pieces(self):
        """
        Fallback method for positioning pieces anywhere on the screen.
        """
        self.piece_rects = []
        
        for i, piece_data in enumerate(self.pieces):
            piece_image = piece_data['image']
            
            # Allow pieces to be scattered anywhere on screen (with margins) 
            # # Leave space for title
            max_x = max(10, WINDOW_WIDTH - piece_image.get_width() - 10)
            max_y = max(80, WINDOW_HEIGHT - piece_image.get_height() - 10) 
            
            # Use piece index for basic positioning
            x = 10 + (i * 25) % max_x
            y = 80 + (i * 35) % max_y
            
            self.piece_rects.append(piece_image.get_rect(topleft=(x, y)))

    def update_piece_positions(self, server_positions):
        """
        Update all piece positions from server data.
        Called when joining a game or receiving position updates.
        """
        if not server_positions:
            return
            
        print(f"Updating piece positions from server data")
        
        for i, piece in enumerate(self.pieces):
            piece_id = piece['id']
            if piece_id in server_positions and i < len(self.piece_rects):
                server_pos = server_positions[piece_id]
                self.piece_rects[i].x = server_pos['x']
                self.piece_rects[i].y = server_pos['y']
                self.piece_positions[piece_id] = (server_pos['x'], server_pos['y'])

    def run(self):
        """The main game loop."""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            
            # Update piece positions from network manager each frame
            self._sync_with_network_manager()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.network_manager.leave_game()

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not self.game_won:
                        self._handle_mouse_down(mouse_pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1 and self.is_dragging:
                        self._handle_mouse_up()

                elif event.type == pygame.MOUSEMOTION:
                    if self.is_dragging and self.selected_piece_index is not None:
                        self._handle_mouse_move(mouse_pos)

            self._draw_game()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

    def _sync_with_network_manager(self):
        """Sync piece positions and lock states with network manager."""
        # Check if puzzle was completed by another player
        if not self.game_won and self.network_manager.is_puzzle_completed():
            self.game_won = True
            solver_info = self.network_manager.get_puzzle_solver()
            if solver_info:
                print(f"PUZZLE SOLVED by {solver_info['ip']}:{solver_info['port']}!")
            else:
                print("PUZZLE SOLVED by another player!")
        
        # Get current positions from network manager
        network_positions = self.network_manager.get_current_piece_positions()
        
        # Update local positions for pieces that aren't being dragged by us
        for i, piece in enumerate(self.pieces):
            piece_id = piece['id']
            
            # Skip if we're dragging this piece
            if self.is_dragging and i == self.selected_piece_index:
                continue
                
            # Update position from network manager if available
            if piece_id in network_positions and i < len(self.piece_rects):
                network_pos = network_positions[piece_id]
                current_pos = (self.piece_rects[i].x, self.piece_rects[i].y)
                network_tuple = (network_pos['x'], network_pos['y'])
                
                # Only update if position changed
                if current_pos != network_tuple:
                    self.piece_rects[i].x = network_pos['x']
                    self.piece_rects[i].y = network_pos['y']
                    self.piece_positions[piece_id] = network_tuple

    def _handle_mouse_down(self, mouse_pos):
        """Handle mouse button down event."""
        # Check pieces from front to back (reverse order)
        for i in range(len(self.piece_rects) - 1, -1, -1):
            if self.piece_rects[i].collidepoint(mouse_pos):
                piece_id = self.pieces[i]['id']
                
                # Check if piece is locked by another player using network manager
                if self.network_manager.is_piece_locked_by_others(piece_id):
                    locker_info = self.network_manager.get_piece_locker_info(piece_id)
                    print(f"Piece {piece_id} is locked by another player: {locker_info}")
                    return
                
                self.is_dragging = True
                self.selected_piece_index = i
                
                self.network_manager.lock_object(piece_id)
                
                # Calculate mouse offset for smooth dragging
                self.mouse_offset_x = mouse_pos[0] - self.piece_rects[i].x
                self.mouse_offset_y = mouse_pos[1] - self.piece_rects[i].y
                
                # Move selected piece to front for rendering
                selected_piece = self.pieces.pop(i)
                selected_rect = self.piece_rects.pop(i)
                self.pieces.append(selected_piece)
                self.piece_rects.append(selected_rect)
                self.selected_piece_index = len(self.pieces) - 1
                break

    def _handle_mouse_up(self):
        """Handle mouse button up event."""
        if self.selected_piece_index is None:
            return
            
        piece_id = self.pieces[self.selected_piece_index]['id']
        piece_rect = self.piece_rects[self.selected_piece_index]
        
        # Check if piece should snap to correct position
        correct_pos = self._get_correct_screen_position(piece_id)
        if correct_pos:
            distance = ((piece_rect.x - correct_pos[0]) ** 2 + 
                       (piece_rect.y - correct_pos[1]) ** 2) ** 0.5
            
            if distance <= self.snap_tolerance:
                # Snap to correct position
                piece_rect.x, piece_rect.y = correct_pos
                print(f"Piece {piece_id} snapped to correct position!")
        
        # Update piece position tracking
        final_pos = piece_rect.topleft
        self.piece_positions[piece_id] = final_pos
        
        # Update network manager's local position tracking
        self.network_manager.update_local_piece_position(piece_id, {"x": final_pos[0], "y": final_pos[1]})
        
        self.network_manager.release_object(piece_id, {"x": final_pos[0], "y": final_pos[1]})
        
        # Check win condition
        if self._check_win_condition():
            self.game_won = True
            print("PUZZLE SOLVED! YOU WIN!")
            self.network_manager.puzzle_solved()
        
        self.is_dragging = False
        self.selected_piece_index = None

    def _handle_mouse_move(self, mouse_pos):
        """Handle mouse movement during dragging."""
        new_x = mouse_pos[0] - self.mouse_offset_x
        new_y = mouse_pos[1] - self.mouse_offset_y
        
        # Keep piece on screen
        piece_rect = self.piece_rects[self.selected_piece_index]
        new_x = max(0, min(new_x, WINDOW_WIDTH - piece_rect.width))
        new_y = max(0, min(new_y, WINDOW_HEIGHT - piece_rect.height))
        
        piece_rect.x = new_x
        piece_rect.y = new_y
        
        # Send move update to server
        piece_id = self.pieces[self.selected_piece_index]['id']
        self.network_manager.move_locked_object(piece_id, {"x": new_x, "y": new_y})

    def _get_correct_screen_position(self, piece_id):
        """Get the correct screen position for a piece using actual piece dimensions."""
        piece = self.puzzle.get_piece_by_id(piece_id)
        if not piece:
            return None
        
        # Calculate position using actual piece sizes
        correct_x = self.board_rect.x + (piece['correct_col'] * self.piece_display_width)
        correct_y = self.board_rect.y + (piece['correct_row'] * self.piece_display_height)
        
        return (correct_x, correct_y)

    def _check_win_condition(self):
        """Check if all pieces are in correct positions."""
        for piece in self.pieces:
            piece_id = piece['id']
            if piece_id not in self.piece_positions:
                return False
            
            current_pos = self.piece_positions[piece_id]
            correct_pos = self._get_correct_screen_position(piece_id)
            
            if not correct_pos:
                return False
            
            distance = ((current_pos[0] - correct_pos[0]) ** 2 + 
                       (current_pos[1] - correct_pos[1]) ** 2) ** 0.5
            
            if distance > self.snap_tolerance:
                return False
        
        return True

    def _draw_game(self):
        """Renders the entire game state."""
        self.screen.fill(COLOR_BACKGROUND)
        
        # Draw UI elements
        self._draw_ui()
        
        # Draw puzzle board
        self._draw_board()
        
        # Draw pieces
        self._draw_pieces()
        
        # Draw win message if game is won
        if self.game_won:
            self._draw_win_message()

    def _draw_ui(self):
        """Draw UI elements with centered title."""
        # Centered title at the top
        title_text = self.font.render(f"Multiplayer Jigsaw Puzzle", True, COLOR_WHITE)
        title_rect = title_text.get_rect(center=(WINDOW_WIDTH // 2, 25))
        self.screen.blit(title_text, title_rect)
        
        # Game info in top-left corner
        game_id_text = f"Game: {self.network_manager.game_id or 'N/A'}"
        game_id_surface = self.small_font.render(game_id_text, True, COLOR_GREY)
        self.screen.blit(game_id_surface, (10, 10))
        
        game_name_text = f"Room: {self.network_manager.game_name or 'N/A'}"
        game_name_surface = self.small_font.render(game_name_text, True, COLOR_GREY)
        self.screen.blit(game_name_surface, (10, 30))
        
        players_text = f"Players: {self.network_manager.current_players}/{self.network_manager.max_players}"
        players_surface = self.small_font.render(players_text, True, COLOR_GREY)
        self.screen.blit(players_surface, (10, 50))
        
        # Host info
        if hasattr(self.network_manager, 'host_info') and self.network_manager.host_info:
            host_text = f"Host: {self.network_manager.host_info['ip']}:{self.network_manager.host_info['port']}"
        else:
            host_text = "Host: N/A"
        host_surface = self.small_font.render(host_text, True, COLOR_GREY)
        self.screen.blit(host_surface, (10, 70))
        
        # Puzzle state and difficulty in top-right corner
        correct_pieces = sum(1 for piece in self.pieces if self._is_piece_correctly_placed(piece['id']))
        total_pieces_count = len(self.pieces)
        completion_percent = int((correct_pieces / total_pieces_count) * 100) if total_pieces_count > 0 else 0
        
        correct_text = f"Correct: {correct_pieces}/{total_pieces_count}"
        correct_surface = self.small_font.render(correct_text, True, COLOR_GREY)
        correct_rect = correct_surface.get_rect(topright=(WINDOW_WIDTH - 10, 10))
        self.screen.blit(correct_surface, correct_rect)
        
        progress_text = f"Progress: {completion_percent}%"
        progress_surface = self.small_font.render(progress_text, True, COLOR_GREY)
        progress_rect = progress_surface.get_rect(topright=(WINDOW_WIDTH - 10, 30))
        self.screen.blit(progress_surface, progress_rect)
        
        difficulty_text = f"Difficulty: {self.difficulty.title()}"
        difficulty_surface = self.small_font.render(difficulty_text, True, COLOR_GREY)
        difficulty_rect = difficulty_surface.get_rect(topright=(WINDOW_WIDTH - 10, 50))
        self.screen.blit(difficulty_surface, difficulty_rect)

    def _draw_board(self):
        """Draw the puzzle board with grid lines using actual dimensions."""
        # Draw board background
        pygame.draw.rect(self.screen, COLOR_BOARD_BG, self.board_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, self.board_rect, 2)
        
        # Draw grid lines using actual piece dimensions
        grid_cols, grid_rows = self.puzzle.get_grid_dimensions()
        
        # Vertical lines
        for i in range(grid_cols + 1):
            x = self.board_rect.x + i * self.piece_display_width
            start_pos = (x, self.board_rect.y)
            end_pos = (x, self.board_rect.y + self.board_rect.height)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos, end_pos, 1)
        
        # Horizontal lines
        for i in range(grid_rows + 1):
            y = self.board_rect.y + i * self.piece_display_height
            start_pos = (self.board_rect.x, y)
            end_pos = (self.board_rect.x + self.board_rect.width, y)
            pygame.draw.line(self.screen, COLOR_GREY, start_pos, end_pos, 1)

    def _draw_pieces(self):
        """Draw all puzzle pieces."""
        for i, piece_data in enumerate(self.pieces):
            piece_rect = self.piece_rects[i]
            piece_id = piece_data['id']
            
            # Draw piece
            self.screen.blit(piece_data['image'], piece_rect)
            
            # Draw border around selected piece (your own)
            if i == self.selected_piece_index and self.is_dragging:
                pygame.draw.rect(self.screen, COLOR_YELLOW, piece_rect, 3)
            
            # Draw border around pieces locked by other players (using network manager)
            elif self.network_manager.is_piece_locked_by_others(piece_id):
                pygame.draw.rect(self.screen, COLOR_ORANGE, piece_rect, 3)
            
            # Draw border around correctly placed pieces
            elif self._is_piece_correctly_placed(piece_id):
                pygame.draw.rect(self.screen, COLOR_GREEN, piece_rect, 2)

    def _is_piece_correctly_placed(self, piece_id):
        """Check if a specific piece is correctly placed."""
        if piece_id not in self.piece_positions:
            return False
        
        current_pos = self.piece_positions[piece_id]
        correct_pos = self._get_correct_screen_position(piece_id)
        
        if not correct_pos:
            return False
        
        distance = ((current_pos[0] - correct_pos[0]) ** 2 + 
                   (current_pos[1] - correct_pos[1]) ** 2) ** 0.5
        
        return distance <= self.snap_tolerance
    
    def _draw_win_message(self):
        """Draw the win message overlay."""
        # Semi-transparent overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(COLOR_BLACK)
        self.screen.blit(overlay, (0, 0))
        
        # Win message
        win_text = self.font.render("PUZZLE COMPLETED!", True, COLOR_GREEN)
        text_rect = win_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(win_text, text_rect)
        
        # Show who solved it
        solver_info = self.network_manager.get_puzzle_solver()
        if solver_info:
            solver_text = f"Solved by: {solver_info['ip']}:{solver_info['port']}"
        else:
            solver_text = "Congratulations! You solved the puzzle!"
        
        sub_text = self.small_font.render(solver_text, True, COLOR_WHITE)
        sub_rect = sub_text.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 40))
        self.screen.blit(sub_text, sub_rect)