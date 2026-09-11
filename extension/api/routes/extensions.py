from fastapi import APIRouter
from pydantic import BaseModel
from api.services.process_manager import process_manager

router = APIRouter()

class ExtensionRegistration(BaseModel):
    extension_id: str
    browser_session_id: str
    status: str

@router.post("/register")
async def register_extension(registration: ExtensionRegistration):
    process_manager.register_extension(registration.extension_id, registration.browser_session_id)
    
    # Check if there's any STARTING process waiting for an extension
    pending_process_id = None
    for pid, proc in process_manager.processes.items():
        if proc.status == "STARTING" and not proc.extension_id:
            pending_process_id = pid
            process_manager.assign_process_to_extension(pid, registration.extension_id)
            break

    return {
        "status": "REGISTERED",
        "assigned_process_id": pending_process_id
    }
