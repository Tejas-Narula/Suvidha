from pydantic import BaseModel
from typing import Dict, Any, Optional

class BrowserCommand(BaseModel):
    type: str
    payload: Optional[Dict[str, Any]] = None
