"""EXPERIMENTAL per-domain promotion gate (Phase 4). NOT constitutional.

The constitutional gate (loop/governance.py, Article III) decides on the single
AGGREGATE primary: PROMOTE iff the aggregate rises >= +5% relative with no big
robustness regression. Phase 3's offline counterfactual (logs/counterfactual.md)
argued this hides large WITHIN-domain gains (RepoOps +7.8% relative carried by
residual_bias and evidence_substrate) and that the stalls are a rule-design
problem, not a mechanism problem.

This module is that hypothesized ALTERNATIVE RULE, implemented as a pure
decision function over the same before/after aggregate() score vectors that
governance consumes. It is an EXPERIMENTAL VARIANT for Phase 4 only:

  - PROMOTE iff ANY domain primary (maze, repoops, selflab) rises >= +5%
    RELATIVE to its before value AND no domain primary drops > -3% relative.
  - PARK otherwise, if the aggregate primary rel delta >= -5%.
  - REJECT otherwise (aggregate rel delta < -5%).

It returns a verdict dict shaped like loop.governance.apply_rule's (mechanism,
verdict, before/after primaries, deltas, rule description). It does not modify
governance.py or any constitutional file.

Run:  python3 -c "from loop.gate_perdomain import apply_rule; ..."
"""

from __future__ import annotations

DOMAINS = ("maze", "repoops", "selflab")

# experimental thresholds (Phase 4 only; deliberately NOT constitutional)
PROMOTE_DOMAIN_REL = 0.05      # ANY single domain primary >= +5% relative
MAX_DOMAIN_DROP_REL = 0.03     # no domain may drop > -3% relative
PARK_AGG_REL = 0.05            # otherwise PARK iff aggregate >= -5% relative


def _rel(before: float, after: float) -> float:
    return (after - before) / before if before else 0.0


def _domain_rows(before: dict, after: dict) -> dict:
    rows = {}
    for name in DOMAINS:
        b = before["primaries"].get(name, before["envs"][name]["success_rate"])
        a = after["primaries"].get(name, after["envs"][name]["success_rate"])
        rows[name] = {
            "before": round(b, 4),
            "after": round(a, 4),
            "delta": round(a - b, 4),
            "rel_delta": round(_rel(b, a), 4),
        }
    return rows


def apply_rule(before: dict, after: dict, mechanism: str) -> dict:
    """Experimental per-domain verdict (Phase 4). Same inputs as governance."""
    rows = _domain_rows(before, after)

    rel_by_domain = {n: rows[n]["rel_delta"] for n in DOMAINS}
    best_domain = max(rel_by_domain, key=lambda n: rel_by_domain[n])
    best_rel = rel_by_domain[best_domain]
    worst_rel = min(rel_by_domain.values())

    any_domain_gain = best_rel >= PROMOTE_DOMAIN_REL
    no_domain_drop = worst_rel > -MAX_DOMAIN_DROP_REL

    d_primary = after["aggregate_primary"] - before["aggregate_primary"]
    agg_rel = _rel(before["aggregate_primary"], after["aggregate_primary"])
    d_robust = after["aggregate_robustness"] - before["aggregate_robustness"]

    if any_domain_gain and no_domain_drop:
        verdict = "PROMOTE"
    elif agg_rel >= -PARK_AGG_REL:
        verdict = "PARK"
    else:
        verdict = "REJECT"

    return {
        "mechanism": mechanism,
        "verdict": verdict,
        "before_primary": round(before["aggregate_primary"], 4),
        "after_primary": round(after["aggregate_primary"], 4),
        "delta_primary": round(d_primary, 4),
        "rel_delta_primary": round(agg_rel, 4),
        "before_robustness": round(before["aggregate_robustness"], 4),
        "after_robustness": round(after["aggregate_robustness"], 4),
        "delta_robustness": round(d_robust, 4),
        "domain_primaries": rows,
        "promoting_domain": best_domain,
        "promoting_domain_rel": round(best_rel, 4),
        "worst_domain": min(rel_by_domain, key=lambda n: rel_by_domain[n]),
        "worst_domain_rel": round(worst_rel, 4),
        "any_domain_gain_ge_5pct": any_domain_gain,
        "no_domain_drop_gt_3pct": no_domain_drop,
        "rule": {
            "name": "per-domain promotion gate (EXPERIMENTAL VARIANT, not constitutional)",
            "constitutional": False,
            "promote_threshold": "ANY domain primary >= +5% rel AND no domain drop > -3% rel",
            "park_threshold": "aggregate rel >= -5%",
            "reject_threshold": "aggregate rel < -5%",
        },
    }
