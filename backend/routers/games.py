from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas
from database import SessionLocal
from typing import List

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/games", tags=["games"])

@router.get("/", response_model=List[schemas.GameShallow])
def list_games(db: Session = Depends(get_db)):
    return db.query(crud.models.Game).all()

@router.get("/{game_id}", response_model=schemas.Game)
def get_game(game_id: int, db: Session = Depends(get_db)):
    game = crud.get_game(db, game_id)
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    return game 