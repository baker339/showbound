from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend import crud, schemas
from backend.database import SessionLocal
from typing import List

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/pitches", tags=["pitches"])

@router.get("/", response_model=List[schemas.Pitch])
def list_pitches(db: Session = Depends(get_db)):
    return db.query(crud.models.Pitch).all()

@router.get("/{pitch_id}", response_model=schemas.Pitch)
def get_pitch(pitch_id: int, db: Session = Depends(get_db)):
    pitch = crud.get_pitch(db, pitch_id)
    if not pitch:
        raise HTTPException(status_code=404, detail="Pitch not found")
    return pitch 