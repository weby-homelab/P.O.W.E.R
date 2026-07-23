"""Single-writer background queue for all vault mutation operations.

POWER 3.2 WTF #6 remediation: concurrent MCP writes (``ingest_note``,
``synthesize_session``, ``generate_index``) plus background index re-generation
previously raced on ``power_search.db`` and could raise
``sqlite3.OperationalError: database is locked``. Combined with the existing WAL
+ busy_timeout settings in ``db.py``, routing every write through one
asyncio worker serializes mutations and eliminates the lock contention.
"""

from __future__ import annotations

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Any, TypeVar

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

T = TypeVar("T")

# Default ceiling for a single queued write job. ``None`` deliberately means
# "wait for completion": using ``float('inf')`` with ``asyncio.wait_for``
# leaves an impractically long timer behind and complicates clean event-loop
# shutdown in clients and tests.
_DEFAULT_JOB_TIMEOUT_S: float | None = None

_queue: asyncio.Queue[Any] | None = None
_worker_task: asyncio.Task[Any] | None = None


def get_queue() -> asyncio.Queue[Any]:
    """Return the process-wide write queue, creating it lazily."""
    global _queue
    if _queue is None:
        _queue = asyncio.Queue()
    return _queue


async def _worker() -> None:
    """Consume write jobs one at a time (single-writer invariant)."""
    queue = get_queue()
    while True:
        job = await queue.get()
        try:
            await job()
        except asyncio.CancelledError:
            # A worker belongs to its event loop.  Never swallow cancellation:
            # ``asyncio.run`` and ASGI/MCP shutdown must be able to drain the
            # loop instead of leaving a permanent pending worker task behind.
            raise
        except Exception:
            logger.exception("write-queue job raised; continuing worker loop")
        finally:
            queue.task_done()
        # Do not retain an idle background task after the current batch.  This
        # makes the queue safe for short-lived CLI/event-loop clients as well
        # as long-lived MCP servers; the next enqueue lazily starts a worker.
        if queue.empty():
            return


def ensure_write_worker() -> None:
    """Start the single-writer background task if it is not already running."""
    global _worker_task
    if _worker_task is None or _worker_task.done():
        loop = asyncio.get_event_loop()
        _worker_task = loop.create_task(_worker())


async def run_blocking(sync_fn: Callable[[], T]) -> T:
    """Run a blocking operation without leaving an executor thread behind.

    FastMCP tools use this for both read and write work.  A scoped executor
    keeps the event loop responsive and joins its worker before the coroutine
    returns, which also makes short-lived CLI loops shut down cleanly.
    """
    with ThreadPoolExecutor(max_workers=1) as executor:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(executor, sync_fn)


async def enqueue_write(
    sync_fn: Callable[[], T], timeout: float | None = _DEFAULT_JOB_TIMEOUT_S
) -> T:
    """Schedule ``sync_fn`` to run serialized by the single-writer worker.

    Returns whatever ``sync_fn`` returns. The callable itself runs in a worker
    thread (via ``asyncio.to_thread``) so the event loop stays responsive while
    the worker holds the single-writer lock for this job.
    """
    ensure_write_worker()
    loop = asyncio.get_event_loop()
    fut: asyncio.Future[T] = loop.create_future()

    async def _job() -> None:
        try:
            result = await run_blocking(sync_fn)
            fut.set_result(result)
        except Exception as exc:
            fut.set_exception(exc)

    await get_queue().put(_job)
    if timeout is None:
        return await fut
    return await asyncio.wait_for(fut, timeout=timeout)


async def drain() -> None:
    """Wait until all queued write jobs have been processed (test helper)."""
    await get_queue().join()


def reset_for_test() -> None:
    """Drop the queue/worker between tests."""
    global _queue, _worker_task
    _queue = None
    _worker_task = None
