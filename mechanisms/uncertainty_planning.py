"""Mechanism 3: UNCERTAINTY-AWARE PLANNING WRAPPER (expected information gain).

Hypothesis (Architect, cycle 3): the maze agent's frontier exploration is
greedy: it walks toward the nearest unknown cell, so it hugs the explored
blob's edge and wastes steps backtracking into wall pockets. A planner that
targets the highest-uncertainty, highest-value cells (those that reveal the
most new map area PER STEP) should explore far more efficiently.

Mechanism: wraps the frontier-selection decision. Each candidate frontier cell
is scored by estimated information gain = (unknown neighbors) / (1 + distance
from the agent). The highest-scoring cell becomes the exploration target.
This compounds with consolidation (reliable map) and attention (focused
candidate set).
"""

from __future__ import annotations

NAME = "uncertainty_planning"


def _score(known_map, cell):
    r, c = cell
    unknown = 0
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if not known_map.is_known(r + dr, c + dc):
            unknown += 1
    pr, pc = known_map.pos
    dist = abs(pr - r) + abs(pc - c) + 1
    gr, gc = known_map.goal
    goal_dist = abs(gr - r) + abs(gc - c) + 1
    # information gain per step, biased toward the goal (value signal)
    return unknown / dist + 0.7 / goal_dist


def HOOK_choose_action(ctx, known_map, frontier_cells):
    """Choose the frontier cell with the best information-gain-per-step."""
    scored = sorted((( _score(known_map, cell), cell) for cell in frontier_cells),
                    reverse=True)
    ctx["uncertainty_planning"]["ranked"] = scored
    if scored:
        ctx["uncertainty_planning"]["choice"] = scored[0][1]
    return ctx


HOOKS = {
    "choose_action": HOOK_choose_action,
}
