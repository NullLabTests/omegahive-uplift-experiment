# STATUS — OmegaHive governed self-uplifting loop (phase 4: per-domain gate real-run complete)

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
**Neither was promoted; the loop did not compound a third time.**

| cycle | mechanism | test | 21-seed before -> after | rel | verdict |
|---|---|---|---|---|---|
| 3 | frontier_memory_v2 | H1 (calibration) | 0.8847 -> 0.8970 | +1.4% | PARK |
| 4 | evidence_substrate | H2 (multi-domain) | 0.8847 -> 0.9220 | +4.2% | PARK |

- H2 (CEILING) strong form refuted: even the largest honest gain on record parked
  because the +5% AGGREGATE gate is the binding constraint. Offline counterfactual
  concluded rule-design (not mechanism-design) was the constraint and predicted a
  per-domain gate would promote residual_bias AND evidence_substrate. See
  `logs/counterfactual.md`.

## Phase-4 result (real-run falsification of the per-domain gate prediction)

Experimental gate (NEW file `loop/gate_perdomain.py`, NOT constitutional):
PROMOTE iff ANY domain primary >= +5% rel AND no domain drops > -3% rel; else
PARK iff aggregate >= -5%; else REJECT. Every number from a real `aggregate()`
run (21 ext + 7 const seeds) under `python3 -m loop.chain_perdomain`.

| stage | hive measured | 21-seed primary | promoting domain (rel) | per-domain verdict | constitutional reference |
|---|---|---|---|---|---|
| baseline | [uncertainty_planning] | 0.8847 | — | — | — |
| Cycle A | + residual_bias | 0.9097 (+2.83%) | **repoops +7.79%** | **PROMOTE** | PARK |
| Cycle B | + evidence_substrate (vs [up, rb]) | 0.9220 (+1.35%) | maze +3.75% (< +5%) | **PARK** | PARK |
| final (diagnostic) | [up, rb, es] | **0.9220** (= es alone, = additive projection) | — | — | — |

- **Prediction verdict: PARTIAL.** residual_bias PROMOTED under the per-domain
  gate — the loop's first promotion since phase 1, confirming the weak form of the
  counterfactual (rule-design matters). But evidence_substrate did NOT promote
  against the grown incumbent (RepoOps already saturated by residual_bias; Maze
  only +3.75% rel), so the predicted two-step chain and first compounding event
  never happened.
- **Compounding: REFUTED.** Diagnostic final hive [up, rb, es] = 0.9220 exactly
  equals evidence_substrate single-shot AND the additive projection. residual_bias
  adds +0.0000 beyond evidence_substrate — the two are redundant RepoOps
  correctors. Total gain from baseline 0.8847 is +0.0373 (+4.2%), identical to the
  phase-3 single-shot. No multiplicative/compounding gain.
- **Governor commentary:** no domain primary regressed in either cycle; robustness
  improved both times. residual_bias repoops delta never negative (0/21 seeds, mean
  +0.0714 sd 0.0729) -> accepted. evidence_substrate maze delta not seed-stable
  (mean +0.0308 sd 0.1146, 5/21 negative) -> parked regardless of the +5% miss.
- **Caveats (honest):** the per-domain gate is gameable (rewards single-domain
  cherry-picking; promoted residual_bias at only +2.83% aggregate) and has no
  robustness clause (a mechanism could trade one domain's robustness for another's
  primary and still promote). This run stayed benign; the risk is structural.
- **4-phase answer to Goertzel's virtuous cycle:** the loop can self-improve one
  step at a time (phases 1 and 4), but no phase produced a second-order /
  compounding improvement. Gains are bounded by finite per-domain headroom plus
  candidate redundancy. Strong self-acceleration is NOT supported by the evidence.
- **Most valuable next experiment:** a maze-only mechanism designed against the
  post-residual_bias state (RepoOps saturated) targeting Maze/SelfLab headroom,
  chained under the per-domain gate, to test whether NON-overlapping candidates
  can beat the 0.9220 single-shot ceiling (compounding requires non-redundancy).

## Final hive state
Phase-4 experimental state (`checkpoints/p4_state.json`): active
`["uncertainty_planning", "residual_bias"]`, promoted `["residual_bias"]`, parked
`["evidence_substrate"]`. Aggregate primary **0.9097** (baseline 0.8847, +2.83%).
Constitutional `checkpoints/hive_state.json` unchanged: active
`["uncertainty_planning"]`, promoted `["uncertainty_planning"]`, parked
[memory_consolidation, attention_budget, residual_bias, frontier_memory,
frontier_memory_v2, evidence_substrate]. Phase 4 is an experimental protocol, not
a constitutional adoption.

## One-command re-runs (from /home/codespace/omegahive-experiment)
```bash
python3 -m loop.chain_perdomain    # phase-4 protocol (baseline + cycle A + cycle B + diagnostics)
python3 -m loop.chaining --phase3  # phase-3 protocol
python3 -m loop.counterfactual     # offline rule counterfactual
```

## Artifacts
- Scorecards: `logs/scorecards/p4-cycle-1-residual_bias-promote.{json,md}`,
  `logs/scorecards/p4-cycle-2-evidence_substrate-park.{json,md}`,
  `logs/scorecards/p4-diagnostic-final-hive.json`; report: `PHASE4_REPORT.md`
- Experimental gate: `loop/gate_perdomain.py`; protocol: `loop/chain_perdomain.py`
- Decisions: `logs/decisions.log`; state: `checkpoints/p4_state.json`
- Git history: `p4-baseline`, `p4-cycle-1-residual_bias-promote`,
  `p4-cycle-2-evidence_substrate-park`

## Constraints honored
No core file modified (driver/governance/runner/envs/mechanisms/chaining/
counterfactual untouched; only NEW files: gate_perdomain.py, chain_perdomain.py,
scorecards, report, state). Pure stdlib; full phase-4 protocol ~7 s; well under
1 GB RSS and 2600 code lines. Every scorecard number is from a real
`aggregate(...)` run; the diagnostic final-hive run is explicitly logged as
DIAGNOSTIC, not a verdict.

## Exit
Phase-4 experiment complete. Clean exit.
