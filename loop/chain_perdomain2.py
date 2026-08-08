"""Phase-5 chaining under the EXPERIMENTAL per-domain promotion gate.

Non-redundancy test (PHASE5_REPORT.md): phase 4 produced the loop's first
per-domain promotion (residual_bias on RepoOps) but its second candidate
(evidence_substrate) was fully REDUNDANT -- same RepoOps effect, +0.0000 on top
of residual_bias -- so the 0.9220 final hive was exactly the single-shot ceiling
and nothing compounded. The phase-5 mission is to discriminate:

  H-NR : compounding requires NON-OVERLAPPING candidates. A maze-only mechanism
         aimed at UNCLAIMED headroom (maze 0.8229, weight 0.40) should clear the
         per-domain gate against the grown incumbent [uncertainty_planning,
         residual_bias] AND push the three-mechanism hive above 0.9220.
  H-GATE: even a well-designed non-overlapping mechanism fails; ceiling confirmed.

This module is an experimental protocol driver, read-only w.r.t. the inviolable
core. It imports aggregate() and the EXPERIMENTAL per-domain gate
(loop.gate_perdomain) and adds NEW files only. Protocol:

  baseline: aggregate(INCUMBENT=[up, rb], 21 seeds) + 7-seed re-run
            (expect ~0.9097 / ~0.9085 per phase-4)
  cycle   : measure [up, rb, <mech>] against the incumbent; per-domain verdict
            via gate_perdomain.apply_rule. If PROMOTE -> incumbent += <mech>.
  final   : if PROMOTE, aggregate([up, rb, <mech>]) on 21 seeds and compare to
            the 0.9220 single-shot ceiling (the headline compounding number).
  audit   : non-redundancy marginal contributions (aggregate-level):
              A = aggregate([up])            (single-mechanism base)
              B = aggregate([up, rb])        (incumbent)
              C = aggregate([up, mech])      (mech alone vs base)
              D = aggregate([up, rb, mech])  (mech on top of incumbent)
            mech's maze gain is present in both C-B(up) and D-B deltas => the
            mechanism is orthogonal on Maze; repoops/selflab deltas must be ~0.

Scorecards: logs/scorecards/p5-*.{json,md}; decisions -> logs/decisions.log;
git commits: p5-baseline, p5-cycle-<mech>-<verdict>.
State: checkpoints/p5_state.json (NEW, separate from p4_state.json).

Run:  python3 -m loop.chain_perdomain2
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
from loop.governance import apply_rule as constitutional_rule  # noqa: E402

CONST_SEEDS = [101, 202, 303, 404, 505, 606, 707]
EXT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203,
             1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

INCUMBENT = ["uncertainty_planning", "residual_bias"]
MECH = "progress_thermostat"
CEILING = 0.9220  # phase-4 single-shot ceiling (evidence_substrate alone)

STATE_PATH = os.path.join(ROOT, "checkpoints", "p5_state.json")
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


def write_cycle_scorecard(name, mech, incumbent, b21, a21, v21, cref21,
                          b7, a7, v7, cref7, variance) -> None:
    os.makedirs(SCORECARDS, exist_ok=True)
    data = {
        "phase": "phase5",
        "name": name,
        "mechanism": mech,
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
        f"# Scorecard: {name} (phase 5 - experimental per-domain gate)", "",
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


def write_audit_scorecard(state, audit: dict, final_primary: float,
                          compounding: dict) -> None:
    name = "p5-audit-nonredundancy"
    data = {
        "phase": "phase5",
        "name": name,
        "mechanism": MECH,
        "incumbent": INCUMBENT,
        "single_mechanism_base": INCUMBENT[:1],
        "measurements": audit,
        "final_hive_primary_21": final_primary,
        "phase4_single_shot_ceiling": CEILING,
        "beats_ceiling": round(final_primary - CEILING, 4),
        "compounding_analysis": compounding,
    }
    with open(os.path.join(SCORECARDS, f"{name}.json"), "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)

    def row(tag, agg, maze, repo, self_):
        return f"| {tag} | {agg:.4f} | {maze:.4f} | {repo:.4f} | {self_:.4f} |"
    md = [
        f"# Scorecard: {name} (phase 5 - non-redundancy audit)", "",
        f"- mechanism: `{MECH}`  (maze-only within-episode explore/exploit thermostat)",
        f"- incumbent: {INCUMBENT} (post-phase-4 grown state)",
        f"- question: does `{MECH}`'s maze gain survive WITH and WITHOUT "
        f"`residual_bias`? If yes it is orthogonal to the incumbent; repoops/"
        f"selflab deltas must be ~0 or the audit is confounded.", "",
        "| configuration | aggregate | maze | repoops | selflab |",
        "|---|---|---|---|---|",
        row("A: [up]", audit["A"]["aggregate_primary"], audit["A"]["primaries"]["maze"],
            audit["A"]["primaries"]["repoops"], audit["A"]["primaries"]["selflab"]),
        row("B: [up, rb] (incumbent)", audit["B"]["aggregate_primary"], audit["B"]["primaries"]["maze"],
            audit["B"]["primaries"]["repoops"], audit["B"]["primaries"]["selflab"]),
        row("C: [up, mech]", audit["C"]["aggregate_primary"], audit["C"]["primaries"]["maze"],
            audit["C"]["primaries"]["repoops"], audit["C"]["primaries"]["selflab"]),
        row("D: [up, rb, mech]", audit["D"]["aggregate_primary"], audit["D"]["primaries"]["maze"],
            audit["D"]["primaries"]["repoops"], audit["D"]["primaries"]["selflab"]),
        "",
        "Marginal contributions (maze primary):",
        f"- mech WITHOUT rb (C - A): {audit['C']['primaries']['maze'] - audit['A']['primaries']['maze']:+.4f} "
        f"(rel {(audit['C']['primaries']['maze']-audit['A']['primaries']['maze'])/audit['A']['primaries']['maze']:+.2%})",
        f"- mech WITH rb (D - B): {audit['D']['primaries']['maze'] - audit['B']['primaries']['maze']:+.4f} "
        f"(rel {(audit['D']['primaries']['maze']-audit['B']['primaries']['maze'])/audit['B']['primaries']['maze']:+.2%})",
        f"- repoops delta of mech (D - B): {audit['D']['primaries']['repoops'] - audit['B']['primaries']['repoops']:+.4f} "
        f"(must be ~0: residual_bias territory)",
        f"- selflab delta of mech (D - B): {audit['D']['primaries']['selflab'] - audit['B']['primaries']['selflab']:+.4f}",
        "",
        f"**FINAL HIVE [up, rb, {MECH}] 21-seed primary: {final_primary:.4f}**",
        f"- phase-4 single-shot ceiling: {CEILING:.4f}",
        f"- beats ceiling by: {final_primary - CEILING:+.4f}",
        f"- compounding analysis: {json.dumps(compounding, indent=2)}",
        "",
    ]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


def main() -> None:
    state = load_json(STATE_PATH, {"active": list(INCUMBENT), "promoted": [],
                                   "parked": [], "rejected": [], "cycles": {}})
    incumbent = list(INCUMBENT)

    log_decision("INFO", f"phase5 starts; mech={MECH} incumbent={incumbent} "
                         f"ceiling={CEILING}")

    # ---- baseline -----------------------------------------------------------
    b21 = aggregate(incumbent, seeds=EXT_SEEDS)
    b7 = aggregate(incumbent, seeds=CONST_SEEDS)
    state["baseline"] = {"incumbent": incumbent, "baseline_21": b21,
                         "baseline_7": b7}
    save_json(STATE_PATH, state)
    log_decision("INFO", f"p5-baseline measured: 21seed primary="
                         f"{b21['aggregate_primary']:.4f} robust="
                         f"{b21['aggregate_robustness']:.4f}; "
                         f"7seed primary={b7['aggregate_primary']:.4f}")
    print(f"p5-baseline: incumbent={incumbent} "
          f"21seed primary={b21['aggregate_primary']:.4f} "
          f"7seed primary={b7['aggregate_primary']:.4f}")
    git_commit("p5-baseline")

    # ---- cycle --------------------------------------------------------------
    a21 = aggregate(incumbent + [MECH], seeds=EXT_SEEDS)
    v21 = gate_perdomain.apply_rule(b21, a21, MECH)
    cref21 = constitutional_rule(b21, a21, MECH)

    a7 = aggregate(incumbent + [MECH], seeds=CONST_SEEDS)
    v7 = gate_perdomain.apply_rule(b7, a7, MECH)
    cref7 = constitutional_rule(b7, a7, MECH)

    dom = v21["promoting_domain"]
    variance = per_seed_variance(incumbent, MECH, dom, EXT_SEEDS)

    name = f"p5-cycle-{MECH}-{v21['verdict'].lower()}"
    write_cycle_scorecard(name, MECH, incumbent, b21, a21, v21, cref21,
                          b7, a7, v7, cref7, variance)

    log_decision(
        "GOVERNOR",
        f"p5-cycle {MECH}: per-domain 21seed before={v21['before_primary']:.4f} "
        f"after={v21['after_primary']:.4f} agg_rel={v21['rel_delta_primary']:+.2%} "
        f"promoting_domain={v21['promoting_domain']}@{v21['promoting_domain_rel']:+.2%} "
        f"worst_domain={v21['worst_domain']}@{v21['worst_domain_rel']:+.2%} "
        f"=> {v21['verdict']}  | constitutional reference={cref21['verdict']} "
        f"({cref21['rel_delta_primary']:+.2%})")
    log_decision(
        "GOVERNOR",
        f"p5-cycle per-domain rows: "
        f"{ {n: (v21['domain_primaries'][n]['rel_delta']) for n in ('maze','repoops','selflab')} }")
    log_decision(
        "GOVERNOR",
        f"p5-cycle {dom} variance (21 seeds): "
        f"mean={variance['mean']:+.4f} sd={variance['sd']:.4f} "
        f"min={variance['min']:+.4f} max={variance['max']:+.4f} "
        f"positive {variance['positive']}/{variance['count']} "
        f"negative {variance['negative']}/{variance['count']}")

    if v21["verdict"] == "PROMOTE":
        state["active"] = list(incumbent + [MECH])
        state["promoted"] = list(dict.fromkeys(state["promoted"] + [MECH]))
        log_decision("INFO", f"p5-cycle PROMOTED {MECH}; incumbent now {state['active']}")
    elif v21["verdict"] == "PARK":
        state["parked"] = list(dict.fromkeys(state["parked"] + [MECH]))
    else:
        state["rejected"] = list(dict.fromkeys(state["rejected"] + [MECH]))

    state["cycles"]["p5-1"] = {
        "mechanism": MECH, "verdict": v21["verdict"],
        "active_after": list(state["active"]),
        "before_primary": v21["before_primary"],
        "after_primary": v21["after_primary"],
        "rel_delta_primary": v21["rel_delta_primary"],
        "promoting_domain": v21["promoting_domain"],
        "promoting_domain_rel": v21["promoting_domain_rel"],
        "worst_domain_rel": v21["worst_domain_rel"],
    }
    save_json(STATE_PATH, state)
    git_commit(f"p5-cycle-{MECH}-{v21['verdict'].lower()}")

    # ---- non-redundancy audit (4 marginal measurements) ---------------------
    log_decision("INFO", "p5 audit: measuring marginal contributions A=[up] "
                         "B=[up,rb] C=[up,mech] D=[up,rb,mech] on 21 seeds")
    A = aggregate([INCUMBENT[0]], seeds=EXT_SEEDS)
    B = b21
    C = aggregate([INCUMBENT[0], MECH], seeds=EXT_SEEDS)
    D = a21
    audit = {"A": A, "B": B, "C": C, "D": D}

    maze_delta_no_rb = C["primaries"]["maze"] - A["primaries"]["maze"]
    maze_delta_with_rb = D["primaries"]["maze"] - B["primaries"]["maze"]
    repo_delta = D["primaries"]["repoops"] - B["primaries"]["repoops"]
    self_delta = D["primaries"]["selflab"] - B["primaries"]["selflab"]
    orthogonal = (repo_delta == 0.0 and self_delta == 0.0
                  and maze_delta_no_rb > 0 and maze_delta_with_rb > 0)

    log_decision(
        "GOVERNOR",
        f"p5-audit (21 seeds): A=[up] agg={A['aggregate_primary']:.4f} "
        f"maze={A['primaries']['maze']:.4f}; C=[up,mech] agg={C['aggregate_primary']:.4f} "
        f"maze={C['primaries']['maze']:.4f} => mech maze delta WITHOUT rb="
        f"{maze_delta_no_rb:+.4f} (rel {maze_delta_no_rb/A['primaries']['maze']:+.2%}); "
        f"mech maze delta WITH rb={maze_delta_with_rb:+.4f} (rel "
        f"{maze_delta_with_rb/B['primaries']['maze']:+.2%}); repoops delta={repo_delta:+.4f} "
        f"selflab delta={self_delta:+.4f} => orthogonal={orthogonal}")

    # ---- final hive / compounding ------------------------------------------
    state["audit"] = {
        "A_up": round(A["aggregate_primary"], 4),
        "C_up_mech": round(C["aggregate_primary"], 4),
        "maze_delta_without_rb": round(maze_delta_no_rb, 4),
        "maze_delta_with_rb": round(maze_delta_with_rb, 4),
        "repoops_delta": round(repo_delta, 4),
        "selflab_delta": round(self_delta, 4),
        "orthogonal": bool(orthogonal),
    }

    final_primary = None
    compounding = {}
    if v21["verdict"] == "PROMOTE":
        hive = list(state["active"])
        f21 = aggregate(hive, seeds=EXT_SEEDS)
        final_primary = f21["aggregate_primary"]
        baseline_agg = b21["aggregate_primary"]
        cycle_delta = v21["delta_primary"]
        additive_projection = baseline_agg + cycle_delta
        compounding = {
            "final_hive": hive,
            "final_hive_primary_21": round(final_primary, 4),
            "phase4_ceiling": CEILING,
            "beats_ceiling": round(final_primary - CEILING, 4),
            "incumbent_primary": round(baseline_agg, 4),
            "cycle_gain": round(cycle_delta, 4),
            "additive_projection": round(additive_projection, 4),
            "compounding_excess": round(final_primary - additive_projection, 4),
        }
        state["final_hive"] = {
            "active": hive,
            "aggregate_primary_21": round(final_primary, 4),
            "aggregate_robustness_21": f21["aggregate_robustness"],
            "phase4_ceiling": CEILING,
            "beats_ceiling": round(final_primary - CEILING, 4),
        }
        save_json(STATE_PATH, state)
        log_decision(
            "GOVERNOR",
            f"p5-final-hive {hive}: 21seed primary={final_primary:.4f} "
            f"robust={f21['aggregate_robustness']:.4f} | phase4 ceiling="
            f"{CEILING:.4f} beats_ceiling={final_primary - CEILING:+.4f} | "
            f"incumbent={baseline_agg:.4f} cycle_gain={cycle_delta:+.4f} "
            f"additive_projection={additive_projection:.4f} "
            f"compounding_excess={final_primary - additive_projection:+.4f} "
            f"| headroom-maze rel={maze_delta_with_rb/B['primaries']['maze']:+.2%}")
        print(f"p5-final-hive {hive}: 21seed primary={final_primary:.4f} "
              f"(beats phase-4 ceiling {CEILING} by "
              f"{final_primary - CEILING:+.4f}; compounding excess "
              f"{final_primary - additive_projection:+.4f})")
        git_commit("p5-final-hive")
    else:
        log_decision("GOVERNOR",
                     f"p5-cycle verdict={v21['verdict']}; no promotion; "
                     f"final hive = incumbent (no compounding event)")

    write_audit_scorecard(state, audit, final_primary or b21["aggregate_primary"],
                          compounding)

    save_json(STATE_PATH, state)
    print(json.dumps({
        "baseline": state["baseline"]["baseline_21"]["aggregate_primary"],
        "cycle": {"mechanism": MECH, "verdict": v21["verdict"],
                  "agg_rel": v21["rel_delta_primary"],
                  "promoting_domain": v21["promoting_domain"],
                  "promoting_domain_rel": v21["promoting_domain_rel"]},
        "final_hive_primary_21": final_primary,
        "phase4_ceiling": CEILING,
        "beats_ceiling": None if final_primary is None else round(final_primary - CEILING, 4),
        "audit": state["audit"],
        "active": state["active"],
    }, indent=2, default=str))
    log_decision("INFO", f"phase-5 finished; final active set: {state['active']} "
                         f"promoted={state['promoted']} parked={state['parked']} "
                         f"rejected={state['rejected']}")


if __name__ == "__main__":
    main()
