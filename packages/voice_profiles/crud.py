
from sqlalchemy.orm import Session
import uuid
from packages.voice_profiles.db import models

def create_voice_profile(db: Session, user_id: str, name: str, description: str, features: bytes):
    profile_id = str(uuid.uuid4())
    db_profile = models.VoiceProfile(
        id=profile_id,
        user_id=user_id,
        name=name,
        description=description,
        features=features,
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return db_profile

def get_voice_profile(db: Session, profile_id: str):
    return db.query(models.VoiceProfile).filter(models.VoiceProfile.id == profile_id).first()

def get_voice_profiles_by_user(db: Session, user_id: str):
    return db.query(models.VoiceProfile).filter(models.VoiceProfile.user_id == user_id).all()

def delete_voice_profile(db: Session, profile_id: str):
    db_profile = db.query(models.VoiceProfile).filter(models.VoiceProfile.id == profile_id).first()
    if db_profile:
        db.delete(db_profile)
        db.commit()
        return True
    return False
