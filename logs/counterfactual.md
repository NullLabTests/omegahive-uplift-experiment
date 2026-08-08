# OFFLINE COUNTERFACTUAL ANALYSIS — is the stall a mechanism problem or a rule-design problem?

Pure offline computation on the ALREADY-MEASURED phase-2 and phase-3 scorecards (logs/scorecards/*.json). No evaluations were re-run; the constitution and the actual verdicts are unchanged. Aggregate weights are constitutional 0.40 maze / 0.35 repoops / 0.25 selflab.

| candidate | phase | actual verdict | actual rel (21s) |
|---|---|---|---|
| `residual_bias` | chained | PARK | +2.8% |
| `frontier_memory` | chained | PARK | +0.6% |
| `frontier_memory_v2` | phase3 | PARK | +1.4% |
| `evidence_substrate` | phase3 | PARK | +4.2% |

## 1. Per-domain promotion gate (PROMOTE iff ANY domain >= +5% rel AND no domain drops > -3%)

| candidate | maze rel | repoops rel | selflab rel | would-be verdict |
|---|---|---|---|---|
| `residual_bias` | +0.0% | +7.8% | +0.0% | **PROMOTE** |
| `frontier_memory` | +1.7% | +0.0% | +0.0% | **PARK** |
| `frontier_memory_v2` | +3.7% | +0.0% | +0.0% | **PARK** |
| `evidence_substrate` | +3.7% | +7.8% | +0.0% | **PROMOTE** |

## 2. Rebalanced weights (same +5% relative gate on the aggregate)

| candidate | rel @ current w | rel @ equal 1/3 | rel @ headroom-proportional | verdict @ equal | verdict @ headroom |
|---|---|---|---|---|---|
| `residual_bias` | +2.8% | +2.7% | (0.55/0.26/0.19) +2.1% | PARK | PARK |
| `frontier_memory` | +0.6% | +0.5% | (0.55/0.26/0.19) +0.9% | PARK | PARK |
| `frontier_memory_v2` | +1.4% | +1.2% | (0.55/0.26/0.19) +1.9% | PARK | PARK |
| `evidence_substrate` | +4.2% | +3.9% | (0.55/0.26/0.19) +4.0% | PARK | PARK |

## 3. Minimal aggregate-weight reallocation to clear +5% (measured deltas only)

| candidate | best per-domain delta | max possible agg rel under any weights | clears +5% possible? | minimal L1 move | minimal weights (m/r/s) |
|---|---|---|---|---|---|
| `residual_bias` | +0.0714 | +8.1% | YES | 0.54 | {'maze': 0.1325, 'repoops': 0.62, 'selflab': 0.2475} |
| `frontier_memory` | +0.0141 | +1.6% | NO (impossible) | — | — |
| `frontier_memory_v2` | +0.0309 | +3.5% | NO (impossible) | — | — |
| `evidence_substrate` | +0.0714 | +8.1% | YES | 0.195 | {'maze': 0.4, 'repoops': 0.4475, 'selflab': 0.1525} |

## Bottom line

Under the CURRENT constitutional rule, 0/4 candidates promote. Under the per-domain gate, 2/4 promote (residual_bias, evidence_substrate) — exactly the two candidates that maxed their own domain (RepoOps +7.8% relative within-domain). Rebalanced weights (equal or headroom-proportional) promote 0/4. Only the two repoops-capable candidates could clear +5% under ANY weight configuration, and only by pushing the repoops weight to ~0.62+. The stalls are therefore a RULE-DESIGN problem (the single aggregate gate hides large within-domain gains), not a mechanism problem.

