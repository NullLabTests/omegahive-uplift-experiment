"""Env B: REPOOPS-LITE — fix a buggy Python function with hidden tests.

Given a buggy function, the Implementer agent must select the best candidate
patch. Each bug carries a signature (feature tags) and candidates come in
styles (good / good_alt / overfit / flaky / broken). Only a subset of tests is
visible at selection time, so visible-test overfitting is punished and
cross-bug memory is the tiebreaker.

Memory model: every time a style is selected, the hive stores an evidence link
`evidence:{feature}:{style}` whose confidence reflects the true hidden outcome,
corrupted by harness NOISE (a good patch can flake on a hidden test, a bad
patch can luck through). Style recall is:

  - BASELINE (single-shot): the most recent observation wins (last-write).
  - WITH memory_consolidation: all observations are merged into a
    confidence-weighted average across confirmations, and duplicates/stale
    atoms are pruned at each eval step (the "before_eval" hook).

attention_budget caps the evidence pool to the most salient entries.
"""

from __future__ import annotations

import random

from hive.atomspace import AtomSpace
from hive.hooks import HookPipe

N_TESTS = 6
VISIBLE = 3
NEUTRAL = 0.35
EVIDENCE_NOISE = 0.5  # harness flake noise on the recorded outcome
N_BUGS = 8


def _styles_passes() -> dict:
    vis = set(range(VISIBLE))
    return {
        "good": set(range(N_TESTS)),
        "good_alt": set(range(N_TESTS)),
        "overfit": set(vis),
        "broken": set(),
        "flaky": set(range(N_TESTS)) - {2, 5},
    }


def _bugs(rng: random.Random) -> list[dict]:
    pool = ["clamp", "sort", "filter", "string", "boundary", "edge"]
    bugs = []
    for i in range(N_BUGS):
        f1 = pool[i % len(pool)]
        f2 = pool[(i + 2) % len(pool)]
        f3 = pool[(i + 4) % len(pool)]
        f4 = pool[(i + 1) % len(pool)]
        f5 = pool[(i + 3) % len(pool)]
        order = ["good", "good_alt", "overfit", "flaky", "broken"]
        rng.shuffle(order)
        if order[-1] == "good" or order[-1] == "good_alt":
            order[-1], order[0] = order[0], order[-1]
        bugs.append({"name": f"bug{i + 1}", "features": [f1, f2, f3, f4, f5],
                     "order": order})
    return bugs


def _write_evidence(atomspace, features, style, hidden_frac, rng, tick) -> None:
    true_conf = 0.1 if hidden_frac < 0.5 else 0.7
    noisy = true_conf + rng.gauss(0, EVIDENCE_NOISE)
    noisy = max(0.02, min(0.98, noisy))
    for f in features:
        atomspace.add_link("evidence", f"evidence:{f}:{style}", "seen",
                           confidence=noisy, ttl=tick)


def _evidence_pool(atomspace, features, style, budget: int) -> list[dict]:
    pool = []
    for f in features:
        pool += atomspace.query_links("evidence", a=f"evidence:{f}:{style}")
    if len(pool) > budget:
        pool = sorted(pool, key=lambda l: l["confidence"] * l.get("ttl", 0),
                      reverse=True)[:budget]
    return pool


def _prior(active: list[str], atomspace, features, style, budget: int) -> float:
    pool = _evidence_pool(atomspace, features, style, budget)
    if not pool:
        return 0.0
    if "memory_consolidation" in active:
        # confidence-weighted consolidation: average across ALL confirmations
        return (sum(l["confidence"] for l in pool) / len(pool)) - NEUTRAL
    # single-shot recall: the most recent observation wins (last-write memory)
    latest = pool[-1]
    return latest["confidence"] - NEUTRAL


def run(active: list[str], atomspace: AtomSpace, pipe: HookPipe, seed: int) -> dict:
    rng = random.Random(seed)
    ctx = {m: {} for m in active}
    budget = 1000 if "attention_budget" not in active else 4

    passes = _styles_passes()
    bugs = _bugs(rng)
    hidden_fracs = []
    tried = []
    rescues = 0
    history = []

    for bug in bugs:
        ctx = pipe.before_eval(ctx, atomspace) if active else ctx
        cands = []
        for style in bug["order"]:
            pass_set = passes[style]
            vis = len([t for t in pass_set if t < VISIBLE]) / VISIBLE
            cands.append({"style": style, "vis": vis, "pass_set": pass_set})

        best, best_score = None, None
        for cand in cands:
            prior = _prior(active, atomspace, bug["features"], cand["style"], budget)
            score = cand["vis"] + prior
            if best_score is None or score > best_score:
                best, best_score = cand, score

        hidden_pass = [t for t in best["pass_set"] if t >= VISIBLE]
        hidden_frac = len(hidden_pass) / (N_TESTS - VISIBLE)
        hidden_fracs.append(hidden_frac)
        tried.append(len(cands))
        history.append((bug["name"], best["style"], round(hidden_frac, 2)))
        if hidden_frac == 0.0:
            rescues += 1
        _write_evidence(atomspace, bug["features"], best["style"], hidden_frac,
                        rng, tick=len(history))
        for f in bug["features"]:
            ctx = pipe.after_write(ctx, atomspace,
                                   key=f"evidence:{f}:{best['style']}",
                                   confidence=hidden_frac)

    success_rate = sum(hidden_fracs) / len(hidden_fracs)
    return {
        "env": "repoops",
        "success_rate": round(success_rate, 4),
        "human_rescue": rescues,
        "robustness": round(min(hidden_fracs), 4),
        "steps": round(sum(tried) / len(tried), 1),
        "_history": history,
    }
