"""Tests for Performance Plan §1-§6 optimizations in searcher / index_worker."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path

from power_framework.core import index_worker
from power_framework.core.searcher import (
    RERANK_CANDIDATE_LIMIT,
    _hybrid_reranked_search,
    _init_db,
    _semantic_search,
    format_search_results,
    search_vault,
)
from power_framework.core.utils import get_cache_dir


@pytest.fixture
def indexed_vault(sample_vault: Path, monkeypatch):
    """Build a full FTS + embedding index for the sample vault once."""

    monkeypatch.setenv("POWER_VAULT_DIR", str(sample_vault))
    from power_framework.core.searcher import _sync_vault_to_db

    db_path = get_cache_dir() / "power_search.db"
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA journal_mode=WAL")
    _init_db(conn)
    _sync_vault_to_db(sample_vault, conn, sync_embeddings=True)
    conn.close()
    return sample_vault


class TestBackgroundIndexer:
    """§1: search_vault must NOT synchronously index; it enqueues a request."""

    def test_search_does_not_block_on_sync(self, sample_vault, monkeypatch):
        monkeypatch.setenv("POWER_VAULT_DIR", str(sample_vault))
        # search_vault should return quickly (within <5s) even on an empty DB
        # because it no longer calls _sync_vault_to_db synchronously.
        import time

        t0 = time.time()
        results = search_vault(sample_vault, "test", mode="fts", max_results=5)
        elapsed = time.time() - t0
        assert elapsed < 5.0
        # On an empty index it legitimately returns nothing.
        assert isinstance(results, list)

    def test_request_sync_enqueues(self, sample_vault, monkeypatch):
        monkeypatch.setenv("POWER_VAULT_DIR", str(sample_vault))
        index_worker.request_sync(sample_vault, mode="fts")
        conn = sqlite3.connect(str(get_cache_dir() / "power_search.db"), timeout=30)
        index_worker._ensure_queue_table(conn)
        row = conn.execute("SELECT mode FROM sync_queue WHERE id = 1").fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "fts"

    def test_coverage_reports_counts(self, indexed_vault):
        indexed, total = index_worker.get_coverage(indexed_vault)
        assert total > 0
        assert indexed == total


class TestSemanticNumpy:
    """§5: _semantic_search uses vectorized numpy cosine."""

    def test_numpy_cosine_returns_ranked(self, indexed_vault):
        res_np = _semantic_search(indexed_vault, "test project resource", max_results=5)
        assert isinstance(res_np, list)
        if res_np:
            scores = [r.score for r in res_np]
            assert scores == sorted(scores, reverse=True)

    def test_semantic_empty_on_no_embeddings(self, tmp_path):
        res = _semantic_search(tmp_path, "anything", max_results=5)
        assert res == []


class TestBoundedRerank:
    """§4: hybrid_reranked passes at most RERANK_CANDIDATE_LIMIT to reranker."""

    def test_rerank_limit_constant(self):
        assert RERANK_CANDIDATE_LIMIT == 20

    def test_hybrid_reranked_returns_results(self, indexed_vault):
        results = _hybrid_reranked_search(indexed_vault, "test project", max_results=5)
        assert isinstance(results, list)
        assert len(results) <= 5


class TestPragmaTuning:
    """§3: _init_db applies cache_size and mmap_size pragmas."""

    def test_pragmas_applied(self, tmp_path):
        conn = sqlite3.connect(str(tmp_path / "t.db"))
        _init_db(conn)
        cache = conn.execute("PRAGMA cache_size").fetchone()[0]
        mmap = conn.execute("PRAGMA mmap_size").fetchone()[0]
        conn.close()
        assert cache == -65536
        assert mmap >= 1024 * 1024 * 1024


class TestCoverageFooter:
    """§6: format_search_results shows honest index coverage when vault given."""

    def test_footer_present_when_indexed(self, indexed_vault):
        results = search_vault(indexed_vault, "test", mode="fts", max_results=5)
        report = format_search_results(results, "test", mode="fts", vault_dir=indexed_vault)
        assert "Index coverage:" in report

    def test_no_footer_without_vault(self):
        from power_framework.core.searcher import SearchResult

        results = [
            SearchResult(
                rel_path="a.md",
                title="A",
                description="d",
                note_type="Resource",
                score=1.0,
                snippet="",
                match_count=1,
            )
        ]
        report = format_search_results(results, "test", mode="fts")
        assert "Index coverage:" not in report


class TestEmbeddingCacheDir:
    """§2: fastembed cache dir is pinned to a persistent location."""

    def test_fastembed_cache_env_set(self):
        import os

        assert "FASTEMBED_CACHE_DIR" in os.environ
        assert "tmp" not in os.environ["FASTEMBED_CACHE_DIR"]
