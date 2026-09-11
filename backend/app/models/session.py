from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ApplicationSession(BaseModel):
    session_id: str
    call_id: Optional[str] = None
    service_id: Optional[str] = None
    mode: str = "fill"
    workflow: Optional[Dict[str, Any]] = None
    
    browser_connected: bool = False
    voice_connected: bool = True
    
    status: str = "active" # active, in_progress, submitted, failed, needs_correction
    current_step: Optional[str] = None
    
    waiting_for_user: bool = False
    user_action: Optional[str] = None
    
    created_at: datetime
    last_activity: datetime
    
    # Store collected data from Sarvam
    collected_data: Dict[str, Any] = {}
    
    # Store extracted query & matched pgvector schema/blueprint
    query: Optional[str] = None
    matched_schema: Optional[Dict[str, Any]] = None
    
    # Store submission info
    submission_id: Optional[str] = None
    submission_message: Optional[str] = None
    field_with_issue: Optional[str] = None
