from __future__ import annotations

from collections.abc import Callable

from .logging import JsonRuntimeLogger
from .schemas import SystemEvent

EventHandler = Callable[[SystemEvent], None]


class EventBus:
    def __init__(self, logger: JsonRuntimeLogger) -> None:
        self._logger = logger
        self._subscribers: list[EventHandler] = []

    def subscribe(self, handler: EventHandler) -> None:
        self._subscribers.append(handler)

    def publish(self, event: SystemEvent) -> None:
        self._logger.append("event", {"event": event.to_dict()})
        for handler in self._subscribers:
            handler(event)
