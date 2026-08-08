"""The four hive agents.

Design note (Constitution Article II): agents are thin, deterministic
processes. Their *judgments* that genuinely need reasoning (Architect proposal
rationale, Governor commentary) are produced by the LLM oracle and logged to
logs/decisions.log; their *mechanics* (choosing the next mechanism, computing
deltas, applying thresholds) are pure Python so the whole run is reproducible
with one command.
"""

from __future__ import annotations

import json
import os
from typing import Any

from hive.bus import Bus


class Agent:
    name = "unnamed"
    role = "unset"

    def __init__(self, bus: Bus) -> None:
        self.bus = bus


class Architect(Agent):
    """Decides WHICH single cognitive mechanism the hive will add next."""

    name = "arch"
    role = "architect"

    def __init__(self, bus: Bus, order: list[str]) -> None:
        super().__init__(bus)
        self.order = order

    def propose(self, cycle: int, active: list[str]) -> str:
        """Propose the cycle'th mechanism from the roster (cycle 1 -> index 0).

        The *reasoning* behind the roster order is authored by the LLM oracle
        in logs/decisions.log for each cycle.
        """
        idx = cycle - 1
        if idx >= len(self.order):
            raise RuntimeError("Architect: no more mechanisms in roster.")
        mech = self.order[idx]
        self.bus.post(self.name, "proposal", {"cycle": cycle, "mechanism": mech,
                                              "active": active})
        return mech


class Implementer(Agent):
    """Writes the mechanism code into mechanisms/."""

    name = "impl"
    role = "implementer"

    def __init__(self, bus: Bus, mechanism_dir: str) -> None:
        super().__init__(bus)
        self.mechanism_dir = mechanism_dir

    def load(self, mech_name: str) -> Any:
        """Load a mechanism module by name from mechanisms/."""
        import importlib
        mod = importlib.import_module(f"mechanisms.{mech_name}")
        self.bus.post(self.name, "implemented", {"mechanism": mech_name})
        return mod


class Evaluator(Agent):
    """Runs the ecology and returns structured score vectors."""

    name = "eval"
    role = "evaluator"

    def run_ecology(self, active: list[str], seed: int) -> dict:
        from eval_ecology.runner import run_ecology
        scores = run_ecology(active, seed)
        self.bus.post(self.name, "eval_result", {"active": active, "seed": seed,
                                                 "scores": scores})
        return scores


class Governor(Agent):
    """Applies the fixed governance rule and produces the verdict."""

    name = "gov"
    role = "governor"

    def __init__(self, bus: Bus) -> None:
        super().__init__(bus)
        self.verdicts: list[dict] = []

    def decide(self, before: dict, after: dict, mechanism: str) -> dict:
        from loop.governance import apply_rule
        verdict = apply_rule(before, after, mechanism)
        self.verdicts.append(verdict)
        self.bus.post(self.name, "verdict", verdict)
        return verdict
