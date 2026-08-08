"""Architect: the cognitive mechanism proposal logic.

The Architect decides WHICH single mechanism the hive adds each cycle. The
order and rationale below are the Architect's reasoning (authored at design
time by the LLM oracle, per the free-model budget constraint) and are logged
verbatim to logs/decisions.log for audit. The mechanism MECHANICS themselves
are pure, precomputed Python in mechanisms/.
"""

from __future__ import annotations

ROSTER = [
    "memory_consolidation",
    "attention_budget",
    "uncertainty_planning",
]

RATIONALE = {
    "memory_consolidation": (
        "The hive's shared memory is single-shot and unmaintained: repeated "
        "facts pile up as raw duplicate links and stale atoms are never "
        "pruned. Confirming an observation only MAXes an atom's confidence "
        "instead of accumulating evidence. Consolidation (merge duplicates, "
        "reinforce confirmed atoms, average redundant evidence on recall) "
        "should make memory a more trustworthy substrate for RepoOps's "
        "cross-bug patch recall. Risk: in a small ecology memory is used "
        "lightly, so the gain may be sub-threshold - which is exactly what "
        "governance must detect honestly."
    ),
    "attention_budget": (
        "SelfLab's quality estimates are polluted by noisy warm-up samples; "
        "RepoOps and Maze process every candidate equally regardless of "
        "relevance. A hard capacity limit on each consider step, focused on "
        "the most salient items (value x recency), should sharpen SelfLab's "
        "estimate, keep RepoOps evidence focused, and stop the Maze agent "
        "from wandering across the whole map. Expected: clear gains in "
        "SelfLab, some in Maze."
    ),
    "uncertainty_planning": (
        "The Maze agent explores blind: its frontier targets are random, so it "
        "wastes most of its step budget re-crossing explored territory. "
        "Targeting frontier cells with the best expected information gain per "
        "step, biased toward the goal, should both cut step counts drastically "
        "and lift success on hard mazes. Expected: the strongest single-env "
        "gain in the ecology."
    ),
}

ARCHITECT_VERDICT_COMMENTARY = {
    "PROMOTE": "Measured improvement exceeds threshold with no robustness "
               "regression; incorporating the mechanism into the hive state.",
    "PARK": "Effect is neutral (within +/-5%): real but sub-threshold. Catalog "
            "the mechanism for possible future re-proposal; it does not join "
            "the active set now.",
    "REJECT": "Measured regression beyond -5%. Discarding the mechanism and its "
              "effect; the hive state reverts to the incumbent.",
}
