# PHASE 5 REPORT — non-redundancy test: does an orthogonal chain beat the single-shot ceiling?

**Protocol:** `python3 -m loop.chain_perdomain2` (NEW files only: `loop/chain_perdomain2.py`,
`mechanisms/progress_thermostat.py`). Experimental per-domain gate
(`loop/gate_perdomain.py`, phase-4, still NOT constitutional) applied to REAL
`aggregate()` measurements (21 extended seeds + 7 constitutional re-run). Every
number below is from a real run.

**Candidate:** `progress_thermostat` — a maze-only, WITHIN-episode
explore/exploit thermostat. Target: Maze (0.8229, weight 0.40), the only domain
with real headroom AND non-trivial weight (RepoOps saturated at 0.9881; SelfLab
0.9386 is only reachable via the parked attention_budget, so any honest SelfLab
effect is impossible — the mechanism honestly targets maze only).

## Mechanism and orthogonality argument (summarized)

The incumbent maze planner `uncertainty_planning` is a STATELESS scorer: at
every decision it re-ranks frontier cells by info-gain-per-step plus a fixed
goal bias, with no memory of the episode. Tracing the failure mode (seed 101
maze 1) shows the agent reaches within 3 cells of the goal, then keeps
committing to high-info-gain cells that lie AWAY from the goal, drifts into a
wall pocket, and burns the 95-step budget on all 5 episodes.

`progress_thermostat` is a STATEFUL within-episode CONTROL layer over that same
decision: it tracks the minimum goal-distance reached so far in the episode
(`best`) and the current position, and (a) flips the objective to pure
goal-proximity exploitation whenever the agent is within `EXPLOIT_NEAR` (5)
cells of the goal, and (b) pulls the frontier back toward the goal whenever the
agent drifts more than `DRIFT` (3) cells beyond its best approach. Away from
the goal it defers 100% to uncertainty_planning. It has no `after_write` hook
(RepoOps is residual_bias's territory), no cross-episode credit transfer
(that's the twice-failed frontier_memory class), and its only hook is
`choose_action` (Maze only). Full rationale in `logs/decisions.log` [ARCHITECT].

## Results

| stage | hive measured | 21-seed primary | agg rel | promoting domain (rel) | per-domain gate | constitutional reference |
|---|---|---|---|---|---|---|
| baseline | [uncertainty_planning, residual_bias] | 0.9097 | — | — | — | — |
| cycle | + progress_thermostat | **0.9480** | +4.21% | **maze +11.65%** (0.8229→0.9188) | **PROMOTE** | PARK (+4.21%) |
| 7-seed re-run | + progress_thermostat | 0.9343 | +2.84% | maze +7.82% | PROMOTE | PARK |

- Robustness improved in the cycle: aggregate 0.5048 → 0.6381 (+0.1333);
  7-seed 0.3143 → 0.6286 (+0.3143). No domain primary dropped (worst rel delta
  in the cycle = 0.00%, both 21- and 7-seed).
- Seed stability (maze, 21 seeds): mean +0.0958, sd 0.1389 (sd > mean), min
  −0.1078, max +0.6161, positive 17/21, negative 3/21 (seeds 505 −0.108,
  1708 −0.062, 606 −0.003). Aggregate per-seed delta: mean +0.0383, sd 0.0556,
  negative 3/21 (−0.043, −0.025, −0.001). Less seed-stable than residual_bias
  (0/21 negative) but never catastrophically negative; effect is real, not
  Gaussian-stable.

## 1. Gate verdict: **H-NR CONFIRMED, H-GATE REFUTED**

`progress_thermostat` PROMOTED under the experimental per-domain gate against
the grown incumbent [uncertainty_planning, residual_bias]: Maze +11.65% rel
clears the +5% bar by a wide margin, no domain dropped > −3%. This is the
loop's second promotion under the experimental gate and the first that targets
a NEW domain (phase-4's residual_bias took RepoOps; this takes Maze).

The alternative hypothesis H-GATE ("even a well-designed non-overlapping
mechanism fails, ceiling confirmed") is refuted: the gate/headroom does NOT
bind for a mechanism aimed at the unclaimed Maze headroom. Phase-4's Phase-4
puzzle is resolved: the binding constraint then was REDUNDANCY
(evidence_substrate's maze gain was bundled with a fully-redundant RepoOps
gain), not the gate.

## 2. The compounding test: **the chain BEATS the 0.9220 single-shot ceiling — additively, not super-additively**

**Headline number: final hive [uncertainty_planning, residual_bias,
progress_thermostat] 21-seed primary = 0.9480**, vs the 0.9220 phase-4
single-shot ceiling (evidence_substrate alone) → **beats it by +0.0260
(+2.8%)**.

Decomposition (all real `aggregate()` runs, 21 seeds):

| configuration | 21-seed primary | note |
|---|---|---|
| [up] (baseline) | 0.8847 | — |
| [up, residual_bias] (phase-4 incumbent) | 0.9097 | rb gain +0.0250 (repoops) |
| [up, progress_thermostat] (pt alone) | 0.9230 | pt gain +0.0383 (maze) |
| **[up, residual_bias, progress_thermostat]** | **0.9480** | final hive |
| additive projection (0.8847 + 0.0250 + 0.0383) | 0.9480 | exact |
| compounding excess (actual − additive) | **+0.0000** | — |

**The chain is perfectly ADDITIVE, not super-additive.** Each mechanism's
marginal gain is identical with and without the other (pt's maze delta is
+0.0959 both with and without rb; rb's repoops delta is +0.0714 both ways).
The final hive exceeds the phase-4 single-shot ceiling because (a) pt alone
already beats es alone (0.9230 > 0.9220 — pt's maze gain is ~3× es's), and
(b) the rb + pt stack covers BOTH the repoops and maze headrooms that es
bundled into a single mechanism. There is no multiplicative/interaction term
(excess exactly 0.0000). So "compounding" is real in the weak additive sense
(non-overlapping gains stack and beat any single shot) but NOT in the strong
sense (no second-order amplification).

## 3. Non-redundancy audit (marginal contributions, 21 seeds)

| configuration | aggregate | maze | repoops | selflab |
|---|---|---|---|---|
| A: [up] | 0.8847 | 0.8229 | 0.9167 | 0.9386 |
| B: [up, rb] (incumbent) | 0.9097 | 0.8229 | 0.9881 | 0.9386 |
| C: [up, mech] | 0.9230 | 0.9188 | 0.9167 | 0.9386 |
| D: [up, rb, mech] | 0.9480 | 0.9188 | 0.9881 | 0.9386 |

- pt's maze gain WITHOUT rb (C − A): **+0.0959** (+11.65% rel)
- pt's maze gain WITH rb (D − B): **+0.0959** (+11.65% rel) — identical ⇒
  **orthogonal on Maze**
- repoops delta of pt (D − B): **+0.0000** — does NOT touch residual_bias's
  territory ⇒ no overlap, audit NOT confounded
- selflab delta of pt (D − B): **+0.0000**

This is the controlled measurement the mission called for: the mechanism's
maze gain is present with AND without residual_bias, and it moves RepoOps
exactly zero. The phase-4 redundancy confound (evidence_substrate ⊇
residual_bias on repoops) is absent here by construction.

## 4. Cumulative 5-phase answer: **the loop self-improves AND chains additively when candidates are non-overlapping — but does not super-compound**

- Phase 1: 0.7768 → 0.8710 (+12.1%) — first promotion (uncertainty_planning).
- Phase 2: 0/2 promotions (residual_bias, frontier_memory) at +5% aggregate.
- Phase 3: 0/2 promotions (frontier_memory_v2, evidence_substrate); counterfactual
  showed the aggregate gate was hiding within-domain gains.
- Phase 4: 1/2 promotion under the per-domain gate (residual_bias); second
  candidate fully redundant (evidence_substrate ⊇ residual_bias), final hive =
  single-shot ceiling exactly. Conclusion: rule-design matters, redundancy binds.
- Phase 5: 1/1 promotion of a provably non-overlapping maze mechanism; final
  hive 0.9480 BEATS the 0.9220 ceiling by +0.0260. **The chain of non-overlapping
  candidates stacks additively and breaks the single-shot ceiling.**

**Honest verdict:** after removing the redundancy confound, the evidence
supports a compounding self-uplifting loop in the ADDITIVE sense: a sequence of
mechanisms aimed at different domain headrooms (RepoOps, then Maze) produces a
final hive higher than any single mechanism, and each promotion is a real,
measured gain. Goertzel's strong claim (self-improvement amplifying itself
super-additively) remains UNSUPPORTED: the compounding excess is exactly
+0.0000 — gains accumulate linearly, not multiplicatively. The loop is a
working additive self-assembler for non-overlapping headroom, not yet a
runaway virtuous cycle.

## 5. The single most valuable next experiment

Test whether the ADDITIVE stack can be pushed further by a second maze-capable
(or multi-domain) mechanism WITHOUT redundancy, i.e. does the maze headroom
survive another orthogonal layer. Two concrete options, in order of value:

1. **Second-order stack test (H-SUPER-ADD):** design a SECOND maze mechanism
   whose signal is provably orthogonal to BOTH uncertainty_planning (stateless
   info-gain) AND progress_thermostat (proximity-based objective flip) — e.g. a
   within-episode dead-end topology memory (pocket detection from discovered
   wall structure) that re-ranks ONLY confirmed-dead-end neighborhoods, leaving
   the thermostat's goal-proximity lever untouched. Chain it against the new
   incumbent [up, rb, pt] under the per-domain gate. If maze clears +5% again
   AND the 4-mechanism hive exceeds 0.9480, the additive stack is confirmed
   non-saturating; if it PARKs, we have measured the practical maze ceiling.
   This is the direct next step of the non-redundancy hypothesis.
2. **Constitutionalization test:** take the two experimental promotions
   (residual_bias, progress_thermostat) through the REAL constitutional gate —
   the aggregate +5% rule — to test whether rule-design should be updated, now
   that within-domain gains demonstrably compose into additive aggregate gains.

## Final hive state (committed)
`checkpoints/p5_state.json`: active `["uncertainty_planning", "residual_bias",
"progress_thermostat"]`, promoted `["progress_thermostat"]`, parked `[]`.
Aggregate primary **0.9480** (from 0.9097, +4.21%; from phase-1 baseline
0.7768: +22.0% cumulative). Constituency `hive_state.json` unchanged (phase-5
is an experimental protocol, not a constitutional adoption).
