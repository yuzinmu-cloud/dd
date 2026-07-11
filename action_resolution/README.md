# Action Resolution Engine

Transforms an Interpreter-produced Action Interpretation into a rule-system-neutral `StandardAction`, analyzes feasibility, routes to a loaded Rule Pack, builds a structured request, and delegates deterministic calculation to `rule_engine`.

It never parses raw natural language in the Rule Engine and contains no NPC, Adventure, or location-specific rules. Improvised actions map to an existing generic check when possible; otherwise they return explicit missing fields or unsupported status.

`steal` is a distinct Standard Action Category and is never conflated with `stealth`. It routes to a skill check only after the holder/target and object are known. A missing object returns `pending_clarification` without invoking the Rule Engine.
