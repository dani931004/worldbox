"""
This file contains all the constants used in the game.
"""

# Map and UI layout
MAP_WIDTH, MAP_HEIGHT = 800, 600  # Increased map area for a bigger world
SIDEBAR_WIDTH = 250  # Wider sidebar for more stats
WIDTH, HEIGHT = MAP_WIDTH + SIDEBAR_WIDTH, MAP_HEIGHT
CELL_SIZE = 10  # Larger cells for better visibility
GRID_WIDTH = MAP_WIDTH // CELL_SIZE
GRID_HEIGHT = MAP_HEIGHT // CELL_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)  # Darker green for grass
BLUE = (0, 105, 148)  # Ocean blue
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
LIGHT_YELLOW = (255, 255, 224)  # Lighter yellow for children
BROWN = (139, 69, 19)
FOREST_GREEN = (34, 139, 34)
DESERT_TAN = (210, 180, 140)
VILLAGE_BROWN = (188, 143, 143)  # Rosy brown for villages
FARMLAND_GOLD = (218, 165, 32)  # Goldenrod for farmland

# Terrain types
TERRAIN_COLORS = {
    "grass": GREEN,
    "water": BLUE,
    "mountain": GRAY,
    "forest": FOREST_GREEN,
    "desert": DESERT_TAN,
    "village": VILLAGE_BROWN,
    "farmland": FARMLAND_GOLD,
}
TERRAIN_MAP = {
    0: "grass",
    1: "water",
    2: "mountain",
    3: "forest",
    4: "desert",
    5: "village",
    6: "farmland",
}
REVERSE_TERRAIN_MAP = {v: k for k, v in TERRAIN_MAP.items()}

# Evolution file
EVOLUTION_FILE = "evolution.json"

# Population control
MAX_POPULATION = 500  # Increased max population
