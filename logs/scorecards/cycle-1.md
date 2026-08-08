# Scorecard: cycle-1

- cycle: 1
- mechanism: memory_consolidation
- seeds: [101, 202, 303, 404, 505, 606, 707]

| metric | before | after | delta |
|---|---|---|---|
| aggregate_primary | 0.7768 | 0.8081 | 0.0313 |
| aggregate_robustness | 0.2857 | 0.3429 | 0.0572 |
| env `maze` success_rate | 0.6929 | 0.6929 | 0.0 |
| env `repoops` success_rate | 0.875 | 0.9643 | 0.0893 |
| env `selflab` success_rate | 0.9386 | 0.9386 | 0.0 |

**VERDICT: PARK**
- relative primary delta: +4.0%
- robustness delta: +0.0572
- rule: {'promote_threshold': '+5% rel primary and robustness drop <= 10 pts', 'park_threshold': '>= -5% rel primary'}
