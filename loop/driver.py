"""THE CORE LOOP DRIVER (Constitution Article II - INVOLABLE).

Governed uplift loop:
  baseline measurement
  -> Architect proposes ONE mechanism
  -> Implementer loads it
  -> Evaluator runs the full ecology BEFORE and AFTER adding it
  -> deltas computed
  -> Governor verdict (PROMOTE / PARK / REJECT)
  -> hive state updated and committed to git as cycle-N-<mech>-<verdict>
  -> repeat

This file must not be modified by any mechanism. Run:
  python3 -m loop.driver            # baseline + all cycles
  python3 -m loop.driver --cycle N  # run cycle N (baseline is cycle 0)
  python3 -m loop.driver --resume   # continue from saved state
  python3 -m loop.driver --cycle N --resume
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

from hive.agents import Architect, Implementer, Evaluator, Governor  # noqa: E402
from hive.bus import Bus  # noqa: E402
from eval_ecology.runner import aggregate, SEEDS  # noqa: E402
from loop import architect as arch  # noqa: E402

STATE_PATH = os.path.join(ROOT, "checkpoints", "hive_state.json")
SCORECARDS = os.path.join(ROOT, "logs", "scorecards")
DECISIONS_LOG = os.path.join(ROOT, "logs", "decisions.log")
BUS_LOG = os.path.join(ROOT, "logs", "bus")

MAX_CYCLE_SECONDS = 30 * 60
MAX_RSS_MB = 1024
MAX_CODE_LINES = 2000


# --------------------------------------------------------------------------
# resource enforcement
# --------------------------------------------------------------------------
def enforce_limits() -> None:
    import resource
    soft, hard = resource.getrlimit(resource.RLIMIT_AS)
    limit = MAX_RSS_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (min(limit, hard if hard > 0 else limit), hard))
    lines = 0
    for dirpath, _dirs, files in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for fn in files:
            if fn.endswith(".py"):
                with open(os.path.join(dirpath, fn), "r") as fh:
                    lines += sum(1 for _ in fh)
    if lines > MAX_CODE_LINES:
        log_decision("WARNING", f"codebase exceeds {MAX_CODE_LINES} lines ({lines})")


def log_decision(kind: str, text: str) -> None:
    os.makedirs(os.path.dirname(DECISIONS_LOG), exist_ok=True)
    with open(DECISIONS_LOG, "a") as fh:
        fh.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {kind}: {text}\n")


# --------------------------------------------------------------------------
# hive state
# --------------------------------------------------------------------------
def load_state() -> dict:
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as fh:
            return json.load(fh)
    return {"active": [], "promoted": [], "parked": [], "rejected": [],
            "cycles": {}}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as fh:
        json.dump(state, fh, indent=2, sort_keys=True)


# --------------------------------------------------------------------------
# scorecards
# --------------------------------------------------------------------------
def write_scorecard(cycle: int, mechanism: str | None, before: dict, after: dict,
                    verdict: dict | None) -> None:
    os.makedirs(SCORECARDS, exist_ok=True)
    name = "baseline" if cycle == 0 else f"cycle-{cycle}"
    data = {
        "cycle": cycle,
        "name": name,
        "mechanism": mechanism,
        "seeds": SEEDS,
        "before": before,
        "after": after if verdict else None,
        "verdict": verdict,
    }
    with open(os.path.join(SCORECARDS, f"{name}.json"), "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
    md = [f"# Scorecard: {name}", "", f"- cycle: {cycle}", 
          f"- mechanism: {mechanism or 'none (baseline)'}",
          f"- seeds: {SEEDS}", "",
          "| metric | before | after | delta |", "|---|---|---|---|"]
    rows = ["aggregate_primary", "aggregate_robustness"]
    for row in rows:
        b = before[row]
        a = after[row] if verdict else None
        d = (round(a - b, 4) if verdict and a is not None else "-")
        md.append(f"| {row} | {b} | {a} | {d} |")
    if verdict:
        for env in before["envs"]:
            b = before["envs"][env]["success_rate"]
            a = after["envs"][env]["success_rate"]
            md.append(f"| env `{env}` success_rate | {b} | {a} | {round(a - b, 4)} |")
        md += ["", f"**VERDICT: {verdict['verdict']}**",
               f"- relative primary delta: {verdict['rel_delta_primary']:+.1%}",
               f"- robustness delta: {verdict['delta_robustness']:+.4f}",
               f"- rule: {verdict['rule']}"]
    with open(os.path.join(SCORECARDS, f"{name}.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")


# --------------------------------------------------------------------------
# git checkpoint
# --------------------------------------------------------------------------
def git_commit(message: str) -> None:
    try:
        subprocess.run(["git", "add", "-A"], cwd=ROOT, check=True,
                       capture_output=True)
        subprocess.run(["git", "commit", "-q", "-m", message], cwd=ROOT,
                       check=True, capture_output=True)
    except subprocess.CalledProcessError as exc:
        log_decision("ERROR", f"git commit failed: {exc.stderr.decode()[:300]}")


# --------------------------------------------------------------------------
# one cycle
# --------------------------------------------------------------------------
def run_cycle(cycle: int, state: dict, do_commit: bool = True) -> None:
    t0 = time.time()
    bus = Bus()
    bus.attach_log(os.path.join(BUS_LOG, f"cycle-{cycle}.jsonl"))

    arch_agent = Architect(bus, arch.ROSTER)
    impl = Implementer(bus, os.path.join(ROOT, "mechanisms"))
    ev = Evaluator(bus)
    gov = Governor(bus)

    active = list(state["active"])
    log_decision("INFO", f"cycle {cycle} starts; active={active}")

    if cycle == 0:
        before = aggregate(active)
        write_scorecard(0, None, before, before, None)
        state["cycles"]["baseline"] = {"active": list(active),
                                       "aggregate_primary": before["aggregate_primary"]}
        save_state(state)
        log_decision("INFO", f"baseline measured agg_primary={before['aggregate_primary']:.4f}")
        if do_commit:
            git_commit(f"baseline: aggregate_primary={before['aggregate_primary']:.4f}")
        return

    mech = arch_agent.propose(cycle, active)
    if mech not in arch.ROSTER:
        raise RuntimeError(f"Architect proposed unknown mechanism {mech}")
    log_decision("ARCHITECT", f"cycle {cycle} proposes '{mech}': {arch.RATIONALE[mech]}")

    impl.load(mech)  # Implementer: ensure the mechanism code is importable
    log_decision("IMPLEMENTER", f"cycle {cycle} loaded mechanisms.{mech}")

    before = aggregate(active)
    after = aggregate(active + [mech])
    verdict = gov.decide(before, after, mech)
    log_decision("GOVERNOR",
                 f"cycle {cycle} {mech}: before={before['aggregate_primary']:.4f} "
                 f"after={after['aggregate_primary']:.4f} "
                 f"rel={verdict['rel_delta_primary']:+.1%} "
                 f"rob={verdict['delta_robustness']:+.4f} "
                 f"=> {verdict['verdict']}")
    log_decision("GOVERNOR",
                 f"cycle {cycle} commentary: {arch.ARCHITECT_VERDICT_COMMENTARY[verdict['verdict']]}")

    write_scorecard(cycle, mech, before, after, verdict)

    if verdict["verdict"] == "PROMOTE":
        state["active"] = list(active + [mech])
        state["promoted"].append(mech)
    elif verdict["verdict"] == "PARK":
        state["parked"].append(mech)
    else:
        state["rejected"].append(mech)

    state["cycles"][str(cycle)] = {
        "mechanism": mech, "verdict": verdict["verdict"],
        "active_after": list(state["active"]),
        "before_primary": before["aggregate_primary"],
        "after_primary": after["aggregate_primary"],
    }
    save_state(state)

    elapsed = time.time() - t0
    if elapsed > MAX_CYCLE_SECONDS:
        log_decision("ERROR", f"cycle {cycle} exceeded wall-clock limit")
    log_decision("INFO", f"cycle {cycle} finished in {elapsed:.1f}s, verdict={verdict['verdict']}")

    if do_commit:
        git_commit(f"cycle-{cycle}-{mech}-{verdict['verdict'].lower()}")
        log_decision("GIT", f"committed cycle-{cycle}-{mech}-{verdict['verdict'].lower()}")


def main() -> None:
    parser = argparse.ArgumentParser(description="OmegaHive governed uplift loop")
    parser.add_argument("--cycle", type=int, default=-1,
                        help="run a specific cycle (0=baseline, 1..3=uplift)")
    parser.add_argument("--resume", action="store_true",
                        help="continue from saved hive state")
    args = parser.parse_args()

    enforce_limits()
    state = load_state() if args.resume else {
        "active": [], "promoted": [], "parked": [], "rejected": [], "cycles": {}}

    cycles = [args.cycle] if args.cycle >= 0 else [0, 1, 2, 3]
    for cyc in cycles:
        if cyc == 0 and args.resume and "baseline" in state.get("cycles", {}):
            log_decision("INFO", "baseline already in state; skipping re-measure")
            continue
        run_cycle(cyc, state)
    log_decision("INFO", "driver finished; final active set: "
                         f"{state['active']}; promoted={state['promoted']} "
                         f"parked={state['parked']} rejected={state['rejected']}")
    print(json.dumps({k: state[k] for k in ("active", "promoted", "parked",
                                            "rejected")}, indent=2))


if __name__ == "__main__":
    main()
