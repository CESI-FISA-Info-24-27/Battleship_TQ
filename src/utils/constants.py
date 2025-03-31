# Screen settings
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TITLE = "Bataille Navale"
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
BLUE = (30, 100, 200)
LIGHT_BLUE = (120, 180, 250)
DARK_BLUE = (10, 40, 80)
RED = (220, 50, 50)
GREEN = (50, 200, 50)
YELLOW = (240, 200, 30)
ORANGE = (240, 150, 30)

# Button colors
BUTTON_HOVER_COLOR = (60, 140, 240)
BUTTON_DISABLED_COLOR = (100, 100, 100)

# Game settings
GRID_SIZE = 10  # 10x10 grid for the game board
CELL_SIZE = 40  # Size of each cell in pixels
BOARD_MARGIN = 50  # Margin around the board

# Responsive settings
SMALL_SCREEN_WIDTH = 640
SMALL_SCREEN_HEIGHT = 480

# Ship settings
SHIPS = [
    {"name": "Porte-avion", "size": 5},
    {"name": "Croiseur", "size": 4},
    {"name": "Contre-torpilleur", "size": 3},
    {"name": "Sous-marin", "size": 3},
    {"name": "Torpilleur", "size": 2}
]

# Network settings
DEFAULT_PORT = 5555
DEFAULT_HOST = "localhost"

# Game states
PLACING_SHIPS = "placing_ships"
WAITING_FOR_OPPONENT = "waiting_for_opponent"
YOUR_TURN = "your_turn"
OPPONENT_TURN = "opponent_turn"
GAME_OVER = "game_over"

# Animation speeds
ANIMATION_SPEED = 0.05