from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any

class SarvamSubmitRequest(BaseModel):
    # Flexible schema to accept any fields collected by the voice agent
    model_config = ConfigDict(extra='allow')
    service_type: str
    case_reference: Optional[str] = None

class SarvamSubmitResponse(BaseModel):
    submission_id: str
    status: str

class SarvamStatusResponse(BaseModel):
    status: str
    message: Optional[str] = None
    field_with_issue: Optional[str] = None
