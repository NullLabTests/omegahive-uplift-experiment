# Scorecard: cycle-3

- cycle: 3
- mechanism: uncertainty_planning
- seeds: [101, 202, 303, 404, 505, 606, 707]

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.7768 | 0.871 | 0.0942 |
| aggregate_robustness | 0.2857 | 0.2857 | 0.0 |
| env `maze` success_rate | 0.6929 | 0.7571 | 0.0642 |
| env `repoops` success_rate | 0.875 | 0.875 | 0.0 |
| env `selflab` success_rate | 0.9386 | 0.9386 | 0.0 |

**VERDICT: PROMOTE**
- relative primary delta: +12.1%
- robustness delta: +0.0000
- rule: {'promote_threshold': '+5% rel primary and robustness drop <= 10 pts', 'park_threshold': '>= -5% rel primary'}
