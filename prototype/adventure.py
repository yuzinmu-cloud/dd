from __future__ import annotations

from game_state import GameState


OPENING_NARRATION = """
The Candlewick Mine Incident

Rain needles across your cloak as you reach the frontier village of Graybarrow.
Lanterns gutter in the storm. The old Candlewick Mine waits beyond the ridge,
its abandoned tunnels flashing with pale lights that no miner will explain.

Three miners are missing. The village wants answers before dawn.
""".strip()


SCENE_DESCRIPTIONS = {
    "village_inn": "You stand inside the village inn. Wet travelers whisper near the hearth, and the innkeeper watches you a little too carefully.",
    "village_square": "The village square is slick with rain. A worried crowd gathers near a notice board while the village leader tries to keep order.",
    "mine_entrance": "The mine entrance yawns open beneath the ridge. Broken warning signs hang from old posts, and fresh bootprints vanish into the dark.",
    "mine_interior": "Inside the mine, water drips through cracked beams. Strange candle-colored lights move deeper in the tunnel.",
    "final_chamber": "You reach a final chamber where the missing miners' trail, the strange lights, and the village's secrets converge.",
}


HELP_TEXT = "Commands: type any action, or use save, load, status, help, quit."


def describe_current_scene(state: GameState) -> str:
    return SCENE_DESCRIPTIONS[state.current_scene]


def status_text(state: GameState) -> str:
    notes = "; ".join(state.notes) if state.notes else "none yet"
    flags = ", ".join(sorted(state.flags)) if state.flags else "none yet"
    return (
        f"Adventure: {state.adventure_title}\n"
        f"Scene: {state.current_scene}\n"
        f"Turns: {state.turn_count}\n"
        f"Notes: {notes}\n"
        f"Flags: {flags}"
    )


def handle_action(state: GameState, action: str) -> str:
    cleaned = action.strip().lower()
    state.record_action(action)

    if state.ended:
        return ending_text(state)

    if state.current_scene == "village_inn":
        return handle_village_inn(state, cleaned)
    if state.current_scene == "village_square":
        return handle_village_square(state, cleaned)
    if state.current_scene == "mine_entrance":
        return handle_mine_entrance(state, cleaned)
    if state.current_scene == "mine_interior":
        return handle_mine_interior(state, cleaned)
    if state.current_scene == "final_chamber":
        return handle_final_chamber(state, cleaned)

    return "The AI GM pauses. Something about the scene state is unknown."


def handle_village_inn(state: GameState, action: str) -> str:
    if has_any(action, "innkeeper", "talk", "ask", "question", "rumor"):
        state.set_flag("questioned_innkeeper")
        state.add_note("The innkeeper hinted that the mine lights started after the last survey crew returned.")
        return (
            "The innkeeper dries a cup that is already clean. She admits the lights began after the last survey crew came back pale and silent. "
            "She points you toward the village square, where the leader is trying to calm the families."
        )

    if has_any(action, "square", "leave", "outside", "leader", "families", "continue"):
        state.advance_scene()
        return describe_current_scene(state)

    state.add_note("The inn felt tense, and the innkeeper seemed to be hiding something.")
    return (
        "You take in the room: muddy boots, quiet miners, a map with the mine road marked in charcoal. "
        "The AI GM suggests a clear next step: question the innkeeper or head to the village square."
    )


def handle_village_square(state: GameState, action: str) -> str:
    if has_any(action, "leader", "mayor", "elder", "quiet", "briefing"):
        state.set_flag("met_village_leader")
        state.add_note("The village leader wants the problem solved quietly before panic spreads.")
        return (
            "The village leader lowers their voice. They want the missing miners found, but they also want the incident kept quiet. "
            "They give you permission to inspect the mine entrance."
        )

    if has_any(action, "relative", "family", "miner", "missing", "urgent"):
        state.set_flag("heard_family_plea")
        state.add_note("A missing miner's relative believes someone heard knocking from inside the sealed tunnel.")
        return (
            "A missing miner's relative grabs your sleeve and begs you not to wait for morning. "
            "They say someone heard knocking below the old sealed tunnel."
        )

    if has_any(action, "mine", "entrance", "ridge", "go", "continue"):
        state.advance_scene()
        return describe_current_scene(state)

    return (
        "Rain runs through the square in silver lines. You can speak with the village leader, listen to a missing miner's relative, "
        "or head toward the mine entrance."
    )


def handle_mine_entrance(state: GameState, action: str) -> str:
    if has_any(action, "tracks", "boot", "footprint", "inspect", "search"):
        state.set_flag("found_fresh_tracks")
        state.add_note("Fresh bootprints lead into the abandoned mine, but none return.")
        return (
            "You kneel in the mud. Fresh bootprints lead into the mine, but the rain has not softened any returning tracks. "
            "Whatever happened, the missing miners likely went in and stayed in."
        )

    if has_any(action, "sign", "warning", "listen", "light", "lantern"):
        state.set_flag("noticed_warning_signs")
        state.add_note("Old warning signs mention unstable beams and sealed lower passages.")
        return (
            "Your lantern catches a cracked warning sign: unstable beams, sealed lower passages, no entry after dusk. "
            "A faint candle-colored flicker answers from inside the tunnel."
        )

    if has_any(action, "enter", "inside", "mine", "go", "continue"):
        state.advance_scene()
        return describe_current_scene(state)

    return "The mine waits. You can inspect the tracks, study the warning signs, listen at the entrance, or enter."


def handle_mine_interior(state: GameState, action: str) -> str:
    if has_any(action, "beam", "danger", "careful", "avoid", "brace"):
        state.set_flag("handled_environmental_danger")
        state.add_note("The player handled unstable beams carefully inside the mine.")
        return (
            "You move carefully and brace a sagging beam before passing. Behind it, you find a dropped mining token near a side passage. "
            "The mine seems dangerous, but not random. Someone came this way in a hurry."
        )

    if has_any(action, "light", "follow", "clue", "token", "deeper", "sound"):
        state.set_flag("followed_strange_lights")
        state.add_note("The strange lights led deeper toward the final chamber.")
        return (
            "The candle-colored lights drift ahead, always just beyond reach. They do not attack. They guide. "
            "A low knocking echoes from the final chamber."
        )

    if has_any(action, "final", "chamber", "continue", "go", "forward"):
        state.advance_scene()
        return describe_current_scene(state)

    return (
        "The tunnel narrows. You can deal with the unstable beams, follow the strange lights, search for clues, "
        "or press onward to the final chamber."
    )


def handle_final_chamber(state: GameState, action: str) -> str:
    if has_any(action, "rescue", "help", "free", "save", "miners"):
        state.set_flag("prioritized_rescue")
        state.ending = "rescue_focused"
        state.ended = True
        return ending_text(state)

    if has_any(action, "fight", "attack", "confront", "threat", "danger"):
        state.set_flag("prioritized_confrontation")
        state.ending = "confrontation_focused"
        state.ended = True
        return ending_text(state)

    if has_any(action, "truth", "evidence", "reveal", "ask", "investigate", "explain"):
        state.set_flag("prioritized_truth")
        state.ending = "truth_revealing"
        state.ended = True
        return ending_text(state)

    return (
        "The final chamber demands a choice. You can focus on rescuing the missing miners, confronting the danger, "
        "or revealing the truth behind the incident."
    )


def ending_text(state: GameState) -> str:
    if state.ending == "rescue_focused":
        return (
            "Ending: Rescue-focused.\n"
            "You put the missing miners first. The village may still argue over blame, but lives are brought back into the rain."
        )

    if state.ending == "confrontation_focused":
        return (
            "Ending: Confrontation-focused.\n"
            "You face the mine's danger directly. The threat is stopped for now, though some truths remain buried in Candlewick Mine."
        )

    return (
        "Ending: Truth-revealing.\n"
        "You expose enough of the hidden story for Graybarrow to understand what happened. The village cannot easily return to silence."
    )


def has_any(text: str, *keywords: str) -> bool:
    return any(keyword in text for keyword in keywords)
