# Scorecard: p6-arm2 (phase 6 - second loop)

- condition: **randomized**
- probe: `frontier_memory_v3` (SAME class in all arms)
- probe config: `{"success_gated": false, "min_confirmations": 1, "beta": 0.1, "penalty": 1.0, "reward": -0.8, "approach": 4, "decay": 0.5}`
- memo: `{"target_domain": "maze", "hook_class_constraint": ["propose (machinery) \u2014 the only hook-class not claimed by any known task mechanism"], "least_covered_task_classes": ["before_eval", "retrieve"], "parameterization": {"success_gated": false, "min_confirmations": 1, "beta": 0.1, "penalty": 1.0, "reward": -0.8, "approach": 4, "decay": 0.5, "rationale": "history carries no noise signal for the probe class; naive single-episode config (the phase-2 frontier_memory design)"}, "failure_signatures": [{"signature": "frontier_memory failed in selflab/retrieve (agg delta +0.0056, sd 0.143): single-episode penalization made credit noise-dominated (per-seed maze sd 0.143 vs mean +0.014; worst single-seed -0.53)", "mechanism": "frontier_memory", "aggregate_delta": 0.0056}, {"signature": "frontier_memory_v2 failed in selflab/retrieve (agg delta +0.0123, sd 0.1146): calibrated success-gated >=2-confirmation credit recovered a small real gain; 5/21 seeds still negative", "mechanism": "frontier_memory_v2", "aggregate_delta": 0.0123}]}`
- incumbent: ['uncertainty_planning', 'residual_bias', 'progress_thermostat'] (21-seed primary 0.9480)
- target domain: maze (remaining headroom 0.0812)
- seeds (21): [101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1102, 1203, 1304, 1405, 1506, 1607, 1708, 1809, 1910, 2011, 2112]

## 21-seed probe measurement

| metric | value |
|---|---|
| aggregate-primary delta | -0.0327 |
| proposal quality Q (delta / headroom) | -0.402803 |
| per-seed delta mean | -0.0327 |
| per-seed delta sd | 0.0679 |
| negative seeds | 15/21 |
| maze per-seed delta mean | -0.0818 |
| maze per-seed delta sd | 0.1697 |
| per-seed deltas | [0.0019, -0.0722, 0.0051, -0.0812, 0.0684, 0.0044, -0.0347, 0.0082, -0.0195, -0.0405, -0.0101, -0.0114, -0.0386, -0.0114, -0.0152, -0.0135, 0.012, -0.2809, -0.1329, -0.0165, -0.0083] |

