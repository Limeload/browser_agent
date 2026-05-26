"""
Human-in-the-loop approval queue.

Flow
----
1. The WebSocket handler calls register() when it encounters an irreversible action,
   attaches an asyncio.Future, and sends action-pending to the frontend.
2. The command execution is scheduled as a background task that awaits the Future.
3. When the user clicks Approve/Deny, the frontend sends approve-action/deny-action
   back over the same WebSocket.
4. The WebSocket handler calls resolve() which sets the Future result and unblocks
   the background task.
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class PendingAction:
    action_id: str
    intent: dict[str, Any]
    future: asyncio.Future


class HITLQueue:
    def __init__(self) -> None:
        self._pending: dict[str, PendingAction] = {}

    def register(
        self, intent: dict[str, Any], future: asyncio.Future
    ) -> str:
        """Register a pending action. Returns the action_id."""
        action_id = str(uuid.uuid4())
        self._pending[action_id] = PendingAction(
            action_id=action_id, intent=intent, future=future
        )
        logger.info("HITL pending: %s  action=%s", action_id, intent.get("action_type"))
        return action_id

    def resolve(
        self,
        action_id: str,
        decision: str,  # "approved" | "denied"
        modified_intent: dict[str, Any] | None = None,
    ) -> bool:
        """Resolve a pending action. Returns False if action_id not found."""
        action = self._pending.pop(action_id, None)
        if action is None:
            return False
        if action.future.done():
            return False
        if decision == "approved":
            action.future.set_result(modified_intent or action.intent)
        else:
            action.future.set_result(None)
        logger.info("HITL resolved: %s  decision=%s", action_id, decision)
        return True

    def cancel(self, action_id: str) -> None:
        action = self._pending.pop(action_id, None)
        if action and not action.future.done():
            action.future.set_result(None)

    def cancel_all(self) -> None:
        for action_id in list(self._pending):
            self.cancel(action_id)

    def list_pending(self) -> list[dict[str, Any]]:
        return [
            {"action_id": a.action_id, "intent": a.intent}
            for a in self._pending.values()
        ]

    # ------------------------------------------------------------------
    # Convenience wrapper used in tests
    # ------------------------------------------------------------------

    async def submit(
        self, intent: dict[str, Any], timeout: float = 5.0
    ) -> dict[str, Any] | None:
        """
        Register an action and wait for it to be resolved.
        Exposes _last_action_id so tests can resolve it.
        Returns the (possibly modified) intent if approved, None if denied/timed-out.
        """
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        action_id = self.register(intent, future)
        self._last_action_id = action_id
        try:
            return await asyncio.wait_for(asyncio.shield(future), timeout=timeout)
        except asyncio.TimeoutError:
            self.cancel(action_id)
            return None
