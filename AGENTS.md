# AGENTS.md - Mini WorldBox Development Guide

## Build/Test Commands
- **Run game**: `python main.py`
- **Install deps**: `pip install -r requirements.txt`
- **Virtual env**: `python -m venv .venv && source .venv/bin/activate`
- **Debug**: Run game and observe behavior (no formal tests)
- **Reset evolution**: Delete `evolution.json` or press 'R' in-game

## Code Style Guidelines
- **Imports**: Group by stdlib, then third-party, then local. Import specific items from constants.
- **Naming**: Classes=PascalCase, functions/methods=snake_case, constants=UPPER_CASE
- **Docstrings**: Use triple quotes for all classes/methods with brief descriptions
- **Comments**: Section headers and inline explanations for complex logic
- **Types**: Add type hints for function parameters and return values
- **Error handling**: Use try/except for file I/O, validate inputs
- **Formatting**: 4-space indentation, max 100 chars/line, blank lines between methods

## Architecture Patterns
- **Entity inheritance**: All entities inherit from `Entity` base class
- **Behavior evolution**: Dynamic behaviors in sets, inherited/mutated during reproduction
- **Cultural learning**: Nearby entities can copy behaviors from each other
- **Persistence**: Evolution data saved to JSON, loaded at startup

## Copilot Rules (from .github/copilot-instructions.md)
- **Main entry**: `main.py` → `Game` → `World.update()` → entity actions
- **Core modules**: game.py (loop/rendering), world.py (terrain/entities), entity.py (AI/behaviors), constants.py (config)
- **Behavior addition**: Extend `Human._perform_actions()`, add to invention list
- **Population control**: `MAX_POPULATION` in constants.py
- **Debug evolution**: Delete evolution.json to reset persistent traits