from pydantic import BaseModel
from datetime import datetime

class BrowserSession(BaseModel):
    id: str
    url: str
    connected: bool
    created_at: datetime
