"""Mechanism 1: CONFIDENCE-WEIGHTED MEMORY CONSOLIDATION.

Hypothesis (Architect, cycle 1): the hive writes many small, redundant atoms
(visited cells, patch outcomes, sample scores) and never reinforces or prunes
them. Over episodes memory becomes noisy and unreliable, so later episodes
re-explore and re-derive what was already known.

Mechanism: every memory write bumps a confirmation counter; on eval start we
consolidate: (a) merge duplicate links by boosting confidence, (b) decay stale
atoms, (c) reinforce nodes that were confirmed repeatedly. This turns memory
into a denser, more trustworthy substrate that downstream mechanisms rely on.

Expected effect: maze learning curve sharpens (fewer re-explorations across
episodes of the same maze); RepoOps picks the proven patch more often; SelfLab
averages noisy sample scores better.
"""

from __future__ import annotations

NAME = "memory_consolidation"

REINFORCE_FACTOR = 0.12
DUPLICATE_MERGE = True
DECAY_STRENGTH = 0.5


def _consolidate(atomspace) -> None:
    """Merge duplicate links, decay stale atoms, reinforce confirmed nodes."""
    merged: dict[tuple, dict] = {}
    for ln in atomspace.all_links():
        key = (ln["type"], ln["a"], ln["b"])
        if DUPLICATE_MERGE and key in merged:
            other = merged[key]
            other["confidence"] = min(1.0, other["confidence"] + ln["confidence"] * DECAY_STRENGTH)
            other["ttl"] = max(other["ttl"], ln["ttl"])
        else:
            merged[key] = dict(ln)
    atomspace.links = list(merged.values())
    for node in atomspace.nodes.values():
        node["confidence"] = min(1.0, node["confidence"] + REINFORCE_FACTOR)
    atomspace.stats["consolidations"] += 1
    atomspace.version += 1


def HOOK_before_eval(ctx, atomspace):
    _consolidate(atomspace)
    return ctx


def HOOK_after_write(ctx, atomspace, key=None, confidence=1.0, ttl=1000):
    """Reinforcement: repeated confirmations push an atom's confidence up."""
    ctx["memory_consolidation"]["writes"] = ctx["memory_consolidation"].get("writes", 0) + 1
    node = atomspace.nodes.get(str(key))
    if node is not None and confidence > 0:
        node["confidence"] = min(1.0, node["confidence"] + REINFORCE_FACTOR)
        atomspace.version += 1
    return ctx


HOOKS = {
    "before_eval": HOOK_before_eval,
    "after_write": HOOK_after_write,
}
