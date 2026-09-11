from fastapi import APIRouter, HTTPException
from app.schemas.session import SessionCreate, SessionResponse, SessionStateResponse
from app.services.session_manager import session_manager
from app.utils.ids import generate_session_id

router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(request: SessionCreate):
    session_id = generate_session_id()
    session = session_manager.create_session(session_id, request.call_id)
    return SessionResponse(
        session_id=session.session_id,
        status=session.status,
        created_at=session.created_at
    )

@router.get("/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return SessionStateResponse(
        session_id=session.session_id,
        service_id=session.service_id,
        browser_connected=session.browser_connected,
        voice_connected=session.voice_connected,
        status=session.status,
        current_step=session.current_step,
        waiting_for_user=session.waiting_for_user,
        user_action=session.user_action
    )

@router.post("/{session_id}/confirm-submission")
async def confirm_submission(session_id: str):
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    session.status = "submission_confirmed"
    # Will trigger logic to send SUBMIT command to browser
    return {"status": "submission_confirmed"}
