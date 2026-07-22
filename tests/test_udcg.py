"""Tests for the legacy discounted lexical-gain proxy and compatibility aliases."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from power_framework.core.metrics.discounted_lexical_gain import (
    discounted_lexical_gain,
    normalized_discounted_lexical_gain,
    utilities_from_relevance,
)
from power_framework.core.metrics.udcg import normalized_udcg, udcg

FIXTURE = Path(__file__).parent / "fixtures" / "search_gt.json"


def test_discounted_lexical_gain_monotonic_in_utility() -> None:
    assert discounted_lexical_gain([1.0, 1.0, 1.0]) > discounted_lexical_gain([1.0, 0.0, 0.0])


def test_discounted_lexical_gain_position_discount() -> None:
    # A highly useful doc at rank 2 scores less than the same doc at rank 1.
    assert discounted_lexical_gain([0.0, 1.0]) < discounted_lexical_gain([1.0, 0.0])


def test_discounted_lexical_gain_empty() -> None:
    assert discounted_lexical_gain([]) == 0.0


def test_normalized_discounted_lexical_gain_perfect_ranking() -> None:
    utils = [1.0, 0.6, 0.3]
    assert normalized_discounted_lexical_gain(utils) == 1.0


def test_normalized_discounted_lexical_gain_reversed() -> None:
    utils = [0.3, 0.6, 1.0]
    n = normalized_discounted_lexical_gain(utils)
    assert 0.0 < n < 1.0


def test_udcg_aliases_emit_deprecation_warning() -> None:
    with pytest.deprecated_call():
        assert udcg([1.0]) == discounted_lexical_gain([1.0])
    with pytest.deprecated_call():
        assert normalized_udcg([1.0]) == normalized_discounted_lexical_gain([1.0])


def test_utilities_from_relevance_bounds() -> None:
    utils = utilities_from_relevance([0, 1, 2, 3])
    assert utils[0] == 0.0
    assert utils[-1] == 1.0
    # sqrt compression: gap 2->3 smaller than 0->1
    assert (utils[3] - utils[2]) < (utils[1] - utils[0])


def test_frozen_gt_fixture_loads() -> None:
    assert FIXTURE.exists(), "frozen GT fixture must exist (FP-6 fix)"
    data = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert "queries" in data
    for group in ("GT-LEXICAL", "GT-SEMANTIC", "GT-RAG"):
        assert group in data["queries"], f"missing GT group {group}"
        assert len(data["queries"][group]) >= 1
