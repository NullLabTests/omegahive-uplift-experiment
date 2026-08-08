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

from eval_ecology.runner import aggregate  # noqa: E402
from loop.governance import apply_rule  # noqa: E402

CONST_SEEDS = [101, 202, 303, 404, 505, 606, 707]
EXT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203,
             1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

MECH_A = "residual_bias"      # designed for RepoOps (different domain)
MECH_B = "frontier_memory"    # designed to compound in Maze

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


def main() -> None:
    parser = argparse.ArgumentParser(description="OmegaHive chaining protocol (phase 2)")
    parser.add_argument("--candidate", choices=["A", "B"], default=None,
                        help="run a single candidate only")
    args = parser.parse_args()

    state = load_json(STATE_PATH, {"active": [], "promoted": [], "parked": [],
                                   "rejected": [], "cycles": {}})
    chaining = load_json(CHAIN_PATH, {"results": {}})

    base_incumbent = list(state["active"])
    if not base_incumbent:
        raise RuntimeError("hive_state has empty active set; phase-1 state required")

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
