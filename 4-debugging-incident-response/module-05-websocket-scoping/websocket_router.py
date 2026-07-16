import asyncio
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status, Depends
from sqlalchemy.orm import Session
import jwt
from app.config import settings
from app.database import get_db
import app.crud as crud
from app.logging_config import logger

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        # Maps active WebSocket to dict containing: 'email' and 'team_ids'
        self.active_connections: dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, token: str, db: Session):
        await websocket.accept()
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing token")
            return None

        # Verify JWT Token
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret,
                algorithms=[settings.jwt_algorithm]
            )
            email = payload.get("sub")
            if not email:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
                return None
        except Exception:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid or expired token")
            return None

        # Fetch authorized team IDs
        team_ids = crud.get_user_team_ids(db, email)
        
        self.active_connections[websocket] = {
            "email": email,
            "team_ids": team_ids
        }
        
        logger.info(
            "websocket_connected",
            email=email,
            teams=team_ids
        )
        return email

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            conn_info = self.active_connections.pop(websocket)
            logger.info("websocket_disconnected", email=conn_info["email"])

    async def broadcast_event(self, team_id: int, event_type: str, actor: str, payload: dict = None):
        if payload is None:
            payload = {}
            
        event = {
            "event_type": event_type,
            "team_id": team_id,
            "actor": actor,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }
        
        disconnected_sockets = []
        for websocket, info in list(self.active_connections.items()):
            if team_id in info["team_ids"]:
                try:
                    await websocket.send_json(event)
                except Exception:
                    disconnected_sockets.append(websocket)
                    
        for ws in disconnected_sockets:
            self.disconnect(ws)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    db: Session = Depends(get_db)
):
    email = await manager.connect(websocket, token, db)
    if not email:
        return

    try:
        while True:
            # Maintain connection and listen for client heartbeats/messages
            data = await websocket.receive_text()
            # Simple heartbeat reply if client pings
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error("websocket_error", email=email, error=str(e))
        manager.disconnect(websocket)
