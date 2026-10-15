
from pydantic import BaseModel
from typing import Optional
import datetime

class VoiceProfileBase(BaseModel):
    name: str
    description: Optional[str] = None

class VoiceProfileCreate(VoiceProfileBase):
    pass

class VoiceProfile(VoiceProfileBase):
    id: str
    user_id: str
    created_at: datetime.datetime

    class Config:
        orm_mode = True
