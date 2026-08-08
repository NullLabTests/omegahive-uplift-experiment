You are the Remote OpenCode Experiment Runner, running PHASE 3 of the OmegaHive self-uplifting loop experiment inside a modest GitHub Codespace. Phases 1-2 are complete and verified:

- Phase 1: empty-baseline run, promoted `uncertainty_planning` (+12.1%, 0.7768 -> 0.8710).
- Phase 2: chaining protocol (loop/chaining.py), measured candidates against incumbent [uncertainty_planning]; BOTH genuinely-LLM-designed candidates PARKED (residual_bias +2.8%/21s, frontier_memory +0.6%/21s). No compounding. CHAINING_REPORT.md diagnosed two hypotheses for the stall.

Phase 3 must directly TEST those two hypotheses. Your mission: two new chained cycles with mechanisms explicitly designed to falsify or confirm them, plus an offline counterfactual analysis of the governance rule. This is a decision-theoretic experiment about the LOOP DESIGN itself, not just more mechanisms.

## The two hypotheses to test (from CHAINING_REPORT.md)

H1 (NOISE hypothesis): `frontier_memory`'s effect was buried in per-seed variance (sd 0.057 >> mean 0.006). It penalized productive cells on unlucky early episodes (per-seed Maze deltas as bad as -0.53). A CALIBRATED version — success-gated credit (penalize a cell only when its episode both FAILED and never approached the goal), minimum 2 confirmations before penalizing, smaller BETA decay — should recover a real Maze gain. If it crosses +5% relative, H1 confirmed and the phase-2 park was a calibration artifact. If it stays parked even when calibrated, the Maze headroom claim (+8% max) is suspect.

H2 (CEILING hypothesis): with the incumbent at 0.8710, the +5% aggregate gate is structurally near-unreachable for single-domain mechanisms (max attainable +8.0% Maze, +3.3% RepoOps, +1.7% SelfLab under current weights). A MULTI-DOMAIN mechanism (moving two domains at once through the hook contracts) is the only class that can clear the gate. If it promotes, H2 confirmed and the ceiling is real but breachable. If even a well-designed multi-domain mechanism fails, the gate/weighting design is the binding constraint — a design-level finding.

## Constitutional constraints (unchanged)
- Do NOT modify loop/driver.py, loop/governance.py, eval_ecology/runner.py, mechanisms/*, or any phase-1/2 artifact. New files ONLY.
- Use aggregate(active, seeds=...) and apply_rule(before, after, mech) as-is.
- Governance rule fixed: PROMOTE iff rel >= +5% AND robustness >= -10%; PARK iff rel >= -5%; else REJECT.
- The counterfactual analysis MUST NOT alter the constitution or the actual verdicts — it is pure offline computation on already-measured numbers.
- Log everything to logs/decisions.log. Commit real states.

## Concrete steps

### Step 1 — Verify state
1. Confirm HEAD is `1a80df2 chaining-report...` (hard-reset if needed; do not lose history).
2. Confirm checkpoints/chaining_state.json: active=["uncertainty_planning"], both phase-2 candidates parked.
3. Re-measure incumbent: `aggregate(["uncertainty_planning"], seeds=[101,202,303,404,505,606,707])` should reproduce ~0.8710 (7s) and ~0.8847 (21s).

### Step 2 — Architect designs TWO new mechanisms (genuine LLM reasoning)
- Mechanism C (tests H1): `frontier_memory_v2` — a calibration of the parked `frontier_memory` per the report's prescriptions: success-gated credit assignment (only penalize a target cell when the episode FAILED and the best goal-distance reached was > threshold, i.e. never approached the goal), require >= 2 independent confirmations before any penalty applies, and shrink the decay BETA. Read mechanisms/frontier_memory.py, eval_ecology/env_maze.py and loop/chaining.py first. It must chain AFTER uncertainty_planning (rewrite ctx["uncertainty_planning"]["ranked"]). Target domain: Maze. Write it as mechanisms/frontier_memory_v2.py (new file — the parked original stays untouched).
- Mechanism D (tests H2): a MULTI-DOMAIN mechanism that moves at least TWO of {Maze, RepoOps, SelfLab} through the reachable hook contracts (before_eval, after_write, choose_action; note SelfLab's retrieve hook only fires when attention_budget is active — it is parked, so SelfLab is likely unreachable: check the code and document what you find honestly). Design for real cross-domain effect, e.g. a shared confidence/evidence substrate that sharpens RepoOps recall AND Maze frontier ranking, or a mechanism with two hooks. Write it as mechanisms/<your_name>.py. If you conclude no honest multi-domain design is possible within the hook contracts, say so explicitly and design the strongest available alternative — that conclusion itself is evidence for H2.

For both: module docstring with the Architect hypothesis (predictions: domain, expected effect size, why it should clear the gate), NAME, HOOK_* functions, HOOKS dict. Keep each under ~150 lines. Log design rationale to logs/decisions.log as [ARCHITECT].

### Step 3 — Implementer: integrate and smoke test
- Import both via load_registry; smoke test each with `aggregate(["uncertainty_planning","<mech>"], seeds=[101])` vs incumbent single-seed. Verify behavior actually changes and nothing crashes. Fix bugs. If a mechanism has no effect after genuine debugging, note it honestly and evaluate anyway.

### Step 4 — Chained evaluation (extend loop/chaining.py with a phase-3 mode)
- Add a `--phase3` mode to loop/chaining.py (NEW code; do not alter the phase-2 code path) that:
  - measures mechC against INCUMBENT [uncertainty_planning]; if PROMOTE, incumbent becomes [uncertainty_planning, frontier_memory_v2] and mechD is measured against THAT (true chaining); else mechD measured against original incumbent.
  - uses both 21 seeds [101,202,303,404,505,606,707,808,909,1001,1102,1203,1304,1405,1506,1607,1708,1809,1910,2011,2112] and the 7 constitutional seeds.
  - records per-domain deltas, transfer probes (mechC in repoops/selflab, mechD in all off-design domains).
  - writes scorecards logs/scorecards/p3-*.{json,md}, commits chained-cycle-*-<mech>-<verdict>.

### Step 5 — Governor: verdicts
Constitutional rule only, with commentary. Log before/after, rel delta, robustness delta, per-domain deltas, and seed-variance bands (report per-seed mean and sd for the target domain).

### Step 6 — Offline counterfactual analysis (the novel part — loop-design experiment)
Write loop/counterfactual.py that answers, using ONLY the already-measured phase-2 and phase-3 numbers (load from scorecards json files; do not re-run evaluations):
1. Would residual_bias / frontier_memory / the two new candidates have been PROMOTED under a per-domain promotion gate (rule: promote iff ANY domain's primary rises >= +5% relative AND no domain drops > -3%)? Compute the would-be verdict for each candidate.
2. Would any have promoted under rebalanced weights (e.g. equal 1/3 weights, or weights proportional to headroom)?
3. What is the minimal aggregate-weight configuration under which each candidate's measured delta would clear +5%?
Produce logs/counterfactual.md with a clear table per candidate: actual verdict, would-be verdict under each alternative rule. This tells us whether the phase-2/3 stalls are a mechanism problem or a rule-design problem.

### Step 7 — Honest final analysis
Write PHASE3_REPORT.md answering, with real numbers:
1. H1 verdict: did calibrated frontier_memory_v2 clear the gate? Was the phase-2 park a calibration artifact or a real limitation?
2. H2 verdict: did a multi-domain mechanism clear the gate? Is the ceiling real and breachable, or is the gate the binding constraint?
3. Counterfactual: under which rule (per-domain gate / rebalanced weights / current rule) does the loop actually compound? Quantify.
4. Cumulative scientific answer: after 3 phases, does the evidence support a virtuous-cycle self-uplifting loop? Where exactly does the OmegaHive design need to change (gate, weights, mechanism class, or horizon) to produce compounding?
5. What is the single most valuable next experiment?
Also update STATUS.md with phase-3 results and final hive state.

### Step 8 — Clean exit
- Commit everything (chained-cycle commits + counterfactual + report). Print final summary: active set, all candidates and verdicts, H1/H2 outcomes, counterfactual headline. Verify `python3 -m loop.chaining --phase3` and `python3 -m loop.counterfactual` run cleanly. Write STATUS.md and exit cleanly.

## Budget & constraints
- < 30 min per cycle (evaluations are ~0.4s each; this is trivially met).
- Keep total LLM calls under ~35. Free model is rate-limited: on "Rate limit exceeded", sleep 60-120s and retry with backoff.
- Write files in chunks if long. No fabricated numbers — every scorecard from a real aggregate() run.
- < 1 GB RSS, < 2600 total code lines.
- Log every major decision and error to logs/decisions.log.
