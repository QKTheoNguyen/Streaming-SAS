
import sqlalchemy
from sqlalchemy import (
    Column,
    String,
    DateTime,
    LargeBinary,
    func,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    created_at = Column(DateTime, default=func.now())
    # Store voice features, not raw audio
    features = Column(LargeBinary, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }

