"""Phase-6 SECOND-LOOP protocol (NEW, experimental, NOT constitutional).

Closes the gap identified by the phase-5 post-analysis: the improvement
machinery sits OUTSIDE the hive (loop/architect.py is static data). Phase 6
builds an IN-BAND proposal machinery — a strategy mechanism occupying the new
`propose` hook — and measures, with a randomized-memo control arm, whether
proposal quality then compounds.

Two hypotheses (either outcome is decisive):
  H-VC : history flowing into the next proposal makes the next proposed
         mechanism measurably better; after a strategy promotion proposal
         quality continues to rise (Goertzel's loop, first machinery-level
         evidence).
  H-LIN: strategy mechanisms are first-order; proposal quality is flat in
         expectation (the additive regime holds even with in-band machinery).

Protocol (three measurement arms, SAME probe class `frontier_memory_v3`, tuned
per-arm ONLY via the memo's parameterization section):
  arm 0 baseline   : empty memo                      -> probe on default config
  arm 1 S active   : memo from success_signature_policy over the real
                     proposal state                  -> probe on memo config
  arm 2 randomized : memo from success_signature_policy over the PERMUTED
                     proposal state (shuffle domain<->hook-class associations)
                     -> probe on misattributed config  (attribution control)
Metric: Q = (probe 21-seed aggregate-primary delta) / (target-domain remaining
headroom), i.e. the fraction of the target domain's remaining headroom captured
in aggregate-weighted terms. Verdict via loop/gate_strategy.py (NEW file).

If the strategy PROMOTES: one additional task-mechanism cycle under S (a
genuinely new maze mechanism, pocket_detector — NOT the probe class) tests
monotonicity (does proposal quality rise a second time?) and computes the
compounding excess exactly, as in phase 5.

Every scorecard is a real aggregate()/run_ecology() measurement; decisions go
to logs/decisions.log; commits: p6-proposal-state, p6-arm0/1/2,
p6-strategy-<verdict>, (p6-cycle2-pocket_detector if promoted).
Read-only w.r.t. the inviolable core (imports aggregate/run_ecology only).

Run:  python3 -m loop.chain_second_loop
"""

from __future__ import annotations

import copy
import json
import os
import statistics
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from eval_ecology.runner import run_ecology  # noqa: E402
from hive.hooks import HookPipe, load_registry  # noqa: E402
from loop import gate_strategy, proposal_state  # noqa: E402
from mechanisms import frontier_memory_v3, pocket_detector  # noqa: E402

CONST_SEEDS = [101, 202, 303, 404, 505, 606, 707]
EXT_SEEDS = [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203,
             1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

INCUMBENT = ["uncertainty_planning", "residual_bias", "progress_thermostat"]
PROBE = "frontier_memory_v3"
STRATEGY = "success_signature_policy"
CYCLE2_MECH = "pocket_detector"
PERM_SEED = 2026
PROBE_HOOK_CLASS = "choose_action"

P6_STATE = os.path.join(ROOT, "checkpoints", "p6_state.json")
SCORECARDS = os.path.join(ROOT, "logs", "scorecards")
DECISIONS = os.path.join(ROOT, "logs", "decisions.log")


def log_decision(kind: str, text: str) -> None:
    os.makedirs(os.path.dirname(DECISIONS), exist_ok=True)
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


# ---------------------------------------------------------------------------
# measurement helpers
# ---------------------------------------------------------------------------

def _primary_of(name: str, env: dict) -> float:
    if name == "maze":
        return 0.5 * env["success_rate"] + 0.5 * env["efficiency"]
    return env["success_rate"]


def per_seed_primaries(active: list[str], seeds: list[int]) -> dict:
    """{seed: {'agg': weighted primary, 'maze': maze primary}} — real runs."""
    out = {}
    for seed in seeds:
        r = run_ecology(active, seed)["envs"]
        maze_p = _primary_of("maze", r["maze"])
        agg = (0.40 * maze_p
               + 0.35 * _primary_of("repoops", r["repoops"])
               + 0.25 * _primary_of("selflab", r["selflab"]))
        out[seed] = {"agg": agg, "maze": maze_p}
    return out


def _mean(xs) -> float:
    return sum(xs) / len(xs)


def _sd(xs) -> float:
    return statistics.pstdev(xs) if len(xs) > 1 else 0.0


def _stats(deltas: list[float]) -> dict:
    return {"mean": round(_mean(deltas), 4), "sd": round(_sd(deltas), 4),
            "negative": sum(1 for d in deltas if d < 0),
            "positive": sum(1 for d in deltas if d > 0),
            "min": round(min(deltas), 4), "max": round(max(deltas), 4)}


# ---------------------------------------------------------------------------
# propose() / strategy invocation
# ---------------------------------------------------------------------------

def run_strategy(state: dict) -> dict:
    """Fire active strategy mechanisms on the `propose` hook over the state."""
    registry = load_registry(os.path.join(ROOT, "mechanisms"))
    pipe = HookPipe([STRATEGY], registry)
    ctx = {STRATEGY: {}}
    ctx = pipe.propose(ctx, state)
    return ctx[STRATEGY].get("memo") or {}


def propose(condition: str, snapshot: dict, permuted: dict | None) -> dict:
    if condition == "baseline":
        return {}
    if condition == "active":
        return run_strategy(snapshot)
    if condition == "randomized":
        return run_strategy(permuted)
    raise ValueError(f"unknown condition {condition}")


# ---------------------------------------------------------------------------
# audit
# ---------------------------------------------------------------------------

def audit_strategy() -> dict:
    from mechanisms import success_signature_policy
    hooks = set(getattr(success_signature_policy, "HOOKS", {}).keys())
    audit = {
        "strategy": STRATEGY,
        "registered_hooks": sorted(hooks),
        "zero_task_hook_handlers": hooks == {"propose"},
        "task_impact": "zero by construction (no before_eval/choose_action/"
                       "after_write/retrieve handler)",
    }
    return audit


# ---------------------------------------------------------------------------
# arms
# ---------------------------------------------------------------------------

def write_arm_scorecard(arm: dict, inc_agg: float) -> None:
    name = f"p6-arm{arm['index']}"
    md = [
        f"# Scorecard: {name} (phase 6 - second loop)", "",
        f"- condition: **{arm['condition']}**",
        f"- probe: `{PROBE}` (SAME class in all arms)",
        f"- probe config: `{json.dumps(arm['config'])}`",
        f"- memo: `{json.dumps(arm['memo'])}`",
        f"- incumbent: {INCUMBENT} (21-seed primary {inc_agg:.4f})",
        f"- target domain: {arm['target_domain']} (remaining headroom "
        f"{arm['target_headroom']:.4f})",
        f"- seeds (21): {EXT_SEEDS}", "",
        "## 21-seed probe measurement", "",
        "| metric | value |", "|---|---|",
        f"| aggregate-primary delta | {arm['delta']:+.4f} |",
        f"| proposal quality Q (delta / headroom) | {arm['q']:+.6f} |",
        f"| per-seed delta mean | {arm['delta_mean']:+.4f} |",
        f"| per-seed delta sd | {arm['delta_sd']:.4f} |",
        f"| negative seeds | {arm['negative_seeds']}/21 |",
        f"| maze per-seed delta mean | {arm['maze_mean']:+.4f} |",
        f"| maze per-seed delta sd | {arm['maze_sd']:.4f} |",
        f"| per-seed deltas | {arm['per_seed_deltas']} |", "",
    ]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    save_json(os.path.join(SCORECARDS, f"{name}.json"), arm)


def run_arm(condition: str, snapshot: dict, permuted: dict | None, index: int,
            inc_seeds: dict) -> dict:
    t0 = time.time()
    log_decision("INFO", f"p6 arm-{index} ({condition}) starts; probe={PROBE} "
                         f"incumbent={INCUMBENT}")
    memo = propose(condition, snapshot, permuted)
    log_decision("PROPOSAL",
                 f"p6 arm-{index} ({condition}) memo: {json.dumps(memo)}")

    frontier_memory_v3.configure(memo.get("parameterization") or {})
    cfg = frontier_memory_v3.configure()
    log_decision("INFO",
                 f"p6 arm-{index} probe configured via memo parameterization: "
                 f"{json.dumps(cfg)}")

    after = per_seed_primaries(INCUMBENT + [PROBE], EXT_SEEDS)
    agg_deltas = [after[s]["agg"] - inc_seeds[s]["agg"] for s in EXT_SEEDS]
    maze_deltas = [after[s]["maze"] - inc_seeds[s]["maze"] for s in EXT_SEEDS]
    agg_delta = _mean(agg_deltas)

    target_domain = memo.get("target_domain") or "maze"
    target_headroom = snapshot["headroom"][target_domain]["remaining_headroom"]
    q = agg_delta / target_headroom if target_headroom else 0.0

    agg_st = _stats(agg_deltas)
    maze_st = _stats(maze_deltas)
    arm = {
        "index": index, "condition": condition, "probe": PROBE,
        "memo": memo, "config": cfg,
        "incumbent": INCUMBENT, "incumbent_primary_21": round(
            _mean([v["agg"] for v in inc_seeds.values()]), 4),
        "target_domain": target_domain,
        "target_headroom": round(target_headroom, 4),
        "delta": round(agg_delta, 4),
        "q": round(q, 6),
        "delta_mean": agg_st["mean"], "delta_sd": agg_st["sd"],
        "negative_seeds": agg_st["negative"],
        "positive_seeds": agg_st["positive"],
        "maze_mean": maze_st["mean"], "maze_sd": maze_st["sd"],
        "maze_negative": maze_st["negative"],
        "per_seed_deltas": [round(d, 4) for d in agg_deltas],
        "seeds": EXT_SEEDS,
    }
    write_arm_scorecard(arm, arm["incumbent_primary_21"])

    log_decision(
        "GOVERNOR",
        f"p6 arm-{index} ({condition}): agg delta={agg_delta:+.4f} "
        f"Q={q:+.6f} (headroom {target_headroom:.4f}) | per-seed "
        f"mean={agg_st['mean']:+.4f} sd={agg_st['sd']:.4f} "
        f"neg={agg_st['negative']}/21 | maze mean={maze_st['mean']:+.4f} "
        f"sd={maze_st['sd']:.4f} | elapsed {time.time()-t0:.1f}s")
    git_commit(f"p6-arm{index}")
    return arm


# ---------------------------------------------------------------------------
# strategy verdict
# ---------------------------------------------------------------------------

def write_strategy_scorecard(verdict: dict, arms: dict) -> None:
    name = f"p6-strategy-{verdict['verdict'].lower()}"
    md = [
        f"# Scorecard: {name} (phase 6 - strategy gate)", "",
        f"- strategy: `{STRATEGY}` (in-band `propose`-hook mechanism)",
        f"- gate: **strategy gate** (EXPERIMENTAL, NOT constitutional): PROMOTE "
        f"iff Q1 >= 1.05*Q0 AND Q1 >= 1.05*Q2 AND neg1 <= neg0 AND matched "
        f"Q1 > Q2 (strict majority); else PARK iff Q1 >= 0.95*Q0, else REJECT.",
        "", "## Three-arm probe measurement (21 seeds)", "",
        "| arm | condition | agg delta | Q | neg seeds |", "|---|---|---|---|---|",
        f"| 0 | baseline (empty memo) | {arms[0]['delta']:+.4f} | "
        f"{arms[0]['q']:+.6f} | {arms[0]['negative_seeds']}/21 |",
        f"| 1 | S active (real history) | {arms[1]['delta']:+.4f} | "
        f"{arms[1]['q']:+.6f} | {arms[1]['negative_seeds']}/21 |",
        f"| 2 | randomized (permuted history) | {arms[2]['delta']:+.4f} | "
        f"{arms[2]['q']:+.6f} | {arms[2]['negative_seeds']}/21 |",
        "", "## Conditions", "",
        f"- Q1 >= 1.05*Q0 : **{verdict['conditions']['q1_ge_1p05_q0']}** "
        f"({verdict['q']['1']:.6f} vs 1.05*{verdict['q']['0']:.6f})",
        f"- Q1 >= 1.05*Q2 : **{verdict['conditions']['q1_ge_1p05_q2']}** "
        f"({verdict['q']['1']:.6f} vs 1.05*{verdict['q']['2']:.6f})",
        f"- no task-axis regression : **{verdict['conditions']['no_task_axis_regression']}** "
        f"(arm1 neg {arms[1]['negative_seeds']} <= arm0 neg {arms[0]['negative_seeds']})",
        f"- memo attribution (matched per-seed Q1>Q2) : "
        f"**{verdict['conditions']['attribution_holds']}** "
        f"(wins {verdict['matched_q1_vs_q2']['wins']}, "
        f"losses {verdict['matched_q1_vs_q2']['losses']}, "
        f"ties {verdict['matched_q1_vs_q2']['ties']})", "",
        f"**VERDICT: {verdict['verdict']}**", "",
    ]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    save_json(os.path.join(SCORECARDS, f"{name}.json"), verdict)


# ---------------------------------------------------------------------------
# monotonicity cycle (if promoted)
# ---------------------------------------------------------------------------

def write_cycle2_scorecard(cyc: dict) -> None:
    name = f"p6-cycle2-{CYCLE2_MECH}"
    md = [
        f"# Scorecard: {name} (phase 6 - monotonicity cycle under S)", "",
        f"- mechanism: `{CYCLE2_MECH}` (genuinely new maze mechanism per S's memo; "
        f"NOT the probe class)",
        f"- memo (S over updated history): `{json.dumps(cyc['memo2'])}`",
        f"- incumbent: {INCUMBENT} (21-seed primary {cyc['incumbent_primary']:.4f})",
        "", "## 21-seed cycle measurement", "",
        "| metric | value |", "|---|---|",
        f"| aggregate-primary delta (g) | {cyc['delta']:+.4f} |",
        f"| second-cycle aggregate | {cyc['final_aggregate']:.4f} |",
        f"| vs 0.9480 | {cyc['final_aggregate'] - 0.9480:+.4f} |",
        f"| additive projection (0.9480 + g) | {cyc['additive_projection']:.4f} |",
        f"| compounding excess | {cyc['compounding_excess']:+.4f} |",
        f"| proposal quality Q2cycle | {cyc['q']:+.6f} |",
        f"| per-seed delta mean/sd | {cyc['delta_mean']:+.4f} / {cyc['delta_sd']:.4f} |",
        f"| negative seeds | {cyc['negative_seeds']}/21 |",
        "", "## Marginal audit (phase-5 style): does the gain depend on hive maturity?",
        "",
        "| configuration | 21-seed primary |", "|---|---|",
        f"| A: [up] | {cyc['audit']['up']:.4f} |",
        f"| A': [up, {CYCLE2_MECH}] | {cyc['audit']['up_mech']:.4f} |",
        f"| B2: [up, rb] | {cyc['audit']['up_rb']:.4f} |",
        f"| C: [up, rb, {CYCLE2_MECH}] | {cyc['audit']['up_rb_mech']:.4f} |",
        f"| B: [up, rb, pt] (incumbent) | {cyc['incumbent_primary']:.4f} |",
        f"| D: [up, rb, pt, {CYCLE2_MECH}] | {cyc['final_aggregate']:.4f} |",
        "",
        f"- gain without pt (C - B2): {cyc['audit']['gain_without_pt']:+.4f}",
        f"- gain with pt (D - B): {cyc['delta']:+.4f}",
        f"- monotonicity: does the mechanism gain MORE on the grown hive? "
        f"{cyc['audit']['gain_with_pt'] - cyc['audit']['gain_without_pt']:+.4f}",
        "",
    ]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    save_json(os.path.join(SCORECARDS, f"{name}.json"), cyc)


def run_second_cycle(state: dict, inc_seeds: dict) -> dict:
    t0 = time.time()
    log_decision("INFO", "p6 cycle-2 starts: strategy re-fires over the UPDATED "
                         "proposal state (three arms now in history)")
    memo2 = run_strategy(state)
    log_decision("PROPOSAL", f"p6 cycle-2 memo (S over updated history): "
                             f"{json.dumps(memo2)}")

    pocket_detector.configure(memo2.get("parameterization") or {})
    log_decision("INFO", "p6 cycle-2 mechanism configured via memo: "
                         f"{json.dumps(pocket_detector.configure())}")

    inc_agg = _mean([v["agg"] for v in inc_seeds.values()])
    after = per_seed_primaries(INCUMBENT + [CYCLE2_MECH], EXT_SEEDS)
    deltas = [after[s]["agg"] - inc_seeds[s]["agg"] for s in EXT_SEEDS]
    st = _stats(deltas)
    g = _mean(deltas)
    final_agg = _mean([after[s]["agg"] for s in EXT_SEEDS])
    additive = inc_agg + g
    target_headroom = state["headroom"]["maze"]["remaining_headroom"]
    q = g / target_headroom if target_headroom else 0.0

    log_decision("INFO", "p6 cycle-2 audit: measuring marginal contributions "
                         "A=[up] A'=[up,mech] B2=[up,rb] C=[up,rb,mech] "
                         "(B=[up,rb,pt]=incumbent, D=[up,rb,pt,mech] already "
                         "measured) on 21 seeds")
    up = per_seed_primaries(["uncertainty_planning"], EXT_SEEDS)
    up_mech = per_seed_primaries(["uncertainty_planning", CYCLE2_MECH], EXT_SEEDS)
    up_rb = per_seed_primaries(["uncertainty_planning", "residual_bias"], EXT_SEEDS)
    up_rb_mech = per_seed_primaries(
        ["uncertainty_planning", "residual_bias", CYCLE2_MECH], EXT_SEEDS)

    cyc = {
        "mechanism": CYCLE2_MECH, "incumbent": INCUMBENT,
        "incumbent_primary": round(inc_agg, 4),
        "memo2": memo2,
        "config": pocket_detector.configure(),
        "delta": round(g, 4),
        "final_aggregate": round(final_agg, 4),
        "additive_projection": round(additive, 4),
        "compounding_excess": round(final_agg - additive, 4),
        "q": round(q, 6),
        "target_headroom": round(target_headroom, 4),
        "delta_mean": st["mean"], "delta_sd": st["sd"],
        "negative_seeds": st["negative"],
        "per_seed_deltas": [round(d, 4) for d in deltas],
        "audit": {
            "up": round(_mean([v["agg"] for v in up.values()]), 4),
            "up_mech": round(_mean([v["agg"] for v in up_mech.values()]), 4),
            "up_rb": round(_mean([v["agg"] for v in up_rb.values()]), 4),
            "up_rb_mech": round(_mean([v["agg"] for v in up_rb_mech.values()]), 4),
            "gain_without_pt": round(
                _mean([v["agg"] for v in up_rb_mech.values()])
                - _mean([v["agg"] for v in up_rb.values()]), 4),
            "gain_with_pt": round(g, 4),
        },
    }
    write_cycle2_scorecard(cyc)

    log_decision(
        "GOVERNOR",
        f"p6 cycle-2 {CYCLE2_MECH}: delta={g:+.4f} final_agg={final_agg:.4f} "
        f"(vs 0.9480: {final_agg-0.9480:+.4f}) additive={additive:.4f} "
        f"compounding_excess={final_agg-additive:+.4f} Q2cycle={q:+.6f} | "
        f"per-seed mean={st['mean']:+.4f} sd={st['sd']:.4f} neg={st['negative']}/21")
    log_decision(
        "GOVERNOR",
        f"p6 cycle-2 marginal audit: gain WITHOUT pt="
        f"{cyc['audit']['gain_without_pt']:+.4f}, gain WITH pt="
        f"{cyc['audit']['gain_with_pt']:+.4f}, monotonic difference="
        f"{cyc['audit']['gain_with_pt']-cyc['audit']['gain_without_pt']:+.4f} "
        f"(elapsed {time.time()-t0:.1f}s)")
    git_commit(f"p6-cycle2-{CYCLE2_MECH}")
    return cyc


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> None:
    t_start = time.time()
    log_decision("INFO", "PHASE 6 starts: second-loop experiment, H-VC vs H-LIN, "
                         "in-band proposal machinery")
    log_decision("ARCHITECT",
                 "success_signature_policy design rationale: the phase-5 "
                 "post-analysis showed the improvement machinery sits outside "
                 "the hive (static ROSTER/RATIONALE in loop/architect.py); the "
                 "proposed strategy is a mechanism occupying the NEW in-band "
                 "'propose' hook so that history (headroom, promotion "
                 "signatures, overlap table, proposal log) is the ONLY channel "
                 "into the next proposal. H-VC mechanism: memo = (a) target "
                 "domain = highest remaining headroom weighted by aggregate "
                 "weight; (b) hook-class constraint = class not in the overlap "
                 "table's covered set; (c) parameterization = success-gated, "
                 ">=2 confirmations (the phase-3 calibration that worked) when "
                 "history shows the probe class's credit was noise-dominated; "
                 "(d) top-2 failure signatures from the proposal log.")

    # ---- proposal-state substrate -----------------------------------------
    state = proposal_state.load()
    if state is None:
        state = proposal_state.build_initial()
        proposal_state.save(state)
        log_decision("INFO", "p6 proposal state initialized from real scorecards")
    else:
        log_decision("INFO", "p6 proposal state loaded from checkpoint")

    # ---- honest governor's audit ------------------------------------------
    audit = audit_strategy()
    log_decision("GOVERNOR",
                 f"p6 audit: strategy {audit['strategy']} registered hooks="
                 f"{audit['registered_hooks']} zero_task_hook_handlers="
                 f"{audit['zero_task_hook_handlers']} ({audit['task_impact']})")
    save_json(os.path.join(SCORECARDS, "p6-audit.json"), audit)

    snapshot = copy.deepcopy(state)
    permuted = proposal_state.permute_associations(snapshot, PERM_SEED)
    log_decision("INFO",
                 f"p6 arm-2 randomization control seed={PERM_SEED} "
                 f"permutation={json.dumps(permuted['permutation'])}")

    git_commit("p6-proposal-state")
    print("p6-proposal-state: substrate initialized, audit passed "
          f"({audit['zero_task_hook_handlers']}), target domain = "
          f"{snapshot['headroom']['maze']['remaining_headroom']} headroom maze")

    # ---- incumbent (21 seeds, measured once) -------------------------------
    inc_seeds = per_seed_primaries(INCUMBENT, EXT_SEEDS)
    inc_agg = _mean([v["agg"] for v in inc_seeds.values()])
    log_decision("INFO",
                 f"p6 incumbent measured on 21 seeds: primary={inc_agg:.4f} "
                 f"(expected ~0.9480)")
    print(f"p6-incumbent: 21-seed primary={inc_agg:.4f}")

    # ---- three arms --------------------------------------------------------
    arm0 = run_arm("baseline", snapshot, None, 0, inc_seeds)
    arm1 = run_arm("active", snapshot, None, 1, inc_seeds)
    arm2 = run_arm("randomized", snapshot, permuted, 2, inc_seeds)

    # ---- strategy gate -----------------------------------------------------
    verdict = gate_strategy.apply_rule(
        {0: arm0, 1: arm1, 2: arm2},
        snapshot["headroom"]["maze"]["remaining_headroom"], STRATEGY)
    write_strategy_scorecard(verdict, {0: arm0, 1: arm1, 2: arm2})

    log_decision(
        "GOVERNOR",
        f"p6 strategy gate: Q0={verdict['q']['0']:+.6f} "
        f"Q1={verdict['q']['1']:+.6f} Q2={verdict['q']['2']:+.6f} | "
        f"deltas {verdict['delta']} | neg {verdict['negative_seeds']} | "
        f"matched Q1>Q2 wins={verdict['matched_q1_vs_q2']['wins']} "
        f"losses={verdict['matched_q1_vs_q2']['losses']} "
        f"ties={verdict['matched_q1_vs_q2']['ties']} | conditions="
        f"{verdict['conditions']} => {verdict['verdict']}")
    git_commit(f"p6-strategy-{verdict['verdict'].lower()}")

    # ---- record arms + verdict into the persistent proposal state ----------
    state["arms"] = {f"arm{i}": arm for i, arm in enumerate((arm0, arm1, arm2))}
    state["strategy_verdict"] = verdict
    state.setdefault("next_log_id", max(
        (e.get("id", 0) for e in state.get("proposal_log", [])), default=0) + 1)
    for arm in (arm0, arm1, arm2):
        state["proposal_log"].append({
            "id": state["next_log_id"], "condition": arm["condition"],
            "mechanism": PROBE, "target_domain": "maze",
            "hook_class": PROBE_HOOK_CLASS,
            "aggregate_delta": arm["delta"],
            "rel_delta": round(arm["delta"] / inc_agg, 4),
            "maze_delta_mean": arm["maze_mean"],
            "maze_delta_sd": arm["maze_sd"],
            "count": len(EXT_SEEDS), "negative_seeds": arm["negative_seeds"],
            "failure_signature": (
                "empty-memo baseline (naive config)" if arm["condition"]
                == "baseline" else
                "memo-guided probe (success-signature policy)" if
                arm["condition"] == "active" else
                "permuted-history memo (misattributed associations)"),
        })
        state["next_log_id"] += 1
    proposal_state.save(state)

    # ---- monotonicity cycle ------------------------------------------------
    outcome = {"verdict": verdict["verdict"], "q": verdict["q"],
               "deltas": verdict["delta"]}
    if verdict["verdict"] == "PROMOTE":
        log_decision("INFO", "p6 strategy PROMOTED; running the monotonicity "
                             "cycle (one additional task-mechanism proposal "
                             "under S, NOT the probe class)")
        cycle2 = run_second_cycle(state, inc_seeds)
        state["cycle2"] = cycle2
        outcome["cycle2"] = cycle2
        proposal_state.save(state)
        print(json.dumps({"outcome": "H-VC", "q0": verdict["q"]["0"],
                          "q1": verdict["q"]["1"], "q2": verdict["q"]["2"],
                          "second_cycle_aggregate": cycle2["final_aggregate"],
                          "compounding_excess": cycle2["compounding_excess"]},
                         indent=2))
    else:
        log_decision("GOVERNOR",
                     f"p6 strategy verdict {verdict['verdict']}: in-band "
                     f"machinery produced no measured compounding (H-LIN "
                     f"supported); no monotonicity cycle run")
        print(json.dumps({"outcome": "H-LIN", "q0": verdict["q"]["0"],
                          "q1": verdict["q"]["1"], "q2": verdict["q"]["2"],
                          "verdict": verdict["verdict"]}, indent=2))

    log_decision("INFO",
                 f"phase-6 finished in {time.time()-t_start:.1f}s; strategy "
                 f"verdict={verdict['verdict']}; proposal state at "
                 f"{proposal_state.STATE_PATH}")


if __name__ == "__main__":
    main()
