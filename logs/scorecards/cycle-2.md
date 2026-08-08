# Scorecard: cycle-2

- cycle: 2
- mechanism: attention_budget
- seeds: [101, 202, 303, 404, 505, 606, 707]

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.7768 | 0.7983 | 0.0215 |
| aggregate_robustness | 0.2857 | 0.3429 | 0.0572 |
| env `maze` success_rate | 0.6929 | 0.6929 | 0.0 |
| env `repoops` success_rate | 0.875 | 0.8929 | 0.0179 |
| env `selflab` success_rate | 0.9386 | 0.9996 | 0.061 |

**VERDICT: PARK**
- relative primary delta: +2.8%
- robustness delta: +0.0572
- rule: {'promote_threshold': '+5% rel primary and robustness drop <= 10 pts', 'park_threshold': '>= -5% rel primary'}
