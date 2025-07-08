from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from database import SessionLocal
from models import Player, PlayerBio, StatTable, StatRow, StandardBattingStat, ValueBattingStat, AdvancedBattingStat, StandardPitchingStat, ValuePitchingStat, AdvancedPitchingStat, StandardFieldingStat, PlayerFeatures, PlayerRatings
from ml_service import ml_service
import time
import numpy as np
import datetime

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/player/{player_id}/bio")
def get_player_bio(player_id: int, db: Session = Depends(get_db)):
    player = db.query(Player).filter(Player.id == player_id).first()
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    bio_fields = {k: getattr(player, k) for k in [
        'full_name', 'birth_date', 'primary_position', 'positions_raw', 'positions', 'bats', 'throws', 'height', 'weight', 'team', 'source_url']}
    return {"player_id": player_id, "bio": bio_fields}

@router.get("/player/{player_id}/stat_tables")
def get_player_stat_tables(player_id: int, db: Session = Depends(get_db)):
    tables = db.query(StatTable).filter(StatTable.player_id == player_id).all()
    return [{"id": t.id, "caption": t.caption, "table_type": t.table_type, "source_url": t.source_url} for t in tables]

@router.get("/player/{player_id}/stats")
def get_player_stats(player_id: int, table_type: str = Query(None), db: Session = Depends(get_db)):
    tables_query = db.query(StatTable).filter(StatTable.player_id == player_id)
    if table_type:
        tables_query = tables_query.filter(StatTable.table_type == table_type)
    tables = tables_query.all()
    all_rows = []
    for t in tables:
        rows = db.query(StatRow).filter(StatRow.stat_table_id == t.id).all()
        for r in rows:
            all_rows.append({"stat_table_id": t.id, "caption": t.caption, "table_type": t.table_type, "row_index": r.row_index, "row_data": r.row_data})
    return all_rows

@router.get("/players/search")
def search_players(name: str, db: Session = Depends(get_db)):
    players = db.query(Player).filter(Player.full_name.ilike(f"%{name}%")).all()
    return [{"id": p.id, "full_name": p.full_name, "primary_position": p.primary_position, "team": p.team} for p in players]

@router.get("/players")
def list_players(skip: int = 0, limit: int = 10000, db: Session = Depends(get_db)):
    players = db.query(Player).offset(skip).limit(limit).all()
    # Optionally, you can include cached features or ratings here if needed, e.g.:
    # features_cache = {pf.player_id: pf for pf in db.query(PlayerFeatures).all()}
    return [{
        "id": p.id,
        "full_name": p.full_name,
        "primary_position": p.primary_position,
        "team": p.team,
        "level": p.level
        # Optionally add: 'features': features_cache.get(p.id).normalized_features if p.id in features_cache else None
    } for p in players]

@router.get("/player/{player_id}/standard_batting")
def get_standard_batting(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(StandardBattingStat).filter(StandardBattingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/value_batting")
def get_value_batting(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(ValueBattingStat).filter(ValueBattingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/advanced_batting")
def get_advanced_batting(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(AdvancedBattingStat).filter(AdvancedBattingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/standard_pitching")
def get_standard_pitching(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(StandardPitchingStat).filter(StandardPitchingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/value_pitching")
def get_value_pitching(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(ValuePitchingStat).filter(ValuePitchingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/advanced_pitching")
def get_advanced_pitching(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(AdvancedPitchingStat).filter(AdvancedPitchingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/standard_fielding")
def get_standard_fielding(player_id: int, db: Session = Depends(get_db)):
    rows = db.query(StandardFieldingStat).filter(StandardFieldingStat.player_id == player_id).all()
    return [row.__dict__ for row in rows]

@router.get("/player/{player_id}/ratings")
def get_player_ratings(player_id: int, db: Session = Depends(get_db)):
    rating = db.query(PlayerRatings).filter(PlayerRatings.player_id == player_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Player ratings not found")
    # Return all fields as dict
    return {c.name: getattr(rating, c.name) for c in rating.__table__.columns}

@router.get("/player/{player_id}/mlb_comps")
def get_player_comparisons(player_id: int, db: Session = Depends(get_db)):
    start = time.time()
    comps = ml_service.get_similar_players(db, player_id)
    if not comps:
        raise HTTPException(status_code=404, detail="No similar players found")
    elapsed = time.time() - start
    print(f"[PERF] /mlb_comps for player {player_id} took {elapsed:.2f}s")
    return {"comparisons": comps}

@router.get("/player/{player_id}/prediction")
def get_player_prediction(player_id: int, db: Session = Depends(get_db)):
    prediction = ml_service.predict_mlb_success(db, player_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Player or prediction not found")
    return prediction

@router.get("/model/metrics")
def get_model_metrics():
    return ml_service.metrics

@router.post("/features/populate")
def populate_player_features(db: Session = Depends(get_db)):
    count = 0
    players = db.query(Player).all()
    for player in players:
        pid = getattr(player, 'id', None)
        if not isinstance(pid, int):
            continue
        feats = ml_service.extract_player_features(db, pid)
        if feats is None:
            continue
        pf = db.query(PlayerFeatures).filter_by(player_id=pid).first()
        if pf:
            pf.raw_features = feats['raw']
            pf.normalized_features = feats['normalized']
        else:
            pf = PlayerFeatures(
                player_id=pid,
                raw_features=feats['raw'],
                normalized_features=feats['normalized']
            )
            db.add(pf)
        count += 1
    db.commit()
    ml_service.refresh_feature_cache(db)
    return {"status": "success", "players_processed": count}

@router.get("/players/ratings")
def get_all_players_ratings(db: Session = Depends(get_db)):
    # Join Player and PlayerRatings to include full_name
    ratings = db.query(PlayerRatings, Player.full_name).join(Player, PlayerRatings.player_id == Player.id).all()
    results = []
    for rating, full_name in ratings:
        row = {c.name: getattr(rating, c.name) for c in rating.__table__.columns}
        row["full_name"] = full_name
        results.append(row)
    return results

@router.post("/ratings/populate")
def populate_player_ratings_and_features(db: Session = Depends(get_db)):
    count = 0
    updated = 0
    players = db.query(Player).all()
    for player in players:
        pid = getattr(player, 'id', None)
        if not isinstance(pid, int):
            continue
        # Compute features
        feats = ml_service.extract_player_features(db, pid)
        if feats is not None:
            pf = db.query(PlayerFeatures).filter_by(player_id=pid).first()
            if pf:
                pf.raw_features = feats['raw']
                pf.normalized_features = feats['normalized']
            else:
                pf = PlayerFeatures(
                    player_id=pid,
                    raw_features=feats['raw'],
                    normalized_features=feats['normalized']
                )
                db.add(pf)
        # Compute ratings
        ratings = ml_service.calculate_mlb_show_ratings(db, pid)
        if ratings is None:
            continue
        # Flatten grades for storage
        grades = ratings.get('grades', {})
        # For two-way, flatten both hitting and pitching
        if ratings.get('player_type') == 'two_way':
            hitting = grades.get('hitting', {})
            pitching = grades.get('pitching', {})
            rating_obj = PlayerRatings(
                player_id=pid,
                overall_rating=ratings.get('overall_rating'),
                potential_rating=ratings.get('potential_rating'),
                confidence_score=ratings.get('confidence_score'),
                player_type=ratings.get('player_type'),
                last_updated=datetime.datetime.utcnow(),
                # Hitting
                contact_left=hitting.get('contact_left'),
                contact_right=hitting.get('contact_right'),
                power_left=hitting.get('power_left'),
                power_right=hitting.get('power_right'),
                vision=hitting.get('vision'),
                discipline=hitting.get('discipline'),
                fielding=hitting.get('fielding'),
                arm_strength=hitting.get('arm_strength'),
                arm_accuracy=hitting.get('arm_accuracy'),
                speed=hitting.get('speed'),
                stealing=hitting.get('stealing'),
                # Pitching
                k_rating=pitching.get('k_rating'),
                bb_rating=pitching.get('bb_rating'),
                gb_rating=pitching.get('gb_rating'),
                hr_rating=pitching.get('hr_rating'),
                command_rating=pitching.get('command_rating'),
                # Historical
                historical_overalls=None,  # Optionally, could merge both
                team=player.team,
                level=player.level
            )
        else:
            rating_obj = PlayerRatings(
                player_id=pid,
                overall_rating=ratings.get('overall_rating'),
                potential_rating=ratings.get('potential_rating'),
                confidence_score=ratings.get('confidence_score'),
                player_type=ratings.get('player_type'),
                last_updated=datetime.datetime.utcnow(),
                contact_left=grades.get('contact_left'),
                contact_right=grades.get('contact_right'),
                power_left=grades.get('power_left'),
                power_right=grades.get('power_right'),
                vision=grades.get('vision'),
                discipline=grades.get('discipline'),
                fielding=grades.get('fielding'),
                arm_strength=grades.get('arm_strength'),
                arm_accuracy=grades.get('arm_accuracy'),
                speed=grades.get('speed'),
                stealing=grades.get('stealing'),
                k_rating=grades.get('k_rating'),
                bb_rating=grades.get('bb_rating'),
                gb_rating=grades.get('gb_rating'),
                hr_rating=grades.get('hr_rating'),
                command_rating=grades.get('command_rating'),
                historical_overalls=ratings.get('historical_overalls'),
                team=player.team,
                level=player.level
            )
        # Upsert logic
        existing = db.query(PlayerRatings).filter_by(player_id=pid).first()
        if existing:
            for attr, value in rating_obj.__dict__.items():
                if attr.startswith('_'):
                    continue
                setattr(existing, attr, value)
            updated += 1
        else:
            db.add(rating_obj)
            count += 1
    db.commit()
    ml_service.refresh_feature_cache(db)
    return {"status": "success", "players_created": count, "players_updated": updated} 