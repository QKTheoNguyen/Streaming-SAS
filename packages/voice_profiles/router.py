
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from packages.voice_profiles import crud, schemas
from packages.voice_profiles.db.database import get_db
from typing import List

router = APIRouter(
    prefix="/voice-profiles",
    tags=["voice-profiles"],
)

# This is a placeholder for a real user authentication system
def get_current_user():
    return "user123"

@router.post("/", response_model=schemas.VoiceProfile)
def create_voice_profile(
    name: str = Form(...),
    description: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user_id: str = Depends(get_current_user),
):
    # In a real application, you would extract features from the audio file here
    # For now, we'll just use the file content as a placeholder
    features = file.file.read()
    return crud.create_voice_profile(
        db=db, user_id=user_id, name=name, description=description, features=features
    )

@router.get("/", response_model=List[schemas.VoiceProfile])
def read_voice_profiles(db: Session = Depends(get_db), user_id: str = Depends(get_current_user)):
    return crud.get_voice_profiles_by_user(db, user_id=user_id)

@router.get("/{profile_id}", response_model=schemas.VoiceProfile)
def read_voice_profile(profile_id: str, db: Session = Depends(get_db)):
    db_profile = crud.get_voice_profile(db, profile_id=profile_id)
    if db_profile is None:
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return db_profile

@router.delete("/{profile_id}")
def delete_voice_profile(profile_id: str, db: Session = Depends(get_db)):
    if not crud.delete_voice_profile(db, profile_id=profile_id):
        raise HTTPException(status_code=404, detail="Voice profile not found")
    return {"message": "Voice profile deleted successfully"}
