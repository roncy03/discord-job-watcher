from __future__ import annotations

from pathlib import Path

from jobbot.store import DedupeStore


def test_store_adds_and_persists(tmp_path: Path) -> None:
    store_path = tmp_path / "store.json"
    store = DedupeStore(store_path)
    store.add("foo", "2024-01-01T00:00:00Z")
    store.save()

    store2 = DedupeStore(store_path)
    assert store2.has("foo")
