"""Env C: SELF-LAB — the hive improves one of its own modules.

The hive's `hive/tools.py` exposes `fuzzy_match` with several candidate
implementations of known true quality. The hive runs a NOISY sample benchmark:
the first samples are systematically more noisy (warm-up), later ones are
clean. It stores each sample in the shared AtomSpace as a link
`sample:{cand} -> score`, then selects the candidate whose estimated quality is
best. The full-benchmark quality of the selection is the reward.

attention_budget improves the estimate by ranking retrieved samples by
salience (recency) and capping the pool, dropping the noisy warm-up samples.
memory_consolidation merges duplicate sample links.

Score vector: quality (full-benchmark of selected impl, normalized),
human_rescue (1 if the worst impl was chosen), steps (samples run),
robustness (best-minimum across seeds is handled by the runner).
"""

from __future__ import annotations

import random

from hive.atomspace import AtomSpace
from hive.hooks import HookPipe
import hive.tools as tools

N_SAMPLES = 6
WARMUP = 2
WARMUP_NOISE = 1.5
CLEAN_NOISE = 0.05
MAX_QUALITY = 0.88  # full-benchmark quality of the best candidate


def _full_quality(name: str) -> float:
    q = tools.CANDIDATES[name]["quality"]
    s = tools.CANDIDATES[name]["speed"]
    return q * (0.5 + 0.5 * min(s / 3.0, 1.0))


def run(active: list[str], atomspace: AtomSpace, pipe: HookPipe, seed: int) -> dict:
    rng = random.Random(seed)
    ctx = {m: {} for m in active}
    use_attention = "attention_budget" in active

    cands = list(tools.CANDIDATES.keys())
    for cand in cands:
        true_q = _full_quality(cand)
        for i in range(N_SAMPLES):
            warm = i < WARMUP
            noise = WARMUP_NOISE if warm else CLEAN_NOISE
            sample = max(0.0, min(1.0, true_q + rng.gauss(0, noise)))
            atomspace.add_link("sample", cand, str(round(sample, 4)),
                               confidence=sample, ttl=1 if warm else 5)

    estimates = {}
    for cand in cands:
        pool = atomspace.query_links("sample", a=cand)
        if use_attention:
            ctx = pipe.retrieve(ctx, atomspace, kind="sample", query=cand,
                                candidates=pool)
            kept = ctx["attention_budget"].get("candidates", pool)
        else:
            kept = pool
        if kept:
            estimates[cand] = sum(l["confidence"] for l in kept) / len(kept)
        else:
            estimates[cand] = 0.0

    best = max(estimates, key=estimates.get)
    tools.set_selected(best)
    quality = tools.quality_score()
    rescue = 1 if best == "v1_naive" else 0
    steps = len(cands) * N_SAMPLES

    return {
        "env": "selflab",
        "quality": round(quality, 4),
        "success_rate": round(quality / MAX_QUALITY, 4),
        "robustness": round(quality / MAX_QUALITY, 4),
        "human_rescue": rescue,
        "steps": steps,
        "_best": best,
        "_estimates": {k: round(v, 3) for k, v in estimates.items()},
    }
