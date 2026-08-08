"""Mechanism 2: ATTENTION BUDGET (relevance-ranked, capacity-limited processing).

Hypothesis (Architect, cycle 2): as memory and search grow, the hive processes
every matching item regardless of relevance, thrashing between noisy
alternatives and spreading its effort too thin. A capacity limit on every
"consider" step, focused on the most salient items, should sharpen decisions.

Mechanism: any `retrieve`/`consider` call is capped at BUDGET items, ranked by
salience = value * recency. Items are either memory links (with confidence/ttl)
or scored planning candidates (dicts with item/value). Applied to:
  - SelfLab: sample retrieval keeps the most recent (clean) quality samples.
  - RepoOps: the evidence pool is capped to the strongest entries.
  - Maze: the frontier candidate set is focused on the highest-value cells.

Expected effect: sharper estimates and steadier, more focused exploration,
compounding with consolidation (reliable memory) and uncertainty planning
(smarter targets).
"""

from __future__ import annotations

NAME = "attention_budget"

BUDGET = 4


def _salience(item) -> float:
    if isinstance(item, dict) and "item" in item:
        return item.get("value", 0.0) * item.get("ttl", 1)
    return item["confidence"] * max(item.get("ttl", 0), 0)


def _item(it):
    return it["item"] if isinstance(it, dict) and "item" in it else it


def HOOK_retrieve(ctx, atomspace, kind=None, query=None, candidates=None):
    """Rank a candidate set by salience and cap it at BUDGET."""
    if candidates is None:
        return ctx
    ranked = sorted(candidates, key=_salience, reverse=True)
    kept = [_item(x) for x in ranked[:BUDGET]]
    ctx["attention_budget"].setdefault("kept", 0)
    ctx["attention_budget"]["kept"] += 1
    ctx["attention_budget"]["budget"] = BUDGET
    ctx["attention_budget"]["returned"] = len(kept)
    ctx["attention_budget"]["candidates"] = kept
    return ctx


HOOKS = {
    "retrieve": HOOK_retrieve,
}
