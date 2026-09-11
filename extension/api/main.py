from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import uuid

from api.routes import automations, extensions, integrations
from api.config import settings
from api.services.process_manager import process_manager
from api.services.websocket_manager import ws_manager
from api.models.process import ProcessStatus

app = FastAPI(title="Suvidha Browser Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(automations.router, prefix="/v1/automations", tags=["Automations"])
app.include_router(extensions.router, prefix="/v1/extensions", tags=["Extensions"])
app.include_router(integrations.router, prefix="/v1/integrations", tags=["Integrations"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.websocket("/v1/ws/{process_id}")
async def websocket_endpoint(websocket: WebSocket, process_id: str):
    await ws_manager.connect(websocket, process_id)
    process = process_manager.get_process(process_id)
    if process and process.status == ProcessStatus.STARTING:
        await trigger_next_action(process_id)
    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event")
            
            if event_type == "TAB_CREATED":
                process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
                await trigger_next_action(process_id)
            elif event_type == "ACTION_COMPLETED":
                # Advance step and trigger next
                if advance_process_state(process_id):
                    await trigger_next_action(process_id)
            elif event_type == "USER_INPUT_REQUIRED":
                process_manager.update_process_status(process_id, ProcessStatus.WAITING_FOR_USER)
            elif event_type == "AUTH_REQUIRED":
                process_manager.update_process_status(process_id, ProcessStatus.WAITING_FOR_AUTH)
            elif event_type == "WAITING_FOR_CONFIRMATION":
                process_manager.update_process_status(process_id, ProcessStatus.WAITING_FOR_CONFIRMATION)
            elif event_type == "CONFIRMATION_RESPONSE":
                confirmed = data.get("payload", {}).get("confirmed")
                if confirmed:
                    # Submit
                    process_manager.update_process_status(process_id, ProcessStatus.RUNNING)
                    await ws_manager.send_command(
                        process_id,
                        command="CLICK_SELECTOR",
                        command_id=f"cmd_{uuid.uuid4().hex[:8]}",
                        payload={"selector": process.intent.submission_config.submit_button_selector}
                    )
                else:
                    process_manager.update_process_status(process_id, ProcessStatus.CANCELLED)
            elif event_type == "PROCESS_COMPLETED":
                process_manager.update_process_status(process_id, ProcessStatus.COMPLETED)
            elif event_type == "USER_INPUT_RESPONSE":
                # Advance state after input, assuming value applied
                if advance_process_state(process_id):
                    await trigger_next_action(process_id)
            elif event_type == "AUTH_COMPLETED":
                # Proceed to next action
                if advance_process_state(process_id):
                    await trigger_next_action(process_id)

    except WebSocketDisconnect:
        print(f"WebSocket disconnected for process {process_id}")
        ws_manager.disconnect(websocket, process_id)
        process_manager.update_process_status(process_id, ProcessStatus.PAUSED)
    except Exception as e:
        print(f"Error in websocket loop: {e}")
        import traceback
        traceback.print_exc()
        ws_manager.disconnect(websocket, process_id)
        process_manager.update_process_status(process_id, ProcessStatus.PAUSED)

def advance_process_state(process_id: str) -> bool:
    process = process_manager.get_process(process_id)
    if not process: return False
    
    nav_len = len(process.intent.navigation_flow)
    fields_len = len(process.intent.form_filling.fields)
    
    if process.current_navigation_step < nav_len - 1:
        process.current_navigation_step += 1
        return True
    elif process.current_navigation_step == nav_len - 1 and nav_len > 0 and process.current_form_field == 0 and fields_len > 0:
        # Move from navigation to form
        process.current_navigation_step += 1
        return True
    elif process.current_form_field < fields_len - 1:
        process.current_form_field += 1
        return True
    elif process.current_form_field == fields_len - 1:
        # Done with forms, move to submission
        process.current_form_field += 1
        return True
    return False

async def trigger_next_action(process_id: str):
    process = process_manager.get_process(process_id)
    if not process: return
    
    nav_len = len(process.intent.navigation_flow)
    fields_len = len(process.intent.form_filling.fields)
    
    if process.status == ProcessStatus.STARTING:
        await ws_manager.send_command(
            process_id,
            command="OPEN_TAB",
            command_id=f"cmd_{uuid.uuid4().hex[:8]}",
            payload={"url": process.intent.target.portal_url}
        )
        return

    # 1. Navigation Flow
    if process.current_navigation_step < nav_len:
        nav = process.intent.navigation_flow[process.current_navigation_step]
        cmd = "NAVIGATE" if nav.action == "navigate" else "CLICK_SELECTOR"
        await ws_manager.send_command(
            process_id,
            command=cmd,
            command_id=f"cmd_{uuid.uuid4().hex[:8]}",
            payload={"url": nav.target_url, "selector": nav.selector}
        )
        return
        
    # 2. Form Filling
    if process.current_form_field < fields_len:
        field = process.intent.form_filling.fields[process.current_form_field]
        
        # We don't have value_source in intent schema necessarily, but assuming empty means wait
        if not field.value and field.is_required:
            process_manager.update_process_status(process_id, ProcessStatus.WAITING_FOR_USER)
            await ws_manager.send_command(
                process_id,
                command="REQUEST_USER_INPUT",
                command_id=f"cmd_{uuid.uuid4().hex[:8]}",
                payload={"question": f"Please provide {field.field_name}", "field_name": field.field_name}
            )
            return
            
        cmd = "FILL_FIELD"
        if field.action == "select_option":
            cmd = "SELECT_OPTION"
        elif field.action == "click":
            cmd = "CLICK_SELECTOR"
            
        await ws_manager.send_command(
            process_id,
            command=cmd,
            command_id=f"cmd_{uuid.uuid4().hex[:8]}",
            payload={"selector": field.selector, "value": field.option_value or field.value}
        )
        return
        
    # 3. Request Confirmation
    process_manager.update_process_status(process_id, ProcessStatus.WAITING_FOR_CONFIRMATION)
    await ws_manager.send_command(
        process_id,
        command="REQUEST_CONFIRMATION",
        command_id=f"cmd_{uuid.uuid4().hex[:8]}",
        payload={"message": "Form is ready for submission."}
    )
