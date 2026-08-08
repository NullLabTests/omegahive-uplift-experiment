"""EXPERIMENTAL strategy gate (Phase 6). NOT constitutional.

Verdict on whether to PROMOTE the in-band strategy mechanism
`success_signature_policy`, based on the three-arm probe measurement:

  PROMOTE iff ALL of:
    Q1 >= 1.05 * Q0   strategy memo beats the empty-memo baseline
    Q1 >= 1.05 * Q2   strategy memo beats the permuted-history control
    neg1 <= neg0      no task-axis regression (probe negative-seed count)
    attribution       per-seed matched Q1 > Q2 on a strict majority of seeds
  PARK  iff Q1 >= 0.95 * Q0   (real but sub-threshold / attribution absent)
  REJECT otherwise            (Q1 < 0.95 * Q0)

Metric: Q = (probe 21-seed aggregate-primary delta) / (target-domain remaining
headroom), i.e. the fraction of the target domain's remaining headroom captured,
in aggregate-weighted terms. Same inputs as governance (real before/after
aggregate vectors); it modifies no constitutional file.

Run:  (no CLI; imported by loop/chain_second_loop.py)
"""

from __future__ import annotations


def apply_rule(arms: dict, target_headroom: float, strategy: str) -> dict:
    """Strategy verdict from the three measured arms.

    arms = {0: arm0, 1: arm1, 2: arm2}; each arm carries:
      q (normalized proposal quality), delta (aggregate delta),
      negative_seeds, per_seed_deltas (list over EXT_SEEDS).
    """
    q = {i: arms[i]["q"] for i in (0, 1, 2)}
    delta = {i: arms[i]["delta"] for i in (0, 1, 2)}
    neg = {i: arms[i]["negative_seeds"] for i in (0, 1, 2)}

    d1 = arms[1]["per_seed_deltas"]
    d2 = arms[2]["per_seed_deltas"]
    wins = sum(1 for a, b in zip(d1, d2) if a > b)
    losses = sum(1 for a, b in zip(d1, d2) if a < b)
    ties = len(d1) - wins - losses
    attribution = wins > losses

    conditions = {
        "q1_ge_1p05_q0": bool(q[1] >= 1.05 * q[0]),
        "q1_ge_1p05_q2": bool(q[1] >= 1.05 * q[2]),
        "no_task_axis_regression": bool(neg[1] <= neg[0]),
        "attribution_holds": bool(attribution),
    }

    if all(conditions.values()):
        verdict = "PROMOTE"
    elif q[1] >= 0.95 * q[0]:
        verdict = "PARK"
    else:
        verdict = "REJECT"

    return {
        "strategy": strategy,
        "verdict": verdict,
        "target_domain_headroom": round(target_headroom, 4),
        "q": {i: round(q[i], 6) for i in (0, 1, 2)},
        "delta": {i: round(delta[i], 4) for i in (0, 1, 2)},
        "negative_seeds": {f"arm{i}": neg[i] for i in (0, 1, 2)},
        "matched_q1_vs_q2": {
            "wins": wins, "losses": losses, "ties": ties,
            "attribution_holds": attribution,
        },
        "conditions": conditions,
        "rule": {
            "name": "strategy gate (EXPERIMENTAL, not constitutional)",
            "constitutional": False,
            "promote_thresholds": "Q1 >= 1.05*Q0 AND Q1 >= 1.05*Q2 AND "
                                  "neg1 <= neg0 AND matched Q1 > Q2 (majority)",
            "park_threshold": "Q1 >= 0.95*Q0",
            "reject_threshold": "Q1 < 0.95*Q0",
        },
    }
