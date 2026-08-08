"""Phase-6 PROPOSAL-STATE SUBSTRATE (NEW, experimental, NOT constitutional).

The in-band channel by which history reaches future proposals. A JSON store
(checkpoints/p6_proposal_state.json) maintained from REAL scorecards only:

  - headroom             per-domain {current_primary, max_observed_primary,
                           remaining_headroom (=1-current, capacity), weight}
  - promotion_signatures per-domain relative deltas of every promoted mechanism,
                           tagged by hook-class touched
  - overlap_table        hook-touch set per known mechanism (derived by importing
                           each mechanism's HOOKS via hive.hooks.load_registry)
  - proposal_log         every memo emitted + resulting mechanism delta

If a cycle runs without this store, that is a baseline-condition arm, logged as
such (loop/chain_second_loop.py, arm 0: empty memo, probe on default config).
This module is read-only w.r.t. the inviolable core; it only imports
hive.hooks.load_registry (no mechanism, env, driver, or governance code).

Run:  (no CLI; imported by loop/chain_second_loop.py)
"""

from __future__ import annotations

import copy
import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from hive.hooks import load_registry  # noqa: E402

DOMAINS = ("maze", "repoops", "selflab")
WEIGHTS = {"maze": 0.40, "repoops": 0.35, "selflab": 0.25}
TASK_HOOKS = ("before_eval", "choose_action", "after_write", "retrieve")

STATE_PATH = os.path.join(ROOT, "checkpoints", "p6_proposal_state.json")


def load(path: str = STATE_PATH) -> dict | None:
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return None


def save(state: dict, path: str = STATE_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)


def overlap_table() -> dict:
    """Hook-touch set per known mechanism, derived by importing each HOOKS."""
    registry = load_registry(os.path.join(ROOT, "mechanisms"))
    table = {}
    for name, mod in registry.items():
        hooks = sorted(getattr(mod, "HOOKS", {}).keys())
        if hooks:
            table[name] = hooks
    return table


def build_initial() -> dict:
    """Initial proposal state from the REAL phase-1..5 scorecards only."""
    current = {"maze": 0.9188, "repoops": 0.9881, "selflab": 0.9386}
    headroom = {}
    for d in DOMAINS:
        headroom[d] = {
            "current_primary": current[d],
            "max_observed_primary": current[d],
            "headroom_below_max": 0.0,
            "remaining_headroom": round(1 - current[d], 4),
            "weight": WEIGHTS[d],
        }

    promotion_signatures = [
        {
            "mechanism": "uncertainty_planning", "domain": "maze",
            "rel_delta": 0.3994, "hook_classes": ["choose_action"],
            "source": "phase-1 promotion (7 seeds): maze primary 0.5898 -> 0.82535",
        },
        {
            "mechanism": "residual_bias", "domain": "repoops",
            "rel_delta": 0.0779, "hook_classes": ["after_write"],
            "source": "phase-4 promotion (21 seeds): repoops +7.79% rel",
        },
        {
            "mechanism": "progress_thermostat", "domain": "maze",
            "rel_delta": 0.1165, "hook_classes": ["choose_action"],
            "source": "phase-5 promotion (21 seeds): maze +11.65% rel",
        },
    ]

    proposal_log = [
        {
            "id": 1, "condition": "historical", "mechanism": "residual_bias",
            "target_domain": "repoops", "hook_class": "after_write",
            "aggregate_delta": 0.0250, "rel_delta": 0.0283,
            "maze_delta_mean": 0.0, "maze_delta_sd": 0.0, "count": 21,
            "negative_seeds": 0,
            "failure_signature": "none (clean; repoops ceiling reached)",
        },
        {
            "id": 2, "condition": "historical", "mechanism": "frontier_memory",
            "target_domain": "maze", "hook_class": "choose_action",
            "aggregate_delta": 0.0056, "rel_delta": 0.0063,
            "maze_delta_mean": 0.0141, "maze_delta_sd": 0.1430, "count": 21,
            "negative_seeds": None,
            "failure_signature": "single-episode penalization made credit "
                                 "noise-dominated (per-seed maze sd 0.143 vs "
                                 "mean +0.014; worst single-seed -0.53)",
        },
        {
            "id": 3, "condition": "historical", "mechanism": "frontier_memory_v2",
            "target_domain": "maze", "hook_class": "choose_action",
            "aggregate_delta": 0.0123, "rel_delta": 0.0139,
            "maze_delta_mean": 0.0309, "maze_delta_sd": 0.1146, "count": 21,
            "negative_seeds": 5,
            "failure_signature": "calibrated success-gated >=2-confirmation "
                                 "credit recovered a small real gain; 5/21 "
                                 "seeds still negative",
        },
        {
            "id": 4, "condition": "historical", "mechanism": "evidence_substrate",
            "target_domain": "maze", "hook_class": "choose_action",
            "aggregate_delta": 0.0373, "rel_delta": 0.0422,
            "maze_delta_mean": 0.0309, "maze_delta_sd": 0.1146, "count": 21,
            "negative_seeds": 5,
            "failure_signature": "multi-domain bundling was fully redundant with "
                                 "residual_bias on repoops (+0.0000 beyond rb)",
        },
        {
            "id": 5, "condition": "historical", "mechanism": "progress_thermostat",
            "target_domain": "maze", "hook_class": "choose_action",
            "aggregate_delta": 0.0383, "rel_delta": 0.0421,
            "maze_delta_mean": 0.0958, "maze_delta_sd": 0.1389, "count": 21,
            "negative_seeds": 3,
            "failure_signature": "none (clean; 17/21 positive)",
        },
    ]

    return {
        "domains": list(DOMAINS),
        "weights": dict(WEIGHTS),
        "active_hive": ["uncertainty_planning", "residual_bias",
                        "progress_thermostat"],
        "headroom": headroom,
        "promotion_signatures": promotion_signatures,
        "overlap_table": overlap_table(),
        "proposal_log": proposal_log,
        "next_log_id": 6,
    }


def permute_associations(state: dict, seed: int) -> dict:
    """Randomization-control copy (arm 2): shuffle domain<->hook-class
    associations.

    A seeded RNG draws a bijective permutation of the domain labels and of the
    hook-class labels, applied to every log entry and promotion signature. Every
    real measurement stays with its mechanism; only the ASSOCIATIONS are
    relabeled, so a strategy reading the copy emits a memo of identical format
    whose attributions are scrambled (the domain/hook-class of every historical
    success and failure is mis-attributed).
    """
    st = copy.deepcopy(state)
    rng = random.Random(seed)

    doms = list(st.get("domains", list(DOMAINS)))
    dom_perm = doms[:]
    rng.shuffle(dom_perm)
    classes = ["choose_action", "after_write", "retrieve", "before_eval"]
    cls_perm = classes[:]
    rng.shuffle(cls_perm)
    dmap = dict(zip(doms, dom_perm))
    cmap = dict(zip(classes, cls_perm))

    for e in st.get("proposal_log", []):
        if e.get("target_domain") in dmap:
            e["target_domain"] = dmap[e["target_domain"]]
        if e.get("hook_class") in cmap:
            e["hook_class"] = cmap[e["hook_class"]]

    for s in st.get("promotion_signatures", []):
        if s.get("domain") in dmap:
            s["domain"] = dmap[s["domain"]]
        if s.get("hook_classes"):
            s["hook_classes"] = [cmap.get(c, c) for c in s["hook_classes"]]

    st["permutation"] = {"seed": seed, "domain_map": dmap,
                         "hook_class_map": cmap}
    return st
