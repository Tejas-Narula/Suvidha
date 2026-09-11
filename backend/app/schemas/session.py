from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

class SessionCreate(BaseModel):
    call_id: str

class SessionResponse(BaseModel):
    session_id: str
    status: str
    created_at: datetime
    service_id: Optional[str] = None

class SessionStateResponse(BaseModel):
    session_id: str
    service_id: Optional[str] = None
    query: Optional[str] = None
    browser_connected: bool
    voice_connected: bool
    status: str
    current_step: Optional[str] = None
    waiting_for_user: bool
    user_action: Optional[str] = None
    workflow: Optional[Dict[str, Any]] = None
    matched_schema: Optional[Dict[str, Any]] = None
    browser_payload: Optional[Dict[str, Any]] = None
