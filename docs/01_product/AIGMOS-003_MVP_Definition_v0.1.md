# AIGMOS-003: MVP Definition

## Version

v0.1

## Status

Draft

## Purpose

Define what the first playable version of AIGMOS includes, excludes, and must prove before broader product or system expansion begins.

This document is a product specification. It does not define final game mechanics, technical implementation, or production rules content.

## MVP One-Sentence Definition

AIGMOS MVP is a solo, text-first AI TRPG experience where one player creates a simple character, enters one constrained fantasy adventure module, interacts with an AI Game Master through free text, receives rule-based outcomes, and can save/resume the session.

## Target First-Time Player Experience

A first-time player should be able to start AIGMOS, understand what kind of experience they are entering, create or choose one simple character, and begin a short fantasy adventure without needing a human Dungeon Master or prior setup.

The player should feel that:

- The AI Game Master understands the current scene.
- Their choices are remembered within the session.
- Their actions can change the immediate outcome of the adventure.
- The adventure has a clear enough goal to complete in one sitting.
- The session can be saved and resumed without losing important context.

TODO: Define the exact onboarding flow.

TODO: Define how much character creation is required before play begins.

TODO: Define the tone and reading level for first-time player-facing text.

## Included Features

The MVP includes only the following product capabilities:

- Single player only
- One player character
- One AI Game Master
- One short adventure module
- Free-text player input
- Basic dice / rule resolution
- Persistent session state
- Save and resume
- Text-only interface

TODO: Define the minimum viable character fields.

TODO: Define what "basic dice / rule resolution" means at MVP scope without committing to a final ruleset.

TODO: Define what data must be preserved in persistent session state.

## Excluded Features

The MVP explicitly excludes the following capabilities:

- Multiplayer
- Open world
- User-generated campaigns
- Full D&D ruleset
- Full class/spell system
- Voice
- Image generation
- Marketplace
- Monetization
- Mobile push notifications

The system should avoid implying that these excluded capabilities are available in the MVP.

TODO: Define how excluded features should be described, hidden, or deferred in the user experience.

## First Playable Session Scope

The first playable session should target a 30-60 minute experience.

Scope:

- One village
- One danger
- One dungeon or enclosed adventure location

Expected content:

- Investigation
- NPC interaction
- One small combat or danger scene
- One ending

Player goal:

- Complete a small adventure and feel that the AI Game Master remembered their choices.

TODO: Define the adventure module premise.

TODO: Define the minimum number of scenes required for the first playable session.

TODO: Define what counts as an ending for MVP validation.

## Success Criteria

The MVP is successful if:

- Player understands what to do within 3 minutes.
- Player can complete a session without human DM help.
- AI GM does not contradict known world state.
- Player choices visibly affect the session.
- Session can be saved and resumed.
- The system avoids pretending unfinished features exist.

TODO: Define how each success criterion will be tested.

TODO: Define what level of AI GM inconsistency is acceptable during early prototype testing.

## Risks

Known MVP risks include:

- The AI Game Master may contradict established session or world state.
- The first adventure may feel too narrow if constraints are not communicated well.
- Free-text input may create expectations beyond MVP scope.
- Basic rule resolution may feel unclear if outcomes are not explained consistently.
- Save/resume may fail to preserve the information players actually care about.
- Players may assume excluded features exist if the interface or language is too broad.

TODO: Define mitigation plans for high-priority risks.

TODO: Define which risks must be resolved before a public demo.

## Open Questions

- What is the exact fantasy premise of the first short adventure module?
- What character fields are required for the first playable session?
- What minimum rule resolution model is enough for MVP validation?
- How visible should dice rolls and rule outcomes be to the player?
- What session state must be remembered to make save/resume feel reliable?
- How should the AI Game Master handle player attempts outside the constrained adventure scope?
- What language should the product use to avoid promising excluded features?
- What internal review process decides when the MVP is ready for first external testers?
