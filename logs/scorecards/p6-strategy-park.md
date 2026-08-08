# Scorecard: p6-strategy-park (phase 6 - strategy gate)

- strategy: `success_signature_policy` (in-band `propose`-hook mechanism)
- gate: **strategy gate** (EXPERIMENTAL, NOT constitutional): PROMOTE iff Q1 >= 1.05*Q0 AND Q1 >= 1.05*Q2 AND neg1 <= neg0 AND matched Q1 > Q2 (strict majority); else PARK iff Q1 >= 0.95*Q0, else REJECT.

## Three-arm probe measurement (21 seeds)

| arm | condition | agg delta | Q | neg seeds |
|---|---|---|---|---|
| 0 | baseline (empty memo) | -0.0327 | -0.402803 | 15/21 |
| 1 | S active (real history) | -0.0260 | -0.320221 | 16/21 |
| 2 | randomized (permuted history) | -0.0327 | -0.402803 | 15/21 |

## Conditions

- Q1 >= 1.05*Q0 : **True** (-0.320221 vs 1.05*-0.402803)
- Q1 >= 1.05*Q2 : **True** (-0.320221 vs 1.05*-0.402803)
- no task-axis regression : **False** (arm1 neg 16 <= arm0 neg 15)
- memo attribution (matched per-seed Q1>Q2) : **False** (wins 7, losses 7, ties 7)

**VERDICT: PARK**

