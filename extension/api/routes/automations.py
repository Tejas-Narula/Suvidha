from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import asyncio
import uuid

from api.models.intent import StartAutomationIntent
from api.models.process import ProcessStatus
from api.services.process_manager import process_manager
from api.services.websocket_manager import ws_manager

router = APIRouter()

@router.post("")
async def start_automation(intent: StartAutomationIntent):
    process = process_manager.create_process(intent)
    process_manager.update_process_status(process.process_id, ProcessStatus.STARTING)
    
    ext_id = process_manager.get_online_extension()
    if not ext_id:
        pass
    else:
        process_manager.assign_process_to_extension(process.process_id, ext_id)

    return {
        "process_id": process.process_id,
        "session_id": process.session_id,
        "status": process.status
    }

@router.post("/{process_id}/pause")
async def pause_process(process_id: str):
    process = process_manager.get_process(process_id)
    if not process: raise HTTPException(status_code=404, detail="Process not found")
    process_manager.update_process_status(process_id, ProcessStatus.PAUSED)
    return {"status": "SUCCESS"}

@router.post("/{process_id}/resume")
async def resume_process(process_id: str):
    process = process_manager.get_process(process_id)
    if not process: raise HTTPException(status_code=404, detail="Process not found")
    process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
    return {"status": "SUCCESS"}

@router.post("/{process_id}/cancel")
async def cancel_process(process_id: str):
    process = process_manager.get_process(process_id)
    if not process: raise HTTPException(status_code=404, detail="Process not found")
    process_manager.update_process_status(process_id, ProcessStatus.CANCELLED)
    return {"status": "SUCCESS"}

@router.get("/{process_id}")
async def get_process(process_id: str):
    process = process_manager.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
    return process

@router.get("/{process_id}/events")
async def get_process_events(process_id: str):
    return ws_manager.get_events(process_id)

class UserInput(BaseModel):
    field_name: str
    value: str

@router.post("/{process_id}/input")
async def provide_user_input(process_id: str, input_data: UserInput):
    process = process_manager.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
    
    # Update the value in the intent
    fields = process.intent.form_filling.fields
    if process.current_form_field < len(fields):
        field = fields[process.current_form_field]
        if field.field_name == input_data.field_name:
            field.value = input_data.value
            
    # Trigger the action again, now it has a value so it will send FILL_FIELD
    from api.main import trigger_next_action
    import asyncio
    asyncio.create_task(trigger_next_action(process_id))
    
    return {"status": "SUCCESS"}

class ConfirmInput(BaseModel):
    confirmed: bool

@router.post("/{process_id}/confirm")
async def confirm_submission(process_id: str, confirm_data: ConfirmInput):
    process = process_manager.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
    if confirm_data.confirmed:
        await ws_manager.send_command(
            process_id, 
            command="CLICK_SELECTOR", 
            command_id=f"cmd_{uuid.uuid4().hex[:8]}", 
            payload={"selector": process.intent.submission_config.submit_button_selector}
        )
    else:
        process_manager.update_process_status(process_id, ProcessStatus.CANCELLED)
    return {"status": "SUCCESS"}



@router.post("/{process_id}/auth-complete")
async def auth_complete(process_id: str):
    process = process_manager.get_process(process_id)
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
    await ws_manager.send_command(
        process_id, 
        command="AUTH_COMPLETED_BY_USER", 
        command_id=f"cmd_{uuid.uuid4().hex[:8]}"
    )
    return {"status": "SUCCESS"}
