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

router = APIRouter(prefix="/grades", tags=["grades"])

@router.get("/", response_model=List[schemas.PlayerGameGrade])
def list_grades(db: Session = Depends(get_db)):
    return db.query(crud.models.PlayerGameGrade).all()

@router.get("/{grade_id}", response_model=schemas.PlayerGameGrade)
def get_grade(grade_id: int, db: Session = Depends(get_db)):
    grade = crud.get_player_game_grade(db, grade_id)
    if not grade:
        raise HTTPException(status_code=404, detail="Grade not found")
    return grade 