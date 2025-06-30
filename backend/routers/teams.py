from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas
from database import SessionLocal
from typing import List
from schemas import TeamShallow

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/teams", tags=["teams"])

@router.get("/", response_model=List[TeamShallow])
def list_teams(db: Session = Depends(get_db)):
    return db.query(crud.models.Team).all()

@router.get("/{team_id}", response_model=schemas.Team)
def get_team(team_id: int, db: Session = Depends(get_db)):
    team = crud.get_team(db, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team 