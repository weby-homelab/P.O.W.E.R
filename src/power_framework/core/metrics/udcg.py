"""Deprecated compatibility wrappers — redirected to udcg_real (EACL-2026)."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from .udcg_real import dcg_at_k, ndcg_at_k

if TYPE_CHECKING:
    from collections.abc import Sequence


def udcg(relevance: Sequence[int], k: int | None = None) -> float:
    """Deprecated alias; use :func:`udcg_real.dcg_at_k` instead."""
    warnings.warn(
        "udcg is deprecated; use power_framework.core.metrics.udcg_real.dcg_at_k",
        DeprecationWarning,
        stacklevel=2,
    )
    return dcg_at_k(relevance, k=k)


def normalized_udcg(relevance: Sequence[int], k: int | None = None) -> float:
    """Deprecated alias; use :func:`udcg_real.ndcg_at_k`."""
    warnings.warn(
        "normalized_udcg is deprecated; use power_framework.core.metrics.udcg_real.ndcg_at_k",
        DeprecationWarning,
        stacklevel=2,
    )
    return ndcg_at_k(relevance, k=k)
