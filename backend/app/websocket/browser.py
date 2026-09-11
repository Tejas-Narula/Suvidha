from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
from app.services.session_manager import session_manager
from app.schemas.events import BrowserEvent
import json
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections[session_id] = websocket
        
        session = session_manager.get_session(session_id)
        if session:
            session.browser_connected = True
            session.status = "in_progress"

    def disconnect(self, session_id: str):
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        session = session_manager.get_session(session_id)
        if session:
            session.browser_connected = False
            if session.status not in ["submitted", "failed"]:
                session.status = "needs_correction"
                session.submission_message = "Browser disconnected."

    async def send_command(self, session_id: str, command: dict):
        if session_id in self.active_connections:
            await self.active_connections[session_id].send_json(command)

manager = ConnectionManager()

@router.websocket("/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                event_data = json.loads(data)
                event = BrowserEvent(**event_data)
                
                # Update session state based on browser events
                session = session_manager.get_session(session_id)
                if not session:
                    continue
                    
                if event.type == "OTP_REQUIRED":
                    session.waiting_for_user = True
                    session.user_action = "OTP"
                    session.status = "needs_correction"
                    session.submission_message = event.payload.get("message", "OTP required on government website")
                    session.field_with_issue = "otp"
                    
                elif event.type == "OTP_COMPLETED":
                    session.waiting_for_user = False
                    session.user_action = None
                    session.status = "in_progress"
                    session.submission_message = "OTP verified, continuing automation."
                    session.field_with_issue = None
                    
                elif event.type == "READY_FOR_SUBMISSION":
                    # The extension is ready. Now we wait for Voice Agent confirmation.
                    session.status = "in_progress"
                    session.submission_message = "Ready for final submission. Awaiting confirmation."
                    
                elif event.type == "SUBMISSION_SUCCESS":
                    session.status = "submitted"
                    session.submission_message = "Successfully submitted."
                    
                elif event.type == "SUBMISSION_FAILED":
                    session.status = "failed"
                    session.submission_message = event.payload.get("message", "Submission failed.")
                    
                elif event.type == "ERROR":
                    session.status = "failed"
                    session.submission_message = event.payload.get("message", "Unknown browser error.")

            except json.JSONDecodeError:
                logger.error("Invalid JSON received from browser")
    except WebSocketDisconnect:
        manager.disconnect(session_id)
