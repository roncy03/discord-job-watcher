from __future__ import annotations

import json
from pathlib import Path
from typing import Dict


class DedupeStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.schema = 1
        self.entries: Dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._persist()
            return
        data = json.loads(self.path.read_text())
        if data.get("schema") != self.schema:
            raise RuntimeError("Unsupported store schema")
        self.entries = data.get("jobs", {})

    def has(self, job_id: str) -> bool:
        return job_id in self.entries

    def add(self, job_id: str, timestamp: str) -> None:
        self.entries[job_id] = timestamp

    def save(self) -> None:
        self._persist()

    def _persist(self) -> None:
        payload = {"schema": self.schema, "jobs": self.entries}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True))
