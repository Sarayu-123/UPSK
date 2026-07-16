from collections import defaultdict
from typing import Any, Awaitable, Callable
import logging

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]

class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(
        self,
        event_type: str,
        handler: EventHandler,
    ) -> None:
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    async def publish(
        self,
        event_type: str,
        payload: dict[str, Any],
    ) -> None:
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(payload)
            except Exception as e:
                logger.error(
                    "Error executing handler %s for event %s: %s",
                    handler.__name__ if hasattr(handler, "__name__") else str(handler),
                    event_type,
                    str(e),
                    exc_info=True
                )

event_bus = EventBus()
