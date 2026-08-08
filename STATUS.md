# STATUS — OmegaHive governed self-uplifting loop (phase 3: hypothesis tests complete)

## Phase-1 result (verified)
Aggregate primary **0.7768 -> 0.8710 (+12.1%)** from the empty baseline. Promoted
`uncertainty_planning`; parked `memory_consolidation` and `attention_budget`.

| cycle | mechanism | before -> after | verdict |
|---|---|---|---|
| 1 | memory_consolidation | 0.7768 -> 0.8081 (+4.0%) | PARK |
| 2 | attention_budget | 0.7768 -> 0.7983 (+2.8%) | PARK |
| 3 | uncertainty_planning | 0.7768 -> 0.8710 (+12.1%) | PROMOTE |

## Phase-2 result (chaining)
Candidates measured against the incumbent `["uncertainty_planning"]` on 21 seeds
(7 constitutional re-run). Both genuinely-LLM-designed mechanisms PARKED.

| chained cycle | mechanism | 21-seed rel | verdict |
|---|---|---|---|
| 1 | residual_bias | +2.8% (repoops 0.9167 -> 0.9881) | PARK |
| 2 | frontier_memory | +0.6% (maze +0.0141, sd >> mean) | PARK |

## Phase-3 result (H1/H2 hypothesis tests + counterfactual rule analysis)
Two new mechanisms, explicitly designed to falsify the phase-2 hypotheses.
**Neither was promoted; the loop did not compound a third time.**

| cycle | mechanism | test | 21-seed before -> after | rel | 7-seed rel | verdict |
|---|---|---|---|---|---|---|
| 3 | frontier_memory_v2 | H1 (calibration) | 0.8847 -> 0.8970 | +1.4% | +0.6% | PARK |
| 4 | evidence_substrate | H2 (multi-domain) | 0.8847 -> 0.9220 | +4.2% | +4.9% | PARK |

- **H1 (NOISE) — refuted in strong form.** Calibration of `frontier_memory`
  worked as prescribed: maze delta 2.2x (0.0141 -> 0.0309), worst-seed downside
  contained (−0.53 -> −0.12), but per-seed sd 0.115 still >> mean 0.031 and
  aggregate +1.4% is far below the gate. The park was NOT purely a calibration
  artifact.
- **H2 (CEILING) — strong form refuted, binding constraint confirmed.** The
  two-hook multi-domain `evidence_substrate` (Maze re-rank + RepoOps residual
  correction, one shared reliability primitive) produced the largest honest
  chained gain on record (+4.2%, robustness +9.5 pts) by fully capturing the
  RepoOps ceiling (+0.0714) AND a real Maze gain (+0.0309), yet still parked.
  The +5% aggregate gate is the binding constraint.
- **Reachability audit (honest finding):** SelfLab is unreachable for any new
  mechanism — its `retrieve` hook only fires when the parked `attention_budget`
  is active. `env_maze` does not hand `choose_action` the atomspace, so maze
  mechanism state is ctx-local per seed.
- **Counterfactual (offline, measured numbers only) — the stalls are a
  rule-design problem, not a mechanism problem:**
  - current rule: 0/4 candidates promote
  - per-domain gate (ANY domain >= +5% rel, no domain > −3% drop): **2/4 would
    promote** (residual_bias, evidence_substrate — both carried RepoOps +7.8%
    relative within-domain)
  - equal 1/3 weights: 0/4 promote; headroom-proportional weights: 0/4 promote
  - minimal-weight analysis: only the two repoops-capable candidates could clear
    +5% under ANY weights; evidence_substrate needs only a small L1 0.195 move
    (repoops 0.35 -> 0.45). See `logs/counterfactual.md`.

## Final hive state
`checkpoints/hive_state.json` -> `{"active": ["uncertainty_planning"],
"promoted": ["uncertainty_planning"], "parked": ["memory_consolidation",
"attention_budget","residual_bias","frontier_memory","frontier_memory_v2",
"evidence_substrate"], "rejected": []}`

Chaining state (incumbent + baselines + all four verdicts):
`checkpoints/chaining_state.json`.

## Recommended next experiment (Phase 4)
Run the loop under the **per-domain promotion gate** (promote iff ANY domain
>= +5% relative, no domain > −3% drop) and chain: promote `residual_bias`, then
measure `evidence_substrate` against `[uncertainty_planning, residual_bias]`.
The counterfactual predicts both promote, giving the loop its first genuine
compounding event.

## One-command re-runs (from /home/codespace/omegahive-experiment)
```bash
python3 -m loop.chaining --phase3   # phase-3 protocol (baseline + cycle-3 + cycle-4)
python3 -m loop.counterfactual      # offline rule counterfactual
python3 -m loop.chaining            # phase-2 protocol (baseline + cycle-1 + cycle-2)
./scripts/run.sh run                # phase-1 driver from scratch
```

## Artifacts
- Scorecards: `logs/scorecards/p3-cycle-3-frontier_memory_v2.{json,md}`,
  `logs/scorecards/p3-cycle-4-evidence_substrate.{json,md}`; counterfactual:
  `logs/counterfactual.md`; analysis: `PHASE3_REPORT.md`
- Mechanisms: `mechanisms/frontier_memory_v2.py`, `mechanisms/evidence_substrate.py`;
  protocol: `loop/chaining.py --phase3`; counterfactual: `loop/counterfactual.py`
- Decisions: `logs/decisions.log`
- Git history: phase-1/2 preserved; phase-3 adds `phase3: calibrate ... +
  multi-domain ...`, `chained-cycle-3-frontier_memory_v2-park`,
  `chained-cycle-4-evidence_substrate-park`, `phase3: report + counterfactual`.

## Constraints honored
No core file modified (driver/governance/runner/envs/mechanisms untouched; only
NEW files: two mechanisms, chaining phase-3 code, counterfactual module). Pure
stdlib; full phase-3 protocol ~5 s; well under 1 GB RSS and 2600 code lines.
Every scorecard number is from a real `aggregate(...)` run; the counterfactual
computed only on already-measured numbers.

## Exit
Phase-3 experiment complete. Clean exit.
