import io
import os 
import sys
import pygame
import requests
from PIL import Image

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'shared'))
from constants import DIFFICULTY_SETTINGS

class Puzzle:
    def __init__(self, image_url, difficulty='easy', resize_to=None):
        self.image_url = image_url
        self.difficulty = difficulty
        self.difficulty_settings = DIFFICULTY_SETTINGS[difficulty]
        
        self.grid_rows = self.difficulty_settings['grid'][1]
        self.grid_cols = self.difficulty_settings['grid'][0]

        self.original_size = (0, 0)
        self.resize_to = resize_to

        self.pieces = []
        self.piece_size = (0, 0)
        
        self._load_and_split_image()
        # self._display_puzzle_info()

    def _calculate_resize_dimensions(self, original_size):
        """
        Calculate appropriate resize dimensions for puzzle
        """
        # If explicit resize dimensions are provided, use them directly
        if self.resize_to:
            return self.resize_to

        # Extract original dimensions and calculate aspect ratio
        original_width = original_size[0]
        original_height = original_size[1]
        aspect_ratio = original_width / original_height

        # Use difficulty-specific target image size
        target_size = self.difficulty_settings['target_image_size']

        # Attempt to resize based on target size while maintaining aspect ratio
        if aspect_ratio > 1:
            resized_width = target_size
            resized_height = int(target_size / aspect_ratio)
        else:
            resized_height = target_size
            resized_width = int(target_size * aspect_ratio)
        
        resized_size = (resized_width, resized_height)
        return resized_size

    def _load_and_split_image(self):
        """
        Load image from URL and split it into puzzle pieces
        """
        if not self.image_url:
            print("Error: No image URL provided.")
            return

        try:
            # Download image from URL
            response = requests.get(self.image_url)
            response.raise_for_status() 

            # Open image with Pillow
            image_file = io.BytesIO(response.content)
            pil_image = Image.open(image_file)
            
            # Store original dimensions
            self.original_size = pil_image.size

            # Resize image to optimal puzzle size
            resize_dimensions = self._calculate_resize_dimensions(self.original_size)
            pil_image = pil_image.resize(resize_dimensions, Image.LANCZOS)

            # Calculate individual piece dimensions
            img_width, img_height = pil_image.size
            self.piece_size = (img_width // self.grid_cols, img_height // self.grid_rows)

            # Split image into puzzle pieces
            piece_id_counter = 0
            for row in range(self.grid_rows):
                for col in range(self.grid_cols):
                    # Calculate crop boundaries for this piece
                    left = col * self.piece_size[0]
                    top = row * self.piece_size[1]
                    right = left + self.piece_size[0]
                    bottom = top + self.piece_size[1]
                    
                    # Crop piece from main image
                    pil_piece = pil_image.crop((left, top, right, bottom))
                    
                    # Convert Pillow image to Pygame surface
                    mode = pil_piece.mode
                    size = pil_piece.size
                    data = pil_piece.tobytes()
                    pygame_piece = pygame.image.fromstring(data, size, mode)
                    
                    # Store piece with metadata
                    self.pieces.append({
                        'id': f'piece_{piece_id_counter}',
                        'image': pygame_piece,
                        'correct_row': row,
                        'correct_col': col,
                        'grid_position': (col, row),
                        'size': size
                    })
                    piece_id_counter += 1

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image: {e}")
        except Exception as e:
            print(f"Error processing image: {e}")

    def _display_puzzle_info(self):
        """
        Display puzzle creation summary
        """
        print(f"Image URL: {self.image_url}")
        print(f"Difficulty: {self.difficulty}")
        print(f"Puzzle created: {len(self.pieces)} pieces")
        print(f"Grid: {self.grid_cols}×{self.grid_rows}")
        print(f"Original size: {self.original_size}")
        print(f"Piece size: {self.piece_size}")

    # -------------------------------------------------------------------------

    def get_pieces(self):
        """
        Return list of all puzzle pieces
        """
        return self.pieces

    def get_piece_by_id(self, piece_id):
        """
        Get a specific piece by its ID
        """
        for piece in self.pieces:
            if piece['id'] == piece_id:
                return piece
        return None

    def get_piece_size(self):
        """
        Return the size of each piece as (width, height)
        """
        return self.piece_size
    
    def get_grid_dimensions(self):
        """
        Return grid dimensions as (cols, rows)
        """
        return (self.grid_cols, self.grid_rows)