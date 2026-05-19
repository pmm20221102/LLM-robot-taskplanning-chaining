# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

Local LLM task planner for hospital robot navigation. Converts natural-language instructions + scene graph JSON into structured `TaskPlan` JSON using Ollama (mistral / gemma4:e4b) with Pydantic schema enforcement.

## Running

```bash
# Start Ollama (must be running before main.py)
ollama serve

# Run the planner
python main.py
```

No build system, no tests, no linting configured. Python 3.13+, dependencies: `ollama`, `pydantic`, `pyyaml`.

## Architecture

The pipeline in `main.py` `call_llm_task_planner()`:

1. **Subgraph extraction** (`extract_relevant_subgraph`) — filters the full scene graph down to entities mentioned in the user instruction, builds a `llm_grounding_index` mapping aliases to canonical IDs.
2. **LLM call** (`run_llm_once`) — sends system prompt + relevant subgraph to Ollama with `TaskPlan` JSON schema as the format constraint.
3. **JSON cleanup** (`extract_json_object`) — strips markdown fences, extracts first valid JSON object.
4. **Schema validation** — `TaskPlan.model_validate_json()`.
5. **Canonicalization** (`canonicalize_task_plan`) — maps any alias target_ids back to exact scene graph IDs via the grounding index.
6. **Semantic validation** (`validate_task_plan_semantics`) — checks step sequencing, executor correctness, grounding, screening/transfer/avoid requirements.
7. **Repair loop** — up to 2 attempts; if validation fails, `build_repair_prompt` sends errors back to the LLM.
8. **Rule-based fallback** (`build_rule_based_transfer_plan`) — deterministic plan for "bring patient from A to B" patterns when LLM fails.

## Key Files

- `config.yaml` — model selection (`models:` with `default: true`) and Ollama `options:` (temperature, num_ctx, etc.)
- `schema.py` — Pydantic models: `TaskPlan`, `TaskStep`, `Constraints`, and Literal type aliases (`AllowedAction`, `AllowedStatus`, etc.)
- `prompt.py` — `SYSTEM_PROMPT`, `build_user_prompt()`, `build_repair_prompt()`. The system prompt contains executor rules, grounding rules, task decomposition rules, and a full good/bad example.
- `scene_graph.json` — multi-floor hospital scene graph input (entities + relations)
- `task_plan_output.json` — last run output

## Conventions

- `target_id` values must match exact scene graph entity IDs or `llm_grounding_index` values — never aliases like `R105` or `A_PATIENT_01`.
- Executor is deterministic per action: `locate_entity` → `scene_graph`, navigation actions → `nav2`, workflow actions → `external_workflow`, etc. (defined in `EXECUTOR_RULES` dict in main.py).
- `task_chain` max 6 steps. Transfer tasks always follow: locate → navigate_to source → escort_to destination → (optional) trigger_workflow.
- Entity scoring uses `normalize_text` (lowercased, non-alphanumeric → space) and `compact_text` (all non-alphanumeric removed) for alias matching.
