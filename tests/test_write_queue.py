"""Tests for the single-writer WriteQueue (WTF #6 remediation)."""

from __future__ import annotations

import asyncio

import pytest

from power_framework.core.write_queue import (
    drain,
    enqueue_write,
    get_queue,
    reset_for_test,
)


@pytest.fixture(autouse=True)
def _reset_queue():
    reset_for_test()
    yield
    reset_for_test()


@pytest.mark.asyncio
async def test_jobs_execute_sequentially_and_complete():
    """All queued write jobs run in submission order via the single writer."""
    order: list[int] = []

    def make_job(i: int) -> int:
        order.append(i)
        return i * 10

    results = await asyncio.gather(
        *(enqueue_write(lambda i=i: make_job(i)) for i in range(10))
    )
    await drain()

    assert results == [0, 10, 20, 30, 40, 50, 60, 70, 80, 90]
    # FIFO ordering proves serialization (no two jobs interleave).
    assert order == list(range(10))


@pytest.mark.asyncio
async def test_exceptions_propagate_to_caller():
    """A failing write job surfaces its error to the awaiting caller."""

    def boom() -> int:
        raise ValueError("simulated write failure")

    with pytest.raises(ValueError, match="simulated write failure"):
        await enqueue_write(boom)

    await drain()


@pytest.mark.asyncio
async def test_concurrent_writes_never_race_on_shared_resource():
    """Simulates a non-thread-safe 'DB write' that would corrupt under true
    parallelism; the single-writer queue must keep mutations serialized."""
    counter = {"value": 0}

    def unsafe_increment() -> int:
        # Read-modify-write without a lock: would lose updates if run in parallel.
        cur = counter["value"]
        # Tiny busy window to maximize chance of a race if ever concurrent.
        counter["value"] = cur + 1
        return counter["value"]

    results = await asyncio.gather(
        *(enqueue_write(unsafe_increment) for _ in range(50))
    )
    await drain()

    assert results == list(range(1, 51))
    assert counter["value"] == 50


@pytest.mark.asyncio
async def test_queue_is_process_wide_singleton():
    await enqueue_write(lambda: 1)
    await drain()
    assert get_queue() is get_queue()
