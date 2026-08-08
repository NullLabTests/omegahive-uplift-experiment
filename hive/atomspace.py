"""AtomSpace-lite: shared persistent memory for the hive.

A minimal JSON-backed store of NODES (concepts/facts) and LINKS (relations
between nodes), each carrying a STI-style confidence weight and a decay clock.

API is deliberately tiny so mechanisms can wrap it.
"""

from __future__ import annotations

import json
import os
import random
import time
from typing import Any


def _norm(node: Any) -> str:
    return str(node)


class AtomSpace:
    """JSON-serializable shared memory."""

    def __init__(self, path: str | None = None, rng: random.Random | None = None):
        self.path = path
        self.rng = rng or random.Random(0)
        self.nodes: dict[str, dict[str, Any]] = {}  # key -> {confidence, ttl, value, refs}
        self.links: list[dict[str, Any]] = []        # {type, a, b, confidence, ttl}
        self.version = 0
        self.stats = {"writes": 0, "reads": 0, "consolidations": 0, "decays": 0}

    # ---- persistence -------------------------------------------------
    def load(self) -> None:
        if self.path and os.path.exists(self.path):
            with open(self.path, "r") as fh:
                data = json.load(fh)
            self.nodes = data.get("nodes", {})
            self.links = data.get("links", [])
            self.version = data.get("version", 0)

    def save(self) -> None:
        if self.path:
            with open(self.path, "w") as fh:
                json.dump(
                    {"nodes": self.nodes, "links": self.links,
                     "version": self.version}, fh, indent=1, sort_keys=True)

    # ---- write / read -------------------------------------------------
    def set_node(self, key: Any, value: Any = True, confidence: float = 1.0,
                 ttl: int = 1000) -> None:
        k = _norm(key)
        prev = self.nodes.get(k)
        conf = confidence if prev is None else max(prev["confidence"], confidence)
        self.nodes[k] = {"confidence": conf, "ttl": ttl, "value": value}
        self.stats["writes"] += 1
        self.version += 1

    def get_node(self, key: Any, default: Any = None) -> Any:
        k = _norm(key)
        self.stats["reads"] += 1
        node = self.nodes.get(k)
        if node is None:
            return default
        node["ttl"] = min(node["ttl"] + 1, 1_000_000)
        return node["value"]

    def node_confidence(self, key: Any) -> float:
        node = self.nodes.get(_norm(key))
        return node["confidence"] if node else 0.0

    def add_link(self, ltype: str, a: Any, b: Any, confidence: float = 0.5,
                 ttl: int = 1000) -> None:
        self.links.append({"type": ltype, "a": _norm(a), "b": _norm(b),
                           "confidence": confidence, "ttl": ttl})
        self.stats["writes"] += 1
        self.version += 1

    def query_links(self, ltype: str, a: Any | None = None,
                    b: Any | None = None) -> list[dict[str, Any]]:
        self.stats["reads"] += 1
        out = []
        for ln in self.links:
            if ln["type"] != ltype:
                continue
            if a is not None and ln["a"] != _norm(a):
                continue
            if b is not None and ln["b"] != _norm(b):
                continue
            out.append(ln)
        return out

    def all_links(self) -> list[dict[str, Any]]:
        return self.links

    # ---- housekeeping -------------------------------------------------
    def decay(self, rate: float = 0.02) -> int:
        """Age every atom; drop dead ones. Returns number dropped."""
        before = len(self.nodes) + len(self.links)
        self.nodes = {k: v for k, v in self.nodes.items() if v["ttl"] > 0}
        for v in self.nodes.values():
            v["ttl"] -= 1
        keep = []
        for ln in self.links:
            ln["ttl"] -= 1
            if ln["ttl"] > 0:
                keep.append(ln)
        self.links = keep
        after = len(self.nodes) + len(self.links)
        dropped = before - after
        self.stats["decays"] += 1
        self.version += 1
        return dropped

    def snapshot(self) -> dict[str, Any]:
        return {
            "n_nodes": len(self.nodes),
            "n_links": len(self.links),
            "version": self.version,
            "stats": dict(self.stats),
        }
