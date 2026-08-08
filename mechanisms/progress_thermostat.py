"""Mechanism E (phase 5): WITHIN-EPISODE EXPLORE/EXPLOIT THERMOSTAT (Maze).

Hypothesis (Architect, phase 5): uncertainty_planning's frontier selection is a
STATELESS scorer -- at every decision it re-ranks cells by information gain per
step plus a fixed goal bias (0.7 / goal_dist), and it CANNOT distinguish "the
agent is 3 cells from the goal and closing" from "the agent is 3 cells from the
goal and exploring a wrong-lobe pocket". It scores both situations identically.
The observed failure mode (verified by tracing) is exactly this: on hard mazes
the agent reaches within a few cells of the goal, then keeps committing to
high-information-gain cells that lie AWAY from the goal, drifts out of the
goal lobe, and burns the 95-step budget (seed 101 maze 1: reaches dist 3 at
step 29, then drifts to dist 7 and fails all 5 episodes). This mechanism is a
WITHIN-EPISODE EXPLORATION/EXPLOITATION THERMOSTAT: it watches the agent's
goal-proximity state (a within-episode trajectory quantity no static scorer
sees) and flips the decision objective from "explore for information" to
"exploit the goal lobe" whenever the agent is within EXPLOIT_NEAR cells of the
goal. It also keeps a drift safety valve: if the agent drifts more than DRIFT
cells beyond its best-approach-so-far, it pulls the frontier back toward the
goal lobe. Away from the goal it defers 100% to uncertainty_planning unchanged.

Orthogonality to uncertainty_planning (why this is NOT a re-tune):
  * uncertainty_planning is STATELESS per-decision scoring; it has no memory of
    the episode and no notion of proximity STATE. It adds a CONSTANT 0.7/goal_dist
    term to every cell every decision.
  * This mechanism is a STATEFUL, within-episode CONTROL LAYER. It does not add
    a static bias to any score; it switches the entire objective function
    between explore and exploit based on the episode's goal-proximity
    trajectory. On most of the map it does NOTHING (pure pass-through). It fires
    only near the goal lobe / on drift -- a regime where uncertainty_planning is
    provably blind to the difference between closing and drifting.
  * It has NO after_write hook (never touches RepoOps -- residual_bias's
    claimed territory) and NO cross-episode credit transfer (nothing like
    frontier_memory/evidence_substrate's episode-boundary weights). Its only
    hook is choose_action; its only effect is re-ordering the SAME candidate
    frontier cells uncertainty_planning ranked.

Domain: maze (0.8229, weight 0.40) -- the only domain with real headroom left.
Expected effect: higher success on hard mazes (the near-goal lobe is exploited
instead of abandoned) and higher efficiency (fewer budget-burning detours).
RepoOps and SelfLab must be unaffected (no hooks there).

NAME / HOOKS registered for auto-discovery by hive.hooks.load_registry.
"""

from __future__ import annotations

NAME = "progress_thermostat"

EXPLOIT_NEAR = 5   # manhattan distance to goal where exploitation kicks in
DRIFT = 3          # drift beyond best-approach allowed before pull-back
GOAL_BIAS = 0.7    # constant kept for the pure-exploit re-rank term
START = (0, 0)


def _dist(a, b) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _exploit_rank(ranked, goal):
    """Order the SAME candidate cells by goal-proximity (exploit lobe)."""
    return sorted(ranked, key=lambda sc_c: _dist(sc_c[1], goal))


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Flip to exploitation when near the goal / when drifting away from it."""
    st = ctx["progress_thermostat"]
    st.setdefault("best", None)
    st.setdefault("pos", None)
    st.setdefault("exploits", 0)
    st.setdefault("pulls", 0)

    pos = known_map.pos
    goal = known_map.goal

    prev = st.get("pos")
    if prev is not None and prev != START and pos == START:
        st["best"] = None  # new episode: reset the progress tracker

    cur = _dist(pos, goal)
    best = st.get("best")
    if best is None or cur < best:
        best = cur
        st["best"] = best
    st["pos"] = pos

    ranked = ctx.get("uncertainty_planning", {}).get("ranked")
    if not ranked:
        ranked = [(0.0, c) for c in frontier_cells]

    near_goal = cur <= EXPLOIT_NEAR
    drifting = cur - best > DRIFT
    if not near_goal and not drifting:
        return ctx  # far lobe, making progress: defer to uncertainty_planning

    pulled = _exploit_rank(ranked, goal)
    if near_goal:
        st["exploits"] += 1
    if drifting:
        st["pulls"] += 1
    if ctx.get("uncertainty_planning", {}).get("ranked") is not None:
        ctx["uncertainty_planning"]["ranked"] = pulled
    return ctx


HOOKS = {
    "choose_action": HOOK_choose_action,
}
