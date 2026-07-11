from __future__ import annotations

import random


def roll_die(sides: int, fixed_roll: int | None = None) -> int:
    if sides < 2:
        raise ValueError("sides must be at least 2")
    if fixed_roll is not None:
        if not 1 <= fixed_roll <= sides:
            raise ValueError("fixed roll outside die range")
        return fixed_roll
    return random.randint(1, sides)


def roll_dice(count: int, sides: int, fixed_rolls: list[int] | None = None) -> list[int]:
    if count < 1:
        raise ValueError("count must be positive")
    if fixed_rolls is not None and len(fixed_rolls) != count:
        raise ValueError("fixed_rolls length must equal count")
    return [roll_die(sides, fixed_rolls[index] if fixed_rolls else None) for index in range(count)]


def roll_d20(fixed_roll: int | None = None) -> int:
    return roll_die(20, fixed_roll)


def calculate_modifier(score: int) -> int:
    return (score - 10) // 2


def apply_advantage(first: int, second: int) -> int:
    return max(first, second)


def apply_disadvantage(first: int, second: int) -> int:
    return min(first, second)
