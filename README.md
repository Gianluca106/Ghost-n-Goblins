# Ghosts 'n Goblins (Python / Pygame)

A from-scratch recreation of the classic arcade platformer **Ghosts 'n Goblins**, built in Python as a university project. The player controls the knight Arthur through a side-scrolling level, fighting zombies, plants, and other undead enemies while jumping, climbing, and throwing weapons.

## Overview

The game reimplements the core mechanics of the original arcade title: platforming physics (gravity, jumping, solid and semi-solid platforms), ladder climbing, a throwable weapon with cooldown, a lives system, and multiple enemy types with distinct behaviors. Level layout, sprite coordinates, and UI settings are all data-driven, loaded from external configuration files rather than hardcoded.

The project builds on top of a minimal 2D game framework (`g2d.py`, `actor.py`) provided as course material by Michele Tomaiuolo ([tomamic.github.io](https://tomamic.github.io/)), which wraps Pygame with a simple `Actor`/`Arena` interface. All game logic, characters, physics, GUI, level design, and tests were implemented as part of this project.

## Key Features

- **Player character (Arthur):** running, jumping, ladder climbing, and throwing a lance with a cooldown timer
- **Physics engine:** gravity, bounding-box collision detection, solid and semi-solid platforms
- **Enemies:** walking zombies that attack on contact, plants that shoot projectiles, bouncing eyeballs, environmental hazards (torches/flames)
- **HUD:** lives display (hearts), custom bitmap-font text rendering, game-over and level-complete screens
- **Data-driven level design:** level layout, sprite sheet coordinates, and UI configuration loaded from plain text files (`level1_config.txt`, `sprites.txt`, `gui_config.txt`)
- **Automated tests:** unit tests (with mocking) covering player movement/physics and enemy behavior

## Tech Stack

- **Language:** Python 3
- **Graphics/Input:** Pygame (via the provided `g2d` wrapper)
- **Testing:** `unittest`, `unittest.mock`

## Project Structure

```
Ghost 'n Goblins/
├── g2d.py                # 2D rendering/input wrapper around Pygame (course-provided)
├── actor.py               # Actor/Arena base interface and collision helpers (course-provided)
├── gnggame.py             # Game logic: all actors (Arthur, enemies, platforms, items) and game state
├── gnggui.py               # GUI layer: rendering, HUD, menus, main entry point
├── level1_config.txt      # Level layout (platforms, ladders, enemy placement)
├── sprites.txt            # Sprite sheet coordinates
├── gui_config.txt         # HUD/text rendering configuration
├── test_arthur.py         # Unit tests for player movement and physics
└── test_enemies.py        # Unit tests for enemy behavior
```

## Running the Game

**1. Requirements**
- Python 3.10+
- Pygame (installed automatically on first run if missing, or manually with `pip install pygame`)

**2. Start the game**
```
python gnggui.py
```

**3. Controls**
- **Arrow Left / Right:** move
- **Arrow Up / Down:** climb ladders / jump
- **Spacebar:** throw weapon
- **Enter:** restart after Game Over or advance after completing a level

## Running the Tests

```
python -m unittest test_arthur.py test_enemies.py
```

---

> Built on top of a minimal 2D game framework (`g2d.py`, `actor.py`) provided as course material, credit to the original author noted in those files.
