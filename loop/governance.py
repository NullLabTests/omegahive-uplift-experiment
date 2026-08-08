"""Governance: the fixed, constitutional decision rule (Article III).

A candidate mechanism is judged on the REAL delta it produces when added to
the incumbent hive state, measured across the full ecology:

  - PROMOTE:  relative aggregate-primary delta >= +5%  AND
              no robustness regression (aggregate robustness drop <= 10 pts)
  - PARK:     otherwise, if relative delta >= -5% (neutral)
  - REJECT:   otherwise (relative delta < -5%)

These thresholds are CONSTITUTIONAL and may not be changed by any mechanism.
"""

from __future__ import annotations


def apply_rule(before: dict, after: dict, mechanism: str) -> dict:
    d_primary = after["aggregate_primary"] - before["aggregate_primary"]
    rel = d_primary / before["aggregate_primary"] if before["aggregate_primary"] else 0.0
    d_robust = after["aggregate_robustness"] - before["aggregate_robustness"]

    if rel >= 0.05 and d_robust >= -0.10:
        verdict = "PROMOTE"
    elif rel >= -0.05:
        verdict = "PARK"
    else:
        verdict = "REJECT"

    return {
        "mechanism": mechanism,
        "verdict": verdict,
        "before_primary": round(before["aggregate_primary"], 4),
        "after_primary": round(after["aggregate_primary"], 4),
        "delta_primary": round(d_primary, 4),
        "rel_delta_primary": round(rel, 4),
        "before_robustness": round(before["aggregate_robustness"], 4),
        "after_robustness": round(after["aggregate_robustness"], 4),
        "delta_robustness": round(d_robust, 4),
        "rule": {
            "promote_threshold": "+5% rel primary and robustness drop <= 10 pts",
            "park_threshold": ">= -5% rel primary",
        },
    }
