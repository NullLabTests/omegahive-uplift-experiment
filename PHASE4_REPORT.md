# PHASE 4 REPORT — real-run falsification of the per-domain gate prediction

**Protocol:** `python3 -m loop.chain_perdomain` (new files only: `loop/gate_perdomain.py`,
`loop/chain_perdomain.py`). Experimental per-domain gate applied to REAL
`aggregate()` measurements (21 extended seeds + 7 constitutional re-run). The
constitutional gate (`loop/governance.py`) was never modified. Every number below
is from a real run.

## Experimental gate (Phase 4 only — NOT constitutional)
PROMOTE iff ANY domain primary (maze, repoops, selflab) rises >= +5% RELATIVE to
its before value AND no domain primary drops > -3% relative; PARK otherwise if
aggregate rel >= -5%; REJECT otherwise.

## Results

| stage | hive measured | 21-seed primary | agg rel | promoting domain (rel) | per-domain gate | constitutional reference |
|---|---|---|---|---|---|---|
| baseline | [uncertainty_planning] | 0.8847 | — | — | — | — |
| Cycle A | + residual_bias | 0.9097 | +2.83% | **repoops +7.79%** (0.9167→0.9881) | **PROMOTE** | PARK (+2.83%) |
| Cycle B | + evidence_substrate (vs grown incumbent [up, rb]) | 0.9220 | +1.35% | maze +3.75% (0.8229→0.8538); repoops +0.00% | **PARK** | PARK (+1.35%) |
| final (diagnostic) | [up, rb, es] | **0.9220** | — | — | — | — |

- Cycle A 7-seed: 0.8710 → 0.9085 (+4.31%) — per-domain PROMOTE; constitution PARK.
- Cycle B 7-seed: 0.9085 → 0.9136 (+0.56%) — per-domain PARK; constitution PARK.
- Robustness never regressed (A: +0.0762, B: +0.0190); no domain primary dropped in
  either cycle (worst rel delta in both cycles = 0.00%).

**Seed stability of the promoting domain (21 seeds):**
- Cycle A (repoops): mean +0.0714, sd 0.0729 (≈ mean), min +0.0000, max +0.2500,
  positive 11/21, negative **0/21**. Never harmful; magnitude varies a lot.
- Cycle B (maze): mean +0.0308, sd 0.1146 (**sd ≈ 3.7 × mean**), min −0.1187,
  max +0.5101, positive 11/21, negative 5/21. Not seed-stable.

## 1. Prediction verdict: **PARTIAL**

The counterfactual (`logs/counterfactual.md`) made two claims: (a) under the
per-domain gate `residual_bias` AND `evidence_substrate` both promote; (b)
promoted in sequence they produce the loop's first genuine compounding event.

- **Claim (a), first half — CONFIRMED with a real run.** `residual_bias` PROMOTED
  under the per-domain gate (RepoOps +7.79% relative), the loop's first promotion
  since phase 1 and the first verdict difference from the constitutional gate
  (which said PARK at +2.83% aggregate). The counterfactual's arithmetic was
  exactly right for this candidate.
- **Claim (a), second half — REFUTED in the chained form.** Measured against the
  GROWN incumbent [up, rb], `evidence_substrate` PARKED: RepoOps contributes
  +0.00% (residual_bias already owns that ceiling) and Maze reaches only +3.75%
  relative — below the +5% single-domain bar. Note the nuance: measured against
  the ORIGINAL incumbent, evidence_substrate WOULD also promote (RepoOps +7.79%),
  and I reproduced that offline. The two candidates would not BOTH promote in
  sequence because their RepoOps effect is the *same effect*.
- **Claim (b) — REFUTED.** No second promotion occurred, so no compounding event.

**Net:** the per-domain gate produced one promotion (rule-design matters — the
aggregate gate was hiding a real within-domain gain), but the predicted two-step
chain and compounding never happened.

## 2. Compounding vs additive — NOT compounding; gains are redundant

Because both did not promote, I ran the final-hive measurement as an explicit
diagnostic (logged as DIAGNOSTIC in `logs/decisions.log`):

| configuration | 21-seed primary |
|---|---|
| [up] (baseline) | 0.8847 |
| [up, residual_bias] | 0.9097 |
| [up, evidence_substrate] (single shot) | 0.9220 |
| **[up, residual_bias, evidence_substrate] (final hive)** | **0.9220** |
| additive projection (0.8847 + 0.0250 + 0.0123) | 0.9220 |

The final hive equals `evidence_substrate` alone (0.9220) and equals the additive
projection exactly. `residual_bias` contributes +0.0000 on top of
`evidence_substrate`: the two mechanisms are near-duplicates on RepoOps (both are
after_write residual correctors). **Real final aggregate = 0.9220; total gain
from baseline = +0.0373 (+4.2%)** — identical to the single-shot phase-3 result.
Even in the hypothetical where both promoted, the chain would have been purely
additive at best and redundant in fact. There is no multiplicative/compounding
gain, and the counterfactual's implied compounding is illusory: its per-candidate
arithmetic (each vs the original incumbent) never modeled the overlap between
candidates.

## 3. What this says about the counterfactual's central claim (rule-design, not mechanism-design)

**Supported in the weak form, refuted in the strong form.**

- Weak form (CONFIRMED): the single aggregate +5% gate was over-locking. The
  per-domain gate promoted a mechanism (residual_bias, +2.83% aggregate) that the
  constitutional gate refused. That is direct evidence that the phase-2/3 stall
  was at least partly a rule-design problem.
- Strong form (REFUTED): "0/4 under the current rule, 2/4 under the per-domain
  gate" implied both would promote and compound. The real chained run shows the
  binding constraint in the sequential setting is **candidate overlap /
  redundancy**, not the gate. The counterfactual was a per-candidate-against-
  original-incumbent analysis; it never measured the interaction between
  candidates. That interaction (evidence_substrate ⊇ residual_bias on RepoOps) is
  what kills the second promotion. So the answer is: rule-design matters, but it
  is not the *binding* constraint on compounding — headroom structure and
  mechanism redundancy are.

## 4. Honest caveats: is the gate gameable? does it create robustness risk?

**Gameable — yes, and phase 4 demonstrates it.** The per-domain gate rewards
single-domain cherry-picking with no requirement to lift the aggregate. `residual_bias`
promoted on RepoOps +7.79% relative while moving the aggregate only +2.83% — below
the constitutional +5% bar it was designed to enforce. A mechanism engineered to
spike one easy domain (e.g., the mean of a noisy domain) clears +5% relative
regardless of aggregate or other domains, as long as no other domain primary drops
>3%. The gate also has no robustness condition at all: the constitutional gate
required robustness drop <= 10 pts; the per-domain gate would promote a mechanism
that traded another domain's robustness for one domain's primary (it constrains
domain primaries only, not robustness).

**Robustness risk — yes.** This run's promotions were benign (robustness
improved both cycles, no domain dropped), so the risk did not materialize, but the
gate provides zero protection if it does. The aggregate gate's
"no robustness regression" clause was the guard the per-domain gate removes.

**Seed stability — mixed.** residual_bias's RepoOps delta never went negative
(0/21), which is why the governor accepts it despite sd ≈ mean; evidence_substrate's
Maze delta has sd 3.7× its mean and 5/21 negative seeds — the governor would not
have promoted it on stability grounds even if it had cleared +5% by luck.

## 5. Cumulative 4-phase answer + the single most valuable next experiment

**Goertzel's virtuous cycle, four phases:**
- Phase 1: 0.7768 → 0.8710 (+12.1%) — one genuine promotion. A cycle exists.
- Phase 2: 0/2 promotions. The loop stalls at chaining.
- Phase 3: 0/2 promotions; hypothesis tests + offline counterfactual point to
  rule design. Loop still cannot chain.
- Phase 4: 1/2 promotion under a more permissive experimental gate — proof the
  loop *can* promote again — but the second candidate's gain is fully redundant,
  so the cycle does NOT compound.

**Four-phase answer: the loop can genuinely self-improve one step at a time, but
it does not accelerate.** Gains are bounded by finite per-domain headroom and by
redundancy between candidate mechanisms; no phase produced a second-order
improvement. Goertzel's hypothesis (self-improvement compounding into a virtuous
cycle) is not supported by four phases of evidence: every measurable improvement
is first-order only.

**Single most valuable next experiment:** a non-redundancy / headroom decomposition.
Now that RepoOps is saturated (0.9881) and residual_bias is the incumbent, measure a
NEW mechanism designed explicitly against the post-residual_bias state targeting the
UNCLAIMED headroom — Maze (0.8229, weight 0.40, ~8% relative of real headroom) and
SelfLab (0.9386, unreachable without re-promoting attention_budget) — under the
per-domain gate, and test whether an ordered chain of NON-overlapping mechanisms
can push the final hive above the 0.9220 single-shot ceiling. That single run
distinguishes the two remaining hypotheses: "compounding requires non-overlapping
candidates" (this report) vs "the gate/headroom still binds." Concretely:
`promote residual_bias` (done), then measure a maze-only new mechanism against
[up, rb]; if it clears +5% on maze AND the three-mechanism hive beats 0.9220,
compounding is real for non-redundant sequences.

## Final hive state (committed)
`checkpoints/p4_state.json`: active `["uncertainty_planning", "residual_bias"]`,
promoted `["residual_bias"]`, parked `["evidence_substrate"]`. Aggregate primary
**0.9097** (from baseline 0.8847, +2.83%). Constituency `hive_state.json` unchanged
(phase-4 is an experimental protocol, not a constitutional adoption).
