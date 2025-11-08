
# Copilot Instructions for Mini WorldBox

This project is a Python/Pygame sandbox god simulation game. Use these guidelines to maximize AI coding agent productivity and maintain project conventions.

## Architecture Overview
- **Main entry:** `main.py` launches the game loop via `Game` in `src/game.py`.
- **Core modules:**
	- `src/game.py`: Game loop, event handling, rendering, and evolution persistence.
	- `src/world.py`: Manages terrain, food, and all entities.
	- `src/entity.py`: Entity classes (Human, Animal, Child, Tree, House) and all AI/behavior logic.
	- `src/constants.py`: All constants, colors, terrain IDs, and config values.
- **Data flow:**
	- The game loop calls `World.update()`, which updates all entities.
	- Entities act based on their own logic and can mutate, invent, or learn behaviors.
	- Evolution data is saved/loaded from `evolution.json`.

## Key Patterns & Conventions
- **Entity Inheritance:** All entities inherit from `Entity`. Humans and Children support dynamic behaviors via a `behaviors` set.
- **Behavior Evolution:**
	- Behaviors are inherited, mutated, and can be invented or learned culturally.
	- New behaviors are added by extending `_perform_actions()` in `Human`.
- **Reproduction:**
	- Humans reproduce if age and population limits allow. Offspring inherit and mutate both traits and behaviors.
- **Persistence:**
	- Evolution traits are saved to `evolution.json` every 100 frames and loaded at startup.
- **Controls:**
	- Left click: add human. Right click: add animal. R: reset evolution.

## Developer Workflows
- **Run the game:**
	```bash
	source .venv/bin/activate
	python main.py
	```
- **Dependencies:**
	- All requirements in `requirements.txt` (mainly `pygame`).
- **No formal tests:**
	- Debug by running the game and observing entity behavior.
- **Evolution debugging:**
	- Delete `evolution.json` to reset persistent evolution.

## Project-Specific Notes
- **Population cap:** Controlled by `MAX_POPULATION` in `src/constants.py`.
- **Behavior invention:** List of possible behaviors is in `Human._maybe_invent_behavior()`.
- **Trait/behavior mutation:** Controlled in `Human._try_reproduce()`.
- **Cultural learning:** Implemented in `Human._cultural_learning()`.
- **Adding new entity types:** Inherit from `Entity` and register in `World`.

## Examples
- To add a new behavior (e.g., 'trade'):
	1. Add to possible behaviors in `Human._maybe_invent_behavior()`.
	2. Implement logic in `Human._perform_actions()`.
	3. Optionally, update documentation in `README.md`.

---

If any section is unclear or missing, please provide feedback for further refinement.