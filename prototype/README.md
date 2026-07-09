# AIGMOS Text Prototype

## Version

v0.1

## Status

Playable prototype

## Purpose

This prototype validates the first minimal solo text adventure loop for AIGMOS using deterministic placeholder logic.

It is based on the MVP adventure premise: The Candlewick Mine Incident.

## How To Run

From the repository root:

```bash
python prototype/main.py
```

## What It Does

- Starts a new solo text adventure.
- Loads the hardcoded premise for The Candlewick Mine Incident.
- Shows opening narration.
- Accepts free-text player input.
- Responds with simple AI-DM-style text based on keywords and current scene.
- Tracks simple in-memory state.
- Supports five scenes:
  - Village inn
  - Village square
  - Mine entrance
  - Mine interior
  - Final chamber
- Supports a simple ending after the final chamber.
- Supports JSON save/load through `save_game.json`.

## Commands

- `help`: show available commands
- `status`: show current state summary
- `save`: save the current session
- `load`: load `save_game.json`
- `quit`: exit the prototype

All other input is treated as an in-world player action.

## What It Does Not Do

- It does not call an external AI API.
- It does not use a full game engine.
- It does not implement a full ruleset.
- It does not include multiplayer.
- It does not include web or mobile UI.
- It does not include accounts, database storage, monetization, voice, image generation, or marketplace features.
- It does not represent final adventure writing, final dialogue, or final game mechanics.

## Save File

The prototype writes `save_game.json` next to `main.py` when the player uses the `save` command.

The save file is intentionally simple and may change as the prototype evolves.
