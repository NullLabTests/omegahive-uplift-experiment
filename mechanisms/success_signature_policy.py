"""Strategy mechanism (phase 6): SUCCESS-SIGNATURE POLICY — the in-band proposal
machinery.

Hypothesis (H-VC, machinery-level): once the proposal strategy is itself a
mechanism occupying the in-band `propose` hook, the history that flows into the
next proposal (headroom map, promotion signatures, overlap table, proposal log)
makes the next proposed mechanism measurably better, and after a strategy
promotion proposal quality continues to rise (Goertzel's loop). H-LIN predicts
flat proposal quality in expectation: the additive regime holds even with
in-band machinery.

Design: this mechanism registers handlers ONLY on the new `propose` hook. It has
NO task-hook handlers (no before_eval / choose_action / after_write / retrieve),
so by construction its task impact is zero; its only output is a PROPOSAL MEMO,
the ONLY channel from history to the next proposed mechanism. Audit:
`set(success_signature_policy.HOOKS) == {"propose"}`.

Memo (structured guidance for the next proposal):
  (a) target_domain         highest remaining headroom weighted by aggregate weight
  (b) hook_class_constraint hook-class NOT in the overlap table's covered set
  (c) parameterization      success-gated, >=2 confirmations (the phase-3
                            calibration that worked), recommended only when the
                            proposal log shows the probe class's credit was
                            noise-dominated; naive config otherwise
  (d) failure_signatures    top-2 failure signatures to avoid (from the log)

When the proposal-state history is PERMUTED (randomization-control condition,
arm 2), the associations this policy reads are scrambled, so the memo keeps the
same format but mis-attributes the success/noise signals.

NAME / HOOKS registered for auto-discovery by hive.hooks.load_registry.
"""

from __future__ import annotations

NAME = "success_signature_policy"

TASK_HOOKS = ("before_eval", "choose_action", "after_write", "retrieve")
FRONTIER_CLASS = ("frontier_memory", "frontier_memory_v2", "frontier_memory_v3")
PROBE_CLASS = "choose_action"
PROBE_DOMAIN = "maze"

NAIVE_PARAMETERIZATION = {
    "success_gated": False,
    "min_confirmations": 1,
    "beta": 0.10,
    "penalty": 1.0,
    "reward": -0.8,
    "approach": 4,
    "decay": 0.5,
    "rationale": "history carries no noise signal for the probe class; naive "
                 "single-episode config (the phase-2 frontier_memory design)",
}

CALIBRATED_PARAMETERIZATION = {
    "success_gated": True,
    "min_confirmations": 2,
    "beta": 0.03,
    "penalty": 1.0,
    "reward": -0.8,
    "approach": 4,
    "decay": 0.5,
    "rationale": "history shows noise-dominated frontier credit; use the "
                 "phase-3 success-gated >=2-confirmations calibration that "
                 "worked",
}


def _weighted_remaining_headroom(state: dict) -> dict:
    out = {}
    for domain, info in state.get("headroom", {}).items():
        out[domain] = info.get("remaining_headroom", 0.0) * info.get("weight", 0.0)
    return out


def _covered_hook_classes(state: dict) -> set:
    covered = set()
    for _mech, classes in state.get("overlap_table", {}).items():
        covered.update(c for c in classes if c != "propose")
    return covered


def _noise_signal(state: dict) -> bool:
    """Probe-class noise signal from the proposal log (honest attribution)."""
    log = state.get("proposal_log", [])
    entries = [e for e in log
               if e.get("mechanism") in FRONTIER_CLASS
               and e.get("target_domain") == PROBE_DOMAIN
               and e.get("hook_class") == PROBE_CLASS]
    if not entries:
        return False
    for e in entries:
        sd = e.get("maze_delta_sd") or 0.0
        mean = e.get("maze_delta_mean") or 0.0
        if sd > 1.5 * abs(mean):
            return True
        neg = e.get("negative_seeds")
        if neg is not None and e.get("count") and neg / e["count"] > 0.25:
            return True
    return False


def HOOK_propose(ctx, proposal_state):
    """Emit the proposal memo from the proposal-state history."""
    state = proposal_state or {}
    memo = {}

    w_hr = _weighted_remaining_headroom(state)
    if w_hr:
        memo["target_domain"] = max(w_hr, key=lambda d: w_hr[d])
    else:
        memo["target_domain"] = None

    covered_all = _covered_hook_classes(state)
    uncovered_all = sorted(set(TASK_HOOKS) - covered_all)
    memo["hook_class_constraint"] = (
        uncovered_all if uncovered_all
        else ["propose (machinery) — the only hook-class not claimed by any "
              "known task mechanism"])

    covered_active = set()
    for mech in state.get("active_hive", []):
        covered_active.update(state.get("overlap_table", {}).get(mech, []))
    memo["least_covered_task_classes"] = sorted(set(TASK_HOOKS) - covered_active)

    if _noise_signal(state):
        memo["parameterization"] = dict(CALIBRATED_PARAMETERIZATION)
    else:
        memo["parameterization"] = dict(NAIVE_PARAMETERIZATION)

    ranked = sorted(state.get("proposal_log", []),
                    key=lambda e: e.get("aggregate_delta", 0.0))
    memo["failure_signatures"] = [
        {
            "signature": f"{e.get('mechanism')} failed in "
                         f"{e.get('target_domain')}/{e.get('hook_class')} "
                         f"(agg delta {e.get('aggregate_delta'):+.4f}, "
                         f"sd {e.get('maze_delta_sd')}): "
                         f"{e.get('failure_signature')}",
            "mechanism": e.get("mechanism"),
            "aggregate_delta": e.get("aggregate_delta"),
        }
        for e in ranked[:2]
    ]

    ctx[NAME]["memo"] = memo
    return ctx


HOOKS = {
    "propose": HOOK_propose,
}
