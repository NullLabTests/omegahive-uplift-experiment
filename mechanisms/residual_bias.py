"""Mechanism A (phase 2, chained cycle 1): RESIDUAL-BIAS EVIDENCE FILTER.

Hypothesis (Architect, chained cycle 1): phase 1 measured every candidate
against the EMPTY baseline, so nothing ever chained; the phase-2 incumbent
already carries uncertainty_planning (Maze). The least-tuned faculty of the
incumbent hive is RepoOps: each evidence link stores ONE noisy observation
(gauss sigma 0.5 wrapped around a true 0.1/0.7 signal) and single-shot recall
trusts the LAST write verbatim, so a genuinely good patch can be beaten by an
overfit patch on a lucky noisy draw. The parked mechanisms did not fix this:
memory_consolidation merges/reinforces globally without using the ground truth
available at write time; attention_budget caps the pool without de-noising it.

Mechanism: a predictive-residual corrector on the evidence stream. At write
time the RepoOps env hands this mechanism the TRUE hidden outcome (the
`confidence` argument) while the stored link holds only the noisy observation.
The mechanism keeps a per-style EMA residual  r[style] = observed - stored,
then rewrites the just-written link confidence to  stored + r[style]. This is a
one-step Kalman-style bias filter: it recovers each patch style's systematic
noise bias, sharpens the prior separation between good / overfit / flaky, and
is orthogonal to both parked mechanisms (it never merges links, never caps the
pool, never touches nodes).

Expected: RepoOps success_rate lifts toward always-picking-good with no effect
on Maze or SelfLab, so it compounds with uncertainty_planning by covering the
one domain the incumbent does not touch. Risk: per-style observations are few
(8 bugs), so the learned residual is noisy early and the delta may be
sub-threshold - governance must read the seed variance honestly.
"""

from __future__ import annotations

NAME = "residual_bias"

ALPHA = 0.35        # EMA learning rate on the residual
CLIP = (0.02, 0.98)  # clamp corrected confidences into the env's valid range


def _style_of(key) -> str:
    return str(key).rsplit(":", 1)[-1]


def HOOK_after_write(ctx, atomspace, key=None, confidence=1.0, ttl=1000):
    """Learn the per-style noise residual and correct the just-written link."""
    st = ctx["residual_bias"]
    residual = st.setdefault("residual", {})
    links = atomspace.query_links("evidence", a=key)
    if not links:
        return ctx
    style = _style_of(key)
    stored = links[-1]["confidence"]
    observed = float(confidence)
    r = observed - stored
    residual[style] = residual.get(style, 0.0) + ALPHA * (r - residual.get(style, 0.0))
    corrected = min(CLIP[1], max(CLIP[0], stored + residual[style]))
    links[-1]["confidence"] = corrected
    st["corrections"] = st.get("corrections", 0) + 1
    return ctx


HOOKS = {
    "after_write": HOOK_after_write,
}
