"""Probe mechanism (phase 6): frontier_memory_v3 — PARAMETERIZED frontier credit.

The probe mechanism class for the phase-6 second-loop experiment (H-VC vs
H-LIN). The SAME mechanism class runs in all three measurement arms; the ONLY
thing that varies between arms is its configuration, set via configure() from
the proposal memo's parameterization section (the only channel from history to
the next mechanism):

  - default (naive, "empty memo" / arm 0): reproduces the phase-2
    frontier_memory design that failed — single-episode penalization
    (success_gated=False, min_confirmations=1, beta=0.10) -> noise-dominated
    per-seed variance (sd 0.143 vs mean +0.014 in phase 2).
  - calibrated ("memo says success-gated, >=2 confirmations" / arm 1):
    reproduces the phase-3 calibration that worked (success_gated=True,
    min_confirmations=2, beta=0.03) -> small, reliable gain (+0.0123 aggregate
    in phase 3).

By construction its task impact is confined to the maze choose_action hook; it
has no before_eval / after_write / retrieve handlers (zero overlap with
memory_consolidation, residual_bias, attention_budget) and no propose hook.

NAME / HOOKS registered for auto-discovery by hive.hooks.load_registry.
"""

from __future__ import annotations

NAME = "frontier_memory_v3"

CFG = {
    "success_gated": False,
    "min_confirmations": 1,
    "beta": 0.10,
    "penalty": 1.0,
    "reward": -0.8,
    "approach": 4,
    "decay": 0.5,
}
START = (0, 0)


def configure(params: dict | None = None) -> dict:
    """Set probe parameters (ONLY from the proposal memo's parameterization)."""
    if params:
        for k, v in params.items():
            if k in CFG:
                CFG[k] = v
    return dict(CFG)


def _dist(pos, goal) -> float:
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])


def _refine(st, ranked):
    out = []
    for score, cell in ranked:
        w = st["weights"].get(cell, 0.0)
        out.append((score / (1.0 + CFG["beta"] * w), cell))
    return sorted(out, reverse=True)


def _credit_previous_episode(st) -> None:
    best = st.get("best_dist", 99.0)
    approached = best <= CFG["approach"]
    for cell in st.get("ep_cells", []):
        w = st["weights"].get(cell, 0.0)
        if approached:
            st["weights"][cell] = CFG["decay"] * w + CFG["reward"]
            if CFG["success_gated"]:
                st.setdefault("misses", {}).pop(cell, None)
        else:
            misses = st.setdefault("misses", {})
            if CFG["success_gated"]:
                misses[cell] = misses.get(cell, 0) + 1
                if misses[cell] >= CFG["min_confirmations"]:
                    st["weights"][cell] = CFG["decay"] * w + CFG["penalty"]
                    st["penalties"] = st.get("penalties", 0) + 1
                else:
                    st["weights"][cell] = CFG["decay"] * w
            else:
                st["weights"][cell] = CFG["decay"] * w + CFG["penalty"]
    st["ep_cells"] = []
    st["best_dist"] = 99.0


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Re-rank uncertainty_planning's ranked cells with frontier credit."""
    st = ctx["frontier_memory_v3"]
    st.setdefault("weights", {})
    st.setdefault("ep_cells", [])
    st.setdefault("best_dist", 99.0)
    goal = known_map.goal
    pos = known_map.pos

    prev_pos = st.get("pos")
    if prev_pos is not None and prev_pos != START and pos == START:
        _credit_previous_episode(st)
    st["pos"] = pos

    d_now = _dist(pos, goal)
    if st.get("best_dist", 99.0) > d_now:
        st["best_dist"] = d_now

    ranked = ctx.get("uncertainty_planning", {}).get("ranked")
    if not ranked:
        ranked = [(0.0, c) for c in frontier_cells]
    refined = _refine(st, ranked)
    if refined:
        st["ep_cells"].append(refined[0][1])
    if ctx.get("uncertainty_planning", {}).get("ranked") is not None:
        ctx["uncertainty_planning"]["ranked"] = refined
    return ctx


HOOKS = {
    "choose_action": HOOK_choose_action,
}
