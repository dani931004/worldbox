"""
This file contains the World class, which manages the game world.
"""
import random
import pygame
from src.constants import (
    GRID_WIDTH,
    GRID_HEIGHT,
    TERRAIN_MAP,
    MAX_POPULATION,
    REVERSE_TERRAIN_MAP,
    TRIBE_COLORS,
    MAP_WIDTH,
    MAP_HEIGHT,
    CELL_SIZE,
    TERRAIN_COLORS,
)
from src.entity import Tree, Human, Child, Animal, House


class World:
    """Manages the game world, including terrain, food, and entities."""

    def __init__(self):
        self.entities = []
        self.terrain = self._generate_terrain()
        self.food = [
            [100 if self.get_terrain_type(x, y) not in ["water", "mountain", "ore", "stone"] else 0 for x in range(GRID_WIDTH)]
            for y in range(GRID_HEIGHT)
        ]
        self.max_population = MAX_POPULATION
        self.tick = 0
        self.spatial_grid = [[[] for _ in range(GRID_WIDTH // 5)] for _ in range(GRID_HEIGHT // 5)]
        self.ground_items = [[{} for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.tribe_relations = {}  # dict of dicts: relations[tribe1][tribe2] = 'neutral'|'allied'|'hostile'
        self.next_tribe_id = 0
        self.terrain_surface = pygame.Surface((MAP_WIDTH, MAP_HEIGHT))
        self._build_terrain_surface()
        self.chopped_trees = []  # list of (x, y, timer)
        self.total_births = 0
        self.total_deaths = 0
        self.interval_energy_sum = 0
        self.ticks_in_interval = 0
        self.births_last_snapshot = 0
        self.deaths_last_snapshot = 0

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
        # Ore deposits
        for _ in range(random.randint(5, 10)):
            ox, oy = random.randint(0, GRID_WIDTH - 1), random.randint(
                0, GRID_HEIGHT - 1
            )
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = ox + dx, oy + dy
                    if (
                        0 <= nx < GRID_WIDTH
                        and 0 <= ny < GRID_HEIGHT
                        and terrain[ny][nx] == 0
                        and random.random() < 0.5
                    ):
                        terrain[ny][nx] = REVERSE_TERRAIN_MAP["ore"]
        # Stone deposits
        for _ in range(random.randint(5, 10)):
            sx, sy = random.randint(0, GRID_WIDTH - 1), random.randint(
                0, GRID_HEIGHT - 1
            )
            for dy in range(-3, 4):
                for dx in range(-3, 4):
                    nx, ny = sx + dx, sy + dy
                    if (
                        0 <= nx < GRID_WIDTH
                        and 0 <= ny < GRID_HEIGHT
                        and terrain[ny][nx] == 0
                        and random.random() < 0.5
                    ):
                        terrain[ny][nx] = REVERSE_TERRAIN_MAP["stone"]
        # Fish in water bodies
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if terrain[y][x] == REVERSE_TERRAIN_MAP["water"] and random.random() < 0.1:
                    terrain[y][x] = REVERSE_TERRAIN_MAP["fish"]
        # Berries in forests
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if terrain[y][x] == REVERSE_TERRAIN_MAP["forest"] and random.random() < 0.15:
                    terrain[y][x] = REVERSE_TERRAIN_MAP["berries"]
        # Trees on land
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if terrain[y][x] in [0, 3] and random.random() < 0.07:  # 7% of grass and forest to tree
                    terrain[y][x] = REVERSE_TERRAIN_MAP["tree"]
        return terrain

    def _variant_color(self, base: tuple[int, int, int], x: int, y: int) -> tuple[int, int, int]:
        """Apply subtle deterministic color variation to a base color."""
        hash_val = (x ^ y) % 21 - 10  # Delta in [-10, 10]
        terrain_type = self.get_terrain_type(x, y)
        if terrain_type == "water":
            hash_val = max(-5, min(5, hash_val))  # Limit to [-5, 5] for water
        r, g, b = base
        r = max(0, min(255, r + hash_val))
        g = max(0, min(255, g + hash_val))
        b = max(0, min(255, b + hash_val))
        return (r, g, b)

    def _build_terrain_surface(self) -> None:
        """Build the pre-rendered terrain surface."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain_type = self.get_terrain_type(x, y)
                base_color = TERRAIN_COLORS[terrain_type]
                color = self._variant_color(base_color, x, y)
                pygame.draw.rect(
                    self.terrain_surface, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )

    def add_entity(self, entity):
        """Add an entity to the world."""
        self.entities.append(entity)
        gx = entity.x // 5
        gy = entity.y // 5
        if 0 <= gx < len(self.spatial_grid[0]) and 0 <= gy < len(self.spatial_grid):
            self.spatial_grid[gy][gx].append(entity)

    def _update_spatial_grid_position(self, entity, old_x, old_y):
        """Update the spatial grid position of an entity."""
        # Remove from old grid cell
        old_gx = old_x // 5
        old_gy = old_y // 5
        if 0 <= old_gx < len(self.spatial_grid[0]) and 0 <= old_gy < len(self.spatial_grid):
            if entity in self.spatial_grid[old_gy][old_gx]:
                self.spatial_grid[old_gy][old_gx].remove(entity)
        # Add to new grid cell
        new_gx = entity.x // 5
        new_gy = entity.y // 5
        if 0 <= new_gx < len(self.spatial_grid[0]) and 0 <= new_gy < len(self.spatial_grid):
            self.spatial_grid[new_gy][new_gx].append(entity)

    def _remove_from_grid(self, entity):
        """Remove an entity from the spatial grid."""
        gx = entity.x // 5
        gy = entity.y // 5
        if 0 <= gx < len(self.spatial_grid[0]) and 0 <= gy < len(self.spatial_grid):
            if entity in self.spatial_grid[gy][gx]:
                self.spatial_grid[gy][gx].remove(entity)

    def get_entities_in_radius(self, x, y, radius):
        """Get entities within a given radius of a point."""
        entities = []
        min_gx = max(0, (x - radius) // 5)
        max_gx = min(len(self.spatial_grid[0]) - 1, (x + radius) // 5)
        min_gy = max(0, (y - radius) // 5)
        max_gy = min(len(self.spatial_grid) - 1, (y + radius) // 5)
        for gy in range(min_gy, max_gy + 1):
            for gx in range(min_gx, max_gx + 1):
                for entity in self.spatial_grid[gy][gx]:
                    if abs(entity.x - x) <= radius and abs(entity.y - y) <= radius:
                        entities.append(entity)
        return entities

    def update(self):
        """Update the world state."""
        # Death counting excluding transformed
        deaths_this_interval = 0
        updated_entities = []
        for e in self.entities:
            alive = e.update()
            if alive and not e.is_dead:
                updated_entities.append(e)
            else:
                # remove from grid
                self._remove_from_grid(e)
                if not alive or e.is_dead:
                    if not hasattr(e, 'transformed') or not e.transformed:
                        self.total_deaths += 1
                        deaths_this_interval += 1
        self.entities = updated_entities
        self.tick += 1
        # Energy accumulation
        total_energy = sum(e.energy for e in self.entities if isinstance(e, (Human, Child)))
        self.interval_energy_sum += total_energy
        self.ticks_in_interval += 1
        if self.tick % 100 == 0:
            human_count = sum(1 for e in self.entities if isinstance(e, Human))
            child_count = sum(1 for e in self.entities if isinstance(e, Child))
            pop_count = human_count + child_count
            avg_energy_per_entity = 0
            if self.ticks_in_interval > 0 and pop_count > 0:
                avg_energy_per_entity = self.interval_energy_sum / (self.ticks_in_interval * pop_count)
            births_interval = self.total_births - self.births_last_snapshot
            deaths_interval = self.total_deaths - self.deaths_last_snapshot
            print(f"Tick {self.tick}: Pop {pop_count} (H:{human_count} C:{child_count}) AvgE/entity {avg_energy_per_entity:.2f} | Births {self.total_births} (+{births_interval}) Deaths {self.total_deaths} (+{deaths_interval})")
            self.births_last_snapshot = self.total_births
            self.deaths_last_snapshot = self.total_deaths
            self.interval_energy_sum = 0
            self.ticks_in_interval = 0
        # Cache entity counts
        self.population_count = len([e for e in self.entities if isinstance(e, (Human, Child))])
        self.animal_count = len([e for e in self.entities if isinstance(e, Animal)])
        self.house_count = len([e for e in self.entities if isinstance(e, House)])
        self.tree_count = len([e for e in self.entities if isinstance(e, Tree)])
        self._regrow_food()
        self._respawn_trees()

    def _regrow_food(self):
        """Regrow food in the world."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain_type = self.get_terrain_type(x, y)
                if terrain_type not in ["water", "mountain", "ore", "stone"] and random.random() < 0.8:  # Increased regrowth rate
                    max_food = (
                        100  # Increased max food
                        if terrain_type in ["village", "farmland"]
                        else 80
                    )
                    regrow_amount = 6 if terrain_type in ["village", "farmland"] else 8  # POPULATION QUICK WIN TWEAK: Increased regrow_amount by ~40% (from 4/6 to 6/8) for better food availability
                    self.food[y][x] = min(max_food, self.food[y][x] + regrow_amount)

    def _respawn_trees(self):
        """Respawn chopped trees at random locations."""
        i = 0
        while i < len(self.chopped_trees):
            x, y, timer = self.chopped_trees[i]
            timer -= 1
            if timer <= 0:
                # Find random valid location
                for _ in range(100):
                    nx = random.randint(0, GRID_WIDTH - 1)
                    ny = random.randint(0, GRID_HEIGHT - 1)
                    if self.get_terrain_type(nx, ny) in ["grass", "forest"] and not self.get_entities_in_radius(nx, ny, 0):
                        self.set_terrain(nx, ny, REVERSE_TERRAIN_MAP["tree"])
                        break
                self.chopped_trees.pop(i)
                continue
            else:
                self.chopped_trees[i] = (x, y, timer)
            i += 1



    def get_terrain_type(self, x, y):
        """Get the terrain type at a given coordinate."""
        return TERRAIN_MAP[self.terrain[y][x]]

    def form_tribe(self, human):
        """Form a new tribe for the human."""
        tribe_id = self.next_tribe_id
        self.next_tribe_id += 1
        human.tribe = tribe_id
        human.color = TRIBE_COLORS[tribe_id % len(TRIBE_COLORS)]
        # Initialize relations with existing tribes
        for other_tribe in list(self.tribe_relations):
            if other_tribe != tribe_id:
                if other_tribe not in self.tribe_relations:
                    self.tribe_relations[other_tribe] = {}
                self.tribe_relations[other_tribe][tribe_id] = 'neutral'
                if tribe_id not in self.tribe_relations:
                    self.tribe_relations[tribe_id] = {}
                self.tribe_relations[tribe_id][other_tribe] = 'neutral'
        return tribe_id

    def get_tribe_relation(self, tribe1, tribe2):
        """Get the relation between two tribes."""
        if tribe1 is None or tribe2 is None or tribe1 == tribe2:
            return 'allied'  # Same tribe or no tribe
        if tribe1 in self.tribe_relations and tribe2 in self.tribe_relations[tribe1]:
            return self.tribe_relations[tribe1][tribe2]
        return 'neutral'

    def update_tribe_relation(self, tribe1, tribe2, action):
        """Update relation based on action: 'steal', 'help', etc."""
        if tribe1 is None or tribe2 is None or tribe1 == tribe2:
            return
        if tribe1 not in self.tribe_relations:
            self.tribe_relations[tribe1] = {}
        if tribe2 not in self.tribe_relations[tribe1]:
            self.tribe_relations[tribe1][tribe2] = 'neutral'
        if tribe2 not in self.tribe_relations:
            self.tribe_relations[tribe2] = {}
        if tribe1 not in self.tribe_relations[tribe2]:
            self.tribe_relations[tribe2][tribe1] = 'neutral'
        
        current = self.tribe_relations[tribe1][tribe2]
        if action == 'steal':
            if current == 'neutral':
                self.tribe_relations[tribe1][tribe2] = 'hostile'
                self.tribe_relations[tribe2][tribe1] = 'hostile'
            elif current == 'allied':
                self.tribe_relations[tribe1][tribe2] = 'hostile'
                self.tribe_relations[tribe2][tribe1] = 'hostile'
        elif action == 'help':
            if current == 'neutral':
                self.tribe_relations[tribe1][tribe2] = 'allied'
                self.tribe_relations[tribe2][tribe1] = 'allied'
        # Add more actions as needed

    def set_terrain(self, x, y, terrain_id):
        """Set the terrain type at a given coordinate."""
        if 0 <= x < GRID_WIDTH and 0 <= y < GRID_HEIGHT:
            self.terrain[y][x] = terrain_id
            # Update terrain surface
            terrain_type = TERRAIN_MAP[terrain_id]
            base_color = TERRAIN_COLORS[terrain_type]
            color = self._variant_color(base_color, x, y)
            pygame.draw.rect(
                self.terrain_surface, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            )
