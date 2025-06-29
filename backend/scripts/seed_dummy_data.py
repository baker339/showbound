import sys
import os
import random
from datetime import date
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal
from backend.models import Player, StandardBattingStat, ValueBattingStat, AdvancedBattingStat, StandardPitchingStat, ValuePitchingStat, AdvancedPitchingStat, StandardFieldingStat

LEVELS = ["MLB", "AAA", "AA", "A", "Rookie"]
TEAMS = [
    "Yankees", "Dodgers", "Red Sox", "Cubs", "Braves", "Astros", "Mets", "Giants", "Padres", "Cardinals",
    "Rainiers", "Stripers", "IronPigs", "Sounds", "Bisons", "Chihuahuas", "Express", "River Cats", "Isotopes", "Bulls"
]
FIRST_NAMES = ["John", "Mike", "Chris", "Alex", "Ryan", "Tyler", "Matt", "Nick", "Jake", "Josh", "Luis", "Jose", "Carlos", "Will", "Luke", "Zach", "Hunter", "Logan", "Dylan", "Ethan"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez"]

YEARS = [str(y) for y in range(2018, 2024)]

random.seed(42)

def random_stat(low, high, decimals=0):
    val = random.uniform(low, high)
    return round(val, decimals) if decimals else int(val)

def random_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def random_team():
    return random.choice(TEAMS)

def random_level():
    return random.choice(LEVELS)

def seed_players(session, n_players=120):
    players = []
    for _ in range(n_players):
        name = random_name()
        team = random_team()
        level = random_level()
        is_pitcher = random.random() < 0.45  # ~45% pitchers, rest position players
        player = Player(full_name=name, team=team, source_url=f"https://example.com/{name.replace(' ', '').lower()}")
        session.add(player)
        session.flush()
        players.append({
            "obj": player,
            "level": level,
            "is_pitcher": is_pitcher,
            "team": team
        })
    return players

def seed_stats(session, player, years, is_pitcher, team):
    for year in years:
        offset = random.randint(-10, 10)
        if not is_pitcher:
            # Batting
            ev = random.uniform(85, 100)
            barrel_pct = random.uniform(2, 15)
            hardh_pct = random.uniform(25, 55)
            bb_pct = random.uniform(5, 18)
            so_pct = random.uniform(10, 35)
            iso = random.uniform(.100, .350)
            sb = random.randint(0, 40)
            fld_pct = round(random.uniform(.950, .999), 3)
            sb_obj = StandardBattingStat(
                player_id=player.id, season=year, team=team, lg="AL", war=random_stat(0,7,2)+offset/10, g=120+offset, pa=500+offset*2, ab=450+offset*2, r=60+offset, h=120+offset, 
                doubles=25+offset, triples=2+offset//2, hr=15+offset//2, rbi=60+offset, sb=sb, cs=3+offset//3, bb=40+offset, so=70+offset, ba=round(.250+offset/1000,3), obp=round(.320+offset/1000,3), slg=round(.400+offset/1000,3), ops=round(.720+offset/1000,3), ops_plus=100+offset, roba=str(round(.350+offset/1000,3)), rbat_plus=100+offset, tb=200+offset, gidp=7+offset//2, hbp=3+offset//2, sh=0, sf=3+offset//2, ibb=5+offset//2, pos="IF", awards=""
            )
            session.add(sb_obj)
            vb = ValueBattingStat(
                player_id=player.id, season=year, team=team, lg="AL", pa=500+offset*2, rbat=10+offset, rbaser=2+offset/10, rdp=1+offset/10, rfield=3+offset/10, rpos=2+offset/10, raa=12+offset, waa=1+offset/10, rrep=8+offset, rar=15+offset, war=2.5+offset/10, waa_wl_pct=str(round(.500+offset/1000,3)), wl_162_pct=str(round(.480+offset/1000,3)), owar=2.0+offset/10, dwar=0.5+offset/10, orar=10+offset, pos="IF", awards=""
            )
            session.add(vb)
            ab = AdvancedBattingStat(
                player_id=player.id, season=year, team=team, lg="AL", pa=500+offset*2, roba=str(round(.350+offset/1000,3)), rbat_plus=100+offset, babip=str(round(.300+offset/1000,3)), iso=str(round(iso,3)), hr_pct=str(round(barrel_pct,2)), so_pct=str(round(so_pct,2)), bb_pct=str(round(bb_pct,2)), ev=str(round(ev,2)), hardh_pct=str(round(hardh_pct,2)), ld_pct=str(round(20.0+offset/10,2)), gb_pct=str(round(40.0+offset/10,2)), fb_pct=str(round(40.0+offset/10,2)), gb_fb=str(round(1.00+offset/100,3)), pull_pct=str(round(40.0+offset/10,2)), cent_pct=str(round(33.0+offset/10,2)), oppo_pct=str(round(27.0+offset/10,2)), wpa=str(round(1.0+offset/10,2)), cwpa=str(round(0.4+offset/10,2)), re24=str(round(10.0+offset,2)), rs_pct=str(round(10.0+offset/10,2)), sb_pct=str(round(75.0+offset,2)), xbt_pct=str(round(50.0+offset,2)), pos="IF", awards=""
            )
            session.add(ab)
        if is_pitcher:
            # Pitching
            ev = random.uniform(85, 100)
            barrel_pct = random.uniform(1, 10)
            hardh_pct = random.uniform(20, 50)
            bb_pct = random.uniform(4, 15)
            so_pct = random.uniform(10, 35)
            iso = random.uniform(.050, .250)
            fld_pct = round(random.uniform(.950, .999), 3)
            sp = StandardPitchingStat(
                player_id=player.id, season=year, team=team, lg="AL", w=8+offset//2, l=8+offset//3, wl_pct=str(round(.500+offset/1000,3)), era=str(round(4.00+offset/100,2)), g=25+offset//2, gs=20+offset//2, gf=2+offset//4, cg=1+offset//4, sho=0, sv=0, ip=str(round(120.1+offset*2,1)), h=110+offset, r=50+offset//2, er=45+offset//2, hr=10+offset//3, bb=35+offset//2, ibb=2+offset//5, so=100+offset, hbp=2+offset//5, bk=0, wp=1+offset//5, bf=500+offset*2, era_plus=100+offset, fip=str(round(4.10+offset/100,2)), whip=str(round(1.30+offset/100,2)), h9=str(round(8.2+offset/10,2)), hr9=str(round(1.1+offset/10,2)), bb9=str(round(2.7+offset/10,2)), so9=str(round(7.5+offset/10,2)), so_w=str(round(2.8+offset/10,2)), awards=""
            )
            session.add(sp)
            vp = ValuePitchingStat(
                player_id=player.id, season=year, team=team, lg="AL", waa=0.5+offset/10, war=1.2+offset/10, ra9=str(round(4.10+offset/100,2)), fip=str(round(4.10+offset/100,2)), wpa=str(round(0.5+offset/10,2)), re24=str(round(5.0+offset,2)), cwpa=str(round(0.2+offset/10,2)), raa=5+offset, rrep=8+offset, rar=10+offset, g=25+offset//2, gs=20+offset//2, ip=str(round(120.1+offset*2,1)), bf=500+offset*2, awards=""
            )
            session.add(vp)
            ap = AdvancedPitchingStat(
                player_id=player.id, season=year, team=team, lg="AL", ip=str(round(120.1+offset*2,1)), k_pct=str(round(so_pct,2)), bb_pct=str(round(bb_pct,2)), hr_pct=str(round(barrel_pct,2)), babip=str(round(.290+offset/1000,3)), lob_pct=str(round(.75+offset/1000,3)), era_minus=str(100+offset), fip_minus=str(100+offset), xfip_minus=str(100+offset), siera=str(round(4.10+offset/100,2)), pli=str(round(1.00+offset/100,2)), inli=str(round(0.95+offset/100,2)), gmli=str(round(1.05+offset/100,2)), exli=str(round(0.90+offset/100,2)), wpa=str(round(0.4+offset/10,2)), re24=str(round(5.0+offset,2)), cwpa=str(round(0.1+offset/10,2)), awards=""
            )
            session.add(ap)
        # All players get fielding
        sf = StandardFieldingStat(
            player_id=player.id, season=year, team=team, lg="AL", pos="IF" if not is_pitcher else "P", g=100+offset, gs=90+offset, cg=1+offset//4, inn=str(round(800.0+offset*5,1)), ch=200+offset, po=190+offset, a=8+offset//2, e=2+offset//3, dp=2+offset//3, fld_pct=str(fld_pct), lgfld_pct=str(round(.985+offset/1000,3)), rtot=5+offset, rtot_yr=1+offset//5, rdrs=4+offset, rdrs_yr=1+offset//5, rf9=str(round(2.0+offset/10,2)), lgrf9=str(round(1.9+offset/10,2)), rfg=str(round(1.9+offset/10,2)), lgrfg=str(round(1.8+offset/10,2)), awards=""
        )
        session.add(sf)

def main():
    session = SessionLocal()
    n_players = 120
    print(f"Seeding {n_players} players across all levels...")
    players = seed_players(session, n_players)
    level_counts = {lvl: 0 for lvl in LEVELS}
    pitcher_count = 0
    hitter_count = 0
    total_years = 0
    for p in players:
        n_years = random.randint(3, 5)
        years = random.sample(YEARS, n_years)
        seed_stats(session, p["obj"], years, p["is_pitcher"], p["team"])
        level_counts[p["level"]] += 1
        if p["is_pitcher"]:
            pitcher_count += 1
        else:
            hitter_count += 1
        total_years += n_years
    session.commit()
    print(f"Seeded {n_players} players:")
    for lvl in LEVELS:
        print(f"  {lvl}: {level_counts[lvl]}")
    print(f"Pitchers: {pitcher_count}, Position Players: {hitter_count}")
    print(f"Total player-seasons seeded: {total_years}")
    session.close()

if __name__ == "__main__":
    main() 