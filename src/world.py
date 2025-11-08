"""
This file contains the World class, which manages the game world.
"""
import random
from src.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    TERRAIN_MAP,
    MAX_POPULATION,
    REVERSE_TERRAIN_MAP,
)
from src.entity import Tree


class World:
    """Manages the game world, including terrain, food, and entities."""

    def __init__(self):
        self.entities = []
        self.terrain = self._generate_terrain()
        self.food = [
            [100 if self.get_terrain_type(x, y) not in ["water", "mountain"] else 0 for x in range(GRID_WIDTH)]
            for y in range(GRID_HEIGHT)
        ]
        self.max_population = MAX_POPULATION
        self._add_initial_trees()

    def _generate_terrain(self):
        """Generate the initial terrain for the world."""
        terrain = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        # Water bands
        for _ in range(random.randint(2, 4)):
            wx = random.randint(10, GRID_WIDTH - 10)
            for y in range(GRID_HEIGHT):
                spread = random.randint(1, 3)
                for dx in range(-spread, spread + 1):
                    nx = wx + dx + int(3 * random.uniform(-1, 1))
                    if 0 <= nx < GRID_WIDTH:
                        terrain[y][nx] = REVERSE_TERRAIN_MAP["water"]
        # Mountain ranges
        for _ in range(random.randint(2, 4)):
            mx = random.randint(10, GRID_WIDTH - 10)
            for y in range(GRID_HEIGHT):
                spread = random.randint(1, 2)
                for dx in range(-spread, spread + 1):
                    nx = mx + dx + int(2 * random.uniform(-1, 1))
                    if 0 <= nx < GRID_WIDTH and terrain[y][nx] == 0:
                        terrain[y][nx] = REVERSE_TERRAIN_MAP["mountain"]
        # Forest patches
        for _ in range(random.randint(10, 20)):
            fx, fy = random.randint(0, GRID_WIDTH - 1), random.randint(
                0, GRID_HEIGHT - 1
            )
            for dy in range(-4, 5):
                for dx in range(-4, 5):
                    nx, ny = fx + dx, fy + dy
                    if (
                        0 <= nx < GRID_WIDTH
                        and 0 <= ny < GRID_HEIGHT
                        and terrain[ny][nx] == 0
                        and random.random() < 0.6
                    ):
                        terrain[ny][nx] = REVERSE_TERRAIN_MAP["forest"]
        # Desert patches
        for _ in range(random.randint(4, 8)):
            dx, dy = random.randint(0, GRID_WIDTH - 1), random.randint(
                0, GRID_HEIGHT - 1
            )
            for y in range(dy, min(dy + 8, GRID_HEIGHT)):
                for x in range(dx, min(dx + 8, GRID_WIDTH)):
                    if terrain[y][x] == 0 and random.random() < 0.8:
                        terrain[y][x] = REVERSE_TERRAIN_MAP["desert"]
        return terrain

    def _add_initial_trees(self):
        """Add initial trees to the world."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if self.get_terrain_type(x, y) == "forest" and random.random() < 0.2:
                    self.add_entity(Tree(x, y, self))
                elif self.get_terrain_type(x, y) == "grass" and random.random() < 0.03:
                    self.add_entity(Tree(x, y, self))

    def add_entity(self, entity):
        """Add an entity to the world."""
        self.entities.append(entity)

    def update(self):
        """Update the world state."""
        self.entities = [e for e in self.entities if e.update()]
        self._regrow_food()

    def _regrow_food(self):
        """Regrow food in the world."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain_type = self.get_terrain_type(x, y)
                if terrain_type not in ["water", "mountain"] and random.random() < 0.5:  # Increased regrowth rate
                    max_food = (
                        100  # Increased max food
                        if terrain_type in ["village", "farmland"]
                        else 80
                    )
                    regrow_amount = 3 if terrain_type in ["village", "farmland"] else 2
                    self.food[y][x] = min(max_food, self.food[y][x] + regrow_amount)

    def get_terrain_type(self, x, y):
        """Get the terrain type at a given coordinate."""
        return TERRAIN_MAP[self.terrain[y][x]]

    def set_terrain(self, x, y, terrain_id):
        """Set the terrain type at a given coordinate."""
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            self.terrain[y][x] = terrain_id
