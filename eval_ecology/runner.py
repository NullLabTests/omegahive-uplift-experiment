"""Ecology runner: runs all environments, merges score vectors, computes the
aggregate primary metric and robustness that governance uses.

The scoring semantics here are CONSTITUTIONAL (Article II): mechanisms and the
driver may not change them. A seed is run for each env and scores averaged so
results are stable and honest.

Aggregate primary = weighted mean of the envs' primary metrics (maze success
rate, repoops hidden success, selflab quality normalized).
Aggregate robustness = min of the envs' robustness-sensitive values.
"""

from __future__ import annotations

import random

from hive.atomspace import AtomSpace
from hive.hooks import HookPipe, load_registry
from eval_ecology import env_maze, env_repoops, env_selflab

SEEDS = [101, 202, 303, 404, 505, 606, 707]
ROSTER = ["memory_consolidation", "attention_budget", "uncertainty_planning"]


def _average(metrics: list[dict]) -> dict:
    out = {}
    keys = [k for k in metrics[0] if not k.startswith("_")]
    for key in keys:
        vals = [m[key] for m in metrics]
        if any(not isinstance(v, (int, float)) for v in vals):
            out[key] = vals[0]
        elif all(isinstance(v, int) for v in vals):
            out[key] = sum(vals) / len(vals)
        else:
            out[key] = round(sum(vals) / len(vals), 4)
    return out


def run_ecology(active: list[str], seed: int) -> dict:
    """Run all three envs with a FRESH atomspace and the given active set."""
    registry = load_registry()
    atomspace = AtomSpace()
    pipe = HookPipe(active, registry)

    # constitutional hooks run in roster order before any env work
    ctx = {m: {} for m in active}
    for hook in ("before_eval",):
        ctx = getattr(pipe, hook)(ctx, atomspace) if active else ctx

    results = {}
    for env_run, name in ((env_maze.run, "maze"),
                          (env_repoops.run, "repoops"),
                          (env_selflab.run, "selflab")):
        try:
            results[name] = env_run(active, atomspace, pipe, seed)
        except Exception as exc:  # noqa: BLE001 - a failed env must not kill the run
            results[name] = {"env": name, "success_rate": 0.0, "efficiency": 0.0,
                             "robustness": 0.0, "steps": 0.0, "_error": str(exc)}

    return {"seed": seed, "active": active, "envs": results,
            "memory": atomspace.snapshot()}


def _primary(env: dict, name: str) -> float:
    if name == "maze":
        # navigation quality = reach the goal AND do it efficiently
        return 0.5 * env["success_rate"] + 0.5 * env["efficiency"]
    if name == "repoops":
        return env["success_rate"]
    return env["success_rate"]


def _robust(env: dict, name: str) -> float:
    if name == "maze":
        return env["robustness"]
    if name == "repoops":
        return env["robustness"]
    return env["success_rate"]


def aggregate(active: list[str], seeds: list[int] | None = None,
              verbose: bool = False) -> dict:
    """Run the full ecology over seeds and produce the official score vector."""
    seeds = seeds or SEEDS
    per_seed = []
    for seed in seeds:
        per_seed.append(run_ecology(active, seed))
    env_avgs = {}
    for name in ("maze", "repoops", "selflab"):
        env_avgs[name] = _average([p["envs"][name] for p in per_seed])

    primaries = {name: _primary(env_avgs[name], name) for name in env_avgs}
    rob = {name: _robust(env_avgs[name], name) for name in env_avgs}
    aggregate_primary = 0.40 * primaries["maze"] + 0.35 * primaries["repoops"] + 0.25 * primaries["selflab"]
    aggregate_robustness = min(rob.values())

    score = {
        "active": list(active),
        "seeds": seeds,
        "aggregate_primary": round(aggregate_primary, 4),
        "aggregate_robustness": round(aggregate_robustness, 4),
        "envs": env_avgs,
        "primaries": primaries,
    }
    if verbose:
        for name, e in env_avgs.items():
            print(f"  {name:8s} primary={_primary(e, name):.3f} "
                  f"robust={_robust(e, name):.3f} { {k: v for k, v in e.items() if not k.startswith('_')} }")
    return score
