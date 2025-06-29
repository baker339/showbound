from backend import models, schemas
from sqlalchemy.orm import Session

def create_team(db: Session, team: schemas.TeamCreate):
    db_team = models.Team(**team.dict())
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    return db_team

def get_team(db: Session, team_id: int):
    return db.query(models.Team).filter(models.Team.id == team_id).first()

def create_player(db: Session, player: schemas.PlayerCreate):
    db_player = models.Player(**player.dict())
    db.add(db_player)
    db.commit()
    db.refresh(db_player)
    return db_player

def get_player(db: Session, player_id: int):
    return db.query(models.Player).filter(models.Player.id == player_id).first()

def create_game(db: Session, game: schemas.GameCreate):
    db_game = models.Game(**game.dict())
    db.add(db_game)
    db.commit()
    db.refresh(db_game)
    return db_game

def get_game(db: Session, game_id: int):
    return db.query(models.Game).filter(models.Game.id == game_id).first()

def create_atbat(db: Session, atbat: schemas.AtBatCreate):
    db_atbat = models.AtBat(**atbat.dict())
    db.add(db_atbat)
    db.commit()
    db.refresh(db_atbat)
    return db_atbat

def get_atbat(db: Session, atbat_id: int):
    return db.query(models.AtBat).filter(models.AtBat.id == atbat_id).first()

def create_pitch(db: Session, pitch: schemas.PitchCreate):
    db_pitch = models.Pitch(**pitch.dict())
    db.add(db_pitch)
    db.commit()
    db.refresh(db_pitch)
    return db_pitch

def get_pitch(db: Session, pitch_id: int):
    return db.query(models.Pitch).filter(models.Pitch.id == pitch_id).first()

def create_player_game_grade(db: Session, grade: schemas.PlayerGameGradeCreate):
    db_grade = models.PlayerGameGrade(**grade.dict())
    db.add(db_grade)
    db.commit()
    db.refresh(db_grade)
    return db_grade

def get_player_game_grade(db: Session, grade_id: int):
    return db.query(models.PlayerGameGrade).filter(models.PlayerGameGrade.id == grade_id).first()
