from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas.sarvam import SarvamSubmitRequest, SarvamSubmitResponse, SarvamStatusResponse
from app.services.session_manager import session_manager
from app.utils.ids import generate_submission_id
from app.config import settings

router = APIRouter()

def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer ") or authorization.split(" ")[1] != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return authorization

@router.post("/submit", response_model=SarvamSubmitResponse)
async def sarvam_submit(request: SarvamSubmitRequest, auth: str = Depends(verify_api_key)):
    """
    Submission endpoint (agent -> backend)
    Can be called initially with just the name, and subsequently with a submission_id to provide missing fields.
    """
    if request.submission_id:
        # Interactive flow: Voice agent is providing missing information
        session = session_manager.get_session_by_submission_id(request.submission_id)
        if not session:
            raise HTTPException(status_code=404, detail="Submission ID not found")
        
        # Update session with new data
        if request.provided_field and request.provided_value:
            session.collected_data[request.provided_field] = request.provided_value
        else:
            # Fallback for dynamic fields just in case
            new_data = request.model_dump(exclude={"service_type", "case_reference", "submission_id", "provided_field", "provided_value"})
            session.collected_data.update(new_data)
        
        # Reset status so the Chrome extension can continue processing
        session.status = "in_progress"
        session.field_with_issue = None
        session.submission_message = "New information received, resuming automation..."
        
        return SarvamSubmitResponse(
            submission_id=session.submission_id,
            status="received_update"
        )
    else:
        # Initial submission
        submission_id = generate_submission_id()
        
        from app.utils.ids import generate_session_id
        session_id = generate_session_id()
        session = session_manager.create_session(session_id)
        session.service_id = request.service_type or "unknown"
        session.collected_data = request.model_dump(exclude={"service_type", "case_reference", "submission_id", "provided_field", "provided_value"})
        session.submission_id = submission_id
        session.status = "received"
        
        return SarvamSubmitResponse(
            submission_id=submission_id,
            status="received"
        )

@router.get("/submit/{submission_id}/status", response_model=SarvamStatusResponse)
async def get_submission_status(submission_id: str, auth: str = Depends(verify_api_key)):
    """
    Status-check endpoint (agent -> backend, during the same call)
    """
    session = session_manager.get_session_by_submission_id(submission_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    return SarvamStatusResponse(
        status=session.status,
        message=session.submission_message,
        field_with_issue=session.field_with_issue
    )
