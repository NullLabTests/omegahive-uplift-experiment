"""Mechanism B (phase 2, chained cycle 2): CROSS-EPISODE FRONTIER CREDIT TRANSFER.

Hypothesis (Architect, chained cycle 2): uncertainty_planning ranks frontier
cells by instantaneous information gain but is STATELESS across episodes of the
same maze - it re-offers the same juicy-looking pocket cell every episode, even
after that pocket has repeatedly dead-ended. The maze runs five episodes per
layout with fresh maps each episode (partial observability), so the only way to
remember "that cell is a dead end" is cross-episode memory. The maze agent also
gives a free, honest progress signal at every frontier decision: the minimum
manhattan distance to the goal reached while exploring.

Mechanism: the mechanism watches each chosen exploration target and the
episode's best (smallest) goal-distance reached. When a new episode begins it
assigns credit to the previous episode's targets: REWARD (-0.8) if that episode
approached the goal within GOAL_THRESHOLD cells, else PENALTY (+1.0). Weights
decay by DECAY per episode. At each frontier decision it re-ranks
uncertainty_planning's ranked candidates:  score /= (1 + BETA * weight[cell]),
so proven-productive cells are nudged up and proven dead-ends nudged down.
This is genuine within-maze transfer (episodes share walls) that compounds the
information-gain score instead of replacing it. Cross-maze pollution is bounded
by per-cell identity (frontier sets are mostly disjoint across layouts) and by
the fast weight decay; that imperfection is accepted and reported honestly.

Expected: better success/efficiency on episodes 2-5 of each maze, especially
hard mazes where greedy IG revisits pockets. Risk: an early unlucky episode may
wrongly penalize a productive cell before the credit accumulates.
"""

from __future__ import annotations

NAME = "frontier_memory"

DECAY = 0.5         # per-episode weight decay (fades cross-maze memories)
PENALTY = 1.0       # weight added to targets of episodes that missed the goal
REWARD = -0.8       # weight added to targets of episodes that approached goal
GOAL_THRESHOLD = 4  # best manhattan distance to goal counted as "productive"
BETA = 0.10         # how strongly learned weights bend the IG score
START = (0, 0)


def _dist(pos, goal) -> float:
    return abs(pos[0] - goal[0]) + abs(pos[1] - goal[1])


def _refine(st, ranked):
    out = []
    for score, cell in ranked:
        weight = st["weights"].get(cell, 0.0)
        out.append((score / (1.0 + BETA * weight), cell))
    return sorted(out, reverse=True)


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Watch targets, assign credit across episodes, re-rank the IG list."""
    st = ctx["frontier_memory"]
    st.setdefault("weights", {})
    st.setdefault("ep_cells", [])
    goal = known_map.goal
    pos = known_map.pos

    prev_pos = st.get("pos")
    if prev_pos is not None and prev_pos != START and pos == START:
        # a new episode began: credit the previous episode's targets
        best = st.get("best_dist", 99.0)
        delta = REWARD if best <= GOAL_THRESHOLD else PENALTY
        for cell in st.get("ep_cells", []):
            st["weights"][cell] = DECAY * st["weights"].get(cell, 0.0) + delta
        st["ep_cells"] = []
        st["best_dist"] = 99.0
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
