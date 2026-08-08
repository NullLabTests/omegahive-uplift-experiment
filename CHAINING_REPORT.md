# CHAINING REPORT (Phase 2) — Does the uplift loop COMPOUND?

## Executive summary

Phase 1 could not test compounding: every candidate was measured against the
EMPTY baseline (`active=[]`), so no cycle ever built on the previous one. Phase 2
fixed that. The Architect (LLM oracle) designed **two genuinely new cognitive
mechanisms from scratch** — `residual_bias` (RepoOps: a predictive-residual
evidence filter) and `frontier_memory` (Maze: cross-episode exploration credit
transfer) — and the chaining protocol measured each **against the current
incumbent hive state** `["uncertainty_planning"]`, on 21 seeds with the 7
constitutional seeds re-run for apples-to-apples comparability.

**Result: no second-order promotion.** Both candidates were PARKED.

| candidate | domain | 21-seed rel | 7-seed rel | per-env delta (21 seeds) | verdict |
|---|---|---|---|---|---|
| `residual_bias` | RepoOps | **+2.8%** | +4.3% | repoops +0.0714; maze 0; selflab 0 | **PARK** |
| `frontier_memory` | Maze | **+0.6%** | +1.2% | maze +0.0141; repoops 0; selflab 0 | **PARK** |

The additional gains are real but sub-threshold. `residual_bias` was parked for
a **structural** reason (it essentially maxed the RepoOps ceiling); `frontier_memory`
was parked for a **noise** reason (its per-seed variance dwarfs its mean). The
compounding virtuous cycle did **not** reproduce at the +5% gate.

## 1. Did the chained loop produce measurable ADDITIONAL improvement beyond 0.8710?

Yes for the raw deltas, no at the promotion gate.

- `residual_bias`: incumbent 0.8710 → **0.9085** (7 seeds, **+4.3%**); 0.8847 → **0.9097** (21 seeds, **+2.8%**). RepoOps primary 0.9167 → **0.9881** (max 1.0).
- `frontier_memory`: incumbent 0.8710 → **0.8814** (7 seeds, **+1.2%**); 0.8847 → **0.8903** (21 seeds, **+0.6%**). Maze primary 0.8229 → **0.8370**.

But because both were parked, the hive state is **unchanged**
(`active=["uncertainty_planning"]`). So there was **no compounded result** — the
gain is *additive and independent* (each mechanism targets a disjoint domain),
not multiplicative or chained. Compounding would have required a PROMOTE on
mechA followed by mechB measured against `[uncertainty_planning, residual_bias]` —
that branch never executed.

## 2. Did the genuinely LLM-designed mechanisms outperform, match, or underperform the precomputed phase-1 mechanisms?

**Match-to-slightly-under, with one important caveat about baseline.**

- `residual_bias` (+2.8% aggregate, +4.3% on the 7 constitutional seeds) is in the
  same band as the precomputed phase-1 *parked* mechanisms (`memory_consolidation`
  +4.0%, `attention_budget` +2.8%) — but those were measured against the **empty**
  baseline, a weaker test. Against a *higher* incumbent (0.8710), `residual_bias`
  delivered a comparable relative gain, and it is strictly non-negative
  (per-seed min = 0.0000 on all 21 seeds). This is a genuinely capable design.
- `frontier_memory` (+0.6%) underperformed the phase-1 *promoted* mechanism
  (`uncertainty_planning` +12.1%) by a wide margin. Its credit-assignment is too
  aggressive on unlucky early episodes and its net effect is noise-level.

**What this says about open-ended Architect idea generation:** two novel mechanisms,
designed purely from the env/hook source code, both produced *domain-targeted,
measurable, perfectly-isolated* effects (transfer probes exactly 0.0000 in the
off-design domains). The Architect's structural reasoning is sound and faithful to
the hook contracts. But **idea generation does not guarantee gate-crossing gain**:
the one domain with real headroom (Maze) required a mechanism whose noise
characteristics were not controlled well enough. Design novelty ≠ measured
improvement; the gate exists precisely to separate them.

## 3. Did the +5% gate hold under 21 seeds vs 7 seeds (stability)?

**The verdicts were stable; the magnitudes were not fully stable.**

- `residual_bias`: +4.3% (7 seeds) vs +2.8% (21 seeds) — PARK in both.
- `frontier_memory`: +1.2% (7 seeds) vs +0.6% (21 seeds) — PARK in both.

The decision boundary is robust to seed set in both cases. But the 1.3–1.5 pt
magnitude shifts confirm the phase-1 concern: 7 seeds under-power the delta
estimate. Notably, even the *higher* 7-seed estimate for `residual_bias` (+4.3%)
does not cross +5%, so the park call is not a seed-luck artifact.

## 4. Does this evidence strengthen or weaken the compounding virtuous-cycle claim?

**Weaken the strong form; strengthen the weak form.**

- **Weakens (strong form):** a second-order, chained improvement did not
  materialize. The phase-1 +12.1% was a "fix the near-random maze policy" win from
  the empty baseline. With a strong maze planner already active, the aggregate
  weighting makes the +5% gate **structurally near-unreachable** for single-domain
  mechanisms: given incumbent levels, the maximum attainable aggregate gain is
  **+8.0% via Maze, +3.3% via RepoOps, +1.7% via SelfLab**. `residual_bias` captured
  ~86% of the RepoOps ceiling and still parked. A +5% second-order gate may be
  unsatisfiable by design until the incumbent itself is much weaker or a mechanism
  spans multiple domains.
- **Strengthens (weak form):** the chained loop is demonstrably **non-destructive**
  (`residual_bias` was never negative on any of 21 seeds), it correctly parked a
  noisy mechanism (`frontier_memory`: sd 0.057 >> mean 0.006), and composition of
  mechanisms produced zero cross-domain bleed. Governance filtered two novel ideas
  on measured evidence, exactly as the constitution requires.

## 5. Where did it stall, and what is needed for a stronger result?

**Stall points:**
1. **Structural ceiling in the weighting.** Only Maze retains enough headroom to
   clear +5% aggregate; a RepoOps-perfect mechanism can at best add +3.3%.
2. **`frontier_memory` noise.** Per-seed Maze delta sd=0.143 vs mean=+0.014; on
   unlucky seeds a wrongly-penalized productive cell persists through the decay
   horizon and costs up to −0.53 primary on a single seed.
3. **Gate granularity.** The single-number aggregate systematically favors "one big
   win" (a phase-1 finding this phase confirms numerically).

**Needed for a stronger result:**
- **Calibrated Maze transfer:** penalize a target only when its episode both *failed*
  *and* never approached the goal (success-gated credit), require ≥2 confirmations
  before penalizing, and shrink BETA.
- **Multi-domain mechanisms** that move RepoOps AND SelfLab together (each is capped
  alone; together they clear the gate).
- **Per-domain promotion gates or rebalanced weights** so a mechanism that maxes its
  own domain (RepoOps 0.9167 → 0.9881!) can be promoted without dragging the whole
  aggregate.
- **Longer horizon with accumulation:** allow the incumbent to hold 2–3 promoted
  mechanisms before the next measurement, then test whether the *product* of gains
  compounds even when each individual delta is sub-threshold.

## One-command re-runs
```bash
python3 -m loop.chaining                # full protocol: baseline + cycle-1 (A) + cycle-2 (B)
python3 -m loop.chaining --candidate A  # single candidate (B uses updated incumbent if A promoted)
```

## Bottom line
The second-order loop ran honestly and produced small, real, non-negative additive
gains — but **no compounding**: both genuinely-LLM-designed candidates parked, for
structural (RepoOps ceiling) and noise (`frontier_memory` variance) reasons. The
evidence therefore **weakens** the strong Goertzel claim (compounding did not
reproduce at the gate) while **strengthening** the governance story (measured,
non-destructive filtering of novel ideas). Sustained compounding remains unproven and
now demonstrably faces a weighting-design ceiling, not just a seed-variance one.
