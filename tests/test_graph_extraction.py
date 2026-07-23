"""Tests for local triplet extraction and persistence (WTF #5 remediation)."""

from __future__ import annotations

import sqlite3

from power_framework.core.db import _init_db
from power_framework.core.graph_extraction import (
    Triplet,
    extract_triplets,
    store_note_triplets,
    store_triplets,
)


def test_extracts_ua_is_a_triplet():
    text = "POWER це AI-native Second Brain toolkit для знань."
    triplets = extract_triplets(text)
    assert triplets
    top = triplets[0]
    assert top.relation == "is_a"
    assert "POWER" in top.subject
    assert "AI-native" in top.object


def test_extracts_en_uses_triplet():
    text = "The reranker uses a cross-encoder to score documents."
    triplets = extract_triplets(text)
    assert any(t.relation == "uses" for t in triplets)


def test_no_triplet_when_no_cue():
    text = "Just a plain sentence without any relationship expressed here."
    assert extract_triplets(text) == []


def test_skips_trivial_self_loop():
    text = "Energy is energy."
    # subject and object are identical -> skipped.
    assert extract_triplets(text) == []


def test_store_triplets_persists_rows(tmp_path):
    db = tmp_path / "search.db"
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    _init_db(conn)
    triplets = [
        Triplet(subject="A", relation="uses", object="B"),
        Triplet(subject="A", relation="is_a", object="C"),
    ]
    written = store_triplets(conn, "note.md", triplets)
    assert written == 2
    rows = conn.execute(
        "SELECT source_path, subject, relation, object FROM relations ORDER BY id"
    ).fetchall()
    assert rows[0] == ("note.md", "A", "uses", "B")
    assert rows[1] == ("note.md", "A", "is_a", "C")
    conn.close()


def test_store_note_triplets_extracts_and_persists(tmp_path, monkeypatch):
    db = tmp_path / "search.db"
    monkeypatch.setenv("POWER_SEARCH_DB", str(db))
    # Pre-create the DB so store_note_triplets finds it.
    conn = sqlite3.connect(str(db))
    conn.execute("PRAGMA journal_mode=WAL")
    _init_db(conn)
    conn.close()

    content = "SQLite це embedded database engine. The framework uses WAL mode."
    written = store_note_triplets(tmp_path, "01_Projects/Note.md", content)
    assert written >= 1

    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT source_path, relation FROM relations WHERE source_path = ?",
        ("01_Projects/Note.md",),
    ).fetchall()
    conn.close()
    assert ("01_Projects/Note.md", "is_a") in rows
    assert ("01_Projects/Note.md", "uses") in rows
