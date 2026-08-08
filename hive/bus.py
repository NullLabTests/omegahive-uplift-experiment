"""Communication bus: per-cycle in-memory message queue, logged to disk.

Messages are tuples of (sender, role, kind, payload, timestamp). Each cycle
gets a fresh bus; the driver persists the transcript to logs/bus/cycle-N.jsonl
so every interaction is auditable.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field


@dataclass
class Message:
    sender: str
    kind: str
    payload: dict
    ts: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {"sender": self.sender, "kind": self.kind,
                "payload": self.payload, "ts": round(self.ts, 3)}


class Bus:
    def __init__(self) -> None:
        self.messages: list[Message] = []
        self._log_path: str | None = None

    def attach_log(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._log_path = path

    def post(self, sender: str, kind: str, payload: dict) -> Message:
        msg = Message(sender=sender, kind=kind, payload=payload)
        self.messages.append(msg)
        if self._log_path:
            with open(self._log_path, "a") as fh:
                fh.write(json.dumps(msg.to_dict()) + "\n")
        return msg

    def drain(self, sender: str, kinds: tuple[str, ...] | None = None) -> list[Message]:
        out = []
        for msg in self.messages:
            if msg.sender == sender:
                continue
            if kinds is None or msg.kind in kinds:
                out.append(msg)
        return out
