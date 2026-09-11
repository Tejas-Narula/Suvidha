from typing import Dict, List, Any
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self):
        # Maps process_id to a list of active WebSockets
        self.active_connections: Dict[str, List[WebSocket]] = {}
        # Stores events for a process
        self.process_events: Dict[str, List[dict]] = {}

    async def connect(self, websocket: WebSocket, process_id: str):
        await websocket.accept()
        if process_id not in self.active_connections:
            self.active_connections[process_id] = []
        self.active_connections[process_id].append(websocket)
        
        if process_id not in self.process_events:
            self.process_events[process_id] = []

    def disconnect(self, websocket: WebSocket, process_id: str):
        if process_id in self.active_connections:
            if websocket in self.active_connections[process_id]:
                self.active_connections[process_id].remove(websocket)

    async def send_command(self, process_id: str, command: str, command_id: str, payload: dict = None):
        if process_id in self.active_connections:
            message = {
                "protocol_version": "1.0",
                "process_id": process_id,
                "command_id": command_id,
                "command": command,
                "payload": payload or {}
            }
            # Record event
            self.process_events[process_id].append(message)
            
            for connection in self.active_connections[process_id]:
                await connection.send_json(message)

    async def broadcast_event(self, process_id: str, event_data: dict):
        if process_id in self.active_connections:
            self.process_events[process_id].append(event_data)
            for connection in self.active_connections[process_id]:
                await connection.send_json(event_data)
                
    def get_events(self, process_id: str) -> List[dict]:
        return self.process_events.get(process_id, [])

ws_manager = WebSocketManager()
