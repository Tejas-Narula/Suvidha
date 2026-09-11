import uuid

def generate_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"

def generate_submission_id() -> str:
    return f"SUB{uuid.uuid4().hex[:8].upper()}"
