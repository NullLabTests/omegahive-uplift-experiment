# Scorecard: chained-cycle-2-frontier_memory

- mechanism: `frontier_memory`
- incumbent: ['uncertainty_planning']
- ext seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]
- const seeds (7): [101, 202, 303, 404, 505, 606, 707]

## 21-seed chained verdict (binding)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.8847 | 0.8903 | +0.0056 |
| aggregate_robustness | 0.4286 | 0.4286 | +0.0000 |

**VERDICT (21 seeds): PARK**  (rel primary +0.6%)

| env | before primary | after primary | delta |
|---|---|---|---|
| maze | 0.8229 | 0.8370 | +0.0141 |
| repoops | 0.9167 | 0.9167 | +0.0000 |
| selflab | 0.9386 | 0.9386 | +0.0000 |

## 7-seed constitutional re-run (apples-to-apples vs phase 1)

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.871 | 0.8814 | +0.0104 |
| aggregate_robustness | 0.2857 | 0.2857 | +0.0000 |

**VERDICT (7 seeds): PARK**  (rel primary +1.2%)

## Transfer probe (domain not designed for)

- mechA in Maze (not designed for): 0.0141
- mechB in RepoOps (not designed for): 0.0
- mechB in SelfLab (not designed for): 0.0

