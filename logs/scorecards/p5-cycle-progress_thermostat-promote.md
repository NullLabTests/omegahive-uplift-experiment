# Scorecard: p5-cycle-progress_thermostat-promote (phase 5 - experimental per-domain gate)

- mechanism: `progress_thermostat`
- incumbent: ['uncertainty_planning', 'residual_bias']
- gate: **per-domain promotion gate** (EXPERIMENTAL, NOT constitutional): PROMOTE iff ANY domain primary >= +5% rel AND no domain drop > -3% rel; else PARK iff aggregate rel >= -5%, else REJECT.
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed per-domain verdict (binding for this experiment)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.9097 | 0.948 | +0.0383 |
| aggregate_robustness | 0.5048 | 0.6381 | +0.1333 |

**VERDICT (per-domain gate, 21 seeds): PROMOTE**  (promoting domain maze at +11.65% rel; worst domain repoops at +0.00% rel)

| env | before primary | after primary | delta | rel delta |
|---|---|---|---|---|
| maze | 0.8229 | 0.9188 | +0.0959 | +11.6500% || repoops | 0.9881 | 0.9881 | +0.0000 | +0.0000% || selflab | 0.9386 | 0.9386 | +0.0000 | +0.0000% |

Constitutional gate reference (21 seeds, unchanged rule): PARK (aggregate rel +4.21%)

## Promoting-domain per-seed variance (21 seeds)

- maze primary delta: mean=+0.0958 sd=0.1389 min=-0.1078 max=+0.6161
- positive on 17/21, negative on 3/21

## 7-seed constitutional re-run (reference)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.9085 | 0.9343 | +0.0258 |
| aggregate_robustness | 0.3143 | 0.6286 | +0.3143 |

**VERDICT (7 seeds): PROMOTE**  (rel primary +2.8%)
- constitutional reference (7 seeds): PARK (aggregate rel +2.84%)

