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
    Called once, mid-call, after the caller confirms all details.
    """
    # For a real implementation, we could associate this with an existing session via call_id.
    # We will create a submission ID that the agent can poll.
    submission_id = generate_submission_id()
    
    # Store the collected data in a new or existing session
    # For simplicity, we create a new session just for this submission for the extension to pick up.
    from app.utils.ids import generate_session_id
    session_id = generate_session_id()
    session = session_manager.create_session(session_id)
    session.service_id = request.service_type
    session.collected_data = request.model_dump(exclude={"service_type", "case_reference"})
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
