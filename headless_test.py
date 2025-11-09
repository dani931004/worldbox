"""
Headless test script for Mini WorldBox to test spatial grid optimization.
"""
import time
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.world import World
from src.entity import Human, Animal, Child, House, Tree
from src.constants import MAX_POPULATION, EVOLUTION_FILE
import json
import random

class HeadlessGame:
    def __init__(self):
        self.world = World()
        self.evolution = self._load_evolution()
        self._add_initial_entities()
        print(f"Initial evolution: {self.evolution}")
        self.tick_times = []
        self.population_history = []

    def _load_evolution(self):
        try:
            with open(EVOLUTION_FILE, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "speed": 1.0,
                "intelligence": 0.0,
                "strength": 1.0,
                "wisdom": 0.0,
                "foraging": 1.3,
            }

    def _add_initial_entities(self):
        for _ in range(20):
            x, y = random.randint(0, self.world.terrain[0].__len__() - 1), random.randint(0, len(self.world.terrain) - 1)
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

    def run_simulation(self, ticks=1000):
        print(f"Starting headless simulation for {ticks} ticks with MAX_POPULATION={MAX_POPULATION}")
        for tick in range(ticks):
            start_time = time.time()
            self.world.update()
            end_time = time.time()
            tick_time = end_time - start_time
            self.tick_times.append(tick_time)
            
            human_count = len([e for e in self.world.entities if isinstance(e, (Human, Child))])
            animal_count = len([e for e in self.world.entities if isinstance(e, Animal)])
            total_pop = human_count + animal_count
            self.population_history.append(total_pop)
            
            if tick % 100 == 0:
                print(f"Tick {tick}: Population {total_pop}, Tick time {tick_time:.4f}s")
        
        # Calculate final averages
        human_entities = [e for e in self.world.entities if isinstance(e, Human)]
        if human_entities:
            final_intelligence = sum(h.intelligence for h in human_entities) / len(human_entities)
            final_wisdom = sum(h.wisdom for h in human_entities) / len(human_entities)
            print(f"Final average intelligence: {final_intelligence:.2f}")
            print(f"Final average wisdom: {final_wisdom:.2f}")
            # Check for new behaviors
            all_behaviors = set()
            for h in human_entities:
                all_behaviors.update(h.behaviors)
            print(f"Behaviors present: {sorted(all_behaviors)}")
        else:
            print("No humans left.")
        self.report()

    def report(self):
        print("\nSimulation Report:")
        print(f"Final Population: {self.population_history[-1]}")
        print(f"Average Tick Time: {sum(self.tick_times)/len(self.tick_times):.4f}s")
        print(f"Max Tick Time: {max(self.tick_times):.4f}s")
        print(f"Min Tick Time: {min(self.tick_times):.4f}s")
        
        # Check if stabilized
        last_100 = self.population_history[-100:]
        avg_last_100 = sum(last_100) / len(last_100)
        if self.population_history[-1] >= MAX_POPULATION * 0.9:
            print("Population stabilized near MAX_POPULATION.")
        else:
            print("Population did not reach stabilization.")
        
        # Check performance
        avg_time = sum(self.tick_times)/len(self.tick_times)
        if avg_time < 0.1:  # Assuming 0.1s is acceptable
            print("Performance: Good, no lag detected.")
        else:
            print("Performance: Potential lag, average tick time high.")

if __name__ == "__main__":
    game = HeadlessGame()
    game.run_simulation(1000)
