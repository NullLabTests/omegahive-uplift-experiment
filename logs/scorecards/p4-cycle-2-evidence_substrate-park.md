# Scorecard: p4-cycle-2-evidence_substrate-park (phase 4 — experimental per-domain gate)

- mechanism: `evidence_substrate`
- incumbent: ['uncertainty_planning', 'residual_bias']
- gate: **per-domain promotion gate** (EXPERIMENTAL, NOT constitutional): PROMOTE iff ANY domain primary >= +5% rel AND no domain drop > -3% rel; else PARK iff aggregate rel >= -5%, else REJECT.
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed per-domain verdict (binding for this experiment)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.9097 | 0.922 | +0.0123 |
| aggregate_robustness | 0.5048 | 0.5238 | +0.0190 |

**VERDICT (per-domain gate, 21 seeds): PARK**  (promoting domain maze at +3.75% rel; worst domain repoops at +0.00% rel)

| env | before primary | after primary | delta | rel delta |
|---|---|---|---|---|
| maze | 0.8229 | 0.8538 | +0.0309 | +3.7500% || repoops | 0.9881 | 0.9881 | +0.0000 | +0.0000% || selflab | 0.9386 | 0.9386 | +0.0000 | +0.0000% |

Constitutional gate reference (21 seeds, unchanged rule): PARK (aggregate rel +1.35%)

## Promoting-domain per-seed variance (21 seeds)

- maze primary delta: mean=+0.0308 sd=0.1146 min=-0.1187 max=+0.5101
- positive on 11/21, negative on 5/21

## 7-seed constitutional re-run (reference)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.9085 | 0.9136 | +0.0051 |
| aggregate_robustness | 0.3143 | 0.3714 | +0.0571 |

**VERDICT (7 seeds): PARK**  (rel primary +0.6%)
- constitutional reference (7 seeds): PARK (aggregate rel +0.56%)

