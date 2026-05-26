"""Tests for the Human-in-the-Loop approval queue."""

import asyncio
import pytest

from backend.hitl_queue import HITLQueue

IRREVERSIBLE_COMMAND = {
    "action_type": "form_submit",
    "reversibility": "irreversible",
    "description": "Submit purchase order",
    "target": "#buy-now",
    "requires_confirmation": True,
}


@pytest.fixture
def queue():
    return HITLQueue()


# ---------------------------------------------------------------------------
# register / resolve basics
# ---------------------------------------------------------------------------

def test_register_creates_pending_entry(queue):
    loop = asyncio.new_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)
    assert action_id
    pending = queue.list_pending()
    assert len(pending) == 1
    assert pending[0]["action_id"] == action_id
    loop.close()


def test_list_pending_empty_by_default(queue):
    assert queue.list_pending() == []


# ---------------------------------------------------------------------------
# approve
# ---------------------------------------------------------------------------

async def test_approve_resolves_future(queue):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)

    result = queue.resolve(action_id, "approved")
    assert result is True
    assert future.done()
    assert future.result() == IRREVERSIBLE_COMMAND


async def test_approve_with_modified_intent(queue):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)

    modified = {**IRREVERSIBLE_COMMAND, "target": "#add-to-cart"}
    queue.resolve(action_id, "approved", modified)
    assert future.result()["target"] == "#add-to-cart"


# ---------------------------------------------------------------------------
# deny
# ---------------------------------------------------------------------------

async def test_deny_resolves_future_with_none(queue):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)

    queue.resolve(action_id, "denied")
    assert future.result() is None


def test_resolve_unknown_action_id_returns_false(queue):
    assert queue.resolve("nonexistent-id", "approved") is False


# ---------------------------------------------------------------------------
# cancel / cancel_all
# ---------------------------------------------------------------------------

async def test_cancel_sets_none_result(queue):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)
    queue.cancel(action_id)
    assert future.done()
    assert future.result() is None
    assert queue.list_pending() == []


async def test_cancel_all_drains_queue(queue):
    loop = asyncio.get_event_loop()
    for _ in range(3):
        queue.register(IRREVERSIBLE_COMMAND, loop.create_future())
    assert len(queue.list_pending()) == 3
    queue.cancel_all()
    assert queue.list_pending() == []


# ---------------------------------------------------------------------------
# submit (async convenience wrapper)
# ---------------------------------------------------------------------------

async def test_submit_approve_flow(queue):
    async def _approve_after_delay():
        await asyncio.sleep(0.01)
        queue.resolve(queue._last_action_id, "approved")

    asyncio.create_task(_approve_after_delay())
    result = await queue.submit(IRREVERSIBLE_COMMAND, timeout=1.0)
    assert result == IRREVERSIBLE_COMMAND


async def test_submit_deny_flow(queue):
    async def _deny_after_delay():
        await asyncio.sleep(0.01)
        queue.resolve(queue._last_action_id, "denied")

    asyncio.create_task(_deny_after_delay())
    result = await queue.submit(IRREVERSIBLE_COMMAND, timeout=1.0)
    assert result is None


async def test_submit_timeout_returns_none(queue):
    result = await queue.submit(IRREVERSIBLE_COMMAND, timeout=0.05)
    assert result is None
    assert queue.list_pending() == []


# ---------------------------------------------------------------------------
# idempotency: resolving twice should not raise
# ---------------------------------------------------------------------------

async def test_double_resolve_is_safe(queue):
    loop = asyncio.get_event_loop()
    future = loop.create_future()
    action_id = queue.register(IRREVERSIBLE_COMMAND, future)
    queue.resolve(action_id, "approved")
    # Second call: action already popped, should return False without raising
    result = queue.resolve(action_id, "approved")
    assert result is False
