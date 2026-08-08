# Scorecard: chained-cycle-1-residual_bias

- mechanism: `residual_bias`
- incumbent: ['uncertainty_planning']
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed chained verdict (binding)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.8847 | 0.9097 | +0.0250 |
| aggregate_robustness | 0.4286 | 0.5048 | +0.0762 |

**VERDICT (21 seeds): PARK**  (rel primary +2.8%)

| env | before primary | after primary | delta |
|---|---|---|---|
| maze | 0.8229 | 0.8229 | +0.0000 |
| repoops | 0.9167 | 0.9881 | +0.0714 |
| selflab | 0.9386 | 0.9386 | +0.0000 |

## 7-seed constitutional re-run (apples-to-apples vs phase 1)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.871 | 0.9085 | +0.0375 |
| aggregate_robustness | 0.2857 | 0.3143 | +0.0286 |

**VERDICT (7 seeds): PARK**  (rel primary +4.3%)

## Transfer probe (domain not designed for)

- mechA in Maze (not designed for): 0.0
- mechB in RepoOps (not designed for): 0.0714
- mechB in SelfLab (not designed for): 0.0

