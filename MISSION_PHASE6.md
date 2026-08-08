You are the Remote OpenCode Experiment Runner, running PHASE 6 of the OmegaHive self-uplifting loop experiment. Phases 1-5 are complete and published. Phase 5 confirmed H-NR: a provably non-overlapping mechanism (progress_thermostat) chained onto the grown hive and produced the best configuration ever measured — [uncertainty_planning, residual_bias, progress_thermostat] = 0.9480 on 21 seeds — beating the 0.9220 single-shot ceiling. But the compounding excess was EXACTLY +0.0000: gains accumulate additively, never super-additively.

The phase-5 report and post-experiment analysis identified WHY the strong (virtuous-cycle) claim fails in this architecture: **the improvement machinery sits outside the hive.** The Architect (`loop/architect.py`) is a static Python module — a fixed roster and rationale dict authored once. The hive's promoted mechanisms improve task performance but NEVER change the machinery that proposes mechanisms. There is no arrow from "better performance" to "better self-improvement." Phase 6 is the decisive test of whether closing that gap activates compounding. THIS IS YOUR MISSION:

**Build the Second Loop: an in-band proposal machinery, where the hive's own strategy mechanisms can modify the mechanism-proposal process — and measure, with a randomized-memo control arm, whether proposal quality then compounds.**

## The two competing hypotheses (Phase 6 must discriminate them)

- H-VC (virtuous cycle / machinery-level compounding): once the proposal strategy is itself a mechanism occupying an in-band hook, history (scorecards, promotion signatures, overlap table) that flows into the next proposal makes the next proposed mechanism measurably better — and after a strategy promotion, proposal quality continues to rise. First real evidence for Goertzel's loop.
- H-LIN (linear): strategy mechanisms are at best first-order — they remove an *informational* barrier but not the *capability* barrier (the LLM oracle's ceiling is fixed). Proposal quality is flat in expectation across cycles; the additive regime holds even with in-band machinery. This is the prior, based on phases 1-5.

**Either outcome is decisive and publishable.** H-VC gives the first evidence ever measured for the self-uplifting loop; H-LIN gives the strongest boundary statement: "even with machinery-level feedback, LLM-proposed mechanism gains are first-order."

## Context (verified state)

- Incumbent (phase-5 experimental state, checkpoints/p5_state.json): active ["uncertainty_planning", "residual_bias", "progress_thermostat"], 21-seed primary 0.9480. Constitutional state (checkpoints/hive_state.json) unchanged: active ["uncertainty_planning"].
- 21-seed diagnostics: maze 0.9188 (0.40 weight), repoops 0.9881 (0.35, saturated), selflab 0.9386 (0.25).
- Known mechanism landscape: up (maze choose_action info-gain planner), residual_bias (repoops after_write corrector), progress_thermostat (maze within-episode explore/exploit thermostat), frontier_memory/_v2 (maze choose_action credit transfer — noise-dominated, calibrated v2 measured +1.4% in phase 3).
- The proposal machinery is STATIC: `loop/architect.py` exports ROSTER and RATIONALE as fixed data; the LLM oracle authors mechanisms at design time but the loop never reads its own history into the next proposal. The hook pipe (`hive/hooks.py`) supports arbitrary hook names — a `propose` hook is a natural, constitutional-legal extension because mechanisms may register any hook; the loop just needs to invoke it.

## Constitutional constraints

- Do NOT modify loop/driver.py, loop/governance.py, eval_ecology/runner.py, mechanisms/*, loop/chaining.py, loop/counterfactual.py, loop/gate_perdomain.py, loop/chain_perdomain.py, or loop/chain_perdomain2.py.
- NEW files only. Phase 6 builds a new experimental protocol `loop/chain_second_loop.py` and a new experimental strategy gate `loop/gate_strategy.py` (both NEW files; neither is constitutional).
- The constitutional rule and constitution are NEVER touched. The strategy gate is explicitly experimental, like phase-4's per-domain gate.
- Every scorecard from a real aggregate() run. Log to logs/decisions.log. Commit real states.

## Concrete steps

1. Verify state: HEAD at phase-5 report commit; checkpoints/p5_state.json shows active ["uncertainty_planning","residual_bias","progress_thermostat"]; incumbent reproduces (~0.9480 on 21 seeds).

2. Build the proposal-state substrate (NEW file, e.g. `loop/proposal_state.py`): a JSON store (`checkpoints/p6_proposal_state.json`) maintained from real scorecards:
   - per-domain headroom map (max observed primary - current primary, per domain),
   - promotion signatures (per-domain relative deltas of every promoted mechanism, tagged by hook-class touched),
   - overlap table (hook-touch set per known mechanism — derive by importing each mechanism's HOOKS),
   - proposal log (every memo emitted + resulting mechanism delta).
   This store is THE channel by which history reaches future proposals. If a cycle runs without it, that is a baseline-condition arm, logged as such.

3. Architect — design ONE strategy mechanism, `success_signature_policy` (mechanisms/success_signature_policy.py):
   - It registers handlers ONLY on the new `propose` hook. It MUST have NO task-hook handlers (no before_eval/choose_action/after_write) — verify this in the audit. By construction its task impact is zero; its only output is a PROPOSAL MEMO.
   - The memo is structured guidance for the next proposal: (a) target domain = highest remaining headroom weighted by its aggregate weight; (b) hook-class constraint = pick a class NOT in the overlap table's covered set; (c) parameterization = success-gated, ≥2 confirmations (the phase-3 calibration that worked); (d) the top-2 failure signatures to avoid (from the proposal log).
   - Module docstring: hypothesis (H-VC mechanism), NAME, HOOKS. Under ~100 lines. Log design rationale to logs/decisions.log as [ARCHITECT].

4. Implement the second-loop protocol — create `loop/chain_second_loop.py` (NEW file):
   - `propose(condition)` runs: strategy mechanisms active in roster fire on the `propose` hook over the proposal state; the resulting memo (or an empty memo for the baseline condition) is logged and handed to the oracle as the ONLY channel from history to the next mechanism.
   - Three measurement arms, SAME probe mechanism class in all three (use the calibrated frontier-memory class, e.g. a frontier_memory_v3 tuned per-arm ONLY via the memo's parameterization section):
     - Arm 0 (baseline condition): empty memo. Measure probe delta Q0 against incumbent on 21 seeds.
     - Arm 1 (S active): memo from success_signature_policy. Measure probe delta Q1.
     - Arm 2 (randomization control — REQUIRED): memo identical in format but with the proposal-state history PERMUTED (shuffle domain↔hook-class associations). Measure probe delta Q2. This is the attribution control: Q1 must beat Q2 or the strategy's guidance is not the cause.
   - Normalize the metric: proposal quality Q = (probe 21-seed primary delta) / (target domain remaining headroom), reported as a fraction of headroom captured. This makes the metric comparable across domains and is the primary axis for strategy governance.
   - Verdict via `loop/gate_strategy.py` (NEW file): PROMOTE S iff Q1 >= 1.05*Q0 AND Q1 >= 1.05*Q2 AND no task-axis regression (probe negative-seed count not worse than arm 0) AND memo attribution holds (Q1 > Q2 on per-seed matched comparison). Otherwise PARK (if Q1 >= 0.95*Q0) or REJECT.
   - Write scorecards logs/scorecards/p6-*.{json,md}; commits: p6-arm0, p6-arm1, p6-arm2, p6-strategy-<verdict>.

5. If the strategy PROMOTES: run ONE additional task-mechanism cycle under S (a genuinely new Maze or SelfLab mechanism per S's memo — NOT the probe class), measure its 21-seed delta and aggregate impact vs 0.9480. This tests monotonicity: does proposal quality rise a second time? Report the second-cycle aggregate vs 0.9480 and vs the additive projection (incumbent + delta). Also compute the compounding excess exactly, as in phase 5.
   If the strategy PARKS or REJECTS: H-LIN is supported — document that in-band machinery produced no compounding, and say so plainly in the report.

6. Honest governor's audit:
   - Verify success_signature_policy has zero task-hook handlers (import-level check, log it).
   - Report per-seed mean/sd for Q0/Q1/Q2; matched per-seed Q1-vs-Q2 comparison (how many seeds favor Q1 — the attribution evidence).
   - Explicitly state the capability-ceiling caveat: even H-VC evidence would be machinery-level compounding; the LLM oracle's fixed capability is not modified by any mechanism, so the strongest form of the claim remains untested and untestable here. Say this in the report regardless of outcome.

7. Write PHASE6_REPORT.md answering, with real numbers:
   1. Did the in-band strategy mechanism improve proposal quality? Q1 vs Q0 vs Q2, with the matched-seed evidence. (H-VC vs H-LIN verdict)
   2. If promoted: the monotonicity cycle — second-cycle mechanism delta, final aggregate vs 0.9480, compounding excess (additive projection vs measured).
   3. The attribution control: did the permuted-memo arm do what it must? What does that say about mechanism-proposal measurement in general?
   4. The five-phase + phase-6 cumulative verdict on the self-uplifting loop, with the capability-ceiling caveat stated explicitly.
   5. The single most valuable next experiment (if any) — or the honest statement that the question is answered.
   Update STATUS.md with phase-6 results and final state.

8. Clean exit: verify `python3 -m loop.chain_second_loop` runs cleanly, commit everything, print final summary (H-VC vs H-LIN outcome, Q1/Q0/Q2, final aggregate if a promotion occurred), write STATUS.md, exit cleanly.

## Budget

- < 30 min per cycle (realistically seconds). Keep LLM calls under ~25; on rate limits sleep 60-120s and retry.
- < 1 GB RSS. New code well under 2600 total lines.
- No fabricated numbers. Log every decision and error. If an arm is skipped or fails, document it and proceed — never substitute a plausible number for a measured one.
