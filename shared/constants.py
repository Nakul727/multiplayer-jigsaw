# Window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 800

# Colors
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_GREY = (200, 200, 200)
COLOR_BACKGROUND = (30, 30, 30)
COLOR_BOARD_BG = (50, 50, 50)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLUE = (0, 0, 255)
COLOR_YELLOW = (255, 255, 0)
COLOR_ORANGE = (255, 165, 0)

# Puzzle
DEFAULT_DIFFICULTY = 'easy'
DIFFICULTY_SETTINGS = {
    'easy': {
        'grid': (3, 3), 
        'pieces': 9,
        'target_image_size': 450,
        'target_piece_size': 150
    },
    'medium': {
        'grid': (4, 5), 
        'pieces': 20,
        'target_image_size': 500,
        'target_piece_size': 100
    },
    'hard': {
        'grid': (6, 8), 
        'pieces': 48,
        'target_image_size': 600,
        'target_piece_size': 75
    }
}