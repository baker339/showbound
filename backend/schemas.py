from pydantic import BaseModel
from typing import Optional, List, TYPE_CHECKING
import datetime

class TeamBase(BaseModel):
    name: str
    abbreviation: str

class TeamCreate(TeamBase):
    pass

class Team(TeamBase):
    id: int
    name: str
    abbreviation: str
    players: Optional[List['Player']] = None
    class Config:
        orm_mode = True

class TeamShallow(BaseModel):
    id: int
    name: str
    abbreviation: str
    class Config:
        orm_mode = True

class PlayerBase(BaseModel):
    name: str
    position: Optional[str] = None
    team_id: Optional[int] = None

class PlayerCreate(PlayerBase):
    pass

class Player(PlayerBase):
    id: int
    team: Optional[Team] = None
    class Config:
        orm_mode = True

class PlayerShallow(BaseModel):
    id: int
    name: str
    position: Optional[str] = None
    team_id: Optional[int] = None
    class Config:
        orm_mode = True

class GameBase(BaseModel):
    date: datetime.datetime
    home_team_id: int
    away_team_id: int

class GameCreate(GameBase):
    pass

class Game(BaseModel):
    id: int
    date: datetime.datetime
    home_team_id: int
    away_team_id: int
    home_team: Optional[TeamShallow] = None
    away_team: Optional[TeamShallow] = None
    at_bats: Optional[List['AtBatShallow']] = None
    class Config:
        orm_mode = True

class GameShallow(BaseModel):
    id: int
    date: datetime.datetime
    home_team: Optional[TeamShallow] = None
    away_team: Optional[TeamShallow] = None
    class Config:
        orm_mode = True

class AtBatBase(BaseModel):
    game_id: int
    batter_id: int
    pitcher_id: int
    inning: int
    result: Optional[str] = None

class AtBatCreate(AtBatBase):
    pass

class AtBat(AtBatBase):
    id: int
    class Config:
        orm_mode = True

class AtBatShallow(BaseModel):
    id: int
    game_id: int
    batter_id: int
    pitcher_id: int
    inning: int
    result: Optional[str] = None
    class Config:
        orm_mode = True

class PitchBase(BaseModel):
    game_id: int
    pitcher_id: int
    batter_id: int
    at_bat_id: int
    inning: int
    pitch_number: Optional[int] = None
    pitch_type: Optional[str] = None
    pitch_result: Optional[str] = None
    description: Optional[str] = None
    release_speed: Optional[float] = None
    release_spin_rate: Optional[float] = None
    plate_x: Optional[float] = None
    plate_z: Optional[float] = None
    zone: Optional[int] = None
    is_strike: Optional[bool] = None
    is_ball: Optional[bool] = None
    is_called_correctly: Optional[bool] = None
    x0: Optional[float] = None
    y0: Optional[float] = None
    z0: Optional[float] = None
    vx0: Optional[float] = None
    vy0: Optional[float] = None
    vz0: Optional[float] = None
    ax: Optional[float] = None
    ay: Optional[float] = None
    az: Optional[float] = None
    sz_top: Optional[float] = None
    sz_bot: Optional[float] = None

class PitchCreate(PitchBase):
    pass

class Pitch(PitchBase):
    id: int
    class Config:
        orm_mode = True

class PlayerGameGradeBase(BaseModel):
    player_id: int
    game_id: int
    grade: float
    notes: Optional[str] = None

class PlayerGameGradeCreate(PlayerGameGradeBase):
    pass

class PlayerGameGrade(PlayerGameGradeBase):
    id: int
    class Config:
        orm_mode = True

class PlayerRatings(BaseModel):
    contact: float
    contact_percentile: Optional[float] = None
    power: float
    power_percentile: Optional[float] = None
    speed: float
    speed_percentile: Optional[float] = None
    defense: float
    defense_percentile: Optional[float] = None
    arm: float
    arm_percentile: Optional[float] = None
    player_type: Optional[int] = None
    class Config:
        orm_mode = True

class PlayerSummary(BaseModel):
    summary: str
    class Config:
        orm_mode = True

class PlayerSimilarity(BaseModel):
    id: int
    name: str
    position: Optional[str] = None
    team_id: Optional[int] = None
    ratings: PlayerRatings
    similarity: float
    player_type: Optional[int] = None
    class Config:
        orm_mode = True

class MLBShowRatings(BaseModel):
    # Hitting ratings
    contact_left: float
    contact_right: float
    power_left: float
    power_right: float
    vision: float
    discipline: float
    clutch: Optional[float] = None
    
    # Fielding ratings
    fielding: float
    arm_strength: float
    arm_accuracy: float
    reaction: Optional[float] = None
    blocking: Optional[float] = None
    speed: float
    stealing: float
    
    # Pitching ratings (for pitchers)
    stamina: Optional[float] = None
    velocity: Optional[float] = None
    control: Optional[float] = None
    break_rating: Optional[float] = None
    clutch_pitching: Optional[float] = None
    
    # Overall ratings
    overall_rating: float
    potential_rating: float
    mlb_comp_rating: Optional[float] = None
    confidence_score: float
    
    class Config:
        orm_mode = True

class ScoutingReportSchema(BaseModel):
    id: int
    scout_name: Optional[str] = None
    report_date: datetime.datetime
    report_text: str
    tools_grades: dict
    future_value: int
    risk_factor: str
    eta_mlb: Optional[int] = None
    
    class Config:
        orm_mode = True

class PlayerComparisonSchema(BaseModel):
    id: int
    mlb_player_id: int
    mlb_player_name: str
    mlb_player_team: Optional[str] = None
    similarity_score: float
    comparison_reason: str
    comp_date: datetime.datetime
    
    class Config:
        orm_mode = True

class MLBSuccessPrediction(BaseModel):
    mlb_debut_probability: float
    projected_career_war: float
    risk_factor: str
    eta_mlb: int
    ceiling_comparison: str
    floor_comparison: str
    
    class Config:
        orm_mode = True

class ProspectListItem(BaseModel):
    id: int
    name: str
    school: Optional[str] = None
    level: str
    position: Optional[str] = None
    organization: Optional[str] = None
    graduation_year: Optional[int] = None
    stats_json: Optional[dict] = None
    notes: Optional[str] = None
    class Config:
        orm_mode = True

class ProspectDetail(BaseModel):
    id: int
    name: str
    school: Optional[str] = None
    level: str
    position: Optional[str] = None
    organization: Optional[str] = None
    graduation_year: Optional[int] = None
    stats_json: Optional[dict] = None
    scouting_report: Optional[str] = None
    notes: Optional[str] = None
    
    # Enhanced data
    mlb_show_ratings: Optional[MLBShowRatings] = None
    similar_players: Optional[List[PlayerComparisonSchema]] = None
    mlb_success_prediction: Optional[MLBSuccessPrediction] = None
    scouting_reports: Optional[List[ScoutingReportSchema]] = None
    
    class Config:
        orm_mode = True

if TYPE_CHECKING:
    Player.update_forward_refs()
    Team.update_forward_refs()
    AtBat.update_forward_refs()
    Game.update_forward_refs()
    AtBatShallow.update_forward_refs()
