from typing import Dict, Optional, List
from datetime import datetime
import uuid
import json

from api.models.process import ProcessState, ProcessStatus
from api.models.intent import StartAutomationIntent

class ProcessManager:
    def __init__(self):
        self.processes: Dict[str, ProcessState] = {}
        self.extensions: Dict[str, dict] = {} # Tracks online extensions

    def create_process(self, intent: StartAutomationIntent) -> ProcessState:
        process_id = f"proc_{uuid.uuid4().hex}"
        state = ProcessState(
            process_id=process_id,
            session_id=intent.session.session_id,
            submission_id=intent.session.submission_id,
            intent=intent
        )
        self.processes[process_id] = state
        return state

    def get_process(self, process_id: str) -> Optional[ProcessState]:
        return self.processes.get(process_id)

    def update_process_status(self, process_id: str, status: ProcessStatus):
        if process_id in self.processes:
            self.processes[process_id].status = status
            self.processes[process_id].updated_at = datetime.utcnow()

    def register_extension(self, extension_id: str, browser_session_id: str):
        self.extensions[extension_id] = {
            "extension_id": extension_id,
            "browser_session_id": browser_session_id,
            "last_seen": datetime.utcnow(),
            "status": "ONLINE"
        }

    def get_online_extension(self) -> Optional[str]:
        # Simple selection: just return the first online extension
        for ext_id, ext_data in self.extensions.items():
            if ext_data["status"] == "ONLINE":
                return ext_id
        return None

    def assign_process_to_extension(self, process_id: str, extension_id: str):
        if process_id in self.processes:
            self.processes[process_id].extension_id = extension_id
            self.processes[process_id].updated_at = datetime.utcnow()

process_manager = ProcessManager()
