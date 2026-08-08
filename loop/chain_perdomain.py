"""Phase-4 chaining under the EXPERIMENTAL per-domain promotion gate.

Falsification test of the Phase-3 counterfactual (logs/counterfactual.md):
the counterfactual claims that under a per-domain gate (PROMOTE iff ANY domain
primary rises >= +5% relative AND no domain drops > -3% relative) the loop would
promote residual_bias AND evidence_substrate, and that promoted IN SEQUENCE they
would give the loop its first genuine compounding event.

This module is an experimental protocol driver. It is read-only w.r.t. the
inviolable core (driver.py / governance.py / runner.py / mechanisms /
chaining.py / counterfactual.py): it imports aggregate() and the EXPERIMENTAL
gate only, and adds NEW files (loop/gate_perdomain.py, this module, scorecards,
state). The constitutional gate (loop/governance.py) is untouched.

Protocol:
  baseline: aggregate(INCUMBENT=["uncertainty_planning"], 21 seeds) + 7-seed run
  Cycle A : measure residual_bias  against the incumbent; per-domain verdict.
            If PROMOTE -> incumbent += residual_bias, else incumbent unchanged.
  Cycle B : measure evidence_substrate against the (possibly grown) incumbent;
            per-domain verdict. If PROMOTE -> incumbent += evidence_substrate.
  Stage   : if BOTH promoted, measure the final hive
            [uncertainty_planning, residual_bias, evidence_substrate] on 21
            seeds and record the aggregate (the headline number).

Scorecards: logs/scorecards/p4-*.{json,md}; decisions -> logs/decisions.log;
git commits: p4-baseline, p4-cycle-A-<mech>-<verdict>, p4-cycle-B-<mech>-<verdict>.

Run:  python3 -m loop.chain_perdomain
"""

from __future__ import annotations

import json
import os
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from eval_ecology.runner import aggregate, run_ecology  # noqa: E402
from loop import gate_perdomain  # noqa: E402
from loop.governance import apply_rule as constitutional_rule  # noqa: E402  (reference only)

CONST_SEEDS = [101, 202, 303, 404, 505, 606, 707]
EXT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203,
             1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

INCUMBENT = ["uncertainty_planning"]
MECH_A = "residual_bias"
MECH_B = "evidence_substrate"

STATE_PATH = os.path.join(ROOT, "checkpoints", "p4_state.json")
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
        log_decision("GIT", f"nothing to commit for {message}")
        return False
    subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT, check=True,
                   capture_output=True)
    log_decision("GIT", f"committed {message}")
    return True


def _primary_of(name: str, env: dict) -> float:
    if name == "maze":
        return 0.5 * env["success_rate"] + 0.5 * env["efficiency"]
    return env["success_rate"]


def per_seed_variance(incumbent: list[str], mech: str, domain: str,
                      seeds: list[int]) -> dict:
    """Per-seed primary deltas for one domain (mean/sd/min/max/counts)."""
    deltas = []
    for seed in seeds:
        b = run_ecology(incumbent, seed)["envs"][domain]
        a = run_ecology(incumbent + [mech], seed)["envs"][domain]
        deltas.append(_primary_of(domain, a) - _primary_of(domain, b))
    n = len(deltas)
    mean = sum(deltas) / n
    sd = statistics.pstdev(deltas) if n > 1 else 0.0
    return {"domain": domain, "count": n, "mean": round(mean, 4),
            "sd": round(sd, 4), "min": round(min(deltas), 4),
            "max": round(max(deltas), 4),
            "positive": sum(1 for d in deltas if d > 0),
            "negative": sum(1 for d in deltas if d < 0)}


def write_scorecard(name, mech, cycle, incumbent, b21, a21, v21, cref21,
                    b7, a7, v7, cref7, variance) -> None:
    os.makedirs(SCORECARDS, exist_ok=True)
    data = {
        "phase": "phase4",
        "name": name,
        "mechanism": mech,
        "cycle": cycle,
        "incumbent": incumbent,
        "gate": "per-domain (EXPERIMENTAL, not constitutional)",
        "ext_seeds": EXT_SEEDS,
        "const_seeds": CONST_SEEDS,
        "before_21": b21, "after_21": a21, "verdict_21": v21,
        "constitutional_reference_21": cref21,
        "before_7": b7, "after_7": a7, "verdict_7": v7,
        "constitutional_reference_7": cref7,
        "variance_promoting_domain": variance,
    }
    with open(os.path.join(SCORECARDS, f"{name}.json"), "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)

    dom = v21["domain_primaries"]
    rows = "".join(
        f"| {n} | {dom[n]['before']:.4f} | {dom[n]['after']:.4f} "
        f"| {dom[n]['delta']:+.4f} | {dom[n]['rel_delta']:+.4%} |"
        for n in ("maze", "repoops", "selflab"))
    vr = variance
    md = [
        f"# Scorecard: {name} (phase 4 — experimental per-domain gate)", "",
        f"- mechanism: `{mech}`",
        f"- incumbent: {incumbent}",
        f"- gate: **per-domain promotion gate** (EXPERIMENTAL, NOT constitutional): "
        f"PROMOTE iff ANY domain primary >= +5% rel AND no domain drop > -3% rel; "
        f"else PARK iff aggregate rel >= -5%, else REJECT.",
        f"- ext seeds (21): {EXT_SEEDS}", f"- const seeds (7): {CONST_SEEDS}", "",
        "## 21-seed per-domain verdict (binding for this experiment)", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v21['before_primary']} | {v21['after_primary']} | {v21['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v21['before_robustness']} | {v21['after_robustness']} | {v21['delta_robustness']:+.4f} |",
        "",
        f"**VERDICT (per-domain gate, 21 seeds): {v21['verdict']}**  "
        f"(promoting domain {v21['promoting_domain']} at {v21['promoting_domain_rel']:+.2%} rel; "
        f"worst domain {v21['worst_domain']} at {v21['worst_domain_rel']:+.2%} rel)",
        "",
        "| env | before primary | after primary | delta | rel delta |",
        "|---|---|---|---|---|", rows,
        "",
        f"Constitutional gate reference (21 seeds, unchanged rule): "
        f"{cref21['verdict']} (aggregate rel {cref21['rel_delta_primary']:+.2%})",
        "", "## Promoting-domain per-seed variance (21 seeds)", "",
        f"- {vr['domain']} primary delta: mean={vr['mean']:+.4f} sd={vr['sd']:.4f} "
        f"min={vr['min']:+.4f} max={vr['max']:+.4f}",
        f"- positive on {vr['positive']}/{vr['count']}, negative on {vr['negative']}/{vr['count']}",
        "", "## 7-seed constitutional re-run (reference)", "",
        "| metric | before | after | delta |", "|---|---|---|---|",
        f"| aggregate_primary | {v7['before_primary']} | {v7['after_primary']} | {v7['delta_primary']:+.4f} |",
        f"| aggregate_robustness | {v7['before_robustness']} | {v7['after_robustness']} | {v7['delta_robustness']:+.4f} |",
        "",
        f"**VERDICT (7 seeds): {v7['verdict']}**  (rel primary {v7['rel_delta_primary']:+.1%})",
        f"- constitutional reference (7 seeds): {cref7['verdict']} "
        f"(aggregate rel {cref7['rel_delta_primary']:+.2%})", "",
    ]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


def run_cycle(state, mech, cycle: int, incumbent: list[str]) -> dict:
    log_decision("INFO", f"p4-cycle-{cycle} starts; mech={mech} incumbent={incumbent}")

    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    a21 = aggregate(incumbent + [mech], seeds=EXT_SEEDS)
    v21 = gate_perdomain.apply_rule(b21, a21, mech)
    cref21 = constitutional_rule(b21, a21, mech)

    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    a7 = aggregate(incumbent + [mech], seeds=CONST_SEEDS)
    v7 = gate_perdomain.apply_rule(b7, a7, mech)
    cref7 = constitutional_rule(b7, a7, mech)

    dom = v21["promoting_domain"]
    variance = per_seed_variance(incumbent, mech, dom, EXT_SEEDS)

    name = f"p4-cycle-{cycle}-{mech}-{v21['verdict'].lower()}"
    write_scorecard(name, mech, cycle, incumbent, b21, a21, v21, cref21,
                    b7, a7, v7, cref7, variance)

    log_decision(
        "GOVERNOR",
        f"p4-cycle-{cycle} {mech}: per-domain 21seed before={v21['before_primary']:.4f} "
        f"after={v21['after_primary']:.4f} agg_rel={v21['rel_delta_primary']:+.2%} "
        f"promoting_domain={v21['promoting_domain']}@{v21['promoting_domain_rel']:+.2%} "
        f"worst_domain={v21['worst_domain']}@{v21['worst_domain_rel']:+.2%} "
        f"=> {v21['verdict']}  | constitutional reference={cref21['verdict']} "
        f"({cref21['rel_delta_primary']:+.2%})")
    log_decision(
        "GOVERNOR",
        f"p4-cycle-{cycle} per-domain rows: "
        f"{ {n: (v21['domain_primaries'][n]['rel_delta']) for n in ('maze','repoops','selflab')} }")
    log_decision(
        "GOVERNOR",
        f"p4-cycle-{cycle} {dom} variance (21 seeds): "
        f"mean={variance['mean']:+.4f} sd={variance['sd']:.4f} "
        f"min={variance['min']:+.4f} max={variance['max']:+.4f} "
        f"positive {variance['positive']}/{variance['count']} "
        f"negative {variance['negative']}/{variance['count']}")

    result = {"cycle": cycle, "mech": mech, "incumbent": list(incumbent),
              "verdict_21": v21, "verdict_7": v7,
              "constitutional_reference_21": cref21,
              "variance_promoting_domain": variance,
              "scorecard": name}

    if v21["verdict"] == "PROMOTE":
        state["active"] = list(incumbent + [mech])
        state["promoted"] = list(dict.fromkeys(state["promoted"] + [mech]))
        log_decision("INFO", f"p4-cycle-{cycle} PROMOTED {mech}; "
                             f"incumbent now {state['active']}")
    elif v21["verdict"] == "PARK":
        state["parked"] = list(dict.fromkeys(state["parked"] + [mech]))
    else:
        state["rejected"] = list(dict.fromkeys(state["rejected"] + [mech]))

    state["cycles"][f"p4-{cycle}"] = {
        "mechanism": mech, "verdict": v21["verdict"],
        "active_after": list(state["active"]),
        "before_primary": v21["before_primary"],
        "after_primary": v21["after_primary"],
        "rel_delta_primary": v21["rel_delta_primary"],
        "promoting_domain": v21["promoting_domain"],
        "promoting_domain_rel": v21["promoting_domain_rel"],
        "worst_domain_rel": v21["worst_domain_rel"],
    }
    save_json(STATE_PATH, state)
    git_commit(f"p4-cycle-{cycle}-{mech}-{v21['verdict'].lower()}")
    return result


def main() -> None:
    state = load_json(STATE_PATH, {"active": list(INCUMBENT), "promoted": [],
                                   "parked": [], "rejected": [], "cycles": {}})
    incumbent = list(INCUMBENT)

    # ---- baseline -----------------------------------------------------------
    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    state["baseline"] = {"incumbent": incumbent, "baseline_21": b21,
                         "baseline_7": b7}
    save_json(STATE_PATH, state)
    log_decision("INFO", f"p4-baseline measured: 21seed primary="
                         f"{b21['aggregate_primary']:.4f} robust="
                         f"{b21['aggregate_robustness']:.4f}; "
                         f"7seed primary={b7['aggregate_primary']:.4f}")
    print(f"p4-baseline: incumbent={incumbent} "
          f"21seed primary={b21['aggregate_primary']:.4f} "
          f"7seed primary={b7['aggregate_primary']:.4f}")
    git_commit("p4-baseline")

    # ---- Cycle A ------------------------------------------------------------
    res_a = run_cycle(state, MECH_A, 1, incumbent)
    incumbent = list(state["active"])

    # ---- Cycle B (against grown incumbent if A promoted) --------------------
    res_b = run_cycle(state, MECH_B, 2, incumbent)

    # ---- final stage ---------------------------------------------------------
    final = {"baseline": state["baseline"],
             "cycle_a": {"verdict": res_a["verdict_21"]["verdict"],
                         "mech": MECH_A,
                         "agg_rel": res_a["verdict_21"]["rel_delta_primary"],
                         "promoting_domain": res_a["verdict_21"]["promoting_domain"],
                         "promoting_domain_rel": res_a["verdict_21"]["promoting_domain_rel"],
                         "after_primary": res_a["verdict_21"]["after_primary"]},
             "cycle_b": {"verdict": res_b["verdict_21"]["verdict"],
                         "mech": MECH_B,
                         "agg_rel": res_b["verdict_21"]["rel_delta_primary"],
                         "promoting_domain": res_b["verdict_21"]["promoting_domain"],
                         "promoting_domain_rel": res_b["verdict_21"]["promoting_domain_rel"],
                         "after_primary": res_b["verdict_21"]["after_primary"]},
             "final_active": list(state["active"]),
             "promoted": state["promoted"],
             "parked": state["parked"],
             "rejected": state["rejected"]}

    if res_a["verdict_21"]["verdict"] == "PROMOTE" and \
       res_b["verdict_21"]["verdict"] == "PROMOTE":
        hive = list(state["active"])
        log_decision("INFO", f"both cycles promoted; measuring final hive {hive} on 21 seeds")
        f21 = aggregate(hive, seeds=EXT_SEEDS)
        # single-shot diagnostic: evidence_substrate alone vs ORIGINAL incumbent
        s21 = aggregate(INCUMBENT + [MECH_B], seeds=EXT_SEEDS)

        baseline_agg = b21["aggregate_primary"]
        sum_of_cycle_gains = (res_a["verdict_21"]["delta_primary"] +
                              res_b["verdict_21"]["delta_primary"])
        additive_projection = baseline_agg + sum_of_cycle_gains
        final["final_hive_21"] = f21
        final["final_hive_primary"] = f21["aggregate_primary"]
        final["single_shot_evidence_substrate_21"] = s21["aggregate_primary"]
        final["sum_of_cycle_gains"] = round(sum_of_cycle_gains, 4)
        final["additive_projection"] = round(additive_projection, 4)
        final["compounding_excess"] = round(
            f21["aggregate_primary"] - additive_projection, 4)
        save_json(STATE_PATH, state)
        log_decision(
            "GOVERNOR",
            f"p4-final-hive {hive}: 21seed primary={f21['aggregate_primary']:.4f} "
            f"robust={f21['aggregate_robustness']:.4f} | baseline={baseline_agg:.4f} "
            f"sum_of_cycle_gains={sum_of_cycle_gains:+.4f} additive_projection="
            f"{additive_projection:.4f} compounding_excess="
            f"{final['compounding_excess']:+.4f} | single-shot es vs original "
            f"incumbent={s21['aggregate_primary']:.4f}")
        print(f"p4-final-hive {hive}: 21seed primary={f21['aggregate_primary']:.4f} "
              f"(baseline {baseline_agg:.4f}; sum of cycle gains {sum_of_cycle_gains:+.4f}; "
              f"compounding excess {final['compounding_excess']:+.4f})")
        git_commit("p4-final-hive-both-promoted")
    else:
        log_decision(
            "GOVERNOR",
            f"not both promoted (A={res_a['verdict_21']['verdict']}, "
            f"B={res_b['verdict_21']['verdict']}); no final-hive aggregate measured "
            f"(current active={state['active']})")

    save_json(STATE_PATH, state)
    print(json.dumps(final, indent=2, default=str))
    log_decision("INFO", f"phase-4 finished; final active set: {state['active']} "
                         f"promoted={state['promoted']} parked={state['parked']} "
                         f"rejected={state['rejected']}")


if __name__ == "__main__":
    main()
