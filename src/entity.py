INTELLIGENCE_CAP = 25.0
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
)


class Entity:
    """Base class for all entities in the game."""

    def __init__(self, x, y, world):
        self.x = x
        self.y = y
        self.world = world
        self.age = 0
        self.energy = 250

    def update(self):
        """Update the entity's state."""
        self.age += 1
        self.energy -= 0.1  # Reduced energy consumption per tick
        return self.energy > 0

    def draw(self, screen):
        """Draw the entity on the screen."""
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
            terrain_type in ["grass", "forest", "desert", "village", "farmland"]
            and self.world.food[self.y][self.x] > 0
        ):
            self.energy = min(100, self.energy + 7)
            self.world.food[self.y][self.x] -= 1
        return True

    def draw(self, screen):
        """Draw the animal on the screen."""
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
    def __init__(self, x, y, world, speed=1.0, intelligence=0.0, strength=1.0, wisdom=0.0, foraging=1.0, behaviors=None):
        super().__init__(x, y, world)
        self.color = YELLOW
        self.speed = speed
        self.intelligence = intelligence
        self.strength = strength
        self.wisdom = wisdom
        self.foraging = foraging
        self.knowledge = set()
        self.inventory = {"wood": 0, "food": 0}
        # Give starting humans basic tools to help them survive
        self.tools = {"axe", "hoe"}
        # Dynamic behaviors: set of behavior names (strings)
        if behaviors is None:
            self.behaviors = set(["farm", "chop", "build"])
        else:
            self.behaviors = set(behaviors)
        self.energy = 300  # Increased starting energy

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
        base_rate = 0.001
        invent_rate = base_rate * (1 + self.intelligence) * (1 + self.wisdom)
        if self.intelligence > 1.5 and self.wisdom > 1.0 and random.random() < min(0.02, invent_rate):
            possible_behaviors = ["merge", "cooperate", "share_food"]
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
        # Look for neighbors within 1 tile
        neighbors = [
            e for e in self.world.entities
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
        if self.age < 15 or self.age > 200:  # Lowered minimum reproduction age to 15
            return
        # Limit population
        human_count = sum(isinstance(e, (Human, Child)) for e in self.world.entities)
        if human_count >= MAX_POPULATION:
            return
        # Find a mate nearby (distance 1)
        for entity in self.world.entities:
            if (
                entity is not self
                and isinstance(entity, Human)
                and abs(entity.x - self.x) <= 1
                and abs(entity.y - self.y) <= 1
                and entity.age >= 15
                and entity.age <= 200
            ):
                if self.energy > 120 and entity.energy > 120 and random.random() < 0.95:
                    self.energy -= 30  # Energy cost for reproduction
                    entity.energy -= 30
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
                        possible_behaviors = ["merge", "cooperate", "share_food"]
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
                                    behaviors=parent_behaviors
                                )
                                self.world.add_entity(child)
                                break
                    break

    def draw(self, screen):
        """Draw the human on the screen."""
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
        if self.energy > 200:
            # Stay in place if energy is sufficient
            pass
        else:
            possible_moves = []
            for dx in range(-max(1, int(self.speed)), max(1, int(self.speed)) + 1):
                for dy in range(-max(1, int(self.speed)), max(1, int(self.speed)) + 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = self.x + dx, self.y + dy
                    if 0 <= nx < GRID_WIDTH and 0 <= ny < GRID_HEIGHT:
                        terrain_type = self.world.get_terrain_type(nx, ny)
                        if "avoid_water" in self.knowledge and terrain_type == "water":
                            continue
                        weight = 1
                        # Always seek food when energy is low, regardless of intelligence
                        if self.energy < 50:
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
                        if self.world.food[ny][nx] > 0 and self.energy < 70:
                            weight *= 2
                        possible_moves.extend([(nx, ny)] * int(weight))
            if possible_moves:
                self.x, self.y = random.choice(possible_moves)
        
        # Eat food after moving (or staying)
        terrain_type = self.world.get_terrain_type(self.x, self.y)
        if terrain_type not in ["water", "mountain"] and self.world.food[self.y][self.x] > 0:
            food_amount = min(self.world.food[self.y][self.x], 5)  # Eat up to 5 food
            self.world.food[self.y][self.x] -= food_amount
            energy_gain = food_amount * 20 * (1 + self.foraging * 0.3)  # Increased energy gain
            self.energy = min(300, self.energy + energy_gain)  # Increased max energy

    def _learn_from_experience(self, survived=False, avoided_danger=False, successful_action=None):
        """Increase wisdom/intelligence from experience. successful_action can be 'farm', 'build', 'invent', etc."""
        if survived:
            self.wisdom = min(INTELLIGENCE_CAP, self.wisdom + 0.005)
            self.intelligence = min(INTELLIGENCE_CAP, self.intelligence + 0.005)
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
                    elif "hoe" in self.tools and random.random() < 0.05:
                        self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["farmland"])
                        self.world.food[self.y][self.x] = min(20, self.world.food[self.y][self.x] + 5)
                        self._learn_from_experience(successful_action='farm')
            elif behavior == "chop":
                if "axe" in self.tools:
                    for entity in self.world.entities:
                        if hasattr(entity, 'color') and entity.color == BROWN and abs(entity.x - self.x) <= 1 and abs(entity.y - self.y) <= 1:
                            if random.random() < 0.1 * self.strength:
                                self.world.entities.remove(entity)
                                self.inventory["wood"] += 1
                                self._learn_from_experience(successful_action='chop')
                                break
            elif behavior == "build":
                if self.inventory["wood"] >= 5 and terrain_type == "grass":
                    if random.random() < 0.05:
                        from src.entity import House
                        self.world.add_entity(House(self.x, self.y, self.world))
                        self.inventory["wood"] -= 5
                        self.world.set_terrain(self.x, self.y, REVERSE_TERRAIN_MAP["village"])
                        self._learn_from_experience(successful_action='build')
            elif behavior == "merge":
                # Try to merge with a nearby human (simulate multicellular evolution)
                for entity in self.world.entities:
                    if (
                        entity is not self
                        and isinstance(entity, Human)
                        and abs(entity.x - self.x) <= 1
                        and abs(entity.y - self.y) <= 1
                        and "merge" in getattr(entity, 'behaviors', set())
                    ):
                        # Merge: create a new 'SuperHuman' with combined traits, remove both parents
                        avg_speed = (self.speed + entity.speed) / 2
                        avg_intelligence = (self.intelligence + entity.intelligence) / 2 + 0.1
                        avg_strength = (self.strength + entity.strength) / 2 + 0.1
                        avg_wisdom = (self.wisdom + entity.wisdom) / 2 + 0.1
                        avg_foraging = (self.foraging + entity.foraging) / 2 + 0.1
                        combined_behaviors = list(self.behaviors | entity.behaviors)
                        # Place new entity at this location
                        superhuman = Human(self.x, self.y, self.world, avg_speed, avg_intelligence, avg_strength, avg_wisdom, avg_foraging, behaviors=combined_behaviors)
                        self.world.add_entity(superhuman)
                        self.world.entities.remove(self)
                        self.world.entities.remove(entity)
                        break
            elif behavior == "cooperate":
                # If nearby human also cooperates, boost building/farming chances this tick
                ally_nearby = any(
                    isinstance(e, Human) and e is not self and "cooperate" in getattr(e, 'behaviors', set())
                    and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1
                    for e in self.world.entities
                )
                if ally_nearby:
                    # Small boosts through knowledge/tools
                    if random.random() < 0.02:
                        self.tools.add("hoe")
                    if random.random() < 0.02:
                        self.tools.add("axe")
            elif behavior == "share_food":
                # Share energy with a nearby hungry human
                if self.energy > 120:
                    for e in self.world.entities:
                        if isinstance(e, Human) and e is not self and abs(e.x - self.x) <= 1 and abs(e.y - self.y) <= 1 and e.energy < 80:
                            delta = min(10, self.energy - 110)
                            if delta > 0:
                                self.energy -= delta
                                e.energy = min(150, e.energy + delta)
                            break
            # Add more behaviors here (e.g., cooperate, share_food, etc.)

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

class Child(Human):
    """Represents a child in the game."""

    def __init__(
        self, x, y, world, speed, intelligence, strength, wisdom, foraging, behaviors=None
    ):
        super().__init__(x, y, world, speed, intelligence, strength, wisdom, foraging, behaviors=behaviors)
        self.color = LIGHT_YELLOW
        self.energy = 300  # Increased starting energy for better survival

    def update(self):
        """Update the child's state."""
        self.energy -= 0.05  # Reduced energy consumption for children
        if not super(Human, self).update():
            return False
        if self.age > 20:
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
            )
            adult.age = 0
            adult.energy = self.energy
            self.world.entities.remove(self)
            self.world.add_entity(adult)
            return False
        return True

    def draw(self, screen):
        """Draw the child on the screen."""
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

    def draw(self, screen):
        """Draw the tree on the screen."""
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


class House(Entity):
    """Represents a house in the game."""

    def __init__(self, x, y, world):
        super().__init__(x, y, world)
        self.color = BROWN

    def update(self):
        """Houses are static."""
        return True

    def draw(self, screen):
        """Draw the house on the screen."""
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


