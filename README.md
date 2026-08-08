# 🐝 OmegaHive — An Empirical Test of the Self-Uplifting Loop Hypothesis

> **Experiment status: COMPLETE — six phases, ~45 measured configurations, final hive 0.9480.**

A governed, reproducible experiment testing whether an AI "hive" can improve
itself through Ben Goertzel's *incremental self-uplifting loop*: start from a
baseline hive, add **one cognitive mechanism at a time**, evaluate it in a
**multi-environment ecology**, measure **real deltas**, then **promote / park /
reject** based on transparent governance — and repeat, hoping each cycle makes
the next one easier (the "virtuous cycle").

This repository contains the complete, runnable implementation, all six phases
of the experiment, every measurement, and an honest analysis. **All code is pure
Python 3.12 with zero third-party dependencies. Every number in every report is
reproducible with one command.**

![python](https://img.shields.io/badge/python-3.12-blue)
![deps](https://img.shields.io/badge/dependencies-zero-green)
![deterministic](https://img.shields.io/badge/21%20seeds-deterministic-orange)
![status](https://img.shields.io/badge/status-complete-darkgreen)

---

## TL;DR — what did we find?

| Phase | What was tested | Outcome |
|---|---|---|
| 1 | Baseline hive + 3 pre-designed mechanisms, empty-baseline evaluation | **+12.1%** real improvement; 1 promoted, 2 parked, 0 rejected |
| 2 | Genuinely novel mechanisms measured against the **incumbent** hive (chaining) | 0/2 promoted — the loop stalls at compounding |
| 3 | Hypothesis tests (noise vs calibration; single-domain vs multi-domain) + offline counterfactual rule analysis | The gate/weighting design — not the mechanisms — is the binding constraint |
| 4 | Real run under an experimental per-domain promotion gate | 1/2 promoted — the loop *can* improve again, but candidate overlap makes compounding illusory |
| 5 | Non-redundancy test: an orthogonal Maze mechanism chained onto the grown hive | **1/1 PROMOTED — final hive 0.9480 beats the 0.9220 single-shot ceiling.** Compounding confirmed in the additive sense |
| 6 | Second loop: the proposal machinery made in-band (a strategy mechanism on a `propose` hook) with a randomized-memo control | **0/1 promoted — H-LIN supported.** The strategy's guidance measurably reduced harm (Q −0.403 → −0.320) but never produced positive proposal quality (7/7/7 matched seeds) |

**Six-phase answer:** the loop genuinely self-improves **one step at a time**,
and — once the redundancy confound is removed — sequences of *non-overlapping*
mechanisms **stack additively and beat any single-shot ceiling**. Final hive
aggregate **0.9480**, up **+22.0% cumulative** from the phase-1 baseline of
0.7768. The compounding excess is exactly **+0.0000**: gains accumulate
linearly, not multiplicatively. And Phase 6 closes the last structural gap —
making the proposal machinery itself in-band — and still finds **no
machinery-level compounding**: LLM-proposed mechanism gains are first-order.
Goertzel's strong claim (self-improvement amplifying itself super-additively
into a runaway virtuous cycle) remains **unsupported at every level tested**;
the loop is a working *additive self-assembler for non-overlapping headroom*,
not an accelerator.

---

## The theory being tested

Goertzel's OmegaHive hypothesis (loosely):

> A colony of agents sharing an AtomSpace-like memory, each cycle proposing one
> new cognitive mechanism, can evaluate it across an ecology of environments and
> promote only what measurably helps — and by doing so enter a virtuous cycle of
> ever-easier self-improvement.

The strong claim is the **compounding**: improvement N should make improvement
N+1 cheaper or larger. This experiment was designed from the start to be able
to test that claim honestly — which meant measuring every candidate against the
**current** hive state (not a fixed baseline), which is exactly what most quick
demonstrations skip.

## The system

```
CONSTITUTION.md        supreme law: inviolable core, governance rule, honesty rules
hive/                  4 agents + AtomSpace-lite shared memory + message bus + hook pipe
eval_ecology/          3 evaluation environments + scoring/aggregation runner
mechanisms/            cognitive mechanisms (each a set of hook handlers)
loop/                  the governed uplift loop, governance rule, chaining & counterfactual protocols
scripts/run.sh         one-command runner
logs/                  decisions log, message bus transcripts, scorecards, cost report
checkpoints/           hive state after every cycle (git commits too)
*.md                   per-phase reports + final analysis
```

### The four agents (Architect → Implementer → Evaluator → Governor)

| Agent | Role |
|---|---|
| **Architect** | Decides *which single mechanism* the hive adds this cycle |
| **Implementer** | Loads/writes the mechanism code into `mechanisms/` |
| **Evaluator** | Runs the full ecology before and after, producing score vectors |
| **Governor** | Applies the fixed constitutional rule and issues a binding verdict |

### Shared memory (AtomSpace-lite)

A JSON-backed store of atoms and links with **confidence weights**, written and
read through a hook pipe so mechanisms compose without knowing about each other.
Mechanisms are pure functions attached to named hooks (`before_eval`,
`after_write`, `choose_action`, ...); the pipe threads a mutable context through
the active ones in roster order.

### The evaluation ecology (each run ~0.4 s, 21 seeds)

| Env | Task | Primary metric |
|---|---|---|
| **Maze-lite** | grid navigation with partial observability, 5 episodes/layout | 0.5·success + 0.5·efficiency |
| **RepoOps-lite** | pick the correct fix for buggy Python snippets using memory evidence | hidden-test success rate |
| **SelfLab** | hive estimates the quality of its own module candidates | normalized quality |

Aggregate primary = 0.40·maze + 0.35·repoops + 0.25·selflab (constitutional).
Aggregate robustness = min of the environments' robustness values.

### The governance rule (constitutional, fixed)

- **PROMOTE**: aggregate-primary relative delta ≥ +5% **and** robustness does
  not drop > −10%
- **PARK**: otherwise, if relative delta ≥ −5% (neutral — real but sub-threshold)
- **REJECT**: relative delta < −5%

The core loop (`loop/driver.py`), scoring (`eval_ecology/runner.py`) and the
governance thresholds (`loop/governance.py`) are **inviolable** — a constitution
article forbids mechanisms or agents from modifying them. The only way to change
hive behavior is to add or modify a *mechanism* through the governed pipeline.

---

## The experiment, phase by phase

### Phase 1 — baseline + first uplift cycles (the "does the loop work at all" test)

Three mechanisms were designed: `memory_consolidation` (merge/reinforce/prune
shared memory), `attention_budget` (capacity-limited candidate focus), and
`uncertainty_planning` (expected-information-gain maze frontier targeting).

| cycle | mechanism | before → after | verdict |
|---|---|---|---|
| 0 | baseline | 0.7768 → 0.7768 | — |
| 1 | memory_consolidation | 0.7768 → 0.8081 (+4.0%) | PARK |
| 2 | attention_budget | 0.7768 → 0.7983 (+2.8%) | PARK |
| 3 | uncertainty_planning | 0.7768 → **0.8710 (+12.1%)** | **PROMOTE** |

Governance behaved exactly as designed: it amplified the one mechanism with a
strong cross-ecology effect and refused two sub-threshold ones. No robustness
regression. **Caveat found:** all three were measured against the *empty*
baseline — the loop had not yet been tested for compounding.

### Phase 2 — the chaining test (does improvement build on improvement?)

Fixed the protocol so every candidate is measured against the **current
incumbent hive** `[uncertainty_planning]`, on 21 seeds with the 7 constitutional
seeds re-run for comparability. The Architect designed two **genuinely novel**
mechanisms from the source code alone: `residual_bias` (a predictive-residual
evidence filter for RepoOps) and `frontier_memory` (cross-episode exploration
credit transfer for Maze).

| candidate | target | 21-seed delta | 7-seed delta | verdict |
|---|---|---|---|---|
| residual_bias | RepoOps | +2.8% | +4.3% | PARK |
| frontier_memory | Maze | +0.6% | +1.2% | PARK |

Both gains were real, strictly non-negative (0/21 negative seeds for
residual_bias), and perfectly domain-isolated (transfer probes exactly 0.0000)
— yet both parked. **No compounding.** Two competing explanations emerged:
`frontier_memory`'s effect was buried in per-seed noise (calibration artifact?),
and the +5% aggregate gate may be structurally near-unreachable for
single-domain mechanisms at this incumbent level (ceiling hypothesis).

### Phase 3 — hypothesis tests + counterfactual rule analysis

Instead of more mechanism cycles, Phase 3 ran a **decision-theoretic experiment
on the loop design itself**:

- **H1 (noise):** a calibrated `frontier_memory_v2` (success-gated credit, ≥2
  confirmations, smaller decay) recovered 2.2× the Maze gain and capped the
  worst-seed downside (−0.53 → −0.12) — but still parked (+1.4%). Per-seed sd
  (0.115) remained 3.7× the mean (0.031). **H1 refuted:** the phase-2 park was
  not a calibration artifact; this mechanism class captures only ~17% of the
  theoretical Maze headroom.
- **H2 (ceiling):** `evidence_substrate`, a two-hook multi-domain mechanism
  (Maze + RepoOps), produced the largest honest chained gain ever measured —
  **+4.2%, robustness +9.5 pts**, 95% of the hard RepoOps ceiling — yet parked
  0.8 points short. **H2 refuted in strong form:** even the best mechanism class
  cannot clear the gate at this incumbent level. The gate/weighting design is
  the binding constraint.
- **Offline counterfactual** (`loop/counterfactual.py`): re-ran the four
  measured candidates under alternative rules *without re-measuring anything*:

  | candidate | actual | per-domain gate | equal 1/3 weights | headroom-prop weights |
  |---|---|---|---|---|
  | residual_bias | PARK | **PROMOTE** (repoops +7.8%) | PARK | PARK |
  | frontier_memory | PARK | PARK | PARK | PARK |
  | frontier_memory_v2 | PARK | PARK | PARK | PARK |
  | evidence_substrate | PARK | **PROMOTE** (repoops +7.8%) | PARK | PARK |

  Under the current rule 0/4 candidates promote; under a per-domain gate 2/4
  would — and both are the candidates that maxed their own domain. This made a
  **crisp falsifiable prediction**: run the loop under a per-domain gate and
  both should promote, producing the first compounding event.

### Phase 4 — real-run falsification of the prediction

Implemented the per-domain gate as an **experimental variant** (new files only;
the constitution was never touched) and ran the real chained protocol:

| stage | hive measured | 21-seed primary | promoting domain | verdict |
|---|---|---|---|---|
| baseline | [uncertainty_planning] | 0.8847 | — | — |
| Cycle A | + residual_bias | 0.9097 | repoops +7.79% rel | **PROMOTE** |
| Cycle B | + evidence_substrate | 0.9220 | maze +3.75% rel; repoops +0.00% | PARK |

**Prediction verdict: PARTIAL.**

- Claim (a) first half — **confirmed:** `residual_bias` promoted (the loop's
  first promotion since phase 1), proving the aggregate gate was over-locking a
  real within-domain gain.
- Claim (a) second half / claim (b) — **refuted:** against the grown incumbent,
  `evidence_substrate` parks, because its RepoOps effect is *the same effect*
  as residual_bias (candidate overlap/redundancy), and its Maze gain is
  sub-threshold and seed-unstable.

The diagnostic final hive `[up, residual_bias, evidence_substrate]` measured
**0.9220 — exactly equal to evidence_substrate alone** and exactly equal to the
additive projection. The counterfactual's implied compounding was illusory: its
per-candidate arithmetic never modeled the overlap between candidates.

> **📌 Key methodological finding (Phase 4):** the offline counterfactual's
> arithmetic failed to model **candidate overlap**. It scored every candidate
> against the *original* incumbent, so two mechanisms that improve the *same*
> domain — `evidence_substrate ⊇ residual_bias` on RepoOps — both looked
> promotable. In a real chained run, the second one contributes **+0.0000**.
> This is itself a scientific result: any self-improvement protocol that
> evaluates candidates in isolation (including most published "agent
> improvement" demonstrations) will systematically *overestimate* compounding
> potential. The correct test of a virtuous cycle must measure candidate
> *interactions*, not just candidate deltas. Phase 5 did exactly that with a
> provably non-overlapping mechanism.

Also demonstrated (honestly): **the per-domain gate is gameable** — it rewards
single-domain cherry-picking with no aggregate requirement and no robustness
guard, which the constitutional gate was designed to enforce.

### Phase 5 — the non-redundancy test (does an orthogonal chain beat the ceiling?)

The phase-4 report's central question: is the 0.9220 single-shot ceiling
absolute, or can a chain of *provably non-overlapping* mechanisms exceed it?
The Architect designed `progress_thermostat` — a **stateful, within-episode
explore/exploit control layer** for Maze: it tracks the best goal-distance
reached so far and flips the objective to pure goal-proximity exploitation near
the goal, and pulls the frontier back whenever the agent drifts beyond its best
approach. It deliberately touches **no** hook that residual_bias or the
twice-failed frontier-memory class uses (no `after_write`, no cross-episode
credit).

| stage | hive measured | 21-seed primary | promoting domain | verdict |
|---|---|---|---|---|
| baseline | [up, residual_bias] | 0.9097 | — | — |
| cycle | + progress_thermostat | **0.9480** | maze +11.65% rel (0.8229→0.9188) | **PROMOTE** |

**H-NR CONFIRMED, H-GATE REFUTED.** The controlled non-redundancy audit showed
the maze gain is **identical with and without** residual_bias (+0.0959 both
ways), and the mechanism moves RepoOps exactly **+0.0000** — orthogonal by
construction, unlike phase-4's confounded candidate.

**Headline: final hive `[uncertainty_planning, residual_bias,
progress_thermostat]` = 0.9480, beating the 0.9220 phase-4 ceiling by +0.0260.**

| configuration | 21-seed primary |
|---|---|
| [up] baseline | 0.8847 |
| [up, residual_bias] | 0.9097 (+0.0250, repoops) |
| [up, progress_thermostat] | 0.9230 (+0.0383, maze) |
| **[up, residual_bias, progress_thermostat]** | **0.9480** |
| additive projection | 0.9480 (exact) |
| compounding excess | **+0.0000** |

**Compounding is real in the additive sense and exactly zero in the
super-additive sense.** The chain stacks linearly, beats every single-shot
configuration, and each promotion is a real, measured, orthogonal gain —
but there is no multiplicative term. From the phase-1 baseline of 0.7768 the
final hive is **+22.0% cumulative**.

### Phase 6 — the second loop (does in-band proposal machinery compound?)

The phase-5 result exposed the deepest structural gap: the improvement
machinery sat *outside* the hive — `loop/architect.py` is static data, so the
loop never read its own history into the next proposal. Phase 6 closed that
gap: a **strategy mechanism** (`success_signature_policy`, zero task-hook
handlers) now sits on a new in-band `propose` hook, reads a proposal-state
substrate (headroom map, promotion signatures, overlap table), and emits a
PROPOSAL MEMO — the *only* channel from history to the next proposed
mechanism. Three arms, same probe class (`frontier_memory_v3`), tuned per-arm
only via the memo, measured against the mature 0.9480 incumbent:

| arm | condition | probe config | agg delta | Q (delta/headroom) | neg seeds |
|---|---|---|---|---|---|
| 0 | baseline (empty memo) | naive | −0.0327 | **−0.402803** | 15/21 |
| 1 | strategy memo (real history) | calibrated | −0.0260 | **−0.320221** | 16/21 |
| 2 | **permuted-memo control** | naive fallback | −0.0327 | **−0.402803** | 15/21 |

**Verdict: PARK → H-LIN supported.** The strategy's guidance is real and
distinguishable (arm 1 ≠ arm 2; the permutation control degraded guidance to
the no-guidance default, so Q2 == Q0 exactly) — but proposal quality never went
positive, negative seeds regressed (16 > 15), and the matched per-seed split is
exactly **7/7/7**. In-band machinery produces informational gains (variance
reduction), not compounding. The monotonicity cycle never ran (no promotion),
so no second-cycle compounding excess exists to compute.

> **📌 The capability-ceiling caveat (stated explicitly, as required):** even a
> positive H-VC result here would be machinery-level compounding only. No
> mechanism modifies the LLM oracle's fixed capability, so the strongest form of
> the self-uplifting claim — that the agent's proposing ability itself grows —
> remains untested and untestable in this architecture. Phase 6 does not change
> that; it makes the boundary statement sharper: **even with machinery-level
> feedback, LLM-proposed mechanism gains are first-order.**

---

## The honest bottom line

- ✅ A governed, single-mechanism-at-a-time improvement loop **works**: real
  measured gains, honest filtering, non-destructive (never a negative seed for
  the best candidates), perfectly domain-isolated, seed-stable verdicts.
- ✅ **Non-overlapping mechanisms chain additively and break single-shot
  ceilings** (phase 5: 0.9480 > 0.9220). With candidate redundancy removed, the
  loop is a working additive self-assembler across domain headrooms.
- ✅ **In-band proposal machinery works as designed** (phase 6): the strategy
  mechanism read real history, produced distinguishable guidance, and the
  permuted-memo control confirmed the attribution — a methodological template
  for anyone testing "agent self-improvement."
- ❌ The **super-additive virtuous cycle does not emerge** in six phases and
  ~45 measured configurations. The compounding excess is exactly **+0.0000**,
  and closing the feedback loop (phase 6) still yields first-order gains only:
  guidance reduced a bad probe's harm but never made proposal quality positive.
  Self-amplification remains unsupported at every level tested.
- 🔬 Three design-level findings, each separately valuable: (1) a single
  aggregate gate hides within-domain gains; (2) per-domain gates fix that but
  invite cherry-picking and drop the robustness guard; (3) **candidate overlap
  is the hidden killer of compounding** — evaluating candidates in isolation
  systematically overestimates compounding potential (the phase-4 callout above),
  and even with overlap fixed, the capability ceiling (a fixed LLM designer)
  keeps gains first-order (phase 6).

## How to reproduce everything

```bash
# full phase-1 run (baseline + 3 cycles), constitution + git checkpoints
python3 -m loop.driver

# one cycle / resume from saved state
python3 -m loop.driver --cycle 3 --resume

# phase-2/3 chaining protocols (21 seeds, scorecards, git checkpoints)
python3 -m loop.chaining
python3 -m loop.chaining --phase3

# phase-4 experimental per-domain gate run
python3 -m loop.chain_perdomain

# phase-5 non-redundancy run (chain_perdomain2 protocol)
python3 -m loop.chain_perdomain2

# phase-6 second-loop protocol (in-band proposal machinery, 3 arms + strategy gate)
python3 -m loop.chain_second_loop

# offline governance counterfactual (reads scorecards only)
python3 -m loop.counterfactual

# or use the runner
./scripts/run.sh run | baseline | cycle N | resume | scorecard N | state | synergy
```

Every command is deterministic (fixed seeds), requires only Python 3.12, and
prints/stores the same numbers in the reports.

## Reading map

| File | What it is |
|---|---|
| `FINAL_REPORT.md` | Phase-1 answer to the research question |
| `CHAINING_REPORT.md` | Phase-2: does the loop compound? |
| `PHASE3_REPORT.md` | Phase-3: hypothesis tests + counterfactual rule analysis |
| `PHASE4_REPORT.md` | Phase-4: real-run falsification of the per-domain gate prediction |
| `PHASE5_REPORT.md` | Phase-5: the non-redundancy test — compounding confirmed (additive) |
| `PHASE6_REPORT.md` | Phase-6: the second loop — in-band machinery tested, H-LIN supported |
| `STATUS.md` | Up-to-date status with all phase results and final hive state |
| `EXPERIMENT_LOG.md` | Full narrative of the run |
| `logs/scorecards/` | Raw before/after score vectors for every measured configuration |
| `logs/decisions.log` | Every architectural decision, verdict, and error |
| `logs/counterfactual.md` | The offline rule counterfactual table |
| `CONSTITUTION.md` | The colony's supreme law (inviolable core) |

## License

MIT — see [LICENSE](LICENSE). All experiment artifacts (code, reports, logs)
are included; the numbers are what they are, warts and all. That is the point.
