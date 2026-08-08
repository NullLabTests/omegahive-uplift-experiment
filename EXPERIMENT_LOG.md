# OmegaHive Experiment Log

Experiment Runner on `opencode/deepseek-v4-flash-free` (free tier). This log narrates the full
governed self-uplifting loop test of Ben Goertzel's incremental self-modification hypothesis.

## Timeline

### 1. Foundation
- Repo initialized at `/home/codespace/omegahive-experiment`.
- Structure: `hive/` (AtomSpace-lite, agents, bus), `mechanisms/` (candidate cognition),
  `eval_ecology/` (3 envs + aggregate runner), `loop/` (driver, architect),
  `logs/`, `checkpoints/`.
- `CONSTITUTION.md` forbids uncontrolled self-modification of the core loop
  (driver.py is inviolable; all change flows through the Governor).
- Commit `acf7d5d`, `38269d3`, `83ccfed`.

### 2. Hive (minimal viable)
- **AtomSpace-lite** (`hive/atomspace.py`): JSON-backed nodes and links with
  `(type, a, b)` keys, confidence, value, ttl; salience = confidence * ttl; add/get/query.
- **4 agents** (`hive/agents.py`): Architect (proposes ONE mechanism per cycle),
  Implementer (import-checks mechanism code), Evaluator (runs full ecology before/after),
  Governor (threshold-based verdict).
- **Bus** (`hive/bus.py`): in-memory message queue per cycle, logged to `logs/bus/cycle-N.jsonl`.

### 3. Evaluation ecology (3 environments, 7 seeds each)
- **Maze-lite** (partial observability): agent expands a frontier of walls it can knock down;
  success + efficiency; blended primary `0.5*success + 0.5*efficiency`.
- **RepoOps-lite**: 8 bug reports, one-good/dual-good hidden patch types with noisy
  evidence links; agent recalls patches from memory and applies them.
- **SelfLab**: hive estimates its own candidate quality from noisy warm-up + clean samples;
  picks best candidate; success = chosen quality / max quality.
- Aggregator (`eval_ecology/runner.py`): weighted primary `0.40 maze + 0.35 repoops +
  0.25 selflab`; robustness = fraction of seeds where all envs succeed.

### 4. Governed uplift loop (`loop/driver.py`)
- Hard limits enforced: 30 min wall-clock, 1 GB `RLIMIT_AS`, 2000 code lines.
- Git checkpoint after baseline and after each cycle verdict.

### 5. Baseline (cycle 0)
```
aggregate_primary     = 0.7768
aggregate_robustness  = 0.2857
maze success          = 0.6929
repoops success       = 0.8750
selflab success       = 0.9386
```

### 6. Cycle 1 — `memory_consolidation`
Architect rationale: shared memory is single-shot; duplicates pile up, stale atoms unpruned;
consolidation (merge duplicates, reinforce confirmed atoms, average on recall) should make
memory a more trustworthy substrate for RepoOps cross-bug patch recall.
Result:
```
before 0.7768 -> after 0.8081  (+4.0% rel, robustness +0.0572)
repoops success 0.8750 -> 0.9643  (+0.0893)   <-- the intended effect, confirmed
maze 0.6929 -> 0.6929 (flat); selflab 0.9386 -> 0.9386 (flat)
VERDICT: PARK  (real, but sub-threshold: +4.0% < +5%)
```
Governance note: a genuinely useful mechanism in RepoOps, yet the aggregate ecology only
registered +4.0%; the loop correctly refused to promote a sub-threshold gain.

### 7. Cycle 2 — `attention_budget`
Architect rationale: SelfLab estimates are polluted by noisy warm-up samples; RepoOps and
Maze process every candidate equally. A hard capacity limit focused on the most salient
items (value x recency) should sharpen estimates.
Result:
```
before 0.7768 -> after 0.7983  (+2.8% rel, robustness +0.0572)
selflab success 0.9386 -> 0.9996  (+0.0610)   <-- intended effect, strong in SelfLab
repoops 0.8750 -> 0.8929  (+0.0179); maze flat
VERDICT: PARK  (+2.8% < +5%)
```
Interesting: attention_budget fixed SelfLab almost completely, but SelfLab's weight (0.25)
is too small to cross the aggregate promote threshold. Honest sub-threshold outcome.

### 8. Cycle 3 — `uncertainty_planning`
Architect rationale: the Maze agent explores blind with random frontier targets, wasting
step budget; targeting frontier cells with best expected information gain per step, biased
toward the goal, should cut steps and lift success.
Result:
```
before 0.7768 -> after 0.8710  (+12.1% rel, robustness flat +0.0000)
maze success 0.6929 -> 0.7571  (+0.0642)   <-- intended effect
repoops 0.8750 -> 0.8750 (flat); selflab flat
VERDICT: PROMOTE  (+12.1% >= +5%, no robustness regression)
```
Final hive state: `active = [uncertainty_planning]`.

### 9. Final state
```
active    = [uncertainty_planning]
promoted  = [uncertainty_planning]
parked    = [memory_consolidation, attention_budget]
rejected  = []
aggregate_primary: 0.7768 -> 0.8710  (+12.1% relative, +0.0942 absolute)
```

## Where the loop broke or stalled
- **Single-domain mechanisms stall at the aggregate gate.** memory_consolidation and
  attention_budget each produced the effect they were designed for (RepoOps +8.9%,
  SelfLab +6.1%) yet both fell below the aggregate +5% promote threshold because their
  domain weights are only 0.35 / 0.25. The loop did its filtering job correctly, but this
  exposes that a coarse single-number aggregate favors one big win over several moderate ones.
- **Only 1 of 3 mechanisms promoted.** In a 3-env ecology with a weighted primary, only the
  mechanism hitting the largest-weight domain (Maze, 0.40) crossed the threshold.
- **No transfer test** was built (mission made it optional); cross-domain knowledge transfer
  is untested here.
