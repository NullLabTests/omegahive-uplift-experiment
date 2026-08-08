"""Mechanism C (phase 3, chained cycle 3): CALIBRATED FRONTIER MEMORY (tests H1).

Hypothesis H1 (NOISE hypothesis, from CHAINING_REPORT.md): the phase-2 park of
`frontier_memory` was a CALIBRATION ARTIFACT, not a real limitation. Its raw
Maze delta was +0.0141 (maze primary 0.8229 -> 0.8370) but its per-seed delta
sd was 0.143 with single-seed lows of -0.53: it penalized a productive cell
after ONE unlucky episode and the penalty persisted through the decay horizon.
If that is true, a calibrated version should recover a real, reliably-positive
Maze gain that clears the +5% aggregate gate (maze carries 0.40 of aggregate
weight and has +8.0% headroom, the largest of any domain).

This mechanism is a strict calibration of the parked `frontier_memory` per the
report's three prescriptions:
  1. SUCCESS-GATED credit: a target cell is PENALIZED only when its episode
     FAILED and never approached the goal (best goal-distance > APPROACH). The
     env does not expose a per-episode success flag to the choose_action hook
     (the hook never fires at the moment the agent reaches the goal), so
     "failed" is proxied honestly by "never approached within APPROACH cells":
     any episode that gets within APPROACH cells of the goal necessarily had
     the goal in view and then auto-stepped to it, so APPROACH<=best_dist is a
     conservative failure proxy (it under-penalizes rather than over-penalizes).
  2. MIN_CONF confirmations: a penalty weight is only applied after the same
     cell missed the goal (never approached) in >= 2 independent episodes, so a
     single unlucky episode can never hurt a productive cell.
  3. SMALLER BETA: the score-bending coefficient drops 0.10 -> 0.03, and the
     penalty is one fixed unit rather than a repeatedly compounded one, so
     per-seed variance collapses while the real signal survives.

Reward side is unchanged in spirit (approached episodes reward their cells) but
also decays gently. The mechanism chains AFTER uncertainty_planning by rewriting
ctx["uncertainty_planning"]["ranked"] at choose_action time.

Architect prediction (falsifiable): Maze primary gains +0.02..+0.08
(aggregate +0.8%..+3.2%) with per-seed sd well below the mean -- a real,
reliably-positive effect. If the calibrated version clears +5% aggregate, H1 is
confirmed (the phase-2 park was a calibration artifact); if it stays parked
even when calibrated, the +8% Maze headroom claim is suspect.
"""

from __future__ import annotations

NAME = "frontier_memory_v2"

DECAY = 0.5          # per-episode weight decay (cross-maze memories fade)
PENALTY = 1.0        # weight added when a cell is confirmed (>=MIN_CONF) dead-end
REWARD = -0.8        # weight added to cells of episodes that approached the goal
APPROACH = 4         # best manhattan distance that counts as "approached the goal"
MIN_CONF = 2         # independent never-approached episodes before any penalty
BETA = 0.03          # score-bending coefficient (shrunk from 0.10 in v1)
START = (0, 0)


def _dist(pos, goal) -> float:
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])


def _refine(st, ranked):
    out = []
    for score, cell in ranked:
        weight = st["weights"].get(cell, 0.0)
        out.append((score / (1.0 + BETA * weight), cell))
    return sorted(out, reverse=True)


def _credit_previous_episode(st) -> None:
    """Apply success-gated credit to the previous episode's target cells."""
    best = st.get("best_dist", 99.0)
    approached = best <= APPROACH
    for cell in st.get("ep_cells", []):
        w = st["weights"].get(cell, 0.0)
        if approached:
            # productive episode: reward the cell and clear any stale misses
            st["weights"][cell] = DECAY * w + REWARD
            st.setdefault("misses", {}).pop(cell, None)
        else:
            # never approached the goal: record a miss, penalize only on MIN_CONF
            misses = st.setdefault("misses", {})
            misses[cell] = misses.get(cell, 0) + 1
            if misses[cell] >= MIN_CONF:
                st["weights"][cell] = DECAY * w + PENALTY
                st["penalties"] = st.get("penalties", 0) + 1
            else:
                st["weights"][cell] = DECAY * w
    st["ep_cells"] = []
    st["best_dist"] = 99.0


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Re-rank uncertainty_planning's ranked list with calibrated memories."""
    st = ctx["frontier_memory_v2"]
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
