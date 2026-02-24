import logging
import asyncio
from typing import Dict, Set
from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections grouped by run_id."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, run_id: str):
        await websocket.accept()
        if run_id not in self.active_connections:
            self.active_connections[run_id] = set()
        self.active_connections[run_id].add(websocket)

    def disconnect(self, websocket: WebSocket, run_id: str):
        if run_id in self.active_connections:
            self.active_connections[run_id].discard(websocket)
            if not self.active_connections[run_id]:
                del self.active_connections[run_id]

    async def broadcast(self, run_id: str, message: str):
        if run_id in self.active_connections:
            dead = []
            for ws in self.active_connections[run_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    dead.append(ws)
            for ws in dead:
                self.active_connections[run_id].discard(ws)


# Global instance
manager = ConnectionManager()


class WebSocketLogHandler(logging.Handler):
    """
    Custom logging handler that broadcasts log records to WebSocket clients
    connected for a specific pipeline run.
    """

    def __init__(self, run_id: str, loop: asyncio.AbstractEventLoop = None):
        super().__init__()
        self.run_id = run_id
        self._loop = loop
        self.log_buffer: list[str] = []

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.log_buffer.append(msg)

            # Broadcast via event loop if available
            if self._loop and self._loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast(self.run_id, msg),
                    self._loop
                )
        except Exception:
            self.handleError(record)
