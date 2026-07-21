"""Legacy normalized lexical-gain metric; this is not EACL-2026 UDCG.

The score discounts a query-term-derived relevance proxy by rank and normalizes
against the ideal ordering of that same retrieved list. It has no distractor
utility, answer utility, or EACL-2026 position treatment, so callers must not
label its output "UDCG".
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def discounted_lexical_gain(
    utilities: Sequence[float], k: int | None = None, *, use_log2: bool = True
) -> float:
    """Compute discounted gain from ranked lexical relevance proxies."""
    if not utilities:
        return 0.0
    if k is not None:
        utilities = list(utilities)[:k]

    total = 0.0
    for i, utility in enumerate(utilities, start=1):
        discount = __import__("math").log2(i + 1) if use_log2 else float(i)
        total += float(utility) / discount
    return total


def normalized_discounted_lexical_gain(utilities: Sequence[float], k: int | None = None) -> float:
    """Normalize legacy discounted lexical gain against the retrieved ideal order."""
    if not utilities:
        return 0.0
    if k is not None:
        utilities = list(utilities)[:k]
    denominator = discounted_lexical_gain(sorted(utilities, reverse=True), k=k)
    return 0.0 if denominator <= 0.0 else discounted_lexical_gain(utilities, k=k) / denominator


def utilities_from_relevance(relevance: Sequence[int], max_relevance: int = 3) -> list[float]:
    """Map graded lexical relevance to a bounded, compressed proxy utility."""
    import math

    return [math.sqrt(max(0, min(item, max_relevance)) / max_relevance) for item in relevance]
