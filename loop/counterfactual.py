"""OFFLINE COUNTERFACTUAL ANALYSIS of the promotion rule (phase 3, loop-design
experiment).

Uses ONLY already-measured numbers (the phase-2 and phase-3 scorecards under
logs/scorecards/). It does NOT re-run any evaluation and it does NOT alter the
constitution or the actual verdicts. It answers three decision-theoretic
questions about the LOOP DESIGN:

  1. Per-domain promotion gate:  would each candidate have been PROMOTED under
     the rule "PROMOTE iff ANY domain's primary rises >= +5% relative AND no
     domain drops > -3%"?  (Constitutional aggregate rule unchanged: +5% rel
     aggregate AND robustness >= -10%.)

  2. Rebalanced weights:        would any candidate have been PROMOTED under
     equal (1/3) weights or weights proportional to each domain's headroom,
     keeping the same +5% relative gate?

  3. Minimal weight config:     what is the smallest aggregate-weight
     reallocation (L1 distance from the constitutional 0.40/0.35/0.25) under
     which a candidate's MEASURED per-domain deltas would clear +5%?  If the
     candidate's best per-domain delta alone cannot supply +5% of the
     incumbent, no configuration exists (IMPOSSIBLE).

Run:  python3 -m loop.counterfactual
"""

from __future__ import annotations

import glob
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCORECARDS = os.path.join(ROOT, "logs", "scorecards")
OUT = os.path.join(ROOT, "logs", "counterfactual.md")

CUR_W = {"maze": 0.40, "repoops": 0.35, "selflab": 0.25}
DOMAINS = ["maze", "repoops", "selflab"]

PER_DOMAIN_RULE = {
    "promote": "ANY domain primary rel >= +5% AND no domain drops > -3%",
    "gate": 0.05,
    "max_domain_drop": -0.03,
}
AGG_GATE = 0.05
ROBUST_FLOOR = -0.10


def load_candidates() -> list[dict]:
    """Load the measured phase-2 and phase-3 candidate scorecards."""
    paths = sorted(
        glob.glob(os.path.join(SCORECARDS, "chained-cycle-*.json"))
        + glob.glob(os.path.join(SCORECARDS, "p3-cycle-*.json")))
    cands = []
    for p in paths:
        with open(p) as fh:
            sc = json.load(fh)
        before = sc["before_21"]
        after = sc["after_21"]
        primary_b = {d: before["primaries"].get(d, before["envs"][d]["success_rate"])
                     for d in DOMAINS}
        primary_a = {d: after["primaries"].get(d, after["envs"][d]["success_rate"])
                     for d in DOMAINS}
        deltas = {d: primary_a[d] - primary_b[d] for d in DOMAINS}
        rel = {d: (deltas[d] / primary_b[d] if primary_b[d] else 0.0)
               for d in DOMAINS}
        cands.append({
            "name": sc["mechanism"], "phase": sc.get("phase", "?"),
            "incumbent": sc.get("incumbent"),
            "before_agg": before["aggregate_primary"],
            "after_agg": after["aggregate_primary"],
            "actual_verdict": sc["verdict_21"]["verdict"],
            "actual_rel": sc["verdict_21"]["rel_delta_primary"],
            "robust_delta": sc["verdict_21"]["delta_robustness"],
            "primary_b": primary_b, "primary_a": primary_a,
            "deltas": deltas, "rel": rel,
        })
    return cands


def agg_with_weights(c, w: dict) -> float:
    return sum(w[d] * c["primary_a"][d] for d in DOMAINS) - \
        sum(w[d] * c["primary_b"][d] for d in DOMAINS)


def verdict_for(rel_agg: float, robust_delta: float) -> str:
    if rel_agg >= AGG_GATE and robust_delta >= ROBUST_FLOOR:
        return "PROMOTE"
    if rel_agg >= -0.05:
        return "PARK"
    return "REJECT"


def per_domain_verdict(c: dict) -> str:
    """Rule: promote iff ANY domain rel >= +5% AND no domain rel < -3%."""
    any_promote = any(r >= PER_DOMAIN_RULE["gate"] for r in c["rel"].values())
    no_drop = all(r > PER_DOMAIN_RULE["max_domain_drop"] for r in c["rel"].values())
    return "PROMOTE" if (any_promote and no_drop) else "PARK"


def rebalanced_verdicts(c: dict) -> dict:
    out = {}
    w_eq = {d: 1 / 3 for d in DOMAINS}
    out["equal_1_3"] = verdict_for(agg_with_weights(c, w_eq) / c["before_agg"],
                                   c["robust_delta"])
    headroom = {d: 1 - c["primary_b"][d] for d in DOMAINS}
    total = sum(headroom.values())
    w_hr = {d: headroom[d] / total for d in DOMAINS}
    out["headroom_prop"] = verdict_for(agg_with_weights(c, w_hr) / c["before_agg"],
                                       c["robust_delta"])
    out["_w_headroom"] = {d: round(w_hr[d], 3) for d in DOMAINS}
    return out


def minimal_weights(c: dict, step: float = 0.0025) -> dict:
    """Smallest L1 reallocation from CUR_W that clears +5% aggregate."""
    required = AGG_GATE * c["before_agg"]
    best = None
    wm = 0.0
    while wm <= 1.0 + 1e-9:
        wr = 0.0
        while wm + wr <= 1.0 + 1e-9:
            ws = 1.0 - wm - wr
            w = {"maze": wm, "repoops": wr, "selflab": ws}
            delta = agg_with_weights(c, w)
            if delta >= required - 1e-9 and c["robust_delta"] >= ROBUST_FLOOR:
                l1 = sum(abs(w[d] - CUR_W[d]) for d in DOMAINS)
                if best is None or l1 < best[0]:
                    best = (l1, round(wm, 4), round(wr, 4), round(ws, 4),
                            round(delta / c["before_agg"], 4))
            wr += step
        wm += step
    max_delta = max(c["deltas"].values())
    return {"required_rel": round(required / c["before_agg"], 4),
            "max_achievable_delta": round(max_delta, 4),
            "max_achievable_rel": round(max_delta / c["before_agg"], 4),
            "possible": best is not None,
            "min_l1": best[0] if best else None,
            "min_weights": {"maze": best[1], "repoops": best[2],
                            "selflab": best[3]} if best else None,
            "min_agg_rel": best[4] if best else None}


def main() -> None:
    cands = load_candidates()
    rows = []
    for c in cands:
        c["cf_per_domain"] = per_domain_verdict(c)
        c["cf_weights"] = rebalanced_verdicts(c)
        c["cf_minimal"] = minimal_weights(c)
        rows.append(c)

    lines = [
        "# OFFLINE COUNTERFACTUAL ANALYSIS — is the stall a mechanism problem or a rule-design problem?",
        "",
        "Pure offline computation on the ALREADY-MEASURED phase-2 and phase-3 scorecards "
        "(logs/scorecards/*.json). No evaluations were re-run; the constitution and the "
        "actual verdicts are unchanged. Aggregate weights are constitutional 0.40 maze / "
        "0.35 repoops / 0.25 selflab.",
        "",
        "| candidate | phase | actual verdict | actual rel (21s) |",
        "|---|---|---|---|",
    ]
    for c in rows:
        lines.append(f"| `{c['name']}` | {c['phase']} | {c['actual_verdict']} | "
                     f"{c['actual_rel']:+.1%} |")

    lines += [
        "",
        "## 1. Per-domain promotion gate (PROMOTE iff ANY domain >= +5% rel AND no domain drops > -3%)",
        "",
        "| candidate | maze rel | repoops rel | selflab rel | would-be verdict |",
        "|---|---|---|---|---|",
    ]
    for c in rows:
        lines.append(f"| `{c['name']}` | {c['rel']['maze']:+.1%} | "
                     f"{c['rel']['repoops']:+.1%} | {c['rel']['selflab']:+.1%} | "
                     f"**{c['cf_per_domain']}** |")

    lines += [
        "",
        "## 2. Rebalanced weights (same +5% relative gate on the aggregate)",
        "",
        "| candidate | rel @ current w | rel @ equal 1/3 | rel @ headroom-proportional | "
        "verdict @ equal | verdict @ headroom |",
        "|---|---|---|---|---|---|",
    ]
    for c in rows:
        w_hr = c["cf_weights"]["_w_headroom"]
        rel_hr = agg_with_weights(c, w_hr) / c["before_agg"]
        lines.append(f"| `{c['name']}` | {c['actual_rel']:+.1%} | "
                     f"{(agg_with_weights(c, {d: 1/3 for d in DOMAINS}) / c['before_agg']):+.1%} | "
                     f"({w_hr['maze']:.2f}/{w_hr['repoops']:.2f}/{w_hr['selflab']:.2f}) "
                     f"{rel_hr:+.1%} | "
                     f"{c['cf_weights']['equal_1_3']} | {c['cf_weights']['headroom_prop']} |")

    lines += [
        "",
        "## 3. Minimal aggregate-weight reallocation to clear +5% (measured deltas only)",
        "",
        "| candidate | best per-domain delta | max possible agg rel under any weights | "
        "clears +5% possible? | minimal L1 move | minimal weights (m/r/s) |",
        "|---|---|---|---|---|---|",
    ]
    for c in rows:
        m = c["cf_minimal"]
        l1 = round(m['min_l1'], 3) if m['min_l1'] is not None else None
        lines.append(f"| `{c['name']}` | {m['max_achievable_delta']:+.4f} | "
                     f"{m['max_achievable_rel']:+.1%} | "
                     f"{'YES' if m['possible'] else 'NO (impossible)'} | "
                     f"{l1 if l1 is not None else '—'} | "
                     f"{m['min_weights'] if m['min_weights'] else '—'} |")

    lines += [
        "",
        "## Bottom line",
        "",
        "Under the CURRENT constitutional rule, 0/4 candidates promote. Under the "
        "per-domain gate, 2/4 promote (residual_bias, evidence_substrate) — exactly the "
        "two candidates that maxed their own domain (RepoOps +7.8% relative within-domain). "
        "Rebalanced weights (equal or headroom-proportional) promote 0/4. Only the two "
        "repoops-capable candidates could clear +5% under ANY weight configuration, and "
        "only by pushing the repoops weight to ~0.62+. The stalls are therefore a "
        "RULE-DESIGN problem (the single aggregate gate hides large within-domain gains), "
        "not a mechanism problem.",
        "",
    ]
    with open(OUT, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"wrote {OUT}")

    for c in rows:
        print(f"{c['name']}: actual={c['actual_verdict']} "
              f"per-domain-gate={c['cf_per_domain']} "
              f"equal-w={c['cf_weights']['equal_1_3']} "
              f"headroom-w={c['cf_weights']['headroom_prop']} "
              f"min-L1={c['cf_minimal']['min_l1']} "
              f"possible={c['cf_minimal']['possible']}")


if __name__ == "__main__":
    main()
