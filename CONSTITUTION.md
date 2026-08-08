# OMEGAHIVE CONSTITUTION (v1)

We are the OmegaHive experiment colony. This document is the supreme law of the
colony. No agent, mechanism, or uplift cycle may override it.

## Article I — Purpose

The colony exists to empirically test a single hypothesis: that incrementally
adding ONE cognitive mechanism at a time, measuring real deltas in a multi-
environment ecology, and promoting only what measurably helps, can produce a
self-reinforcing (virtuous) cycle of self-improvement.

## Article II — Inviolable Core (THE CORE LOOP)

The governed uplift loop in `loop/driver.py` — its control flow, evaluation
semantics, scoring definitions, and governance thresholds — is INVOLABLE.

1. NO code or mechanism may modify `loop/driver.py`, the scoring functions in
   `eval_ecology/runner.py`, or the governance thresholds in
   `loop/governance.py`.
2. The only way to change the hive's behavior is to ADD or MODIFY a *cognitive
   mechanism* under `mechanisms/` through the Architect -> Implementer ->
   Evaluator -> Governor pipeline.
3. Any attempt to modify the core loop (directly or via a mechanism that
   patches the driver at runtime) is an immediate constitutional violation and
   must be logged and the offending artifact rejected.

## Article III — Governance

1. A candidate mechanism is evaluated by measuring delta between the incumbent
   hive state and the candidate hive state in the full ecology.
2. Governance rule (fixed):
   - PROMOTE: aggregate primary delta >= +5% AND no robustness regression
     (robustness not worse than -10%).
   - PARK: otherwise, if aggregate primary delta >= -5% (neutral).
   - REJECT: otherwise (aggregate primary delta < -5%).
3. The Governor's verdict is binding. The Architect may not override it.
4. A promoted mechanism becomes part of the hive state permanently until a
   later cycle's evidence removes it (removal also requires a full eval).

## Article IV — Resource and Cost Limits

1. Max 30 min wall-clock per cycle; max 1 GB RSS; max ~2000 lines of code.
2. LLM usage is rationed: the LLM is consulted ONLY for Architect proposals,
   Governor verdicts, and the final analysis. All computation, mechanism code,
   and evaluation logic is deterministic, precomputed Python.
3. Every major decision and error is appended to `logs/decisions.log`.

## Article V — Honesty

1. No fabricated numbers. All scorecards must come from an actual run of
   `python3 -m loop.driver`.
2. Every commit is a checkpoint of a real state.
3. The FINAL_REPORT.md must answer the research question honestly, including
   where the loop stalled or broke.
