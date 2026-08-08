"""Chaining protocol for phase 2: does the uplift loop COMPOUND?

Phase 1 measured every candidate against the EMPTY baseline, so cycles never
chained. This module measures each candidate against the CURRENT INCUMBENT hive
state on a 21-seed set (EXT_SEEDS) for statistical power, with the 7
constitutional seeds re-run for apples-to-apples comparability with phase 1.

Protocol (per candidate, in order A then B):
  before = aggregate(incumbent, seeds=EXT_SEEDS)
  after  = aggregate(incumbent + [mech], seeds=EXT_SEEDS)
  verdict = apply_rule(before, after, mech)     # 21-seed verdict is binding
  also log the same deltas on the 7 constitutional seeds
  record scorecard, update hive_state if PROMOTE, git-commit the checkpoint

The incumbent for B is the post-A hive state IF A was promoted (true chaining),
otherwise the original phase-1 incumbent.

Read-only w.r.t. the inviolable core: it imports aggregate() and apply_rule()
but never modifies driver.py / governance.py / runner.py / mechanisms.

Run:
  python3 -m loop.chaining            # full protocol (baseline + A + B)
  python3 -m loop.chaining --candidate A|B
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from eval_ecology.runner import aggregate, run_ecology  # noqa: E402
from loop.governance import apply_rule  # noqa: E402

CONST_SEEDS = [101, 202, 303, 404, 505, 606, 707]
EXT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203,
             1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

MECH_A = "residual_bias"      # designed for RepoOps (different domain)
MECH_B = "frontier_memory"    # designed to compound in Maze

# phase-3 hypothesis-testing candidates
MECH_C = "frontier_memory_v2"     # tests H1: calibrated frontier memory (Maze)
MECH_D = "evidence_substrate"     # tests H2: multi-domain substrate (Maze+RepoOps)

STATE_PATH = os.path.join(ROOT, "checkpoints", "hive_state.json")
CHAIN_PATH = os.path.join(ROOT, "checkpoints", "chaining_state.json")
SCORECARDS = os.path.join(ROOT, "logs", "scorecards")
DECISIONS = os.path.join(ROOT, "logs", "decisions.log")


def log_decision(kind: str, text: str) -> None:
    with open(DECISIONS, "a") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {kind}: {text}\n")


def load_json(path: str, default):
    if os.path.exists(path):
        with open(path) as fh:
            return json.load(fh)
    return default


def save_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)


def git_commit(message: str) -> bool:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if not dirty:
        return False
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT, check=True,
                   capture_output=True)
    log_decision("GIT", f"committed {message}")
    return True


def per_env_delta(before: dict, after: dict) -> dict:
    """Per-domain primary delta (success-oriented, same as governance primaries)."""
    out = {}
    for name in ("maze", "repoops", "selflab"):
        b = before["primaries"].get(name, before["envs"][name]["success_rate"])
        a = after["primaries"].get(name, after["envs"][name]["success_rate"])
        out[name] = round(a - b, 4)
    return out


def write_scorecards(chain, mech, incumbent, b21, a21, v21, b7, a7, v7,
                     transfer) -> None:
    os.makedirs(SCORECARDS, exist_ok=True)
    data = {
        "phase": "chained",
        "name": chain,
        "mechanism": mech,
        "incumbent": incumbent,
        "ext_seeds": EXT_SEEDS,
        "const_seeds": CONST_SEEDS,
        "before_21": b21, "after_21": a21, "verdict_21": v21,
        "before_7": b7, "after_7": a7, "verdict_7": v7,
        "per_env_delta_21": per_env_delta(b21, a21),
        "transfer_probe": transfer,
    }
    with open(os.path.join(SCORECARDS, f"{chain}.json"), "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)

    md = [
        f"# Scorecard: {chain}", "",
        f"- mechanism: `{mech}`",
        f"- incumbent: {incumbent}",
        f"- ext seeds (21): {EXT_SEEDS}", f"- const seeds (7): {CONST_SEEDS}", "",
        "## 21-seed chained verdict (binding)", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v21['before_primary']} | {v21['after_primary']} | {v21['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v21['before_robustness']} | {v21['after_robustness']} | {v21['delta_robustness']:+.4f} |",
        "",
        f"**VERDICT (21 seeds): {v21['verdict']}**  (rel primary {v21['rel_delta_primary']:+.1%})",
        "",
        "| env | before primary | after primary | delta |", "|---|---|---|---|",
    ]
    for name in ("maze", "repoops", "selflab"):
        b = b21["primaries"].get(name, b21["envs"][name]["success_rate"])
        a = a21["primaries"].get(name, a21["envs"][name]["success_rate"])
        md.append(f"| {name} | {b:.4f} | {a:.4f} | {a - b:+.4f} |")
    md += [
        "", "## 7-seed constitutional re-run (apples-to-apples vs phase 1)", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v7['before_primary']} | {v7['after_primary']} | {v7['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v7['before_robustness']} | {v7['after_robustness']} | {v7['delta_robustness']:+.4f} |",
        "", f"**VERDICT (7 seeds): {v7['verdict']}**  (rel primary {v7['rel_delta_primary']:+.1%})",
        "", "## Transfer probe (domain not designed for)", "",
        f"- mechA in Maze (not designed for): {transfer.get('mechA_in_maze')}",
        f"- mechB in RepoOps (not designed for): {transfer.get('mechB_in_repoops')}",
        f"- mechB in SelfLab (not designed for): {transfer.get('mechB_in_selflab')}",
        "",
    ]
    with open(os.path.join(SCORECARDS, f"{chain}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


def run_candidate(state, chaining, mech, cycle: int, incumbent: list[str]) -> dict:
    log_decision("INFO", f"chained-cycle-{cycle} starts; mech={mech} incumbent={incumbent}")

    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    a21 = aggregate(incumbent + [mech], seeds=EXT_SEEDS)
    v21 = apply_rule(b21, a21, mech)

    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    a7 = aggregate(incumbent + [mech], seeds=CONST_SEEDS)
    v7 = apply_rule(b7, a7, mech)

    # transfer probe: per-domain delta of the OTHER domains
    env_d = per_env_delta(b21, a21)
    transfer = {
        "mechA_in_maze": env_d["maze"],
        "mechB_in_repoops": env_d["repoops"],
        "mechB_in_selflab": env_d["selflab"],
    }

    name = f"chained-cycle-{cycle}-{mech}"
    write_scorecards(name, mech, incumbent, b21, a21, v21, b7, a7, v7, transfer)

    log_decision(
        "GOVERNOR",
        f"chained-cycle-{cycle} {mech}: 21seed before={v21['before_primary']:.4f} "
        f"after={v21['after_primary']:.4f} rel={v21['rel_delta_primary']:+.1%} "
        f"rob={v21['delta_robustness']:+.4f} => {v21['verdict']}  "
        f"| 7seed rel={v7['rel_delta_primary']:+.1%} verdict={v7['verdict']}  "
        f"| per-env {env_d}")
    log_decision("GOVERNOR",
                 f"chained-cycle-{cycle} transfer probe: {transfer}")

    result = {"cycle": cycle, "mech": mech, "incumbent": list(incumbent),
              "verdict_21": v21, "verdict_7": v7, "per_env_delta_21": env_d,
              "transfer_probe": transfer}

    if v21["verdict"] == "PROMOTE":
        state["active"] = list(incumbent + [mech])
        state["promoted"] = list(dict.fromkeys(state["promoted"] + [mech]))
        log_decision("INFO", f"chained-cycle-{cycle} PROMOTED {mech}; "
                             f"active now {state['active']}")
    elif v21["verdict"] == "PARK":
        state["parked"] = list(dict.fromkeys(state["parked"] + [mech]))
    else:
        state["rejected"] = list(dict.fromkeys(state["rejected"] + [mech]))

    state["cycles"][f"chained-{cycle}"] = {
        "mechanism": mech, "verdict": v21["verdict"],
        "active_after": list(state["active"]),
        "before_primary": v21["before_primary"],
        "after_primary": v21["after_primary"],
        "rel_delta_primary": v21["rel_delta_primary"],
        "delta_robustness": v21["delta_robustness"],
    }
    save_json(STATE_PATH, state)
    chaining["results"][mech] = result
    chaining["incumbent"] = list(state["active"])
    save_json(CHAIN_PATH, chaining)

    git_commit(f"chained-cycle-{cycle}-{mech}-{v21['verdict'].lower()}")
    return result


def run_baseline(state, chaining) -> None:
    b21 = aggregate(state["active"], seeds=EXT_SEEDS)
    b7 = aggregate(state["active"], seeds=CONST_SEEDS)
    data = {"incumbent": list(state["active"]), "baseline_21": b21,
            "baseline_7": b7, "seeds_21": EXT_SEEDS, "seeds_7": CONST_SEEDS}
    chaining.update(data)
    save_json(CHAIN_PATH, chaining)
    log_decision("INFO", f"chained baseline measured: 21seed primary="
                         f"{b21['aggregate_primary']:.4f} robust={b21['aggregate_robustness']:.4f}; "
                         f"7seed primary={b7['aggregate_primary']:.4f}")
    git_commit("chained-baseline")
    print(f"chained-baseline: incumbent={state['active']} "
          f"21seed primary={b21['aggregate_primary']:.4f} "
          f"7seed primary={b7['aggregate_primary']:.4f}")


# ---------------------------------------------------------------------------
# PHASE 3: hypothesis-testing chaining (H1 calibration, H2 multi-domain).
# New code path only; the phase-2 protocol above is untouched.
# ---------------------------------------------------------------------------

PHASE3_C = ("frontier_memory_v2", 3, "maze")   # (mech, cycle, target domain)
PHASE3_D = ("evidence_substrate", 4, "maze")   # D is multi-domain (maze+repoops)


def _primary_of(name: str, env: dict) -> float:
    if name == "maze":
        return 0.5 * env["success_rate"] + 0.5 * env["efficiency"]
    return env["success_rate"]


def _per_seed_primaries(active: list[str], seed: int) -> dict:
    r = run_ecology(active, seed)
    return {n: _primary_of(n, r["envs"][n]) for n in ("maze", "repoops", "selflab")}


def _variance_band(incumbent: list[str], mech: str, domain: str,
                   seeds: list[int]) -> dict:
    """Per-seed primary deltas for the target domain (mean/sd/min/max)."""
    deltas = []
    for seed in seeds:
        b = _per_seed_primaries(incumbent, seed)[domain]
        a = _per_seed_primaries(incumbent + [mech], seed)[domain]
        deltas.append(a - b)
    n = len(deltas)
    mean = sum(deltas) / n
    sd = (sum((d - mean) ** 2 for d in deltas) / n) ** 0.5
    return {"domain": domain, "count": n, "mean": round(mean, 4),
            "sd": round(sd, 4), "min": round(min(deltas), 4),
            "max": round(max(deltas), 4),
            "positive": sum(1 for d in deltas if d > 0),
            "negative": sum(1 for d in deltas if d < 0)}


def write_p3_scorecards(name, mech, incumbent, target_domain, b21, a21, v21,
                        b7, a7, v7, per_env, transfer, variance) -> None:
    os.makedirs(SCORECARDS, exist_ok=True)
    data = {
        "phase": "phase3",
        "name": name,
        "mechanism": mech,
        "incumbent": incumbent,
        "target_domain": target_domain,
        "ext_seeds": EXT_SEEDS,
        "const_seeds": CONST_SEEDS,
        "before_21": b21, "after_21": a21, "verdict_21": v21,
        "before_7": b7, "after_7": a7, "verdict_7": v7,
        "per_env_delta_21": per_env,
        "transfer_probe": transfer,
        "variance_target": variance,
    }
    with open(os.path.join(SCORECARDS, f"{name}.json"), "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)

    v = variance
    md = [
        f"# Scorecard: {name} (phase 3)", "",
        f"- mechanism: `{mech}`", f"- incumbent: {incumbent}",
        f"- target domain: {target_domain}",
        f"- ext seeds (21): {EXT_SEEDS}", f"- const seeds (7): {CONST_SEEDS}", "",
        "## 21-seed chained verdict (binding)", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v21['before_primary']} | {v21['after_primary']} | {v21['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v21['before_robustness']} | {v21['after_robustness']} | {v21['delta_robustness']:+.4f} |",
        "",
        f"**VERDICT (21 seeds): {v21['verdict']}**  (rel primary {v21['rel_delta_primary']:+.1%})",
        "",
        "| env | before primary | after primary | delta |", "|---|---|---|---|",
    ]
    for name_e in ("maze", "repoops", "selflab"):
        b = b21["primaries"].get(name_e, b21["envs"][name_e]["success_rate"])
        a = a21["primaries"].get(name_e, a21["envs"][name_e]["success_rate"])
        md.append(f"| {name_e} | {b:.4f} | {a:.4f} | {a - b:+.4f} |")
    md += [
        "", "## Target-domain per-seed variance (21 seeds)", "",
        f"- {v['domain']} primary delta: mean={v['mean']:+.4f} sd={v['sd']:.4f} "
        f"min={v['min']:+.4f} max={v['max']:+.4f}",
        f"- positive on {v['positive']}/{v['count']}, negative on {v['negative']}/{v['count']}",
        "", "## 7-seed constitutional re-run", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v7['before_primary']} | {v7['after_primary']} | {v7['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v7['before_robustness']} | {v7['after_robustness']} | {v7['delta_robustness']:+.4f} |",
        "", f"**VERDICT (7 seeds): {v7['verdict']}**  (rel primary {v7['rel_delta_primary']:+.1%})",
        "", "## Transfer probe", "",
    ]
    for k, val in transfer.items():
        md.append(f"- {k}: {val:+.4f}")
    md.append("")
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


def run_phase3_candidate(state, chaining, mech, cycle: int, incumbent: list[str],
                         target_domain: str, transfer_keys: list[str]) -> dict:
    log_decision("INFO", f"phase3 cycle-{cycle} starts; mech={mech} "
                         f"incumbent={incumbent} target={target_domain}")
    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    a21 = aggregate(incumbent + [mech], seeds=EXT_SEEDS)
    v21 = apply_rule(b21, a21, mech)

    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    a7 = aggregate(incumbent + [mech], seeds=CONST_SEEDS)
    v7 = apply_rule(b7, a7, mech)

    per_env = per_env_delta(b21, a21)
    transfer = {k: per_env.get(d, 0.0) for k, d in transfer_keys}
    variance = _variance_band(incumbent, mech, target_domain, EXT_SEEDS)

    name = f"p3-cycle-{cycle}-{mech}"
    write_p3_scorecards(name, mech, incumbent, target_domain, b21, a21, v21,
                        b7, a7, v7, per_env, transfer, variance)

    log_decision(
        "GOVERNOR",
        f"phase3-cycle-{cycle} {mech}: 21seed before={v21['before_primary']:.4f} "
        f"after={v21['after_primary']:.4f} rel={v21['rel_delta_primary']:+.1%} "
        f"rob={v21['delta_robustness']:+.4f} => {v21['verdict']}  "
        f"| 7seed rel={v7['rel_delta_primary']:+.1%} verdict={v7['verdict']}  "
        f"| per-env {per_env}")
    log_decision(
        "GOVERNOR",
        f"phase3-cycle-{cycle} target-domain variance ({target_domain}, 21 seeds): "
        f"mean={variance['mean']:+.4f} sd={variance['sd']:.4f} "
        f"min={variance['min']:+.4f} max={variance['max']:+.4f} "
        f"positive {variance['positive']}/{variance['count']} "
        f"negative {variance['negative']}/{variance['count']}")
    log_decision("GOVERNOR", f"phase3-cycle-{cycle} transfer probe: {transfer}")

    result = {"cycle": cycle, "mech": mech, "incumbent": list(incumbent),
              "target_domain": target_domain, "verdict_21": v21,
              "verdict_7": v7, "per_env_delta_21": per_env,
              "transfer_probe": transfer, "variance_target": variance,
              "scorecard": name}

    if v21["verdict"] == "PROMOTE":
        state["active"] = list(incumbent + [mech])
        state["promoted"] = list(dict.fromkeys(state["promoted"] + [mech]))
        log_decision("INFO", f"phase3-cycle-{cycle} PROMOTED {mech}; "
                             f"active now {state['active']}")
    elif v21["verdict"] == "PARK":
        state["parked"] = list(dict.fromkeys(state["parked"] + [mech]))
    else:
        state["rejected"] = list(dict.fromkeys(state["rejected"] + [mech]))

    state["cycles"][f"chained-{cycle}"] = {
        "mechanism": mech, "verdict": v21["verdict"],
        "active_after": list(state["active"]),
        "before_primary": v21["before_primary"],
        "after_primary": v21["after_primary"],
        "rel_delta_primary": v21["rel_delta_primary"],
        "delta_robustness": v21["delta_robustness"],
    }
    save_json(STATE_PATH, state)
    chaining["results"][mech] = result
    chaining["incumbent"] = list(state["active"])
    save_json(CHAIN_PATH, chaining)

    git_commit(f"chained-cycle-{cycle}-{mech}-{v21['verdict'].lower()}")
    return result


def run_phase3(state, chaining) -> dict:
    """True chaining: C vs incumbent; if C promotes, D measures against the
    [incumbent + C] state, else D measures against the original incumbent."""
    incumbent = list(chaining["incumbent"] or state["active"])
    log_decision("ARCHITECT", f"phase3 baseline incumbent={incumbent}")

    # re-measure the incumbent fresh so phase-3 numbers are internally consistent
    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    chaining["baseline_21"] = b21
    chaining["baseline_7"] = b7
    save_json(CHAIN_PATH, chaining)
    log_decision("INFO", f"phase3 baseline measured: 21seed primary="
                         f"{b21['aggregate_primary']:.4f} robust="
                         f"{b21['aggregate_robustness']:.4f}; 7seed primary="
                         f"{b7['aggregate_primary']:.4f}")

    mech_c, cycle_c, domain_c = PHASE3_C
    res_c = run_phase3_candidate(
        state, chaining, mech_c, cycle_c, incumbent, domain_c,
        transfer_keys=[("mechC_in_repoops", "repoops"),
                       ("mechC_in_selflab", "selflab")])

    # true chaining: D's incumbent depends on whether C promoted
    mech_d, cycle_d, domain_d = PHASE3_D
    incumbent_d = list(chaining["incumbent"])
    res_d = run_phase3_candidate(
        state, chaining, mech_d, cycle_d, incumbent_d, domain_d,
        transfer_keys=[("mechD_in_selflab", "selflab"),
                       ("mechD_in_maze", "maze"),
                       ("mechD_in_repoops", "repoops")])

    return {"c": res_c, "d": res_d}


def main() -> None:
    parser = argparse.ArgumentParser(description="OmegaHive chaining protocol (phase 2)")
    parser.add_argument("--candidate", choices=["A", "B"], default=None,
                        help="run a single candidate only")
    parser.add_argument("--phase3", action="store_true",
                        help="run the phase-3 hypothesis-testing chaining")
    args = parser.parse_args()

    state = load_json(STATE_PATH, {"active": [], "promoted": [], "parked": [],
                                   "rejected": [], "cycles": {}})
    chaining = load_json(CHAIN_PATH, {"results": {}})

    base_incumbent = list(state["active"])
    if not base_incumbent:
        raise RuntimeError("hive_state has empty active set; phase-1 state required")

    if args.phase3:
        res = run_phase3(state, chaining)
        final = {"active": state["active"], "promoted": state["promoted"],
                 "parked": state["parked"], "rejected": state["rejected"]}
        print(json.dumps({"phase3_final": final,
                          "cycle3": {"verdict": res["c"]["verdict_21"]["verdict"],
                                     "rel": res["c"]["verdict_21"]["rel_delta_primary"],
                                     "variance": res["c"]["variance_target"]},
                          "cycle4": {"verdict": res["d"]["verdict_21"]["verdict"],
                                     "rel": res["d"]["verdict_21"]["rel_delta_primary"],
                                     "incumbent": res["d"]["incumbent"],
                                     "variance": res["d"]["variance_target"]}},
                         indent=2))
        log_decision("INFO", "phase3 finished; final active set: "
                             f"{state['active']} promoted={state['promoted']} "
                             f"parked={state['parked']} rejected={state['rejected']}")
        return

    run_baseline(state, chaining)

    cands = {"A": MECH_A, "B": MECH_B}
    order = ["A", "B"] if not args.candidate else [args.candidate]

    for label in order:
        mech = cands[label]
        incumbent = list(chaining["incumbent"])
        run_candidate(state, chaining, mech, 1 if label == "A" else 2, incumbent)

    final = {"active": state["active"], "promoted": state["promoted"],
             "parked": state["parked"], "rejected": state["rejected"]}
    print(json.dumps({"final": final,
                      "results": {k: {"verdict": v["verdict_21"]["verdict"],
                                      "rel": v["verdict_21"]["rel_delta_primary"],
                                      "incumbent": v["incumbent"]}
                                  for k, v in chaining["results"].items()}},
                     indent=2))
    log_decision("INFO", "chaining finished; final active set: "
                         f"{state['active']} promoted={state['promoted']} "
                         f"parked={state['parked']} rejected={state['rejected']}")


if __name__ == "__main__":
    main()
