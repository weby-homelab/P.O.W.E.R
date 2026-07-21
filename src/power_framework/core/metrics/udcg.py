"""Deprecated compatibility wrappers for the former pseudo-UDCG metric."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

from .discounted_lexical_gain import (
    discounted_lexical_gain,
    normalized_discounted_lexical_gain,
)

if TYPE_CHECKING:
    from collections.abc import Sequence


def udcg(utilities: Sequence[float], k: int | None = None, *, use_log2: bool = True) -> float:
    """Deprecated alias; use :func:`discounted_lexical_gain` instead."""
    warnings.warn(
        "udcg is deprecated; use discounted_lexical_gain", DeprecationWarning, stacklevel=2
    )
    return discounted_lexical_gain(utilities, k=k, use_log2=use_log2)


def normalized_udcg(utilities: Sequence[float], k: int | None = None) -> float:
    """Deprecated alias; use :func:`normalized_discounted_lexical_gain`."""
    warnings.warn(
        "normalized_udcg is deprecated; use normalized_discounted_lexical_gain",
        DeprecationWarning,
        stacklevel=2,
    )
    return normalized_discounted_lexical_gain(utilities, k=k)
