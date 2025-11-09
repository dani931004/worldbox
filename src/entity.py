INTELLIGENCE_CAP = 100.0
"""
This file contains the entity classes for the game.
"""
import random
import pygame
from src.constants import (
    CELL_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    YELLOW,
    LIGHT_YELLOW,
    BROWN,
    FOREST_GREEN,
    GRAY,
    GREEN,
    MAX_POPULATION,
    REVERSE_TERRAIN_MAP,
    FOOD_TYPES,
    FOOD_ENERGY,
    ORANGE,
    DARK_BROWN,
    TRIBE_COLORS,
)


class Entity:
    """Base class for all entities in the game."""

    def __init__(self, x, y, world):
        self.x = x
        self.y = y
        self.world = world
        self.age = 0
        self.energy = 250
        self.is_dead = False

    def update(self):
        """Update the entity's state."""
        self.age += 1
        self.energy -= 0.1  # Reduced energy consumption per tick
        if self.energy <= 0:
            self.is_dead = True
        return self.energy > 0

    def draw(self, screen, camera=None):
        """Draw the entity on the screen."""
        pass

    def _move(self):
        """Move the entity. Subclasses should override."""
        pass


class Animal(Entity):
    """Represents an animal in the game."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = GREEN

    def update(self):
        """Update the animal's state."""
        if not super().update():
            return False
        # Random movement, avoid water and mountains
        dx = random.choice([-1, 0, 1])
        dy = random.choice([-1, 0, 1])
        nx, ny = self.x + dx, self.y + dy
        if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
            terrain_type = self.world.get_terrain_type(nx, ny)
            if terrain_type not in ["water", "mountain"]:
                self.x, self.y = nx, ny
        # Eat on fertile land
        terrain_type = self.world.get_terrain_type(self.x, self.y)
        if (
            terrain_type in ["grass", "forest", "desert", "village", "farmland", "berries"]
            and self.world.food[self.y][self.x] > 0
        ):
            self.energy = min(100, self.energy + 7)
            self.world.food[self.y][self.x] -= 1
        return True

    def draw(self, screen, camera=None):
        """Draw the animal on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + CELL_SIZE // 2
            wy = self.y * CELL_SIZE + CELL_SIZE // 2
            sx, sy = camera.world_to_screen(wx, wy)
            radius = max(1, int((CELL_SIZE // 2 - 2) * camera.zoom))
            pygame.draw.circle(screen, self.color, (sx, sy), radius)
        else:
            pygame.draw.circle(
                screen,
                self.color,
                (
                    self.x * CELL_SIZE + CELL_SIZE // 2,
                    self.y * CELL_SIZE + CELL_SIZE // 2,
                ),
                CELL_SIZE // 2 - 2,
            )


class Human(Entity):
    def __init__(self, x, y, world, speed=1.0, intelligence=0.0, strength=1.0, wisdom=0.0, foraging=1.0, behaviors=None, tribe=None):
        super().__init__(x, y, world)
        self.tribe = tribe
        self.color = TRIBE_COLORS[self.tribe % len(TRIBE_COLORS)] if self.tribe is not None else YELLOW
        self.speed = speed
        self.intelligence = intelligence
        self.strength = strength
        self.wisdom = wisdom
        self.foraging = foraging
        self.knowledge = set()
        self.inventory = {"wood": 0, "food": 0, "ore": 0, "stone": 0, "fish": 0, "berries": 0, "meat": 0}
        # Give starting humans basic tools to help them survive
        self.tools = {"axe", "hoe"}
        # Dynamic behaviors: set of behavior names (strings)
        if behaviors is None:
            self.behaviors = set(["farm", "cooperate", "explore"])
        else:
            self.behaviors = set(behaviors)
        self.energy = 400  # POPULATION QUICK WIN TWEAK: Increased starting energy from 300 to 400
        #print(f"New Human created at ({x},{y}) with energy {self.energy} and traits: speed={self.speed}, intelligence={self.intelligence}, strength={self.strength}, wisdom={self.wisdom}, foraging={self.foraging}")

    def update(self):
        """Update the human's state."""
        if not super().update():
            return False
        # Learn from survival (each update = survived another tick)
        self._learn_from_experience(survived=True)
        self._evolve_behaviors()
        self._move()
        self._perform_actions()
        self._try_reproduce()
        # Chance to invent a new behavior
        self._maybe_invent_behavior()
        # Cultural learning: copy behaviors from nearby humans
        self._cultural_learning()
        return True

    def _maybe_invent_behavior(self):
        """Chance to invent a new behavior based on intelligence/wisdom."""
        # Only invent if intelligence and wisdom are high enough
        base_rate = 0.01
        invent_rate = base_rate * (1 + self.intelligence) * (1 + self.wisdom)
        if self.intelligence > 1.5 and self.wisdom > 1.0 and random.random() < min(0.02, invent_rate):
            possible_behaviors = ["cooperate", "share_food", "gather", "mine", "fish", "forage", "hunt", "drop_items", "pick_up", "group_hunt", "store_items", "build_storage", "build_campfire", "build_shelter", "trade", "farm_advanced", "craft_tools", "explore", "alliance", "chop_tree", "build_house", "build_village"]
            options = [b for b in possible_behaviors if b not in self.behaviors]
            if options:
                new_behavior = random.choice(options)
                self.behaviors.add(new_behavior)
            # Optionally: print or log invention
            # print(f"Human at ({self.x},{self.y}) invented {new_behavior}")

    def _cultural_learning(self):
        """Learn behaviors from nearby humans with probability scaling by intelligence/wisdom."""
        learn_rate = 0.01 * (1 + 0.5 * self.intelligence + 0.5 * self.wisdom)
        if random.random() > min(0.25, learn_rate):
            return
        # Look for neighbors within 1 tile using spatial grid
        nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
        neighbors = [
            e for e in nearby
            if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1
        ]
        if not neighbors:
            return
        teacher = random.choice(neighbors)
        teachable = list(teacher.behaviors - self.behaviors)
        if teachable:
            self.behaviors.add(random.choice(teachable))

    def _try_reproduce(self):
        """Attempt to reproduce with a nearby human if conditions are met."""
        # Only adults can reproduce, and not too old
        if self.age < 5 or self.age > 350:  # POPULATION QUICK WIN TWEAK: Extended max reproductive age from 200 to 350
            return
        # Limit population
        human_count = sum(isinstance(e, (Human, Child)) for e in self.world.entities)
        if human_count >= MAX_POPULATION:
            return
        # Find a mate nearby (distance 1)
        nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
        for entity in nearby:
            if (
                entity is not self
                and isinstance(entity, Human)
                and abs(entity.x - self.x) <= 1
                and abs(entity.y - self.y) <= 1
                and entity.age >= 5
                and entity.age <= 350 # POPULATION QUICK WIN TWEAK
            ):
                if self.energy > 120 and entity.energy > 120 and random.random() < 0.95:
                    #print(f"Reproducing: {self} and {entity} at ({self.x},{self.y})")
                    self.energy -= 9 # POPULATION QUICK WIN TWEAK
                    entity.energy -= 9 # POPULATION QUICK WIN TWEAK
                    # Child traits: average + small mutation
                    def mutate(val):
                        return max(0.1, min(INTELLIGENCE_CAP, val + random.uniform(-0.05, 0.05)))
                    child_speed = mutate((self.speed + entity.speed) / 2)
                    child_intelligence = mutate((self.intelligence + entity.intelligence) / 2)
                    child_strength = mutate((self.strength + entity.strength) / 2)
                    child_wisdom = mutate((self.wisdom + entity.wisdom) / 2)
                    child_foraging = mutate((self.foraging + entity.foraging) / 2)
                    # Inherit and mutate behaviors
                    parent_behaviors = list(self.behaviors | entity.behaviors)
                    # Small chance to add or remove a behavior
                    if random.random() < 0.1:
                        # Add a new random behavior
                        possible_behaviors = ["cooperate", "share_food", "gather", "mine", "fish", "forage", "hunt", "drop_items", "pick_up", "group_hunt", "store_items", "build_storage", "build_campfire", "build_shelter", "form_tribe", "raid", "defend", "trade", "farm_advanced", "craft_tools", "explore", "alliance", "chop_tree", "build_house", "build_village"]
                        new_behavior_candidates = [b for b in possible_behaviors if b not in parent_behaviors]
                        if new_behavior_candidates:
                            new_behavior = random.choice(new_behavior_candidates)
                            parent_behaviors.append(new_behavior)
                    if len(parent_behaviors) > 1 and random.random() < 0.05:
                        parent_behaviors.pop(random.randrange(len(parent_behaviors)))
                    # Place child at random adjacent tile
                    offsets = [(-1,0),(1,0),(0,-1),(0,1),(0,0)]
                    random.shuffle(offsets)
                    for dx, dy in offsets:
                        cx, cy = self.x + dx, self.y + dy
                        if 0 <= cx < GRID_WIDTH and 0 <= cy < GRID_HEIGHT:
                            # Only spawn if tile is not water or mountain and not occupied
                            terrain = self.world.get_terrain_type(cx, cy)
                            if terrain not in ["water", "mountain"] and not any(e.x == cx and e.y == cy for e in self.world.entities):
                                child = Child(
                                    cx, cy, self.world,
                                    child_speed, child_intelligence, child_strength, child_wisdom, child_foraging,
                                    behaviors=parent_behaviors, tribe=self.tribe
                                )
                                self.world.add_entity(child)
                                self.world.total_births += 1
                                break
                    break

    def draw(self, screen, camera=None):
        """Draw the human on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + CELL_SIZE // 2
            wy = self.y * CELL_SIZE + CELL_SIZE // 2
            sx, sy = camera.world_to_screen(wx, wy)
            scale = camera.zoom
            # Head
            pygame.draw.circle(screen, self.color, (sx, sy - int(3 * scale)), max(1, int(2 * scale)))
            # Body
            pygame.draw.line(
                screen, self.color, (sx, sy - int(1 * scale)), (sx, sy + int(3 * scale)), max(1, int(1 * scale))
            )
            # Arms
            pygame.draw.line(
                screen, self.color, (sx - int(2 * scale), sy), (sx + int(2 * scale), sy), max(1, int(1 * scale))
            )
            # Legs
            pygame.draw.line(
                screen,
                self.color,
                (sx, sy + int(3 * scale)),
                (sx - int(1 * scale), sy + int(5 * scale)),
                max(1, int(1 * scale)),
            )
            pygame.draw.line(
                screen,
                self.color,
                (sx, sy + int(3 * scale)),
                (sx + int(1 * scale), sy + int(5 * scale)),
                max(1, int(1 * scale)),
            )
        else:
            center_x = self.x * CELL_SIZE + CELL_SIZE // 2
            center_y = self.y * CELL_SIZE + CELL_SIZE // 2
            # Head
            pygame.draw.circle(screen, self.color, (center_x, center_y - 3), 2)
            # Body
            pygame.draw.line(
                screen, self.color, (center_x, center_y - 1), (center_x, center_y + 3), 1
            )
            # Arms
            pygame.draw.line(
                screen, self.color, (center_x - 2, center_y), (center_x + 2, center_y), 1
            )
            # Legs
            pygame.draw.line(
                screen,
                self.color,
                (center_x, center_y + 3),
                (center_x - 1, center_y + 5),
                1,
            )
            pygame.draw.line(
                screen,
                self.color,
                (center_x, center_y + 3),
                (center_x + 1, center_y + 5),
                1,
            )

    def _move(self):
        """Move the human, always seeking food when energy is low."""
        move_range = max(1, int(self.speed * (2 if "explore" in self.behaviors else 1)))
        possible_moves = []
        weights = []
        for dx in range(-move_range, move_range + 1):
            for dy in range(-move_range, move_range + 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = self.x + dx, self.y + dy
                if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                    terrain_type = self.world.get_terrain_type(nx, ny)
                    if "avoid_water" in self.knowledge and terrain_type == "water":
                        continue
                    weight = 1
                    if "explore" not in self.behaviors:
                        # Always seek food when energy is low, regardless of intelligence
                        if self.energy < 120:  # Adjusted threshold for seeking food when energy is low
                            if terrain_type in [
                                "grass",
                                "forest",
                                "desert",
                                "village",
                                "farmland",
                            ]:
                                weight = 2
                            elif terrain_type == "water":
                                weight = 0.5
                        if self.world.food[ny][nx] > 0 and self.energy < 160:  # Adjusted threshold for prioritizing food tiles
                            weight *= 2
                    possible_moves.append((nx, ny))
                    weights.append(weight)
        # Check for high resources to settle
        high_resource = False
        nearby_food = sum(self.world.food[y][x] for dx in (-1,0,1) for dy in (-1,0,1) if 0 <= (x := self.x + dx) < GRID_WIDTH and 0 <= (y := self.y + dy) < GRID_HEIGHT)
        if nearby_food > 100:
            high_resource = True
        nearby_trees = sum(1 for dx in (-1,0,1) for dy in (-1,0,1) if 0 <= (x := self.x + dx) < GRID_WIDTH and 0 <= (y := self.y + dy) < GRID_HEIGHT and self.world.get_terrain_type(x, y) == "tree")
        if nearby_trees > 5:
            high_resource = True
        if self.intelligence > 50 and high_resource:
            if random.random() > 0.05:  # 5% chance to allow movement even in resource-rich areas
                possible_moves = []
                weights = []
        # Apply explore bonus
        explore_bonus = 2 if "explore" in self.behaviors else 1
        weights = [w * explore_bonus for w in weights]
        if possible_moves:
            old_x, old_y = self.x, self.y
            self.x, self.y = random.choices(possible_moves, weights=weights, k=1)[0]
            self.world._update_spatial_grid_position(self, old_x, old_y)
        
        # Eat food after moving (or staying)
        terrain_type = self.world.get_terrain_type(self.x, self.y)
        # First, try to eat from inventory if hungry
        if self.energy < 100:
            for food in FOOD_TYPES:
                if self.inventory[food] > 0:
                    self.inventory[food] -= 1
                    energy_gain = FOOD_ENERGY[food] * (1 + self.foraging * 0.3)
                    self.energy = min(300, self.energy + energy_gain)
                    break
        # Then, eat from ground if still hungry and on fertile land
        if self.energy < 100 and terrain_type not in ["water", "mountain"] and self.world.food[self.y][self.x] > 0:
            food_amount = min(self.world.food[self.y][self.x], 5)  # Eat up to 5 food
            self.world.food[self.y][self.x] -= food_amount
            energy_gain = food_amount * FOOD_ENERGY["food"] * (1 + self.foraging * 0.3)  # Increased energy gain
            self.energy = min(300, self.energy + energy_gain)  # Increased max energy

    def _learn_from_experience(self, survived=False, avoided_danger=False, successful_action=None):
        """Increase wisdom/intelligence from experience. successful_action can be 'farm', 'build', 'invent', etc."""
        if survived:
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
        if avoided_danger:
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.03)
        if successful_action == 'farm':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.02)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'build':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.025)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.015)
        elif successful_action == 'invent':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.03)
        elif successful_action == 'chop':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'gather':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'mine':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.02)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'fish':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'forage':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
        elif successful_action == 'hunt':
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.01)
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.01)
    def _perform_actions(self):
        """Perform actions based on dynamic behaviors. Successful actions increase intelligence/wisdom."""
        terrain_type = self.world.get_terrain_type(self.x, self.y)
        # Dynamic behavior execution
        for behavior in list(self.behaviors):
            if behavior == "farm":
                if terrain_type in ["grass", "forest"] and random.random() < 0.15 * self.foraging:
                    if hasattr(self, 'advanced_farming') and self.advanced_farming:
                        self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["farmland"])
                        self.world.food[self.y][self.x] = min(25, self.world.food[self.y][self.x] + 8)
                        self._learn_from_experience(successful_action='farm')
                    elif "hoe" in self.tools and random.random() < 0.15:
                        self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["farmland"])
                        self.world.food[self.y][self.x] = min(20, self.world.food[self.y][self.x] + 5)
                        self._learn_from_experience(successful_action='farm')
            elif behavior == "chop":
                if "axe" in self.tools:
                    nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                    for entity in nearby:
                        if hasattr(entity, 'color') and entity.color == BROWN and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                            if random.random() < 0.1 * self.strength:
                                entity.is_dead = True
                                self.world._remove_from_grid(entity)
                                self.inventory["wood"] += 1
                                self._learn_from_experience(successful_action='chop')
                                break
            elif behavior == "chop_tree":
                if terrain_type == "tree":
                    self.world.set_terrain(self.x, self.y, 0)  # grass
                    self.inventory["wood"] += 1
                    self.world.chopped_trees.append((self.x, self.y, 600))
                    self._learn_from_experience(successful_action='chop')
            elif behavior == "build":
                if self.inventory["wood"] >= 5 and terrain_type == "grass":
                    if random.random() < 0.05:
                        self.world.add_entity(House(self.x, self.y, self.world))
                        self.inventory["wood"] -= 5
                        self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["village"])
                        self._learn_from_experience(successful_action='build')
            elif behavior == "merge":
                # Try to merge with a nearby human (simulate multicellular evolution)
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                for entity in nearby:
                    if (
                        entity is not self
                        and isinstance(entity, Human)
                        and abs(entity.x - self.x) <= 1
                        and abs(entity.y - self.y) <= 1
                        and "merge" in getattr(entity, 'behaviors', set())
                    ):
                        # Merge: create a new 'SuperHuman' with combined traits, remove both parents
                        print(f"Merging humans at ({self.x},{self.y}) and ({entity.x},{entity.y})")
                        avg_speed = (self.speed + entity.speed) / 2
                        avg_intelligence = (self.intelligence + entity.intelligence) / 2 + 0.1
                        avg_strength = (self.strength + entity.strength) / 2 + 0.1
                        avg_wisdom = (self.wisdom + entity.wisdom) / 2 + 0.1
                        avg_foraging = (self.foraging + entity.foraging) / 2 + 0.1
                        combined_behaviors = list(self.behaviors | entity.behaviors)
                        # Place new entity at this location
                        superhuman = Human(self.x, self.y, self.world, avg_speed, avg_intelligence, avg_strength, avg_wisdom, avg_foraging, behaviors=combined_behaviors)
                        self.world.add_entity(superhuman)
                        self.is_dead = True
                        entity.is_dead = True
                        self.world._remove_from_grid(self)
                        self.world._remove_from_grid(entity)
                        break
            elif behavior == "cooperate":
                # If nearby human also cooperates and is allied, boost building/farming chances this tick
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                ally_nearby = any(
                    isinstance(e, Human) and e is not self and "cooperate" in getattr(e, 'behaviors', set())
                    and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1
                    and self.world.get_tribe_relation(self.tribe, e.tribe) == 'allied'
                    for e in nearby
                )
                if ally_nearby:
                    # Small boosts through knowledge/tools
                    if random.random() < 0.02:
                        self.tools.add("hoe")
                    if random.random() < 0.02:
                        self.tools.add("axe")
            elif behavior == "share_food":
                # Share energy with a nearby hungry human from allied or same tribe
                if self.energy > 150:  # Trigger when energy is sufficiently high
                    nearby = self.world.get_entities_in_radius(self.x, self.y, 2)
                    for e in nearby:
                        if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 2 and abs(e.y - self.y) <= 2 and e.energy < 120:  # Extended distance and adjusted recipient threshold
                            relation = self.world.get_tribe_relation(self.tribe, e.tribe)
                            if relation in ['allied', 'neutral']:  # Share with allies and neutrals
                                delta = min(20, self.energy - 140)  # Increased max share and adjusted base
                                if delta > 0:
                                    self.energy -= delta
                                    e.energy = min(220, e.energy + delta)  # Increased recipient cap
                                break
            elif behavior == "gather":
                if terrain_type in ["grass", "forest", "farmland", "berries"] and self.world.food[self.y][self.x] > 0:
                    amount = min(10, self.world.food[self.y][self.x])
                    self.world.food[self.y][self.x] -= amount
                    if terrain_type == "berries":
                        self.inventory["berries"] += amount
                    else:
                        self.inventory["food"] += amount
                    self.energy += amount * 10
                    self._learn_from_experience(successful_action='gather')
            elif behavior == "mine":
                if terrain_type in ["ore", "stone"] and random.random() < 0.1:
                    resource = "ore" if terrain_type == "ore" else "stone"
                    self.inventory[resource] += 1
                    self.world.set_terrain(self.x, self.y, 0)  # Remove deposit
                    self._learn_from_experience(successful_action='mine')
            elif behavior == "fish":
                if terrain_type == "fish" and random.random() < 0.1:
                    self.inventory["fish"] += 1
                    self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["water"])  # Turn back to water
                    self._learn_from_experience(successful_action='fish')
            elif behavior == "forage":
                if terrain_type == "berries" and random.random() < 0.1:
                    self.inventory["berries"] += 1
                    self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["forest"])  # Turn back to forest
                    self._learn_from_experience(successful_action='forage')
            elif behavior == "hunt":
                # Find nearby animals
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                for entity in nearby:
                    if isinstance(entity, Animal) and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                        if random.random() < 0.1 * self.strength:
                            entity.is_dead = True
                            self.world._remove_from_grid(entity)
                            self.inventory["meat"] += 1
                            self.energy -= 5  # Energy cost for hunting
                            self._learn_from_experience(successful_action='hunt')
                            break

            elif behavior == "drop_items":
                # Drop some items on the ground for others
                if random.random() < 0.05:
                    for item in FOOD_TYPES + ["wood", "ore", "stone"]:
                        if self.inventory[item] > 0:
                            amount = min(1, self.inventory[item])
                            self.world.ground_items[self.y][self.x][item] = self.world.ground_items[self.y][self.x].get(item, 0) + amount
                            self.inventory[item] -= amount
                            break
            elif behavior == "pick_up":
                # Pick up items from the ground
                if random.random() < 0.1:
                    for item in FOOD_TYPES + ["wood", "ore", "stone"]:
                        if self.world.ground_items[self.y][self.x].get(item, 0) > 0:
                            amount = min(1, self.world.ground_items[self.y][self.x][item])
                            self.inventory[item] += amount
                            self.world.ground_items[self.y][self.x][item] -= amount
                            break

            elif behavior == "group_hunt":
                # Hunt with group for larger animals or better success
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                allies = [e for e in nearby if isinstance(e, Human) and e is not self and "group_hunt" in getattr(e, 'behaviors', set()) and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1]
                group_size = 1 + len(allies)
                success_chance = min(0.5, 0.1 * self.strength * group_size)  # Boosted by group
                for entity in nearby:
                    if isinstance(entity, Animal) and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                        if random.random() < success_chance:
                            entity.is_dead = True
                            self.world._remove_from_grid(entity)
                            self.inventory["meat"] += 1
                            self.energy -= 5  # Energy cost
                            self._learn_from_experience(successful_action='hunt')
                            # Share with allies
                            for ally in allies:
                                if random.random() < 0.5:
                                    ally.inventory["meat"] += 1
                            break

            elif behavior == "store_items":
                # Store items in nearby storage pile
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                for entity in nearby:
                    if isinstance(entity, StoragePile) and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                        for item in self.inventory:
                            if self.inventory[item] > 0:
                                amount = min(1, self.inventory[item])
                                entity.stored_items[item] += amount
                                self.inventory[item] -= amount
                                break
                        break

            elif behavior == "build_storage":
                if self.inventory["wood"] >= 3 and terrain_type == "grass":
                    # Check for allies to boost chance
                    nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                    allies = [e for e in nearby if isinstance(e, Human) and e is not self and "cooperate" in getattr(e, 'behaviors', set()) and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1 and self.world.get_tribe_relation(self.tribe, e.tribe) == 'allied']
                    chance = 0.05 * (1 + len(allies) * 0.5)  # Boost by allies
                    if random.random() < chance:
                        self.world.add_entity(StoragePile(self.x, self.y, self.world))
                        self.inventory["wood"] -= 3
                        self._learn_from_experience(successful_action='build')

            elif behavior == "build_campfire":
                if self.inventory["wood"] >= 2 and terrain_type == "grass":
                    nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                    allies = [e for e in nearby if isinstance(e, Human) and e is not self and "cooperate" in getattr(e, 'behaviors', set()) and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1 and self.world.get_tribe_relation(self.tribe, e.tribe) == 'allied']
                    chance = 0.05 * (1 + len(allies) * 0.5)
                    if random.random() < chance:
                        self.world.add_entity(Campfire(self.x, self.y, self.world))
                        self.inventory["wood"] -= 2
                        self._learn_from_experience(successful_action='build')

            elif behavior == "build_shelter":
                if self.inventory["wood"] >= 4 and terrain_type == "grass":
                    nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                    allies = [e for e in nearby if isinstance(e, Human) and e is not self and "cooperate" in getattr(e, 'behaviors', set()) and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1 and self.world.get_tribe_relation(self.tribe, e.tribe) == 'allied']
                    chance = 0.05 * (1 + len(allies) * 0.5)
                    if random.random() < chance:
                        self.world.add_entity(Shelter(self.x, self.y, self.world))
                        self.inventory["wood"] -= 4
                        self._learn_from_experience(successful_action='build')

            elif behavior == "form_tribe":
                if self.tribe is None and random.random() < 0.01:  # Small chance to form tribe
                    self.world.form_tribe(self)

            elif behavior == "raid":
                # Attack nearby hostile tribe humans
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                for e in nearby:
                    if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1:
                        relation = self.world.get_tribe_relation(self.tribe, e.tribe)
                        if relation == 'hostile':
                            if random.random() < 0.1 * self.strength:
                                # Attack: reduce energy
                                e.energy -= 20
                                self.world.update_tribe_relation(self.tribe, e.tribe, 'steal')  # Reinforce hostility
                                break

            elif behavior == "defend":
                # Boost defense against nearby hostiles, but for now just stay
                nearby = self.world.get_entities_in_radius(self.x, self.y, 2)
                hostiles_nearby = any(
                    isinstance(e, Human) and e is not self and self.world.get_tribe_relation(self.tribe, e.tribe) == 'hostile'
                    and abs(e.x - self.x) <= 2 and abs(e.y - self.y) <= 2
                    for e in nearby
                )
                if hostiles_nearby:
                    # Stay and defend, perhaps boost strength temporarily
                    pass  # For now, just presence

            elif behavior == "trade":
                # Exchange resources with allied tribes
                nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
                for e in nearby:
                    if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1:
                        relation = self.world.get_tribe_relation(self.tribe, e.tribe)
                        if relation == 'allied' and random.random() < 0.1:
                            # Exchange some items
                            for item in ["wood", "food", "ore", "stone"]:
                                if self.inventory[item] > 0 and e.inventory[item] < 5:
                                    self.inventory[item] -= 1
                                    e.inventory[item] += 1
                                    self._learn_from_experience(successful_action='gather')  # Benefit
                                    break

            elif behavior == "farm_advanced":
                # Improved farming with better yields
                if terrain_type in ["grass", "forest", "farmland"] and random.random() < 0.2 * self.foraging:
                    self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["farmland"])
                    self.world.food[self.y][self.x] = min(30, self.world.food[self.y][self.x] + 10)
                    self._learn_from_experience(successful_action='farm')

            elif behavior == "craft_tools":
                # Create advanced tools like axes from ore+wood
                if self.inventory["ore"] >= 1 and self.inventory["wood"] >= 1 and random.random() < 0.05:
                    self.inventory["ore"] -= 1
                    self.inventory["wood"] -= 1
                    self.tools.add("axe")  # Or advanced axe
                    self._learn_from_experience(successful_action='build')

            elif behavior == "explore":
                # Humans move further to discover new areas - perhaps increase movement range temporarily
                # For now, just a boost to movement or something, but since movement is in _move, maybe add a flag
                if random.random() < 0.1:
                    # Discover new knowledge or something
                    self.knowledge.add("explore_bonus")
                    self._learn_from_experience(successful_action='gather')

            elif behavior == "alliance":
                # Actively form alliances with nearby tribes
                nearby = self.world.get_entities_in_radius(self.x, self.y, 2)
                for e in nearby:
                    if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 2 and abs(e.y - self.y) <= 2:
                        if self.world.get_tribe_relation(self.tribe, e.tribe) == 'neutral' and random.random() < 0.02:
                            self.world.update_tribe_relation(self.tribe, e.tribe, 'allied')
                            self._learn_from_experience(successful_action='cooperate')
            elif behavior == "chop_tree":
                if terrain_type == "tree":
                    self.world.set_terrain(self.x, self.y, 0)  # grass
                    self.inventory["wood"] += 1
                    self.world.chopped_trees.append((self.x, self.y, 600))
                    self._learn_from_experience(successful_action='chop')
            elif behavior == "build_house":
                if self.inventory["wood"] >= 5 and terrain_type == "grass":
                    self.world.add_entity(House(self.x, self.y, self.world))
                    self.inventory["wood"] -= 5
                    self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["village"])
                    self._learn_from_experience(successful_action='build')
            elif behavior == "build_village":
                # Count nearby houses
                nearby_houses = sum(1 for e in self.world.get_entities_in_radius(self.x, self.y, 1) if isinstance(e, House))
                if nearby_houses >= 3:
                    # Set 3x3 area to village
                    for dx in range(-1, 2):
                        for dy in range(-1, 2):
                            nx, ny = self.x + dx, self.y + dy
                            if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT and self.world.get_terrain_type(nx, ny) == "grass":
                                self.world.set_terrain(nx, ny, REVERSE_TERRAIN_MAP["village"])
                    self._learn_from_experience(successful_action='build')

    def _evolve_behaviors(self):
        """Unlock new behaviors as intelligence/wisdom increase."""
        # Example: form groups if intelligence and wisdom are high
        if self.intelligence > 1.5 and self.wisdom > 1.5 and not hasattr(self, 'can_form_groups'):
            self.can_form_groups = True
        # Example: advanced farming
        if self.intelligence > 1.8 and not hasattr(self, 'advanced_farming'):
            self.advanced_farming = True
        # Example: build better houses
        if self.wisdom > 1.8 and not hasattr(self, 'better_building'):
            self.better_building = True
        # Learn to avoid water as wisdom grows
        if self.wisdom > 1.2:
            self.knowledge.add("avoid_water")
        # Unlock trade at intelligence >20
        if self.intelligence > 20 and "trade" not in self.behaviors:
            self.behaviors.add("trade")
        # Unlock farm_advanced at wisdom >30
        if self.wisdom > 30 and "farm_advanced" not in self.behaviors:
            self.behaviors.add("farm_advanced")
        # Unlock craft_tools at intelligence >40
        if self.intelligence > 40 and "craft_tools" not in self.behaviors:
            self.behaviors.add("craft_tools")
        # Unlock explore at wisdom >20
        if self.wisdom > 20 and "explore" not in self.behaviors:
            self.behaviors.add("explore")
        # Unlock alliance at intelligence >60
        if self.intelligence > 60 and "alliance" not in self.behaviors:
            self.behaviors.add("alliance")
        # Unlock chop_tree at intelligence >10
        if self.intelligence > 10 and "chop_tree" not in self.behaviors:
            self.behaviors.add("chop_tree")
        # Unlock build_house and build_village at intelligence >50 and wisdom >40
        if self.intelligence > 50 and self.wisdom > 40:
            if "build_house" not in self.behaviors:
                self.behaviors.add("build_house")
            if "build_village" not in self.behaviors:
                self.behaviors.add("build_village")

class Child(Human):
    """Represents a child in the game."""

    def __init__(
        self, x, y, world, speed, intelligence, strength, wisdom, foraging, behaviors=None, tribe=None
    ):
        super().__init__(x, y, world, speed, intelligence, strength, wisdom, foraging, behaviors=behaviors, tribe=tribe)
        self.color = LIGHT_YELLOW if self.tribe is None else TRIBE_COLORS[self.tribe % len(TRIBE_COLORS)]
        self.energy = 500  # POPULATION QUICK WIN TWEAK: Increased starting energy from 400 to 500
        #print(f"New Child created at ({x},{y}) with energy {self.energy} and traits: speed={speed}, intelligence={intelligence}, strength={strength}, wisdom={wisdom}, foraging={foraging}")

    def update(self):
        """Update the child's state."""
        if not super().update():
            return False
        if self.age > 15:
            adult = Human(
                self.x,
                self.y,
                self.world,
                self.speed,
                self.intelligence,
                self.strength,
                self.wisdom,
                self.foraging,
                behaviors=self.behaviors,
                tribe=self.tribe
            )
            adult.age = 0
            adult.energy = self.energy
            self.is_dead = True
            self.world._remove_from_grid(self)
            self.world.add_entity(adult)
            return False
        return True

    def draw(self, screen, camera=None):
        """Draw the child on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + CELL_SIZE // 2
            wy = self.y * CELL_SIZE + CELL_SIZE // 2
            sx, sy = camera.world_to_screen(wx, wy)
            scale = camera.zoom
            # Head
            pygame.draw.circle(screen, self.color, (sx, sy - int(2 * scale)), max(1, int(1 * scale)))
            # Body
            pygame.draw.line(
                screen, self.color, (sx, sy - int(1 * scale)), (sx, sy + int(2 * scale)), max(1, int(1 * scale))
            )
            # Arms
            pygame.draw.line(
                screen, self.color, (sx - int(1 * scale), sy), (sx + int(1 * scale), sy), max(1, int(1 * scale))
            )
            # Legs
            pygame.draw.line(
                screen,
                self.color,
                (sx, sy + int(2 * scale)),
                (sx - int(1 * scale), sy + int(3 * scale)),
                max(1, int(1 * scale)),
            )
            pygame.draw.line(
                screen,
                self.color,
                (sx, sy + int(2 * scale)),
                (sx + int(1 * scale), sy + int(3 * scale)),
                max(1, int(1 * scale)),
            )
        else:
            center_x = self.x * CELL_SIZE + CELL_SIZE // 2
            center_y = self.y * CELL_SIZE + CELL_SIZE // 2
            # Head
            pygame.draw.circle(screen, self.color, (center_x, center_y - 2), 1)
            # Body
            pygame.draw.line(
                screen, self.color, (center_x, center_y - 1), (center_x, center_y + 2), 1
            )
            # Arms
            pygame.draw.line(
                screen, self.color, (center_x - 1, center_y), (center_x + 1, center_y), 1
            )
            # Legs
            pygame.draw.line(
                screen,
                self.color,
                (center_x, center_y + 2),
                (center_x - 1, center_y + 3),
                1,
            )
            pygame.draw.line(
                screen,
                self.color,
                (center_x, center_y + 2),
                (center_x + 1, center_y + 3),
                1,
            )


class Tree(Entity):
    """Represents a tree in the game."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = BROWN

    def update(self):
        """Trees are static."""
        return True

    def draw(self, screen, camera=None):
        """Draw the tree on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + CELL_SIZE // 2
            wy = self.y * CELL_SIZE + CELL_SIZE - 4
            sx, sy = camera.world_to_screen(wx, wy)
            scale = camera.zoom
            pygame.draw.rect(
                screen,
                self.color,
                (
                    sx - int(1 * scale),
                    sy,
                    max(1, int(2 * scale)),
                    max(1, int(4 * scale)),
                ),
            )
            pygame.draw.circle(
                screen,
                FOREST_GREEN,
                (
                    sx,
                    sy - int(2 * scale),
                ),
                max(1, int(3 * scale)),
            )
        else:
            pygame.draw.rect(
                screen,
                self.color,
                (
                    self.x * CELL_SIZE + CELL_SIZE // 2 - 1,
                    self.y * CELL_SIZE + CELL_SIZE - 4,
                    2,
                    4,
                ),
            )
            pygame.draw.circle(
                screen,
                FOREST_GREEN,
                (
                    self.x * CELL_SIZE + CELL_SIZE // 2,
                    self.y * CELL_SIZE + CELL_SIZE - 6,
                ),
                3,
            )


class StoragePile(Entity):
    """Represents a storage pile for items."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = DARK_BROWN
        self.stored_items = {"wood": 0, "food": 0, "ore": 0, "stone": 0, "fish": 0, "berries": 0, "meat": 0}

    def update(self):
        """Storage piles are static but can provide benefits."""
        # Boost nearby humans' inventory capacity or something, but for now static
        return True

    def draw(self, screen, camera=None):
        """Draw the storage pile on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + 2
            wy = self.y * CELL_SIZE + CELL_SIZE - 4
            sx, sy = camera.world_to_screen(wx, wy)
            width = max(1, int(4 * camera.zoom))
            height = max(1, int(4 * camera.zoom))
            pygame.draw.rect(screen, self.color, (sx, sy, width, height))
        else:
            pygame.draw.rect(
                screen,
                self.color,
                (self.x * CELL_SIZE + 2, self.y * CELL_SIZE + CELL_SIZE - 4, 4, 4),
            )


class Campfire(Entity):
    """Represents a campfire that boosts nearby stats."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = ORANGE

    def update(self):
        """Campfire boosts nearby entities."""
        # Find nearby humans and boost their energy
        nearby = self.world.get_entities_in_radius(self.x, self.y, 2)
        for entity in nearby:
            if isinstance(entity, Human) and abs(entity.x - self.x) <= 2 and abs(entity.y - self.y) <= 2:
                entity.energy = min(300, entity.energy + 0.5)  # Small energy boost
                entity.strength = min(INTELLIGENCE_CAP, entity.strength + 0.001)  # Slight strength boost over time
        return True

    def draw(self, screen, camera=None):
        """Draw the campfire on the screen."""
        if camera:
            wx = self.x * CELL_SIZE + CELL_SIZE // 2
            wy = self.y * CELL_SIZE + CELL_SIZE // 2
            sx, sy = camera.world_to_screen(wx, wy)
            radius = max(1, int((CELL_SIZE // 2 - 1) * camera.zoom))
            pygame.draw.circle(screen, self.color, (sx, sy), radius)
        else:
            pygame.draw.circle(
                screen,
                self.color,
                (
                    self.x * CELL_SIZE + CELL_SIZE // 2,
                    self.y * CELL_SIZE + CELL_SIZE // 2,
                ),
                CELL_SIZE // 2 - 1,
            )


class Shelter(Entity):
    """Represents a basic shelter that provides protection."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = DARK_BROWN

    def update(self):
        """Shelter reduces energy loss for nearby humans."""
        nearby = self.world.get_entities_in_radius(self.x, self.y, 1)
        for entity in nearby:
            if isinstance(entity, Human) and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                # Reduce energy loss by boosting slightly
                entity.energy = min(300, entity.energy + 0.2)
        return True

    def draw(self, screen, camera=None):
        """Draw the shelter on the screen."""
        if camera:
            scale = camera.zoom
            wx_base = self.x * CELL_SIZE
            wy_base = self.y * CELL_SIZE + CELL_SIZE
            # Rect: +1, -5, 6, 4
            rect_wx = wx_base + 1
            rect_wy = wy_base - 5
            sx, sy = camera.world_to_screen(rect_wx, rect_wy)
            width = max(1, int(6 * scale))
            height = max(1, int(4 * scale))
            pygame.draw.rect(screen, self.color, (sx, sy, width, height))
            # Polygon
            points = [
                (wx_base, wy_base - 5),
                (wx_base + 3, wy_base - 7),
                (wx_base + 6, wy_base - 5),
            ]
            screen_points = [camera.world_to_screen(px, py) for px, py in points]
            pygame.draw.polygon(screen, GRAY, screen_points)
        else:
            pygame.draw.rect(
                screen,
                self.color,
                (self.x * CELL_SIZE + 1, self.y * CELL_SIZE + CELL_SIZE - 5, 6, 4),
            )
            pygame.draw.polygon(
                screen,
                GRAY,
                [
                    (self.x * CELL_SIZE, self.y * CELL_SIZE + CELL_SIZE - 5),
                    (self.x * CELL_SIZE + 3, self.y * CELL_SIZE + CELL_SIZE - 7),
                    (self.x * CELL_SIZE + 6, self.y * CELL_SIZE + CELL_SIZE - 5),
                ],
            )


class House(Entity):
    """Represents a house in the game."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = BROWN

    def update(self):
        """Houses are static."""
        return True

    def draw(self, screen, camera=None):
        """Draw the house on the screen."""
        if camera:
            scale = camera.zoom
            wx_base = self.x * CELL_SIZE
            wy_base = self.y * CELL_SIZE + CELL_SIZE
            # Rect: +1, -6, 8, 5
            rect_wx = wx_base + 1
            rect_wy = wy_base - 6
            sx, sy = camera.world_to_screen(rect_wx, rect_wy)
            width = max(1, int(8 * scale))
            height = max(1, int(5 * scale))
            pygame.draw.rect(screen, self.color, (sx, sy, width, height))
            # Polygon
            points = [
                (wx_base, wy_base - 6),
                (wx_base + 5, wy_base - 9),
                (wx_base + 10, wy_base - 6),
            ]
            screen_points = [camera.world_to_screen(px, py) for px, py in points]
            pygame.draw.polygon(screen, GRAY, screen_points)
        else:
            pygame.draw.rect(
                screen,
                self.color,
                (self.x * CELL_SIZE + 1, self.y * CELL_SIZE + CELL_SIZE - 6, 8, 5),
            )
            pygame.draw.polygon(
                screen,
                GRAY,
                [
                    (self.x * CELL_SIZE, self.y * CELL_SIZE + CELL_SIZE - 6),
                    (self.x * CELL_SIZE + 5, self.y * CELL_SIZE + CELL_SIZE - 9),
                    (self.x * CELL_SIZE + 10, self.y * CELL_SIZE + CELL_SIZE - 6),
                ],
            )


