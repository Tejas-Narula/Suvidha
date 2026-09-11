import logging
from fastapi import APIRouter, Depends, HTTPException, Header
from app.schemas.sarvam import SarvamSubmitRequest, SarvamSubmitResponse, SarvamStatusResponse
from app.services.session_manager import session_manager
from app.services.vector_service import vector_service
from app.services.browser_agent import browser_agent_service
from app.utils.ids import generate_submission_id, generate_session_id
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

def verify_api_key(authorization: str = Header(...)):
    if not authorization.startswith("Bearer ") or authorization.split(" ")[1] != settings.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API Key")
    return authorization

@router.post("/submit", response_model=SarvamSubmitResponse)
async def sarvam_submit(request: SarvamSubmitRequest, auth: str = Depends(verify_api_key)):
    """
    Submission endpoint (Voice Agent -> Backend):
    1. Extracts the user's intent / query from the application.
    2. Performs pgvector semantic similarity search against Supabase government schemas.
    3. Persists the matched schema blueprint in the ApplicationSession.
    4. Generates dynamic field-mapped JSON and calls Browser Agent API (with MOCK VARIABLE).
    5. Handles subsequent interactive updates when missing fields or OTP are provided.
    """
    if request.submission_id:
        # Interactive flow: Voice agent is providing missing information / OTP
        session = session_manager.get_session_by_submission_id(request.submission_id)
        if not session:
            raise HTTPException(status_code=404, detail="Submission ID not found")
        
        # Update session with new data
        if request.provided_field and request.provided_value:
            session.collected_data[request.provided_field] = request.provided_value
        else:
            new_data = request.model_dump(
                exclude={"service_type", "case_reference", "submission_id", "provided_field", "provided_value"},
                exclude_none=True
            )
            session.collected_data.update(new_data)
        
        # Re-dispatch updated payload to Browser Agent
        await browser_agent_service.dispatch_to_browser_agent(session)
        
        # Reset status so the Chrome extension can continue processing
        session.status = "in_progress"
        session.field_with_issue = None
        session.submission_message = "New information received, resuming automation..."
        
        return SarvamSubmitResponse(
            submission_id=session.submission_id,
            status="received_update"
        )
    else:
        # Initial submission flow
        submission_id = generate_submission_id()
        session_id = generate_session_id()
        session = session_manager.create_session(session_id)
        
        # Dump collected fields
        collected_data = request.model_dump(
            exclude={"service_type", "case_reference", "submission_id", "provided_field", "provided_value"},
            exclude_none=True
        )
        
        # Step 1: Extract citizen query
        query_text = vector_service.extract_query_text(collected_data, request.service_type)
        session.query = query_text
        session.collected_data = collected_data
        session.submission_id = submission_id
        
        # Step 2: Query pgvector database with the extracted query
        logger.info(f"Querying pgvector for query: '{query_text}'")
        matched_schema = await vector_service.search_service(query_text)
        
        # Step 3: Store matched schema & automation workflow in session
        if matched_schema:
            session.matched_schema = matched_schema
            session.service_id = matched_schema.get("service_title", request.service_type or "unknown")
            session.workflow = {
                "portal_url": matched_schema.get("portal_url"),
                "form_url": matched_schema.get("form_url"),
                "navigation_steps": matched_schema.get("navigation_steps", []),
                "form_fields": matched_schema.get("form_fields", []),
                "submit_button_selector": matched_schema.get("submit_button_selector"),
                "submission_steps": matched_schema.get("submission_steps", [])
            }
            session.submission_message = f"Matched service blueprint: {session.service_id}"
        else:
            session.service_id = request.service_type or "unknown"
            session.submission_message = "Application received. Searching government services..."

        session.status = "received"
        
        # Step 4: Generate dynamic field mapping and dispatch to Browser Agent API (with MOCK VARIABLE)
        await browser_agent_service.dispatch_to_browser_agent(session)
        
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
