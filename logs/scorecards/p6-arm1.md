# Scorecard: p6-arm1 (phase 6 - second loop)

- condition: **active**
- probe: `frontier_memory_v3` (SAME class in all arms)
- probe config: `{"success_gated": true, "min_confirmations": 2, "beta": 0.03, "penalty": 1.0, "reward": -0.8, "approach": 4, "decay": 0.5}`
- memo: `{"target_domain": "maze", "hook_class_constraint": ["propose (machinery) \u2014 the only hook-class not claimed by any known task mechanism"], "least_covered_task_classes": ["before_eval", "retrieve"], "parameterization": {"success_gated": true, "min_confirmations": 2, "beta": 0.03, "penalty": 1.0, "reward": -0.8, "approach": 4, "decay": 0.5, "rationale": "history shows noise-dominated frontier credit; use the phase-3 success-gated >=2-confirmations calibration that worked"}, "failure_signatures": [{"signature": "frontier_memory failed in maze/choose_action (agg delta +0.0056, sd 0.143): single-episode penalization made credit noise-dominated (per-seed maze sd 0.143 vs mean +0.014; worst single-seed -0.53)", "mechanism": "frontier_memory", "aggregate_delta": 0.0056}, {"signature": "frontier_memory_v2 failed in maze/choose_action (agg delta +0.0123, sd 0.1146): calibrated success-gated >=2-confirmation credit recovered a small real gain; 5/21 seeds still negative", "mechanism": "frontier_memory_v2", "aggregate_delta": 0.0123}]}`
- incumbent: ['uncertainty_planning', 'residual_bias', 'progress_thermostat'] (21-seed primary 0.9480)
- target domain: maze (remaining headroom 0.0812)
- seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

## 21-seed probe measurement

| metric | value |
|---|---|
| aggregate-primary delta | -0.0260 |
| proposal quality Q (delta / headroom) | -0.320221 |
| per-seed delta mean | -0.0260 |
| per-seed delta sd | 0.0271 |
| negative seeds | 16/21 |
| maze per-seed delta mean | -0.0650 |
| maze per-seed delta sd | 0.0677 |
| per-seed deltas | [0.0004, -0.0722, 0.0051, -0.0745, 0.026, 0.0044, -0.0347, 0.0082, -0.0177, -0.0329, -0.0633, -0.0456, -0.0424, -0.0114, -0.0152, -0.0129, -0.0228, -0.0567, -0.0424, -0.038, -0.0076] |

