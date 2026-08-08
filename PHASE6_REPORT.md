# PHASE 6 REPORT — the second loop: is in-band proposal machinery compounding? (H-VC vs H-LIN)

**Protocol:** `python3 -m loop.chain_second_loop` (NEW files only:
`loop/chain_second_loop.py`, `loop/proposal_state.py`, `loop/gate_strategy.py`,
`mechanisms/success_signature_policy.py`, `mechanisms/frontier_memory_v3.py`,
`mechanisms/pocket_detector.py`). Every number below is from a REAL
`run_ecology()` measurement on the same 21 extended seeds
[101..2112] plus the 7 constitutional seeds as context. The core is untouched.

**Incumbent (phase-5 experimental state):** `[uncertainty_planning, residual_bias,
progress_thermostat]`, 21-seed aggregate primary **0.9480** (reproduced exactly).

**The setup that closes the phase-5 gap:** the improvement machinery previously sat
OUTSIDE the hive (`loop/architect.py` is static data — the loop never read its own
history into the next proposal). Phase 6 puts a strategy mechanism ON a new in-band
`propose` hook: `success_signature_policy` (zero task-hook handlers, audit-verified)
reads the proposal-state substrate (`checkpoints/p6_proposal_state.json` — headroom
map, promotion signatures, overlap table, proposal log) and emits a PROPOSAL MEMO.
That memo is the ONLY channel from history to the next proposed mechanism, and it is
handed to the oracle verbatim.

**The probe:** the SAME mechanism class `frontier_memory_v3` in all three arms, tuned
per-arm ONLY via the memo's parameterization section. Target domain = maze (the only
domain with real remaining headroom, 0.0812 = 1 − 0.9188, weight 0.40).

## Results (21 seeds, target-domain headroom 0.0812)

| arm | condition | memo | probe config | agg delta | Q (delta/headroom) | neg seeds | maze mean / sd |
|---|---|---|---|---|---|---|---|
| 0 | baseline | `{}` (empty) | naive (success_gated=F, min_conf=1, β=0.10) | −0.0327 | **−0.402803** | 15/21 | −0.0818 / 0.1697 |
| 1 | S active | real-history memo | calibrated (success_gated=T, min_conf=2, β=0.03) | −0.0260 | **−0.320221** | 16/21 | −0.0650 / 0.0677 |
| 2 | randomized | PERMUTED-history memo | naive fallback (success_gated=F, min_conf=1, β=0.10) | −0.0327 | **−0.402803** | 15/21 | −0.0818 / 0.1697 |

Strategy-gate conditions (`loop/gate_strategy.py`, EXPERIMENTAL, NOT constitutional):

| condition | result |
|---|---|
| Q1 ≥ 1.05·Q0 | **True** (−0.320 vs 1.05·−0.403 = −0.423) |
| Q1 ≥ 1.05·Q2 | **True** (−0.320 vs 1.05·−0.403 = −0.423) |
| no task-axis regression (neg1 ≤ neg0) | **False** (16 > 15) |
| memo attribution (matched per-seed Q1>Q2, strict majority) | **False** (wins 7, losses 7, ties 7) |
| **VERDICT** | **PARK** (Q1 ≥ 0.95·Q0 holds, so not REJECT) |

## 1. Did the in-band strategy improve proposal quality? → H-LIN supported (PARK)

Q1 (−0.320) is less harmful than both Q0 and Q2 (−0.403) on the aggregate
axis: the strategy's memo — which correctly read the proposal log's failure
signatures and recommended the phase-3 success-gated, ≥2-confirmation
calibration — tightened the probe's maze tail (sd 0.1697 → 0.0677) and
recovered ~21% of the probe's aggregate harm (−0.0327 → −0.0260). That is a
REAL informational benefit: machinery-level feedback works, and the arm-2
control proves it (see §3).

But proposal quality did NOT rise, and it did not even beat the baseline on the
robustness axis. The calibrated probe is still net-harmful (Q1 < 0), its
negative-seed count REGRESSED (16 vs 15), and the matched per-seed Q1-vs-Q2
comparison is exactly **7 wins / 7 losses / 7 ties** — perfectly symmetric, i.e.
the strategy's guidance beat the control on no strict majority of seeds. The
aggregate gain is a variance/tail effect, not a per-seed advantage.

The gate is deliberately strict and it did its job: **PARK.** The in-band
machinery produced no measured compounding. **H-LIN is supported: strategy
mechanisms are first-order — they remove an informational barrier (which config
hurts less) but not the capability barrier (a probe class with zero remaining
maze headroom cannot be turned positive by better guidance).**

## 2. Monotonicity cycle

**Not run.** The strategy PARKED, so the constitution-consistent path (promotion
first, then one additional task-mechanism cycle under S, `pocket_detector`) was
never reached. There is no second-cycle aggregate to report and no compounding
excess to compute; the loop did not promote a strategy, so proposal quality was
never given a second chance to rise.

## 3. Attribution control: what the permuted-memo arm did, and what it says

Arm 2 got a memo identical in format but built from a PERMUTED proposal state
(seed 2026: maze↔selflab and choose_action↔retrieve associations scrambled).
The permutation erased the noise signal for the maze/choose_action probe class,
so the strategy fell back to the NAIVE parameterization — arm 2's config is
bit-for-bit the arm-0 baseline config, and consequently **Q2 == Q0 == −0.402803
exactly.** The control did exactly what it must: scrambled attribution degraded
the strategy's guidance to the no-guidance default.

This is the honest lesson for mechanism-proposal measurement in general:
aggregate delta can be dominated by a few tail seeds (arm 1's advantage is
entirely variance reduction — its 21 per-seed deltas cluster tightly around
−0.026 while arm 0/2 carry −0.281 and −0.133 outliers), so the aggregate Q ratio
is necessary but not sufficient. The matched per-seed comparison is the
attribution test, and here it is symmetric. A proposal-quality metric that
reported "arm 1 improved Q by 20%" without the 7/7/7 matched result would have
over-claimed.

## 4. Cumulative five-phase + phase-6 verdict on the self-uplifting loop

- The loop self-improves and chains ADDITIVELY when candidates are
  non-overlapping (phases 1–5: baseline 0.7768 → final 0.9480, +22.0%).
- Phase 6 closes the feedback gap (proposal machinery now in-band) and measures
  the machinery's own output. The strategy mechanism reads real history and
  produces real, distinguishable guidance (arm 1 ≠ arm 2 by design). Yet the
  strongest measured outcome of that guidance is "less harm from a bad probe" —
  never positive proposal quality.
- **Strongest possible boundary statement so far:** even with machinery-level
  feedback, LLM-proposed mechanism gains are first-order. Goertzel's virtuous
  cycle remains unsupported at every level tested: no super-additive term
  (phase 5 excess exactly +0.0000), and no machinery-level compounding (phase 6).
- **Capability-ceiling caveat (stated explicitly, as required):** even a
  positive H-VC result here would be machinery-level compounding only. No
  mechanism modifies the LLM oracle's fixed capability; the strongest form of
  the self-uplifting claim — that the agent's proposing ability itself grows —
  is untested and untestable in this architecture, and phase 6 does not change
  that.

## 5. Single most valuable next experiment

The phase-6 probe class (`frontier_memory` lineage) has now failed three times
(phases 2, 3, and 6) and was pre-designated for this phase because it is the
only class with a known calibration history — i.e., it was chosen precisely so
the memo channel would have an informative signal to carry. That design was
right for validating the machinery, but it cannot test compounding: a probe with
zero positive headroom on its target domain cannot demonstrate that better
proposal quality compounds.

The decisive next experiment is the same second-loop protocol against a probe
class that HAS real headroom: a genuinely new **SelfLab** mechanism
(selflab 0.9386, weight 0.25, only reachable via the parked attention_budget —
no honest SelfLab mechanism exists yet), with `success_signature_policy` (or a
newer strategy) reading the same substrate. If in-band guidance can convert a
positive-headroom probe into a promotion, THEN the monotonicity cycle becomes
runnable and machinery-level compounding becomes testable. Until a probe can be
positive, the H-VC vs H-LIN question is answered only at the margin (H-LIN for
informational guidance), not at the capability level.

## Governor's audit

- **Zero task-hook handlers (import-level check, logged):**
  `set(success_signature_policy.HOOKS) == {"propose"}` → `True`. Registered
  hooks `["propose"]`; task impact zero by construction (no before_eval /
  choose_action / after_write / retrieve handler). Scorecard
  `logs/scorecards/p6-audit.json`.
- **Per-seed stats (21 seeds):** Q0 mean −0.0327 sd 0.0679; Q1 mean −0.0260 sd
  0.0271; Q2 mean −0.0327 sd 0.0679. Matched Q1-vs-Q2: 7 wins / 7 losses / 7
  ties (verified against the stored per-seed delta vectors).
- All probe measurements ran on the real `aggregate()`/`run_ecology()` path;
  probe config per arm came ONLY from the memo's parameterization section.
  The randomization control used a fixed seed (2026) and is deterministic.
- Logs: `logs/decisions.log` (PHASE 6, per-arm GOVERNOR/PROPOSAL entries,
  strategy-gate line, verdict). Commits: `p6-proposal-state`, `p6-arm0`,
  `p6-arm1`, `p6-arm2`, `p6-strategy-park`, `p6-final-state`.

## Final state

`checkpoints/p6_proposal_state.json`: three-arm measurement (Q0 = Q2 = −0.402803,
Q1 = −0.320221), strategy verdict **PARK**, proposal log entries 6–8. Hive state
unchanged: `[uncertainty_planning, residual_bias, progress_thermostat]` =
**0.9480**. Phase 6 is an experimental protocol, not a constitutional adoption.

## Exit

Phase-6 experiment complete. `python3 -m loop.chain_second_loop` exits cleanly
(0) and, on re-run, refuses to duplicate the arms (clean-exit guard: strategy
verdict already recorded → no re-measurement). Clean exit.
