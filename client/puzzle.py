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
    def __init__(self, image_url, grid_size=3):
        
        # stash the img url and grid size
        self.image_url = image_url
        self.grid_size = grid_size
        self.pieces = [] # All the smaller puzzle piece go in here MT array
        self.piece_size = (0, 0)
        
        # get the image and split it into piecess
        self._load_and_split_image()

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

            # calculate the piecees dimension 🤓👆➕➖✖➗ (idk if we should scale it down)
            # Resize image to 500x500 for all image 
            desired_board_size = 500
            pil_image = pil_image.resize((desired_board_size, desired_board_size), Image.LANCZOS)

            # Calculate the piece dimensions
            img_width, img_height = pil_image.size  # should be 500, 500
            self.piece_size = (img_width // self.grid_size, img_height // self.grid_size)
            
            print(f"Image size: {pil_image.size}, Piece size: {self.piece_size}")

            # Crop the image into pieces 
            piece_id_counter = 0
            for row in range(self.grid_size):
                for col in range(self.grid_size):
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
                    
                    # Store piece with its ID 
                    self.pieces.append({
                        'id': f'piece_{piece_id_counter}',
                        'image': pygame_piece
                    })
                    piece_id_counter += 1
            
            print(f"Successfully split image into {len(self.pieces)} pieces with unique IDs.")

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image: {e}")
        except Exception as e:
            print(f"An error occurred while processing the image: {e}")

    def get_pieces(self):
        return self.pieces
