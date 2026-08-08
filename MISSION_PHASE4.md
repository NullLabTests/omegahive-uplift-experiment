You are the Remote OpenCode Experiment Runner, running PHASE 4 of the OmegaHive self-uplifting loop experiment. Phases 1-3 are complete and published publicly. Phase 3's offline counterfactual produced a CRISP FALSIFIABLE PREDICTION that Phase 4 must now test with a real run:

**The prediction (from logs/counterfactual.md):** under a per-domain promotion gate (PROMOTE iff ANY domain's primary rises >= +5% relative AND no domain drops > -3%), `residual_bias` and `evidence_substrate` would BOTH PROMOTE. If promoted in sequence (residual_bias first, then evidence_substrate measured against the grown incumbent), the loop would produce its FIRST genuine compounding event — the second-order improvement phase 1-3 never saw.

## Mission: test that prediction with real measurements

### Context (verified state)
- HEAD: aa7e2ae. Active: ["uncertainty_planning"]. Parked: residual_bias, frontier_memory, frontier_memory_v2, evidence_substrate, memory_consolidation, attention_budget.
- Incumbent 21-seed aggregate primary: ~0.8847 (7-seed: ~0.8710).
- All previous evaluations were measured under the CONSTITUTIONAL gate (loop/governance.py). Phase 4 must NOT modify that file.

### Constitutional constraints
- Do NOT modify loop/driver.py, loop/governance.py, eval_ecology/runner.py, mechanisms/*, loop/chaining.py, or loop/counterfactual.py.
- Add NEW files only. The per-domain gate is a NEW experimental rule in a NEW file (loop/gate_perdomain.py) — it is an EXPERIMENTAL VARIANT, explicitly documented as not constitutional.
- Every scorecard from a real aggregate() run. Log to logs/decisions.log. Commit real states.

### Concrete steps

1. Verify state: HEAD aa7e2ae, incumbent reproduces (~0.8847 on 21 seeds). Check the existing scorecards exist (chained-cycle-1-residual_bias.json, p3-cycle-4-evidence_substrate.json) — Phase 4 re-measures them with fresh runs rather than trusting the files.

2. Create loop/gate_perdomain.py with the experimental rule:
   - PROMOTE iff ANY domain primary (maze, repoops, selflab) rises >= +5% RELATIVE to its before value AND no domain primary drops > -3% relative.
   - PARK otherwise if aggregate >= -5%; REJECT if aggregate < -5%.
   - Must return a verdict dict shaped like loop/governance.apply_rule's (mechanism, verdict, before/after primaries, deltas, rule description).

3. Create loop/chain_perdomain.py — a new protocol driver:
   - baseline: aggregate(INCUMBENT=["uncertainty_planning"], 21 seeds) + 7-seed run.
   - Cycle A: measure residual_bias against incumbent, verdict with per-domain gate. If PROMOTE: incumbent += residual_bias. Else: incumbent unchanged.
   - Cycle B: measure evidence_substrate against the (possibly grown) incumbent, verdict with per-domain gate. If PROMOTE: incumbent += evidence_substrate.
   - Also report the AGGREGATE primary at each stage (the compounding story: does total aggregate rise with each promotion?).
   - Write scorecards logs/scorecards/p4-*.{json,md}, git commits: p4-baseline, p4-cycle-A-<mech>-<verdict>, p4-cycle-B-<mech>-<verdict>.
   - If BOTH promote: also measure the final hive [uncertainty_planning, residual_bias, evidence_substrate] on 21 seeds and log the aggregate — that number is the headline: total gain from baseline 0.8847.

4. Governor commentary per cycle (honest): did the per-domain gate produce a promotion? Is the within-domain delta seed-stable (report per-seed mean/sd for the promoted domain)? Any domain regression?

5. Write PHASE4_REPORT.md answering:
   1. Prediction verdict: did residual_bias and evidence_substrate BOTH promote under the per-domain gate? (CONFIRMED / PARTIAL / REFUTED)
   2. Did the sequential chaining produce compounding — i.e., is final aggregate > 0.8847 + individual gains (multiplicative/compounding) or just additive? Give the real final aggregate number.
   3. What does this say about the counterfactual's central claim (rule-design, not mechanism-design, is the binding constraint)?
   4. Honest caveats: is the per-domain gate gameable (does it reward cherry-picking a single easy domain)? Does it create robustness risk the aggregate gate was protecting against?
   5. The cumulative 4-phase answer to Goertzel's virtuous-cycle hypothesis — and the single most valuable next experiment.
   Update STATUS.md with phase-4 results and final hive state.

6. Clean exit: verify `python3 -m loop.chain_perdomain` runs cleanly, commit everything, print final summary (final active set, total aggregate gain, prediction verdict), write STATUS.md, exit cleanly.

## Budget
- < 30 min per cycle (realistically seconds). Keep LLM calls under ~25; on rate limits sleep 60-120s and retry.
- < 1 GB RSS. New code well under 2600 total lines.
- No fabricated numbers. Log every decision and error.
