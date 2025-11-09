# Mini WorldBox - Sandbox God Sim

A simple Python implementation of a mini WorldBox-like game using Pygame.

## Features

- Grid-based world (80x60 cells) for a larger and more detailed simulation
- Diverse terrain: Grass, Water, Mountains, Forest, Desert, Village, Farmland
- Food system: Fertile tiles have limited food that regrows over time
- Trees: Static entities that can be chopped for wood
- Houses: Structures built by humans using wood
- Two entity types: Humans (stick figures) and Animals (green circles)
- Humans can farm, drink, chop trees, cook, and build houses
- Reproduction creates children that grow into adults with inherited traits
- Population control to prevent map overload (max 500 humans/children)
- Entities have life cycles: movement, eating, aging, death
- Humans learn to avoid dangerous terrain and evolve traits (speed, intelligence, strength, wisdom, foraging) over generations
- Evolution persistence: Traits saved between sessions
- Improved graphics with more detailed entities and terrain
- Dynamic map evolution: Terrain changes based on human activities

### Dynamic Behavior Evolution

- Humans have a set of behaviors that can evolve over time.
- Behaviors are inherited by offspring and can mutate (added/removed).
- Cultural learning: nearby humans can copy behaviors from each other.
- Invention: intelligent and wise humans can invent new behaviors.

Emergent behaviors currently available:
- merge: two consenting humans can merge into a stronger individual (multi-cellular-like evolution)
- cooperate: nearby cooperators get small boosts that help them specialize faster
- share_food: well-fed humans share energy with hungry neighbors

## Requirements

- Python 3.x
- Pygame

## Installation

1.  Create a virtual environment: `python -m venv .venv`
2.  Activate it: `source .venv/bin/activate` (Linux/Mac) or `.venv\Scripts\activate` (Windows)
3.  Install dependencies: `pip install -r requirements.txt`

## Running the Game

Run `python main.py` to start the game.

## Controls

-   Left click: Place a human
-   Right click: Place an animal
-   R key: Reset evolution to starting values
-   Close window: Quit game
-   Arrow keys: Pan camera
-   Mouse wheel: Zoom in/out
-   F11: Toggle fullscreen
-   F1: Toggle FPS benchmark (samples 300 frames, shows avg/min/max)
-   FPS counter in sidebar
-   Legend and stats displayed

## Rendering Improvements

- Pre-rendered terrain surface with subtle per-tile color variation
- smoothscale for zoom<1

## Camera

- Clamped zoom with additive zoom_by() behavior

## Performance & Population Tweaks (Nov 2025)

- Quick wins applied: Human energy 300->400; Child 400->500; Reproduction cost 15->9; Max reproductive age 200->350; Food regrow +~40%.
- Headless test (100 ticks): Final population ~19, avg tick ~0.037s.

## Evolution Persistence

Human evolution (average traits) is automatically saved to `evolution.json` and persists between game sessions. When you restart the game, new humans will start with the evolved traits from the previous session.

Press **R** to reset evolution back to default starting values.

## Terrain

- Green: Grass (provides food, can be farmed by humans, houses can be built)
- Blue: Water (humans learn to avoid, provides hydration)
- Gray: Mountains (impassable for animals)
- Dark Green: Forest (provides food, can be farmed, has trees)
- Tan: Desert (provides some food)
- Brown: Village (settlements built by humans, rich in food)
- Gold: Farmland (improved agricultural land from intensive farming)

## Human Activities

- **Farming**: Humans farm on grass and forest to increase food production, can create farmland
- **Drinking**: Humans gain energy from water tiles
- **Chopping**: Humans can chop nearby trees for wood (strength affects success rate), clears forest to grass
- **Cooking**: Humans with food and wood can cook for extra energy
- **Building**: Humans with 5+ wood can build houses on grass tiles, creates village terrain
- **Evolution**: Humans evolve speed, intelligence, strength, and wisdom traits
- **Cultural learning**: Humans learn behaviors from nearby humans
- **Invention**: High-intelligence/wisdom humans can invent new behaviors (merge, cooperate, share_food)

## Map Evolution

The world changes based on human activities:
- **Deforestation**: Chopping trees converts forest to grass
- **Urbanization**: Building houses transforms grass into villages
- **Agriculture**: Intensive farming can turn grass into farmland
- **Resource Management**: Food regrows on all fertile lands, with villages and farmland producing more

## Evolution

Humans start with baseline traits and learn from their environment. Over time, they reproduce, passing traits to offspring with small mutations. Behaviors are also inherited and can be added/removed during reproduction. Intelligent and wise humans can invent entirely new behaviors, and neighbors can learn from one another. This leads to visible behavioral diversity across generations.

### Tips
- Larger populations increase the chance of invention and cultural spread.
- Behaviors like cooperate and share_food improve group survival.
- Merging is rare and requires two adjacent humans that both know merge.
- Delete evolution.json to reset; note that starting population grows slowly and is mechanics-limited, not CPU-bound.

## Future Enhancements

- More terrain types and resources
- Advanced AI behaviors
- God powers (disasters, blessings)
- Civilization building
- Better graphics and UI