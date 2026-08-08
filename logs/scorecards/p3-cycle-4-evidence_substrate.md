# Scorecard: p3-cycle-4-evidence_substrate (phase 3)

- mechanism: `evidence_substrate`
- incumbent: ['uncertainty_planning']
- target domain: maze
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed chained verdict (binding)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.8847 | 0.922 | +0.0373 |
| aggregate_robustness | 0.4286 | 0.5238 | +0.0952 |

**VERDICT (21 seeds): PARK**  (rel primary +4.2%)

| env | before primary | after primary | delta |
|---|---|---|---|
| maze | 0.8229 | 0.8538 | +0.0309 |
| repoops | 0.9167 | 0.9881 | +0.0714 |
| selflab | 0.9386 | 0.9386 | +0.0000 |

## Target-domain per-seed variance (21 seeds)

- maze primary delta: mean=+0.0308 sd=0.1146 min=-0.1187 max=+0.5101
- positive on 11/21, negative on 5/21

## 7-seed constitutional re-run

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.871 | 0.9136 | +0.0426 |
| aggregate_robustness | 0.2857 | 0.3714 | +0.0857 |

**VERDICT (7 seeds): PARK**  (rel primary +4.9%)

## Transfer probe

- mechD_in_selflab: +0.0000
- mechD_in_maze: +0.0309
- mechD_in_repoops: +0.0714

