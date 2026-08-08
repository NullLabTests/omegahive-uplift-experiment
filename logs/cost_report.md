# Cost Report

## Model
- Model: free `opencode/deepseek-v4-flash-free` (free tier, rate-limited)

## LLM usage policy (per MISSION.md)
- Cognitive mechanisms and eval environments are **hardcoded pure-Python** (no LLM calls).
- The governed loop runs headless: Architect proposals, Implementer loading, Evaluation, and
  Governor verdicts are deterministic code. **Zero LLM tokens are spent inside the loop.**
- LLM context was used only for authoring source files and these reports (not measured by the loop).

## Compute (measured, wall-clock)
| phase | wall-clock |
|---|---|
| baseline (cycle 0) | ~0.2 s |
| cycle 1 (memory_consolidation) | ~1.1 s |
| cycle 2 (attention_budget) | ~1.1 s |
| cycle 3 (uncertainty_planning) | ~1.0 s |
| total driver run | ~3.4 s |

Per ecology aggregate = 3 environments x 7 seeds = 21 eval runs; each env run is a single
deterministic Python episode (millisecond scale). Two aggregates (before/after) per cycle.

## Resource limits (enforced in loop/driver.py)
- Wall-clock per cycle: max 30 min (actual ~1 s).
- Address space: max 1024 MB via `RLIMIT_AS` (actual tens of MB).
- Codebase: max 2000 lines (actual 1507 lines).

## Storage
- `checkpoints/hive_state.json` — authoritative hive state.
- `logs/scorecards/*.{json,md}` — per-cycle scorecards.
- `logs/bus/cycle-*.jsonl` — inter-agent bus messages.
- `logs/decisions.log` — every architectural/governance decision.
- Git commits: `baseline`, `cycle-1-*-park`, `cycle-2-*-park`, `cycle-3-*-promote`.

## Git log (progressive changes)
```
0bbbc1e cycle-3-uncertainty_planning-promote
5c8103c cycle-2-attention_budget-park
964c3fb cycle-1-memory_consolidation-park
b2aad71 baseline: aggregate_primary=0.7768
83ccfed feat: governed uplift loop, hive core, mechanisms, ecology evals, run scripts
38269d3 update: execution directive
acf7d5d init: mission + config
```
