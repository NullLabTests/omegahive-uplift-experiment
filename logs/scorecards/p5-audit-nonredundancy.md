# Scorecard: p5-audit-nonredundancy (phase 5 - non-redundancy audit)

- mechanism: `progress_thermostat`  (maze-only within-episode explore/exploit thermostat)
- incumbent: ['uncertainty_planning', 'residual_bias'] (post-phase-4 grown state)
- question: does `progress_thermostat`'s maze gain survive WITH and WITHOUT `residual_bias`? If yes it is orthogonal to the incumbent; repoops/selflab deltas must be ~0 or the audit is confounded.

| configuration | aggregate | maze | repoops | selflab |
|---|---|---|---|---|
| A: [up] | 0.8847 | 0.8229 | 0.9167 | 0.9386 |
| B: [up, rb] (incumbent) | 0.9097 | 0.8229 | 0.9881 | 0.9386 |
| C: [up, mech] | 0.9230 | 0.9188 | 0.9167 | 0.9386 |
| D: [up, rb, mech] | 0.9480 | 0.9188 | 0.9881 | 0.9386 |

Marginal contributions (maze primary):
- mech WITHOUT rb (C - A): +0.0959 (rel +11.65%)
- mech WITH rb (D - B): +0.0959 (rel +11.65%)
- repoops delta of mech (D - B): +0.0000 (must be ~0: residual_bias territory)
- selflab delta of mech (D - B): +0.0000

**FINAL HIVE [up, rb, progress_thermostat] 21-seed primary: 0.9480**
- phase-4 single-shot ceiling: 0.9220
- beats ceiling by: +0.0260
- compounding analysis: {
  "final_hive": [
    "uncertainty_planning",
    "residual_bias",
    "progress_thermostat"
  ],
  "final_hive_primary_21": 0.948,
  "phase4_ceiling": 0.922,
  "beats_ceiling": 0.026,
  "incumbent_primary": 0.9097,
  "cycle_gain": 0.0383,
  "additive_projection": 0.948,
  "compounding_excess": 0.0
}

