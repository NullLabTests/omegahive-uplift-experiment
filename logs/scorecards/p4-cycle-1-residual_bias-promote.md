# Scorecard: p4-cycle-1-residual_bias-promote (phase 4 — experimental per-domain gate)

- mechanism: `residual_bias`
- incumbent: ['uncertainty_planning']
- gate: **per-domain promotion gate** (EXPERIMENTAL, NOT constitutional): PROMOTE iff ANY domain primary >= +5% rel AND no domain drop > -3% rel; else PARK iff aggregate rel >= -5%, else REJECT.
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed per-domain verdict (binding for this experiment)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.8847 | 0.9097 | +0.0250 |
| aggregate_robustness | 0.4286 | 0.5048 | +0.0762 |

**VERDICT (per-domain gate, 21 seeds): PROMOTE**  (promoting domain repoops at +7.79% rel; worst domain maze at +0.00% rel)

| env | before primary | after primary | delta | rel delta |
|---|---|---|---|---|
| maze | 0.8229 | 0.8229 | +0.0000 | +0.0000% || repoops | 0.9167 | 0.9881 | +0.0714 | +7.7900% || selflab | 0.9386 | 0.9386 | +0.0000 | +0.0000% |

Constitutional gate reference (21 seeds, unchanged rule): PARK (aggregate rel +2.83%)

## Promoting-domain per-seed variance (21 seeds)

- repoops primary delta: mean=+0.0714 sd=0.0729 min=+0.0000 max=+0.2500
- positive on 11/21, negative on 0/21

## 7-seed constitutional re-run (reference)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.871 | 0.9085 | +0.0375 |
| aggregate_robustness | 0.2857 | 0.3143 | +0.0286 |

**VERDICT (7 seeds): PROMOTE**  (rel primary +4.3%)
- constitutional reference (7 seeds): PARK (aggregate rel +4.31%)

