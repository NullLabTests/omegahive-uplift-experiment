# PHASE 3 REPORT — hypothesis tests (H1, H2) + counterfactual rule analysis

Phase 3 was not another mechanism cycle; it was a **decision-theoretic experiment
on the loop design itself**. It tested the two hypotheses that CHAINING_REPORT.md
advanced for the phase-2 stall — (H1) the `frontier_memory` park was a
calibration artifact (noise), and (H2) the +5% aggregate gate is structurally
unreachable for single-domain mechanisms — plus an **offline counterfactual
analysis** of the promotion rule. All numbers below come from real
`aggregate(...)` runs (21 seeds, with the 7 constitutional seeds re-run) and from
pure offline computation on the measured scorecards. No inviolable core file was
modified.

## The two hypothesis-testing mechanisms

| mech | tests | hooks | design | 21-seed verdict |
|---|---|---|---|---|
| `frontier_memory_v2` | H1 | `choose_action` (Maze) | calibrated `frontier_memory`: success-gated credit (penalize only a cell whose episode failed AND never approached the goal, best_dist > 4), MIN_CONF=2 confirmations before any penalty, BETA 0.10→0.03 | **PARK (+1.4%)** |
| `evidence_substrate` | H2 | `choose_action` (Maze) + `after_write` (RepoOps) | multi-domain: one shared reliability primitive — per-feature EMA residual correction on RepoOps evidence (the recipe that took `residual_bias` to +2.8%) plus the calibrated confirmation-gated Maze re-ranking | **PARK (+4.2%)** |

**Reachability audit (documented honestly):** the runner fires `before_eval`,
`choose_action` and `after_write` in the current hive. `retrieve` fires **only**
for SelfLab and **only** when `attention_budget` is active — it is PARKED, so
**SelfLab is genuinely unreachable by any new mechanism** (a `retrieve` hook
would be dead code). A second hook-contract fact: `env_maze` calls
`choose_action(ctx, known_map, frontier)` **without** the atomspace, so the maze
side of any mechanism is ctx-local per seed, while `env_repoops` **does** hand
the atomspace to `after_write`. The multi-domain design is therefore: two hooks,
one shared primitive, two storage sites (ctx for maze, atomspace for repoops).
These two facts are themselves findings about what the hook contracts permit.

## 1. H1 verdict — was the phase-2 park a calibration artifact?

**H1 (strong form: calibration recovers a gate-clearing Maze gain) is REFUTED.**
The calibration worked exactly as prescribed, but the effect is still
sub-threshold and still variance-dominated.

| metric (21 seeds) | `frontier_memory` v1 | `frontier_memory_v2` |
|---|---|---|
| aggregate before → after | 0.8847 → 0.8903 (+0.6%) | 0.8847 → 0.8970 (**+1.4%**) |
| maze primary | +0.0141 | +0.0309 (2.2x) |
| per-seed maze delta mean / sd | +0.0141 / 0.1434 | +0.0308 / 0.1146 |
| per-seed min / max | −0.5262 / — | −0.1187 / +0.5101 |
| robustness delta | 0.0 | 0.0 |

The calibration contained the catastrophic downside (worst seed −0.53 → −0.12),
more than doubled the mean gain, and lifted aggregate +0.6% → +1.4%. But **sd
(0.115) is still 3.7x the mean (0.031)**, and +1.4% is nowhere near the +5%
gate. Two honest caveats: the effect is net-positive (11/21 seeds positive,
5/21 negative, downside capped), and on lucky seeds the reward-side transfer is
very strong (max +0.51). Conclusion: **the phase-2 park was not purely a
calibration artifact.** The +8.0% Maze headroom claim is mathematically real
(0.40 weight × (1.0 − 0.823) primary) but the calibrated mechanism captures only
~17% of it; clearing +5% would require capturing ~62% of all remaining Maze
headroom, which this mechanism class does not do.

## 2. H2 verdict — did a multi-domain mechanism clear the gate?

**H2 (strong form: a multi-domain mechanism promotes) is also REFUTED — but
narrowly, and the ceiling is real.** `evidence_substrate` produced the largest
honest aggregate gain of any chained candidate ever measured:

| metric (21 seeds) | value |
|---|---|
| aggregate before → after | 0.8847 → 0.9220 (**+4.2%**), robustness 0.4286 → 0.5238 (**+9.5 pts, improved**) |
| maze primary | +0.0309 |
| repoops primary | 0.9167 → 0.9881 (+0.0714, 95% of the hard RepoOps ceiling) |
| selflab primary | 0.0000 (perfect isolation) |
| 7-seed | 0.8710 → 0.9136 (+4.9%) |

The multi-domain design works as intended — the aggregate is exactly the sum of
its two hooks (maze +1.4% + repoops +2.8% = +4.2%) — and it is the closest any
candidate has come to the gate (+4.2% vs the required +5.0%). But it **did not
promote**. Under the H2 decision rule, that means **the gate/weighting design is
the binding constraint — a design-level finding**: even a well-designed
two-hook mechanism that fully captures the RepoOps ceiling *and* a real Maze
gain lands 0.8 points short. The `+5% aggregate` gate is, by construction,
nearly unsatisfiable at this incumbent level regardless of mechanism class.

## 3. Counterfactual — under which rule does the loop actually compound?

Offline analysis on the four measured candidates (2 phase-2 + 2 phase-3),
`logs/counterfactual.md`. No evaluations re-run, no verdicts changed.

| candidate | actual | per-domain gate | equal 1/3 w | headroom-prop w | clears +5% under any weights? |
|---|---|---|---|---|---|
| `residual_bias` | PARK +2.8% | **PROMOTE** (repoops +7.8%) | PARK | PARK | YES, but only at repoops w ≥ 0.62 (L1 0.54) |
| `frontier_memory` | PARK +0.6% | PARK | PARK | PARK | **NO — impossible** (max +1.6%) |
| `frontier_memory_v2` | PARK +1.4% | PARK | PARK | PARK | **NO — impossible** (max +3.5%) |
| `evidence_substrate` | PARK +4.2% | **PROMOTE** (repoops +7.8%) | PARK | PARK | YES, at a small L1 0.195 (repoops 0.45, selflab 0.15) |

**Headline:** the phase-2/3 stalls are a **rule-design problem, not a mechanism
problem**. Under the current rule 0/4 candidates promote. Under a per-domain
gate (PROMOTE iff ANY domain ≥ +5% relative, no domain drops > −3%) **2/4 would
promote** — exactly the two candidates that maxed their own domain (RepoOps
+7.8% relative within-domain). Rebalancing weights toward equal or headroom
proportionality promotes **0/4** (it dilutes the one domain that has usable
gain). So a per-domain gate would have produced the loop's first compounding
event twice over.

## 4. Cumulative scientific answer — is there a virtuous self-uplifting loop?

**After three phases the evidence supports a *non-destructive, honest filtering*
loop, but NOT a *compounding* one at the current gate.**

- Phase 1 (+12.1%) was a one-time, empty-baseline win: fixing a near-random Maze
  policy. It is not reproducible evidence of compounding.
- Phases 2–3 produced real, small, reliably non-negative, perfectly-isolated
  additive gains (+2.8%, +0.6%, +1.4%, +4.2%) and **zero second-order
  promotions**. Every candidate passed honest, seed-stable governance; every
  transfer probe was exactly 0.0000 in off-design domains; `evidence_substrate`
  even improved robustness.
- The counterfactual shows the compound failure is a **gate/weighting artifact**:
  two candidates achieved a +7.8% within-domain improvement that the single
  aggregate number hides.

**Where the design must change (in order of leverage):**
1. **Gate** — the single aggregate gate is the binding constraint. A per-domain
   promotion gate (promote iff ANY domain ≥ +5% relative, no domain > −3% drop)
   would have promoted `residual_bias` and `evidence_substrate`.
2. **Weights** — only a reallocation toward the domain with usable headroom
   (RepoOps) helps; even the small L1 0.195 move (repoops 0.35→0.45) lets
   `evidence_substrate` clear +5%. Equal or headroom-proportional weights do
   *not* help.
3. **Mechanism class** — multi-domain is confirmed as the right (indeed the
   only) class that can approach the gate; the additive two-hook design works.
4. **Horizon** — allow the incumbent to accumulate 2–3 sub-threshold gains and
   re-measure; +2.8% + +4.2% would compound additively even though each alone
   parks.

## 5. The single most valuable next experiment

**Phase 4: run the loop under the per-domain promotion gate.** The counterfactual
gives a crisp falsifiable prediction — `residual_bias` and `evidence_substrate`
would both promote — so Phase 4 can finally test whether a governed loop that
promotes per-domain gains *then* chains (measure `evidence_substrate` against
`[uncertainty_planning, residual_bias]`) produces a second-order, compounding
hive. It directly measures the counterfactual's central claim, is cheap (the
evaluations are ~0.4s each), and would turn the loop's first genuine compounding
event into evidence either for or against the per-domain gate.

## One-command re-runs
```bash
python3 -m loop.chaining --phase3   # phase-3 protocol: baseline + cycle-3 (C) + cycle-4 (D)
python3 -m loop.counterfactual      # offline rule counterfactual (reads scorecards only)
```

## Bottom line
H1: calibrated `frontier_memory_v2` is real and 2.2x better than v1 but stays
variance-dominated (+1.4%) — the park was **not** a calibration artifact. H2:
the multi-domain `evidence_substrate` set the phase record (+4.2%, robustness
improved) but still parks — **the gate is the binding constraint**. Counterfactual:
the stalls are a rule-design problem; a per-domain gate would have produced two
compounding promotions. The loop filters honestly and non-destructively; whether
it *compounds* is now a testable question about the gate, not about the
mechanisms.
