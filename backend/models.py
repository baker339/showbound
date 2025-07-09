from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
import re
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy import PickleType
try:
    from backend.database import Base
except ImportError:
    from database import Base
import datetime

# Position mapping for canonical codes
POSITION_MAP = {
    "Rightfielder": "RF",
    "Shortstop": "SS",
    "Second Baseman": "2B",
    "Leftfielder": "LF",
    "Centerfielder": "CF",
    "First Baseman": "1B",
    "Third Baseman": "3B",
    "Catcher": "C",
    "Pitcher": "P",
    "Designated Hitter": "DH",
    # Add more as needed
}

def parse_positions(positions_raw):
    if not positions_raw:
        return []
    parts = re.split(r',| and ', positions_raw)
    return [POSITION_MAP.get(part.strip(), part.strip()) for part in parts if part.strip()]

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    full_name = Column(String)
    bref_id = Column(String, unique=True, index=True)
    birth_date = Column(String)
    debut_date = Column(String)  # MLB debut date (raw or parsed)
    primary_position = Column(String)
    positions_raw = Column(String)
    positions = Column(MutableList.as_mutable(PickleType))  # List of codes, e.g., ["RF", "SS", "2B"]
    bats = Column(String)
    throws = Column(String)
    height = Column(String)
    weight = Column(String)
    team = Column(String)
    level = Column(String, nullable=False, default="MLB")
    image_url = Column(String)  # URL to player image
    source_url = Column(String)
    bio_json = Column(JSONB)
    # ... add other canonical bio fields as needed
    # Stat table relationships
    standard_batting_stats = relationship('StandardBattingStat', back_populates='player', cascade="all, delete-orphan")
    value_batting_stats = relationship('ValueBattingStat', back_populates='player', cascade="all, delete-orphan")
    advanced_batting_stats = relationship('AdvancedBattingStat', back_populates='player', cascade="all, delete-orphan")
    standard_pitching_stats = relationship('StandardPitchingStat', back_populates='player', cascade="all, delete-orphan")
    value_pitching_stats = relationship('ValuePitchingStat', back_populates='player', cascade="all, delete-orphan")
    advanced_pitching_stats = relationship('AdvancedPitchingStat', back_populates='player', cascade="all, delete-orphan")
    standard_fielding_stats = relationship('StandardFieldingStat', back_populates='player', cascade="all, delete-orphan")

# --- Batting Stat Tables ---
class StandardBattingStat(Base):
    __tablename__ = 'standard_batting_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    war = Column(Float)
    g = Column(Integer)
    pa = Column(Integer)
    ab = Column(Integer)
    r = Column(Integer)
    h = Column(Integer)
    doubles = Column(Integer)
    triples = Column(Integer)
    hr = Column(Integer)
    rbi = Column(Integer)
    sb = Column(Integer)
    cs = Column(Integer)
    bb = Column(Integer)
    so = Column(Integer)
    ba = Column(String)
    obp = Column(String)
    slg = Column(String)
    ops = Column(String)
    ops_plus = Column(Integer)
    roba = Column(String)
    rbat_plus = Column(Integer)
    tb = Column(Integer)
    gidp = Column(Integer)
    hbp = Column(Integer)
    sh = Column(Integer)
    sf = Column(Integer)
    ibb = Column(Integer)
    pos = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='standard_batting_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_std_batting_uc'),)

class ValueBattingStat(Base):
    __tablename__ = 'value_batting_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    pa = Column(Integer)
    rbat = Column(Float)
    rbaser = Column(Float)
    rdp = Column(Float)
    rfield = Column(Float)
    rpos = Column(Float)
    raa = Column(Float)
    waa = Column(Float)
    rrep = Column(Float)
    rar = Column(Float)
    war = Column(Float)
    waa_wl_pct = Column(String)
    wl_162_pct = Column(String)
    owar = Column(Float)
    dwar = Column(Float)
    orar = Column(Float)
    pos = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='value_batting_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_val_batting_uc'),)

class AdvancedBattingStat(Base):
    __tablename__ = 'advanced_batting_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    pa = Column(Integer)
    roba = Column(String)
    rbat_plus = Column(Integer)
    babip = Column(String)
    iso = Column(String)
    hr_pct = Column(String)
    so_pct = Column(String)
    bb_pct = Column(String)
    ev = Column(String)
    hardh_pct = Column(String)
    ld_pct = Column(String)
    gb_pct = Column(String)
    fb_pct = Column(String)
    gb_fb = Column(String)
    pull_pct = Column(String)
    cent_pct = Column(String)
    oppo_pct = Column(String)
    wpa = Column(String)
    cwpa = Column(String)
    re24 = Column(String)
    rs_pct = Column(String)
    sb_pct = Column(String)
    xbt_pct = Column(String)
    pos = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='advanced_batting_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_adv_batting_uc'),)

# --- Pitching Stat Tables ---
class StandardPitchingStat(Base):
    __tablename__ = 'standard_pitching_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    w = Column(Integer)
    l = Column(Integer)
    wl_pct = Column(String)
    era = Column(String)
    g = Column(Integer)
    gs = Column(Integer)
    gf = Column(Integer)
    cg = Column(Integer)
    sho = Column(Integer)
    sv = Column(Integer)
    ip = Column(String)
    h = Column(Integer)
    r = Column(Integer)
    er = Column(Integer)
    hr = Column(Integer)
    bb = Column(Integer)
    ibb = Column(Integer)
    so = Column(Integer)
    hbp = Column(Integer)
    bk = Column(Integer)
    wp = Column(Integer)
    bf = Column(Integer)
    era_plus = Column(Integer)
    fip = Column(String)
    whip = Column(String)
    h9 = Column(String)
    hr9 = Column(String)
    bb9 = Column(String)
    so9 = Column(String)
    so_w = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='standard_pitching_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_std_pitching_uc'),)

class ValuePitchingStat(Base):
    __tablename__ = 'value_pitching_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    waa = Column(Float)
    war = Column(Float)
    ra9 = Column(String)
    fip = Column(String)
    wpa = Column(String)
    re24 = Column(String)
    cwpa = Column(String)
    raa = Column(Float)
    rrep = Column(Float)
    rar = Column(Float)
    g = Column(Integer)
    gs = Column(Integer)
    ip = Column(String)
    bf = Column(Integer)
    awards = Column(String)
    player = relationship('Player', back_populates='value_pitching_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_val_pitching_uc'),)

class AdvancedPitchingStat(Base):
    __tablename__ = 'advanced_pitching_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    ip = Column(String)
    k_pct = Column(String)
    bb_pct = Column(String)
    hr_pct = Column(String)
    babip = Column(String)
    lob_pct = Column(String)
    era_minus = Column(String)
    fip_minus = Column(String)
    xfip_minus = Column(String)
    siera = Column(String)
    pli = Column(String)
    inli = Column(String)
    gmli = Column(String)
    exli = Column(String)
    wpa = Column(String)
    re24 = Column(String)
    cwpa = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='advanced_pitching_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', name='_adv_pitching_uc'),)

# --- Fielding Stat Tables ---
class StandardFieldingStat(Base):
    __tablename__ = 'standard_fielding_stats'
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    season = Column(String)
    age = Column(String)
    team = Column(String)
    lg = Column(String)
    pos = Column(String)
    g = Column(Integer)
    gs = Column(Integer)
    cg = Column(Integer)
    inn = Column(String)
    ch = Column(Integer)
    po = Column(Integer)
    a = Column(Integer)
    e = Column(Integer)
    dp = Column(Integer)
    fld_pct = Column(String)
    lgfld_pct = Column(String)
    rtot = Column(Integer)
    rtot_yr = Column(Integer)
    rdrs = Column(Integer)
    rdrs_yr = Column(Integer)
    rf9 = Column(String)
    lgrf9 = Column(String)
    rfg = Column(String)
    lgrfg = Column(String)
    awards = Column(String)
    player = relationship('Player', back_populates='standard_fielding_stats')
    __table_args__ = (UniqueConstraint('player_id', 'season', 'team', 'pos', name='_std_fielding_uc'),)

class PlayerFeatures(Base):
    __tablename__ = 'player_features'
    player_id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    raw_features = Column(PickleType, nullable=False)
    normalized_features = Column(PickleType, nullable=False)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    player = relationship('Player')

class LevelWeights(Base):
    __tablename__ = 'level_weights'
    id = Column(Integer, primary_key=True)
    weights_json = Column(JSON)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)

class PlayerRatings(Base):
    __tablename__ = 'player_ratings'
    player_id = Column(Integer, ForeignKey('players.id'), primary_key=True)
    overall_rating = Column(Float)
    potential_rating = Column(Float)
    confidence_score = Column(Float)
    player_type = Column(String)
    last_updated = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    # Hitting ratings
    contact_left = Column(Float)
    contact_right = Column(Float)
    power_left = Column(Float)
    power_right = Column(Float)
    vision = Column(Float)
    discipline = Column(Float)
    fielding = Column(Float)
    arm_strength = Column(Float)
    arm_accuracy = Column(Float)
    speed = Column(Float)
    stealing = Column(Float)
    # Pitching ratings
    k_rating = Column(Float)
    bb_rating = Column(Float)
    gb_rating = Column(Float)
    hr_rating = Column(Float)
    command_rating = Column(Float)
    # Historical overalls (JSON or text)
    historical_overalls = Column(JSON)
    # Optionally, add team, level, etc. for denormalized fast access
    team = Column(String)
    level = Column(String)
