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
    MAP_HEIGHT,
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
from src.camera import Camera


class Game:
    """Manages the main game loop, event handling, and rendering."""

    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Mini WorldBox")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 20)
        self.world = World()
        self.evolution = self._load_evolution()
        self.camera = Camera(MAP_WIDTH, MAP_HEIGHT, self.screen.get_width() - SIDEBAR_WIDTH, self.screen.get_height())
        self._add_initial_entities()
        self.running = True
        # Benchmark attributes
        self.benchmark_active = False
        self.fps_samples = []
        self.benchmark_stats = None
        self.benchmark_max_samples = 300

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

    def _compute_benchmark_stats(self):
        """Compute benchmark statistics from fps_samples."""
        if not self.fps_samples:
            return
        self.benchmark_stats = {
            'avg': sum(self.fps_samples) / len(self.fps_samples),
            'min': min(self.fps_samples),
            'max': max(self.fps_samples),
            'count': len(self.fps_samples)
        }

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
                        max(0.5, self.evolution["intelligence"]),
                        self.evolution["strength"],
                        max(0.5, self.evolution["wisdom"]),
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
            self.clock.tick(60)  # Allow up to 60 FPS
            frame_count += 1
        pygame.quit()

    def handle_events(self):
        """Handle user input and events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                self.screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
                self.camera.set_view(event.w - SIDEBAR_WIDTH, event.h)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self._reset_evolution()
                elif event.key == pygame.K_F11:
                    if self.screen.get_flags() & pygame.FULLSCREEN:
                        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
                        self.camera.set_view(WIDTH - SIDEBAR_WIDTH, HEIGHT)
                    else:
                        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                        self.camera.set_view(self.screen.get_width() - SIDEBAR_WIDTH, self.screen.get_height())
                elif event.key == pygame.K_F1:
                    self.benchmark_active = not self.benchmark_active
                    if self.benchmark_active:
                        self.fps_samples = []
                        self.benchmark_stats = None
                    else:
                        if self.fps_samples:
                            self._compute_benchmark_stats()
            elif event.type == pygame.MOUSEWHEEL:
                self.camera.zoom_by(0.1 if event.y > 0 else -0.1)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                if mx >= self.screen.get_width() - SIDEBAR_WIDTH:
                    # Inside sidebar, ignore
                    pass
                else:
                    wx, wy = self.camera.screen_to_world(mx, my)
                    grid_x = int(wx // CELL_SIZE)
                    grid_y = int(wy // CELL_SIZE)
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
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.camera.move(-10, 0)
        if keys[pygame.K_RIGHT]:
            self.camera.move(10, 0)
        if keys[pygame.K_UP]:
            self.camera.move(0, -10)
        if keys[pygame.K_DOWN]:
            self.camera.move(0, 10)
        self.world.update()
        # Benchmark sampling
        if self.benchmark_active:
            self.fps_samples.append(self.clock.get_fps())
            if len(self.fps_samples) >= self.benchmark_max_samples:
                self._compute_benchmark_stats()
                self.benchmark_active = False
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
        viewport_w = self.screen.get_width() - SIDEBAR_WIDTH
        viewport_h = self.screen.get_height()
        self.camera.set_view(viewport_w, viewport_h)
        src_rect = self.camera.get_src_rect()
        # Clip to world bounds
        src_rect = src_rect.clip(pygame.Rect(0, 0, MAP_WIDTH, MAP_HEIGHT))
        subsurface = self.world.terrain_surface.subsurface(src_rect)
        if self.camera.zoom < 1.0:
            scaled = pygame.transform.smoothscale(subsurface, (viewport_w, viewport_h))
        else:
            scaled = pygame.transform.scale(subsurface, (viewport_w, viewport_h))
        self.screen.blit(scaled, (0, 0))
        # Draw entities
        for entity in self.world.entities:
            wx = entity.x * CELL_SIZE + CELL_SIZE // 2
            wy = entity.y * CELL_SIZE + CELL_SIZE // 2
            if src_rect.left <= wx < src_rect.right and src_rect.top <= wy < src_rect.bottom:
                entity.draw(self.screen, self.camera)

    def draw_sidebar(self):
        """Draw the sidebar with stats and legend."""
        sidebar_x = self.screen.get_width() - SIDEBAR_WIDTH
        pygame.draw.rect(
            self.screen, BLACK, (sidebar_x, 0, SIDEBAR_WIDTH, self.screen.get_height())
        )
        pygame.draw.rect(
            self.screen, WHITE, (sidebar_x, 0, SIDEBAR_WIDTH, self.screen.get_height()), 2
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

        human_count = self.world.population_count
        animal_count = self.world.animal_count
        house_count = self.world.house_count
        tree_count = self.world.tree_count
        
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
            "FPS": f"{self.clock.get_fps():.0f}",
        }

        for i, (name, value) in enumerate(stats.items()):
            self.screen.blit(
                self.font_small.render(f"{name}: {value}", True, WHITE),
                (legend_x, stats_y + i * 20),
            )

        # Benchmark display
        extra_lines = 0
        if self.benchmark_active:
            bench_text = f"Benchmark: sampling ({len(self.fps_samples)}/{self.benchmark_max_samples})"
            self.screen.blit(
                self.font_small.render(bench_text, True, WHITE),
                (legend_x, stats_y + len(stats) * 20 + extra_lines * 20),
            )
            extra_lines += 1
        elif self.benchmark_stats is not None:
            avg_text = f"Bench Avg: {self.benchmark_stats['avg']:.0f}"
            min_text = f"Bench Min: {self.benchmark_stats['min']:.0f}"
            max_text = f"Bench Max: {self.benchmark_stats['max']:.0f}"
            self.screen.blit(
                self.font_small.render(avg_text, True, WHITE),
                (legend_x, stats_y + len(stats) * 20 + extra_lines * 20),
            )
            extra_lines += 1
            self.screen.blit(
                self.font_small.render(min_text, True, WHITE),
                (legend_x, stats_y + len(stats) * 20 + extra_lines * 20),
            )
            extra_lines += 1
            self.screen.blit(
                self.font_small.render(max_text, True, WHITE),
                (legend_x, stats_y + len(stats) * 20 + extra_lines * 20),
            )
            extra_lines += 1

        controls_y = stats_y + len(stats) * 20 + extra_lines * 20 + 30
        self.screen.blit(self.font.render("Controls", True, WHITE), (legend_x, controls_y))
        controls_y += 30
        self.screen.blit(self.font_small.render("L-Click: Add Human", True, WHITE), (legend_x, controls_y))
        self.screen.blit(self.font_small.render("R-Click: Add Animal", True, WHITE), (legend_x, controls_y + 20))
        self.screen.blit(self.font_small.render("R: Reset Evolution", True, WHITE), (legend_x, controls_y + 40))
        self.screen.blit(self.font_small.render("Arrow Keys: Pan", True, WHITE), (legend_x, controls_y + 60))
        self.screen.blit(self.font_small.render("Mouse Wheel: Zoom", True, WHITE), (legend_x, controls_y + 80))
        self.screen.blit(self.font_small.render("F11: Toggle Fullscreen", True, WHITE), (legend_x, controls_y + 100))
        self.screen.blit(self.font_small.render("F1: Toggle FPS Benchmark", True, WHITE), (legend_x, controls_y + 120))
        self.screen.blit(self.font_small.render("Close: Quit", True, WHITE), (legend_x, controls_y + 140))
