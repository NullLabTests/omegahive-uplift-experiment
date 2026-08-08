# STATUS — OmegaHive governed self-uplifting loop (phase 2: chaining complete)

## Phase-1 result (verified)
Aggregate primary **0.7768 -> 0.8710 (+12.1%)** from the empty baseline. Promoted
`uncertainty_planning`; parked `memory_consolidation` and `attention_budget`.

| cycle | mechanism | before -> after | verdict |
|---|---|---|---|
| 1 | memory_consolidation | 0.7768 -> 0.8081 (+4.0%) | PARK |
| 2 | attention_budget | 0.7768 -> 0.7983 (+2.8%) | PARK |
| 3 | uncertainty_planning | 0.7768 -> 0.8710 (+12.1%) | PROMOTE |

## Phase-2 result (chaining)
Every candidate was measured against the **current incumbent** `["uncertainty_planning"]`
(not the empty baseline) on 21 seeds, with the 7 constitutional seeds re-run for comparability.
Two genuinely LLM-designed mechanisms were evaluated: `residual_bias` (RepoOps) and
`frontier_memory` (Maze). **Neither was promoted.**

| chained cycle | mechanism | 21-seed before -> after | rel | 7-seed rel | verdict |
|---|---|---|---|---|---|
| 1 | residual_bias | 0.8847 -> 0.9097 | +2.8% | +4.3% | PARK |
| 2 | frontier_memory | 0.8847 -> 0.8903 | +0.6% | +1.2% | PARK |

- `residual_bias`: RepoOps primary 0.9167 -> 0.9881 (never negative on any of 21 seeds);
  parked due to the structural RepoOps weight ceiling (+3.3% max possible via repoops alone).
- `frontier_memory`: Maze primary 0.8229 -> 0.8370 but per-seed sd 0.057 >> mean 0.006;
  parked as noise-level.
- Transfer probes were exactly 0.0000 in off-design domains (perfect isolation).
- **Compounding did NOT occur** (no second PROMOTE); hive state unchanged.

## Final hive state
`checkpoints/hive_state.json` -> `{"active": ["uncertainty_planning"],
"promoted": ["uncertainty_planning"], "parked": ["memory_consolidation","attention_budget",
"residual_bias","frontier_memory"], "rejected": []}`

Chaining state (incumbent + baselines + verdicts): `checkpoints/chaining_state.json`.

## One-command re-runs (from /home/codespace/omegahive-experiment)
```bash
python3 -m loop.chaining                # full chaining protocol (baseline + cycle-1 + cycle-2)
python3 -m loop.chaining --candidate A  # single candidate
./scripts/run.sh run            # phase-1 driver from scratch (baseline + 3 cycles)
./scripts/run.sh state          # show hive state
```

## Artifacts
- Scorecards: `logs/scorecards/chained-baseline.*`, `logs/scorecards/chained-cycle-1-residual_bias.{json,md}`,
  `logs/scorecards/chained-cycle-2-frontier_memory.{json,md}`
- Mechanisms: `mechanisms/residual_bias.py`, `mechanisms/frontier_memory.py`; protocol: `loop/chaining.py`
- Decisions: `logs/decisions.log`; analysis: `CHAINING_REPORT.md`
- Git history: phase-1 (`baseline`, `cycle-N-...`) preserved; phase-2 adds
  `chained-baseline`, `chained-cycle-1-residual_bias-park`, `chained-cycle-2-frontier_memory-park`, `chaining-report`.

## Constraints honored
No core file modified (driver/governance/runner/envs/mechanisms untouched; only NEW files added);
pure stdlib; ~3.5 s per full chaining run; well under 1 GB RSS and 2400 code lines.

## Exit
Phase-2 experiment complete. Clean exit.
