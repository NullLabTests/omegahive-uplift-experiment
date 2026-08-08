# Scorecard: p3-cycle-3-frontier_memory_v2 (phase 3)

- mechanism: `frontier_memory_v2`
- incumbent: ['uncertainty_planning']
- target domain: maze
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed chained verdict (binding)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.8847 | 0.897 | +0.0123 |
| aggregate_robustness | 0.4286 | 0.4286 | +0.0000 |

**VERDICT (21 seeds): PARK**  (rel primary +1.4%)

| env | before primary | after primary | delta |
|---|---|---|---|
| maze | 0.8229 | 0.8538 | +0.0309 |
| repoops | 0.9167 | 0.9167 | +0.0000 |
| selflab | 0.9386 | 0.9386 | +0.0000 |

## Target-domain per-seed variance (21 seeds)

- maze primary delta: mean=+0.0308 sd=0.1146 min=-0.1187 max=+0.5101
- positive on 11/21, negative on 5/21

## 7-seed constitutional re-run

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.871 | 0.8761 | +0.0051 |
| aggregate_robustness | 0.2857 | 0.2857 | +0.0000 |

**VERDICT (7 seeds): PARK**  (rel primary +0.6%)

## Transfer probe

- mechC_in_repoops: +0.0000
- mechC_in_selflab: +0.0000

