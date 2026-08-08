"""Hook pipe: the integration point for cognitive mechanisms.

Each mechanism module exports HOOKS = {hook_name: handler}. The pipe runs the
enabled handlers (in roster order) for a given hook, threading a mutable
context so mechanisms compose. Env code calls pipe.<hook_name>(...) and never
needs to know which mechanisms are active.

This is the ONLY place mechanisms meet the runtime pipeline. Constitution
Article II forbids mechanisms from touching loop/driver.py or runner.py.
"""

from __future__ import annotations

import importlib
from typing import Any


class HookPipe:
    def __init__(self, active: list[str], registry: dict[str, Any]):
        self.handlers: dict[str, list[Any]] = {}
        for name in active:
            mod = registry.get(name)
            if mod is None:
                continue
            for hook, fn in getattr(mod, "HOOKS", {}).items():
                self.handlers.setdefault(hook, []).append(fn)
        self.active = list(active)

    def __getattr__(self, hook: str) -> Any:
        def _call(*args: Any, **kwargs: Any):
            ctx = args[0] if args else {}
            for fn in self.handlers.get(hook, []):
                out = fn(ctx, *args[1:], **kwargs)
                if out is not None:
                    ctx = out
            return ctx
        return _call

    def is_active(self, name: str) -> bool:
        return name in self.active


def load_registry(mechanism_dir: str = "mechanisms") -> dict[str, Any]:
    """Import every module in mechanisms/ and index it by its NAME."""
    import os
    registry = {}
    for fn in sorted(os.listdir(mechanism_dir)):
        if fn.startswith("_") or not fn.endswith(".py"):
            continue
        mod = importlib.import_module(f"mechanisms.{fn[:-3]}")
        name = getattr(mod, "NAME", None)
        if name:
            registry[name] = mod
    return registry
