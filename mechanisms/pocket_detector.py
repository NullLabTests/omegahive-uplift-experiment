"""Mechanism (phase 6, cycle 2): POCKET_DETECTOR — within-episode dead-end pocket
memory (Maze).

Proposed under S (success_signature_policy) per the phase-6 memo: target domain
maze (highest weighted remaining headroom), success-gated credit with >=2
confirmations (the memo's parameterization), and no redundancy with the
incumbent's levers:
  * uncertainty_planning is a STATELESS per-decision info-gain scorer with a
    fixed goal bias; it has no memory of discovered wall topology.
  * progress_thermostat flips the decision objective by GOAL PROXIMITY within an
    episode; it never reads wall structure.
This mechanism reads DISCOVERED WALL TOPOLOGY (a signal neither up nor pt uses):
a frontier cell is a "pocket" when its exploration-graph degree is closed — it
has at most one undiscovered exit (open neighbor), i.e. it is a dead-end lobe of
the explored region. Credit is success-gated (only episodes that never
approached the goal record a miss) and a penalty is applied only after >=2
confirmations, with a small beta, exactly per the memo's parameterization.
At choose_action time it re-ranks uncertainty_planning's ranked cells:
score /= (1 + beta * weight[cell]).

No after_write / before_eval / retrieve handlers (zero overlap with
residual_bias / memory_consolidation / attention_budget) and no propose hook.
Configured via configure() from the proposal memo (same channel as the probe).

NAME / HOOKS registered for auto-discovery by hive.hooks.load_registry.
"""

from __future__ import annotations

NAME = "pocket_detector"

CFG = {
    "success_gated": True,
    "min_confirmations": 2,
    "beta": 0.03,
    "penalty": 1.0,
    "reward": -0.8,
    "approach": 4,
    "decay": 0.5,
}
START = (0, 0)


def configure(params: dict | None = None) -> dict:
    if params:
        for k, v in params.items():
            if k in CFG:
                CFG[k] = v
    return dict(CFG)


def _dist(pos, goal) -> float:
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])


def _open_exits(known_map, cell) -> int:
    r, c = cell
    opens = 0
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if not (0 <= nr < known_map.grid and 0 <= nc < known_map.grid):
            continue
        if not known_map.is_known(nr, nc):
            opens += 1
    return opens


def _is_pocket(known_map, cell) -> bool:
    return _open_exits(known_map, cell) <= 1


def _refine(st, ranked):
    out = []
    for score, cell in ranked:
        w = st["weights"].get(cell, 0.0)
        out.append((score / (1.0 + CFG["beta"] * w), cell))
    return sorted(out, reverse=True)


def _credit_previous_episode(st) -> None:
    best = st.get("best_dist", 99.0)
    approached = best <= CFG["approach"]
    for cell, pocket in st.get("ep_cells", []):
        w = st["weights"].get(cell, 0.0)
        if approached:
            st["weights"][cell] = CFG["decay"] * w + CFG["reward"]
            if CFG["success_gated"]:
                st.setdefault("misses", {}).pop(cell, None)
        elif pocket:
            misses = st.setdefault("misses", {})
            misses[cell] = misses.get(cell, 0) + 1
            if misses[cell] >= CFG["min_confirmations"]:
                st["weights"][cell] = CFG["decay"] * w + CFG["penalty"]
                st["penalties"] = st.get("penalties", 0) + 1
            else:
                st["weights"][cell] = CFG["decay"] * w
        else:
            st["weights"][cell] = CFG["decay"] * w
    st["ep_cells"] = []
    st["best_dist"] = 99.0


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Track targets + pocket topology; re-rank confirmed dead-end lobes down."""
    st = ctx["pocket_detector"]
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
        st["ep_cells"].append((refined[0][1], _is_pocket(known_map, refined[0][1])))
    if ctx.get("uncertainty_planning", {}).get("ranked") is not None:
        ctx["uncertainty_planning"]["ranked"] = refined
    return ctx


HOOKS = {
    "choose_action": HOOK_choose_action,
}
