import pygame
import requests
import io
from PIL import Image

class Puzzle:
    """
    Manages the puzzle state, get the image, including fetching the image,
    splitting it into pieces with unique IDs, and tracking their properties.
    """
    # Init
    def __init__(self, image_url, resize_to=None):
        
        # stash the img url and grid size (always 3x3)
        self.image_url = image_url
        self.resize_to = resize_to
        self.grid_cols = 3  # Fixed to 3x3
        self.grid_rows = 3  # Fixed to 3x3
        self.pieces = [] # All the smaller puzzle piece go in here MT array
        self.piece_size = (0, 0)
        self.original_size = (0, 0)
        
        print(f"Creating 3x3 puzzle: {self.grid_cols}x{self.grid_rows} = {self.grid_cols * self.grid_rows} pieces")
        
        # get the image and split it into piecess
        self._load_and_split_image()

    def _calculate_resize_dimensions(self, original_width, original_height):
        """Calculate appropriate resize dimensions for 3x3 puzzle"""
        if self.resize_to:
            return self.resize_to
        
        # Fixed base size for 3x3 puzzle (150px per piece)
        base_size = 450
        aspect_ratio = original_width / original_height
        
        if aspect_ratio > 1:  # Wider than tall
            width = base_size
            height = int(base_size / aspect_ratio)
        else:  # Taller than wide
            height = base_size
            width = int(base_size * aspect_ratio)
        
        return (width, height)

    # load the img and split them, giving them unique id
    def _load_and_split_image(self):
        if not self.image_url:
            print("Error: NO Image URL provided.")
            return

        try:
            # getting the image
            print(f"Loading image from: {self.image_url}")
            response = requests.get(self.image_url)
            response.raise_for_status() 

            #  ppen the image with Pillow
            image_file = io.BytesIO(response.content)
            pil_image = Image.open(image_file)
            
            # Store original size
            self.original_size = pil_image.size
            print(f"Original image size: {self.original_size}")

            # calculate the piecees dimension 🤓👆➕➖✖➗ (idk if we should scale it down)
            # Calculate and apply resize dimensions
            resize_dimensions = self._calculate_resize_dimensions(
                self.original_size[0], self.original_size[1]
            )
            pil_image = pil_image.resize(resize_dimensions, Image.LANCZOS)
            print(f"Resized image to: {resize_dimensions}")

            # Calculate the piece dimensions
            img_width, img_height = pil_image.size
            self.piece_size = (img_width // self.grid_cols, img_height // self.grid_rows)
            
            print(f"Image size: {pil_image.size}, Piece size: {self.piece_size}")

            # Crop the image into pieces (always 3x3 = 9 pieces)
            piece_id_counter = 0
            for row in range(self.grid_rows):
                for col in range(self.grid_cols):
                    left   = col  * self.piece_size [0]
                    top    = row  * self.piece_size [1]
                    right  = left + self.piece_size [0]
                    bottom = top  + self.piece_size [1]
                    
                    pil_piece = pil_image.crop((left, top, right, bottom))
                    
                    # Convert Pillow image to Pygame
                    mode = pil_piece.mode
                    size = pil_piece.size
                    data = pil_piece.tobytes()
                    pygame_piece = pygame.image.fromstring(data, size, mode)
                    
                    # Store piece with its ID and metadata
                    self.pieces.append({
                        'id': f'piece_{piece_id_counter}',
                        'image': pygame_piece,
                        'correct_row': row,
                        'correct_col': col,
                        'grid_position': (col, row),
                        'size': size
                    })
                    piece_id_counter += 1
            
            print(f"Successfully split image into {len(self.pieces)} pieces with unique IDs.")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image: {e}")
        except Exception as e:
            print(f"An error occurred while processing the image: {e}")

    def get_pieces(self):
        """Return list of all puzzle pieces"""
        return self.pieces

    def get_piece_by_id(self, piece_id):
        """Get a specific piece by its ID"""
        for piece in self.pieces:
            if piece['id'] == piece_id:
                return piece
        return None

    def get_grid_dimensions(self):
        """Return grid dimensions as (cols, rows) - always (3, 3)"""
        return (self.grid_cols, self.grid_rows)

    def get_piece_size(self):
        """Return the size of each piece as (width, height)"""
        return self.piece_size