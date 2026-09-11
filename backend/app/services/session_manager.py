import threading
from typing import Dict, Optional
from datetime import datetime
from app.models.session import ApplicationSession

class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, ApplicationSession] = {}
        self._lock = threading.Lock()
        
    def create_session(self, session_id: str, call_id: Optional[str] = None) -> ApplicationSession:
        with self._lock:
            now = datetime.utcnow()
            session = ApplicationSession(
                session_id=session_id,
                call_id=call_id,
                created_at=now,
                last_activity=now
            )
            self._sessions[session_id] = session
            return session
            
    def get_session(self, session_id: str) -> Optional[ApplicationSession]:
        with self._lock:
            return self._sessions.get(session_id)
            
    def get_session_by_submission_id(self, submission_id: str) -> Optional[ApplicationSession]:
        with self._lock:
            for session in self._sessions.values():
                if session.submission_id == submission_id:
                    return session
            return None
            
    def update_session(self, session_id: str, **kwargs):
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            for key, value in kwargs.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            session.last_activity = datetime.utcnow()
            return session
            
    def delete_session(self, session_id: str):
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]

session_manager = SessionManager()
