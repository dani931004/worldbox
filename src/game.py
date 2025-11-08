"""
This file contains the Game class, which manages the main game loop and rendering.
"""
import pygame
import json
import os
import random
from src.constants import (
    WIDTH,
    HEIGHT,
    MAP_WIDTH,
    SIDEBAR_WIDTH,
    CELL_SIZE,
    GRID_WIDTH,
    GRID_HEIGHT,
    BLACK,
    WHITE,
    TERRAIN_COLORS,
    EVOLUTION_FILE,
    TERRAIN_MAP,
)
from src.world import World
from src.entity import Human, Animal, Child, House, Tree


class Game:
    """Manages the main game loop, event handling, and rendering."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mini WorldBox")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        self.world = World()
        self.evolution = self._load_evolution()
        self._add_initial_entities()
        self.running = True

    def _load_evolution(self):
        """Load evolution data from file."""
        try:
            with open(EVOLUTION_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "speed": 1.0,
                "intelligence": 0.0,
                "strength": 1.0,
                "wisdom": 0.0,
                "foraging": 1.3,  # Increased foraging for better survival
            }

    def _save_evolution(self):
        """Save evolution data to file."""
        human_entities = [e for e in self.world.entities if isinstance(e, Human)]
        if human_entities:
            self.evolution["speed"] = sum(h.speed for h in human_entities) / len(
                human_entities
            )
            self.evolution["intelligence"] = sum(
                h.intelligence for h in human_entities
            ) / len(human_entities)
            self.evolution["strength"] = sum(h.strength for h in human_entities) / len(
                human_entities
            )
            self.evolution["wisdom"] = sum(h.wisdom for h in human_entities) / len(
                human_entities
            )
            self.evolution["foraging"] = sum(h.foraging for h in human_entities) / len(
                human_entities
            )
            with open(EVOLUTION_FILE, "w") as f:
                json.dump(self.evolution, f)

    def _reset_evolution(self):
        """Reset evolution to default values."""
        self.evolution = {
            "speed": 1.0,
            "intelligence": 0.0,
            "strength": 1.0,
            "wisdom": 0.0,
            "foraging": 1.3,  # Increased foraging for better survival
        }
        try:
            os.remove(EVOLUTION_FILE)
        except OSError:
            pass

    def _add_initial_entities(self):
        """Add some initial entities to the world."""
        for _ in range(10):
            x, y = random.randint(0, GRID_WIDTH - 1), random.randint(
                0, GRID_HEIGHT - 1
            )
            if self.world.get_terrain_type(x, y) not in ["water", "mountain"]:
                self.world.add_entity(
                    Human(
                        x,
                        y,
                        self.world,
                        self.evolution["speed"],
                        self.evolution["intelligence"],
                        self.evolution["strength"],
                        self.evolution["wisdom"],
                        self.evolution["foraging"],
                    )
                )

    def run(self):
        """Main game loop."""
        frame_count = 0
        while self.running:
            self.handle_events()
            self.update(frame_count)
            self.draw()
            self.clock.tick(15)  # Increased FPS for smoother experience
            frame_count += 1
        pygame.quit()

    def handle_events(self):
        """Handle user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._reset_evolution()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                grid_x, grid_y = mx // CELL_SIZE, my // CELL_SIZE
                if 0 <= grid_x < GRID_WIDTH and 0 <= grid_y < GRID_HEIGHT:
                    if event.button == 1:  # Left click
                        self.world.add_entity(
                            Human(
                                grid_x,
                                grid_y,
                                self.world,
                                self.evolution["speed"],
                                self.evolution["intelligence"],
                                self.evolution["strength"],
                                self.evolution["wisdom"],
                                self.evolution["foraging"],
                            )
                        )
                    elif event.button == 3:  # Right click
                        self.world.add_entity(Animal(grid_x, grid_y, self.world))

    def update(self, frame_count):
        """Update game state."""
        self.world.update()
        if frame_count % 100 == 0:
            self._save_evolution()

    def draw(self):
        """Draw the game world and UI."""
        self.screen.fill(BLACK)
        self.draw_world()
        self.draw_sidebar()
        pygame.display.flip()

    def draw_world(self):
        """Draw the game world."""
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                terrain_type = self.world.get_terrain_type(x, y)
                color = TERRAIN_COLORS[terrain_type]
                pygame.draw.rect(
                    self.screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )
        for entity in self.world.entities:
            entity.draw(self.screen)

    def draw_sidebar(self):
        """Draw the sidebar with stats and legend."""
        sidebar_x = MAP_WIDTH
        pygame.draw.rect(
            self.screen, BLACK, (sidebar_x, 0, SIDEBAR_WIDTH, HEIGHT)
        )
        pygame.draw.rect(
            self.screen, WHITE, (sidebar_x, 0, SIDEBAR_WIDTH, HEIGHT), 2
        )

        legend_x = sidebar_x + 15
        legend_y = 20
        self.screen.blit(
            self.font.render("Legend", True, WHITE), (legend_x, legend_y)
        )
        legend_y += 30

        for i, (name, color) in enumerate(TERRAIN_COLORS.items()):
            pygame.draw.rect(self.screen, color, (legend_x, legend_y + i * 20, 10, 10))
            self.screen.blit(
                self.font_small.render(name.capitalize(), True, WHITE),
                (legend_x + 20, legend_y + i * 20),
            )
        
        stats_y = legend_y + len(TERRAIN_COLORS) * 20 + 20
        self.screen.blit(self.font.render("Stats", True, WHITE), (legend_x, stats_y))
        stats_y += 30

        human_count = len([e for e in self.world.entities if isinstance(e, (Human, Child))])
        animal_count = len([e for e in self.world.entities if isinstance(e, Animal)])
        house_count = len([e for e in self.world.entities if isinstance(e, House)])
        tree_count = len([e for e in self.world.entities if isinstance(e, Tree)])
        
        stats = {
            "Humans": human_count,
            "Animals": animal_count,
            "Houses": house_count,
            "Trees": tree_count,
            "Speed": f"{self.evolution['speed']:.2f}",
            "Intelligence": f"{self.evolution['intelligence']:.2f}",
            "Strength": f"{self.evolution['strength']:.2f}",
            "Wisdom": f"{self.evolution['wisdom']:.2f}",
            "Foraging": f"{self.evolution['foraging']:.2f}",
        }

        for i, (name, value) in enumerate(stats.items()):
            self.screen.blit(
                self.font_small.render(f"{name}: {value}", True, WHITE),
                (legend_x, stats_y + i * 20),
            )

        controls_y = stats_y + len(stats) * 20 + 30
        self.screen.blit(self.font.render("Controls", True, WHITE), (legend_x, controls_y))
        controls_y += 30
        self.screen.blit(self.font_small.render("L-Click: Add Human", True, WHITE), (legend_x, controls_y))
        self.screen.blit(self.font_small.render("R-Click: Add Animal", True, WHITE), (legend_x, controls_y + 20))
        self.screen.blit(self.font_small.render("R: Reset Evolution", True, WHITE), (legend_x, controls_y + 40))
        self.screen.blit(self.font_small.render("Close: Quit", True, WHITE), (legend_x, controls_y + 60))
