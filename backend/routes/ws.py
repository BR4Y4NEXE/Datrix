import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.services.log_handler import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/logs/{run_id}")
async def websocket_logs(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for real-time log streaming.
    Connect to /ws/logs/{run_id} to receive live log messages
    while a pipeline is running.
    """
    await manager.connect(websocket, run_id)
    logger.info(f"WebSocket client connected for run {run_id}")

    try:
        # Keep connection alive until client disconnects
        while True:
            # Wait for any message from client (ping/pong or close)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
        logger.info(f"WebSocket client disconnected for run {run_id}")
    except Exception:
        manager.disconnect(websocket, run_id)
