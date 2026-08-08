"""SelfLab target module: the hive's own 'tools' library.

SelfLab picks an improved implementation of `fuzzy_match` from the candidates
below. The candidate set is fixed and precomputed (Constitution: LLM-free
mechanics). Each candidate is a genuinely different algorithm with different
quality and speed; the *true* quality is what a full benchmark measures, while
the hive only sees a NOISY sample benchmark and must use memory to converge on
the best candidate.

This module may be modified only through the SelfLab env's selection result,
which the loop persists into the hive state checkpoint.
"""

from __future__ import annotations

CANDIDATES = {
    "v1_naive": {"quality": 0.62, "speed": 1.0},
    "v2_lower": {"quality": 0.74, "speed": 1.4},
    "v3_sorted": {"quality": 0.83, "speed": 2.0},
    "v4_bucket": {"quality": 0.91, "speed": 2.8},
}

SELECTED = "v1_naive"


def fuzzy_match(a: str, b: str) -> float:
    """Naive baseline: character-level Jaccard. Correct but slow-ish."""
    sa, sb = set(a.lower()), set(b.lower())
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union


def set_selected(name: str) -> None:
    global SELECTED
    if name in CANDIDATES:
        SELECTED = name


def quality_score() -> float:
    """Full-benchmark quality of the currently selected implementation."""
    q = CANDIDATES[SELECTED]["quality"]
    s = CANDIDATES[SELECTED]["speed"]
    return q * (0.5 + 0.5 * min(s / 3.0, 1.0))
