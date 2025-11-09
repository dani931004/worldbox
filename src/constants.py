"""
This file contains all the constants used in the game.
"""

# Map and UI layout
MAP_WIDTH, MAP_HEIGHT = 1920, 1440  # Doubled map size for bigger world
SIDEBAR_WIDTH = 250  # Wider sidebar for more stats
WIDTH, HEIGHT = MAP_WIDTH + SIDEBAR_WIDTH, MAP_HEIGHT
CELL_SIZE = 8  # Smaller cells for larger map
GRID_WIDTH = MAP_WIDTH // CELL_SIZE
GRID_HEIGHT = MAP_HEIGHT // CELL_SIZE

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 128, 0)  # Darker green for grass
BLUE = (0, 105, 148)  # Ocean blue
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
LIGHT_YELLOW = (255, 255, 224)  # Lighter yellow for children
BROWN = (139, 69, 19)
FOREST_GREEN = (34, 139, 34)
DESERT_TAN = (210, 180, 140)
VILLAGE_BROWN = (188, 143, 143)  # Rosy brown for villages
FARMLAND_GOLD = (218, 165, 32)  # Goldenrod for farmland
STONE_GRAY = (64, 64, 64)  # Dark gray for stone deposits
FISH_BLUE = (173, 216, 230)  # Light blue for fish
BERRY_RED = (220, 20, 60)  # Crimson for berries
ORANGE = (255, 165, 0)  # Orange for campfire
DARK_BROWN = (101, 67, 33)  # Dark brown for storage and shelter

# Tribe colors
TRIBE_COLORS = [YELLOW, RED, BLUE, GREEN, PURPLE]

# Terrain types
TERRAIN_COLORS = {
    "grass": GREEN,
    "water": BLUE,
    "mountain": GRAY,
    "forest": FOREST_GREEN,
    "desert": DESERT_TAN,
    "village": VILLAGE_BROWN,
    "farmland": FARMLAND_GOLD,
    "ore": (105, 105, 105),  # Dark gray for ore deposits
    "stone": STONE_GRAY,
    "fish": FISH_BLUE,
    "berries": BERRY_RED,
    "tree": GREEN,
}
TERRAIN_MAP = {
    0: "grass",
    1: "water",
    2: "mountain",
    3: "forest",
    4: "desert",
    5: "village",
    6: "farmland",
    7: "ore",
    8: "stone",
    9: "fish",
    10: "berries",
    11: "tree",
}
REVERSE_TERRAIN_MAP = {v: k for k, v in TERRAIN_MAP.items()}

# Evolution file
EVOLUTION_FILE = "evolution.json"

# Population control
MAX_POPULATION = 100  # Reduced for better performance

# Food types and energy
FOOD_TYPES = ["food", "berries", "fish", "meat"]
FOOD_ENERGY = {
    "food": 20,
    "berries": 15,
    "fish": 25,
    "meat": 30,
}
