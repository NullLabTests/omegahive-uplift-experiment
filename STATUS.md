# STATUS — OmegaHive governed self-uplifting loop (phase 5: non-redundancy test complete)

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

## Phase-5 result (non-redundancy test: H-NR vs H-GATE)
Experimental per-domain gate again (NEW files only: `mechanisms/progress_thermostat.py`,
`loop/chain_perdomain2.py`, `checkpoints/p5_state.json`). A maze-only, within-episode
explore/exploit thermostat aimed at the UNCLAIMED Maze headroom, measured against
the grown incumbent [uncertainty_planning, residual_bias] on 21 + 7 seeds.

| stage | hive measured | 21-seed primary | agg rel | promoting domain (rel) | per-domain gate | constitutional reference |
|---|---|---|---|---|---|---|
| baseline | [up, residual_bias] | 0.9097 | — | — | — | — |
| cycle | + progress_thermostat | **0.9480** | +4.21% | **maze +11.65%** (0.8229->0.9188) | **PROMOTE** | PARK (+4.21%) |
| 7-seed re-run | + progress_thermostat | 0.9343 | +2.84% | maze +7.82% | PROMOTE | PARK |

- **Verdict: H-NR CONFIRMED, H-GATE REFUTED.** The non-overlapping mechanism
  cleared the per-domain gate against the grown incumbent (maze +11.65% rel, no
  domain dropped; robustness improved 0.5048->0.6381).
- **Headline: final hive [up, rb, progress_thermostat] 21-seed primary = 0.9480,
  beating the 0.9220 phase-4 single-shot ceiling by +0.0260 (+2.8%).**
- **Compounding: ADDITIVE, not super-additive.** base [up] 0.8847 + rb gain
  +0.0250 + pt gain +0.0383 = 0.9480 = final hive exactly; compounding excess
  +0.0000. The chain stacks non-overlapping gains linearly and beats any single
  shot (pt alone 0.9230 already > es 0.9220), but no multiplicative term exists.
- **Non-redundancy audit (21 seeds):** pt's maze gain is +0.0959 WITHOUT rb
  (C-A) and +0.0959 WITH rb (D-B) — identical, hence orthogonal on Maze; repoops
  delta +0.0000 and selflab delta +0.0000 — no overlap with residual_bias, audit
  not confounded.
- **Governor:** maze per-seed delta mean +0.0958, sd 0.1389 (sd > mean), 17/21
  positive, 3/21 negative (worst -0.108). Aggregate per-seed mean +0.0383, 3/21
  negative. Real but not Gaussian-stable; no domain regression on aggregate.
- **Cumulative 5-phase answer:** the loop self-improves and CHAINS additively
  when candidates are non-overlapping (RepoOps then Maze), and the chained hive
  beats the single-shot ceiling. Goertzel's strong super-additive self-amplification
  remains unsupported (excess exactly +0.0000). Additive self-assembler: YES;
  runaway virtuous cycle: no evidence.
- **Most valuable next experiment:** a SECOND maze mechanism orthogonal to BOTH
  up (stateless info-gain) and progress_thermostat (proximity objective-flip),
  e.g. within-episode dead-end topology memory, chained against [up, rb, pt] to
  test whether the additive stack saturates or keeps climbing.

## Final hive state
Phase-5 experimental state (`checkpoints/p5_state.json`): active
`["uncertainty_planning", "residual_bias", "progress_thermostat"]`, promoted
`["progress_thermostat"]`. Aggregate primary **0.9480** (from phase-4 incumbent
0.9097, +4.21%; from phase-1 baseline 0.7768: +22.0% cumulative). Constitutional
`checkpoints/hive_state.json` unchanged (phase-5 is an experimental protocol, not
a constitutional adoption).

## One-command re-runs (from /home/codespace/omegahive-experiment)
```bash
python3 -m loop.chain_perdomain2   # phase-5 protocol (baseline + cycle + audit + final hive)
python3 -m loop.chain_perdomain    # phase-4 protocol (baseline + cycle A + cycle B + diagnostics)
python3 -m loop.chaining --phase3  # phase-3 protocol
python3 -m loop.counterfactual     # offline rule counterfactual
```

## Artifacts
- Scorecards: `logs/scorecards/p5-cycle-progress_thermostat-promote.{json,md}`,
  `logs/scorecards/p5-audit-nonredundancy.{json,md}`; report: `PHASE5_REPORT.md`
- Experimental gate: `loop/gate_perdomain.py`; protocols: `loop/chain_perdomain.py`,
  `loop/chain_perdomain2.py`
- Mechanism: `mechanisms/progress_thermostat.py`
- Decisions: `logs/decisions.log`; state: `checkpoints/p5_state.json`
- Git history: `p5-baseline`, `p5-cycle-progress_thermostat-promote`,
  `p5-final-hive`

## Constraints honored
No core file modified (driver/governance/runner/envs/mechanisms/chaining/
counterfactual/gate_perdomain/chain_perdomain untouched; only NEW files:
progress_thermostat.py, chain_perdomain2.py, scorecards, report, state). Pure
stdlib; full phase-5 protocol ~10 s; well under 1 GB RSS and 2600 code lines.
Every scorecard number is from a real `aggregate(...)` run.

## Exit
Phase-5 experiment complete. Clean exit.
