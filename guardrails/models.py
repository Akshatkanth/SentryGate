from pydantic import BaseModel
from typing import Optional

class GuardrailResult(BaseModel):
    blocked: bool
    reason: Optional[str] = None
    category: Optional[str] = None
