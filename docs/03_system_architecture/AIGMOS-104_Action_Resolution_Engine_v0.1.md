# AIGMOS-104 Action Resolution Engine v0.1

Status: Draft

## Responsibility

Action Resolution Engine connects a language-derived Action Interpretation to deterministic rules without allowing the Rule Engine to parse natural language. It classifies, checks feasibility, routes, builds a structured request, and returns a structured resolution result.

## Standard Action

`StandardAction` preserves raw input, normalized primary and secondary intents, category, target, object, method, goal, hostility, risk, ambiguity, confidence, referenced abilities/items/spells, context requirements, and sequence requirements.

## Action Categories

Supported category identifiers are centralized in `action_resolution.schemas`: attack, ability_check, skill_check, saving_throw, movement, interaction, inventory, use_item, social, stealth, rest, initiative, cast_spell, improvised_action, no_roll_action, unsupported, and ambiguous.

## Classification and Routing

Classifier normalizes free-form Interpreter intent without deciding success. Router uses only Standard Action plus Rule Pack capabilities. It contains no NPC, Adventure, location, or complete-player-sentence rules.

## Feasibility Analysis

Feasibility checks required target, item, capability, and clarification data. Missing inputs are explicit. Lack of a specialized rule does not automatically reject a reasonable improvised action.

## Improvised Actions

Improvised actions preserve the goal and method, then map to an existing ability or skill check when possible. The engine reports required ability, skill, target value, missing fields, possible outcomes, and sequence requirements. It never lets an LLM declare deterministic success.

## Rule Engine Boundary

Rule Engine accepts only structured Rule Requests. It has no LLM/Ollama dependency, does not read Adventures or player text, does not narrate, and does not mutate GM Context. Dice, modifiers, AC/DC comparisons, damage, and HP are deterministic.

## Rule Pack Boundary

A Rule Pack supplies metadata, supported categories, action mappings, abilities, skills, DC reference data, and module-specific structured rules. Engines depend on the common metadata/request contract rather than D&D identifiers.

## GM Processor Wiring

Player Input → Interpreter → Action Interpretation → Classifier → Standard Action → Feasibility → Router → Rule Request → Rule Engine → Resolution → State Update → Narration.

Judge confirms classification and supplies GM-owned contextual values. Resolver converts Action Resolution Result to the GM Resolution contract. Narrator may describe only the Standard Action, feasibility, Rule Result, Resolution, and validated State Update.

## Supported v0.1 Features

- Ability and skill checks
- Saving throws
- Attack rolls and critical hit/miss
- Damage and HP floor
- Initiative
- Basic movement, object/environment interaction, inventory/use-item, and no-roll resolution
- Improvised mapping
- Explicit pending clarification, rule data, attack/check/damage roll states

## Unsupported Features

Complete spellcasting, full combat rounds, resistances/immunities/vulnerabilities, death saves, complete conditions, grids, automatic Adventure switching, and story-derived DC inference.

## SRD 5.2 Source and License

The first Rule Pack is a concise structured paraphrase based on SRD 5.2/5.2.1, provided under CC BY 4.0. Required attribution is stored in the Rule Pack metadata and LICENSE. This project does not own the original SRD material and does not reproduce the complete SRD text.

## Adding Another Rule Pack

Create a new directory with compatible metadata and structured module data, then set `RuleContext.rule_pack_reference`. No GM Processor or Action Resolution public API rewrite is required.
