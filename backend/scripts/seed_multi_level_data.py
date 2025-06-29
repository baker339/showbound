import random
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.database import SessionLocal, engine
from backend.models import (
    Player, StandardBattingStat, ValueBattingStat, AdvancedBattingStat,
    StandardPitchingStat, ValuePitchingStat, AdvancedPitchingStat,
    StandardFieldingStat
)

# MLB Teams
MLB_TEAMS = [
    'Yankees', 'Red Sox', 'Blue Jays', 'Orioles', 'Rays',
    'Guardians', 'Twins', 'White Sox', 'Tigers', 'Royals',
    'Astros', 'Rangers', 'Mariners', 'Athletics', 'Angels',
    'Braves', 'Phillies', 'Mets', 'Marlins', 'Nationals',
    'Cardinals', 'Brewers', 'Cubs', 'Reds', 'Pirates',
    'Diamondbacks', 'Dodgers', 'Padres', 'Giants', 'Rockies'
]

# Minor League Teams by Level
AAA_TEAMS = [
    'Scranton/Wilkes-Barre RailRiders', 'Worcester Red Sox', 'Buffalo Bisons', 'Norfolk Tides', 'Durham Bulls',
    'Columbus Clippers', 'St. Paul Saints', 'Charlotte Knights', 'Toledo Mud Hens', 'Omaha Storm Chasers',
    'Sugar Land Space Cowboys', 'Round Rock Express', 'Tacoma Rainiers', 'Las Vegas Aviators', 'Salt Lake Bees',
    'Gwinnett Stripers', 'Lehigh Valley IronPigs', 'Syracuse Mets', 'Jacksonville Jumbo Shrimp', 'Rochester Red Wings',
    'Memphis Redbirds', 'Nashville Sounds', 'Iowa Cubs', 'Louisville Bats', 'Indianapolis Indians',
    'Reno Aces', 'Oklahoma City Dodgers', 'El Paso Chihuahuas', 'Sacramento River Cats', 'Albuquerque Isotopes'
]

AA_TEAMS = [
    'Somerset Patriots', 'Portland Sea Dogs', 'New Hampshire Fisher Cats', 'Bowie Baysox', 'Erie SeaWolves',
    'Akron RubberDucks', 'Wichita Wind Surge', 'Birmingham Barons', 'Erie SeaWolves', 'Northwest Arkansas Naturals',
    'Corpus Christi Hooks', 'Frisco RoughRiders', 'Arkansas Travelers', 'Midland RockHounds', 'Rocket City Trash Pandas',
    'Mississippi Braves', 'Reading Fightin Phils', 'Binghamton Rumble Ponies', 'Pensacola Blue Wahoos', 'Harrisburg Senators',
    'Springfield Cardinals', 'Biloxi Shuckers', 'Tennessee Smokies', 'Chattanooga Lookouts', 'Altoona Curve',
    'Amarillo Sod Poodles', 'Tulsa Drillers', 'San Antonio Missions', 'Richmond Flying Squirrels', 'Hartford Yard Goats'
]

A_PLUS_TEAMS = [
    'Hudson Valley Renegades', 'Greenville Drive', 'Vancouver Canadians', 'Aberdeen IronBirds', 'Bowling Green Hot Rods',
    'Lake County Captains', 'Cedar Rapids Kernels', 'Winston-Salem Dash', 'West Michigan Whitecaps', 'Quad Cities River Bandits',
    'Asheville Tourists', 'Hickory Crawdads', 'Everett AquaSox', 'Lansing Lugnuts', 'Inland Empire 66ers',
    'Rome Braves', 'Jersey Shore BlueClaws', 'Brooklyn Cyclones', 'Jupiter Hammerheads', 'Wilmington Blue Rocks',
    'Peoria Chiefs', 'Wisconsin Timber Rattlers', 'South Bend Cubs', 'Dayton Dragons', 'Greensboro Grasshoppers',
    'Hillsboro Hops', 'Great Lakes Loons', 'Fort Wayne TinCaps', 'Eugene Emeralds', 'Spokane Indians'
]

A_TEAMS = [
    'Tampa Tarpons', 'Salem Red Sox', 'Dunedin Blue Jays', 'Delmarva Shorebirds', 'Charleston RiverDogs',
    'Lynchburg Hillcats', 'Fort Myers Mighty Mussels', 'Kannapolis Cannon Ballers', 'Lakeland Flying Tigers', 'Columbia Fireflies',
    'Fayetteville Woodpeckers', 'Down East Wood Ducks', 'Modesto Nuts', 'Stockton Ports', 'Rancho Cucamonga Quakes',
    'Augusta GreenJackets', 'Clearwater Threshers', 'St. Lucie Mets', 'Palm Beach Cardinals', 'Fredericksburg Nationals',
    'Peoria Chiefs', 'Carolina Mudcats', 'Myrtle Beach Pelicans', 'Daytona Tortugas', 'Greensboro Grasshoppers',
    'Visalia Rawhide', 'Lake Elsinore Storm', 'San Jose Giants', 'Fresno Grizzlies', 'Asheville Tourists'
]

RK_TEAMS = [
    'FCL Yankees', 'FCL Red Sox', 'FCL Blue Jays', 'FCL Orioles', 'FCL Rays',
    'ACL Guardians', 'ACL Twins', 'ACL White Sox', 'ACL Tigers', 'ACL Royals',
    'ACL Astros', 'ACL Rangers', 'ACL Mariners', 'ACL Athletics', 'ACL Angels',
    'FCL Braves', 'FCL Phillies', 'FCL Mets', 'FCL Marlins', 'FCL Nationals',
    'FCL Cardinals', 'FCL Brewers', 'FCL Cubs', 'FCL Reds', 'FCL Pirates',
    'ACL Diamondbacks', 'ACL Dodgers', 'ACL Padres', 'ACL Giants', 'ACL Rockies'
]

# Player names (first and last)
FIRST_NAMES = [
    'Mike', 'John', 'David', 'James', 'Robert', 'Michael', 'William', 'Richard', 'Joseph', 'Thomas',
    'Christopher', 'Charles', 'Daniel', 'Matthew', 'Anthony', 'Mark', 'Donald', 'Steven', 'Paul', 'Andrew',
    'Joshua', 'Kenneth', 'Kevin', 'Brian', 'George', 'Edward', 'Ronald', 'Timothy', 'Jason', 'Jeffrey',
    'Ryan', 'Jacob', 'Gary', 'Nicholas', 'Eric', 'Jonathan', 'Stephen', 'Larry', 'Justin', 'Scott',
    'Brandon', 'Benjamin', 'Samuel', 'Frank', 'Gregory', 'Raymond', 'Alexander', 'Patrick', 'Jack', 'Dennis'
]

LAST_NAMES = [
    'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez',
    'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin',
    'Lee', 'Perez', 'Thompson', 'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson',
    'Walker', 'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores',
    'Green', 'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter', 'Roberts'
]

def clear_database():
    """Clear all data from the database"""
    print("Clearing database...")
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM standard_fielding_stats"))
        conn.execute(text("DELETE FROM advanced_pitching_stats"))
        conn.execute(text("DELETE FROM value_pitching_stats"))
        conn.execute(text("DELETE FROM standard_pitching_stats"))
        conn.execute(text("DELETE FROM advanced_batting_stats"))
        conn.execute(text("DELETE FROM value_batting_stats"))
        conn.execute(text("DELETE FROM standard_batting_stats"))
        conn.execute(text("DELETE FROM players"))
        conn.commit()
    print("Database cleared.")

def generate_realistic_batting_stats(level, season=2024):
    """Generate realistic batting stats based on level"""
    if level == 'MLB':
        return {
            'season': season,
            'team': random.choice(MLB_TEAMS),
            'g': random.randint(80, 162),
            'pa': random.randint(300, 700),
            'ab': random.randint(250, 600),
            'r': random.randint(30, 120),
            'h': random.randint(60, 200),
            'doubles': random.randint(10, 50),
            'triples': random.randint(1, 10),
            'hr': random.randint(5, 40),
            'rbi': random.randint(30, 120),
            'sb': random.randint(0, 30),
            'cs': random.randint(0, 10),
            'bb': random.randint(20, 100),
            'so': random.randint(50, 200),
            'ba': round(random.uniform(0.200, 0.350), 3),
            'obp': round(random.uniform(0.280, 0.420), 3),
            'slg': round(random.uniform(0.350, 0.600), 3),
            'ops': round(random.uniform(0.650, 0.950), 3),
            'tb': random.randint(100, 350),
            'gidp': random.randint(5, 25),
            'hbp': random.randint(0, 20),
            'sh': random.randint(0, 10),
            'sf': random.randint(0, 10),
            'ibb': random.randint(0, 15),
            'age': random.randint(22, 35)
        }
    else:
        # Minor league stats (generally lower)
        return {
            'season': season,
            'team': random.choice(AAA_TEAMS if level == 'AAA' else 
                                AA_TEAMS if level == 'AA' else
                                A_PLUS_TEAMS if level == 'A+' else
                                A_TEAMS if level == 'A' else RK_TEAMS),
            'g': random.randint(50, 140),
            'pa': random.randint(200, 500),
            'ab': random.randint(180, 450),
            'r': random.randint(20, 80),
            'h': random.randint(40, 150),
            'doubles': random.randint(8, 35),
            'triples': random.randint(1, 8),
            'hr': random.randint(3, 25),
            'rbi': random.randint(20, 80),
            'sb': random.randint(0, 25),
            'cs': random.randint(0, 8),
            'bb': random.randint(15, 70),
            'so': random.randint(40, 150),
            'ba': round(random.uniform(0.180, 0.320), 3),
            'obp': round(random.uniform(0.250, 0.380), 3),
            'slg': round(random.uniform(0.300, 0.500), 3),
            'ops': round(random.uniform(0.600, 0.850), 3),
            'tb': random.randint(70, 250),
            'gidp': random.randint(3, 20),
            'hbp': random.randint(0, 15),
            'sh': random.randint(0, 8),
            'sf': random.randint(0, 8),
            'ibb': random.randint(0, 10),
            'age': random.randint(18, 28)
        }

def generate_realistic_pitching_stats(level, season=2024):
    """Generate realistic pitching stats based on level"""
    if level == 'MLB':
        return {
            'season': season,
            'team': random.choice(MLB_TEAMS),
            'w': random.randint(5, 20),
            'l': random.randint(3, 15),
            'wl_pct': round(random.uniform(0.300, 0.800), 3),
            'era': round(random.uniform(2.50, 5.50), 2),
            'g': random.randint(20, 70),
            'gs': random.randint(0, 35),
            'gf': random.randint(0, 50),
            'cg': random.randint(0, 3),
            'sho': random.randint(0, 2),
            'sv': random.randint(0, 40),
            'ip': round(random.uniform(50, 200), 1),
            'h': random.randint(40, 200),
            'r': random.randint(20, 100),
            'er': random.randint(15, 80),
            'hr': random.randint(5, 30),
            'bb': random.randint(15, 80),
            'ibb': random.randint(0, 10),
            'so': random.randint(30, 200),
            'hbp': random.randint(0, 15),
            'bk': random.randint(0, 3),
            'wp': random.randint(0, 10),
            'bf': random.randint(200, 800),
            'era_plus': random.randint(80, 150),
            'fip': round(random.uniform(3.00, 5.50), 2),
            'whip': round(random.uniform(1.10, 1.50), 2),
            'h9': round(random.uniform(7.0, 10.0), 1),
            'hr9': round(random.uniform(0.5, 1.5), 1),
            'bb9': round(random.uniform(2.0, 4.5), 1),
            'so9': round(random.uniform(6.0, 11.0), 1),
            'so_w': round(random.uniform(1.5, 4.0), 1),
            'age': random.randint(22, 35)
        }
    else:
        # Minor league stats
        return {
            'season': season,
            'team': random.choice(AAA_TEAMS if level == 'AAA' else 
                                AA_TEAMS if level == 'AA' else
                                A_PLUS_TEAMS if level == 'A+' else
                                A_TEAMS if level == 'A' else RK_TEAMS),
            'w': random.randint(3, 15),
            'l': random.randint(2, 12),
            'wl_pct': round(random.uniform(0.250, 0.750), 3),
            'era': round(random.uniform(2.00, 6.00), 2),
            'g': random.randint(15, 50),
            'gs': random.randint(0, 25),
            'gf': random.randint(0, 30),
            'cg': random.randint(0, 2),
            'sho': random.randint(0, 1),
            'sv': random.randint(0, 25),
            'ip': round(random.uniform(30, 150), 1),
            'h': random.randint(25, 150),
            'r': random.randint(15, 80),
            'er': random.randint(10, 60),
            'hr': random.randint(3, 20),
            'bb': random.randint(10, 60),
            'ibb': random.randint(0, 8),
            'so': random.randint(20, 150),
            'hbp': random.randint(0, 12),
            'bk': random.randint(0, 2),
            'wp': random.randint(0, 8),
            'bf': random.randint(150, 600),
            'era_plus': random.randint(70, 130),
            'fip': round(random.uniform(2.50, 6.00), 2),
            'whip': round(random.uniform(1.00, 1.60), 2),
            'h9': round(random.uniform(6.5, 11.0), 1),
            'hr9': round(random.uniform(0.3, 1.8), 1),
            'bb9': round(random.uniform(1.8, 5.0), 1),
            'so9': round(random.uniform(5.0, 12.0), 1),
            'so_w': round(random.uniform(1.2, 4.5), 1),
            'age': random.randint(18, 28)
        }

def generate_realistic_fielding_stats(level, season=2024):
    """Generate realistic fielding stats based on level"""
    positions = ['C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF', 'P']
    pos = random.choice(positions)
    
    if level == 'MLB':
        return {
            'season': season,
            'team': random.choice(MLB_TEAMS),
            'pos': pos,
            'g': random.randint(50, 162),
            'gs': random.randint(30, 150),
            'cg': random.randint(0, 10),
            'inn': round(random.uniform(200, 1400), 1),
            'ch': random.randint(50, 500),
            'po': random.randint(30, 400),
            'a': random.randint(10, 200),
            'e': random.randint(0, 20),
            'dp': random.randint(0, 50),
            'fld_pct': round(random.uniform(0.950, 1.000), 3),
            'lgfld_pct': round(random.uniform(0.950, 1.000), 3),
            'rtot': random.randint(-15, 15),
            'rtot_yr': random.randint(-15, 15),
            'rdrs': random.randint(-15, 15),
            'rdrs_yr': random.randint(-15, 15),
            'rf9': round(random.uniform(1.5, 3.5), 1),
            'lgrf9': round(random.uniform(1.5, 3.5), 1),
            'rfg': round(random.uniform(1.5, 3.5), 1),
            'lgrfg': round(random.uniform(1.5, 3.5), 1),
            'age': random.randint(22, 35)
        }
    else:
        return {
            'season': season,
            'team': random.choice(AAA_TEAMS if level == 'AAA' else 
                                AA_TEAMS if level == 'AA' else
                                A_PLUS_TEAMS if level == 'A+' else
                                A_TEAMS if level == 'A' else RK_TEAMS),
            'pos': pos,
            'g': random.randint(30, 120),
            'gs': random.randint(20, 100),
            'cg': random.randint(0, 8),
            'inn': round(random.uniform(150, 1000), 1),
            'ch': random.randint(30, 350),
            'po': random.randint(20, 300),
            'a': random.randint(8, 150),
            'e': random.randint(0, 25),
            'dp': random.randint(0, 40),
            'fld_pct': round(random.uniform(0.930, 0.995), 3),
            'lgfld_pct': round(random.uniform(0.930, 0.995), 3),
            'rtot': random.randint(-20, 20),
            'rtot_yr': random.randint(-20, 20),
            'rdrs': random.randint(-20, 20),
            'rdrs_yr': random.randint(-20, 20),
            'rf9': round(random.uniform(1.2, 3.8), 1),
            'lgrf9': round(random.uniform(1.2, 3.8), 1),
            'rfg': round(random.uniform(1.2, 3.8), 1),
            'lgrfg': round(random.uniform(1.2, 3.8), 1),
            'age': random.randint(18, 28)
        }

def create_player_with_stats(session, level, player_id):
    """Create a player with realistic stats for their level, with multiple seasons"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    full_name = f"{first_name} {last_name}"
    
    # Determine position first
    primary_position = random.choice(['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF'])
    is_pitcher = primary_position == 'P'
    
    # Create player
    player = Player(
        full_name=full_name,
        birth_date=datetime.now() - timedelta(days=random.randint(6570, 12775)),  # 18-35 years old
        primary_position=primary_position,
        bats=random.choice(['L', 'R', 'S']),
        throws=random.choice(['L', 'R']),
        height=f"{random.randint(5, 6)}-{random.randint(8, 11)}",
        weight=random.randint(160, 250),
        team=random.choice(MLB_TEAMS if level == 'MLB' else 
                          AAA_TEAMS if level == 'AAA' else
                          AA_TEAMS if level == 'AA' else
                          A_PLUS_TEAMS if level == 'A+' else
                          A_TEAMS if level == 'A' else RK_TEAMS),
        level=level,
        source_url=f"https://example.com/player/{player_id}"
    )
    session.add(player)
    session.flush()  # Get the ID

    # Generate a random number of seasons (1-8)
    num_seasons = random.randint(1, 8)
    current_year = 2024
    start_year = current_year - num_seasons + 1
    years = list(range(start_year, current_year + 1))

    for idx, year in enumerate(years):
        # Age increases each season
        age = 18 if level != 'MLB' else 22
        age = age + idx + random.randint(0, 2)
        # Team can change each season
        team = random.choice(MLB_TEAMS if level == 'MLB' else 
                             AAA_TEAMS if level == 'AAA' else
                             AA_TEAMS if level == 'AA' else
                             A_PLUS_TEAMS if level == 'A+' else
                             A_TEAMS if level == 'A' else RK_TEAMS)
        
        # MLB players get standard, value, and advanced stats
        if level == 'MLB':
            batting_stats = generate_realistic_batting_stats(level, season=year)
            batting_stats['player_id'] = player.id
            batting_stats['team'] = team
            batting_stats['age'] = age
            session.add(StandardBattingStat(**batting_stats))
            
            # Value batting stats
            value_batting = {
                'player_id': player.id,
                'season': year,
                'team': team,
                'pa': batting_stats['pa'],
                'rbat': random.randint(-30, 30),
                'rbaser': random.randint(-10, 15),
                'rdp': random.randint(-10, 5),
                'rfield': random.randint(-15, 20),
                'rpos': random.randint(-5, 10),
                'raa': random.randint(-40, 50),
                'waa': round(random.uniform(-4.0, 5.0), 1),
                'rrep': random.randint(20, 40),
                'rar': random.randint(-20, 60),
                'war': round(random.uniform(-2.0, 7.0), 1),
                'waa_wl_pct': round(random.uniform(0.400, 0.600), 3),
                'wl_162_pct': round(random.uniform(0.400, 0.600), 3),
                'owar': round(random.uniform(-1.0, 5.0), 1),
                'dwar': round(random.uniform(-1.0, 3.0), 1),
                'orar': random.randint(-10, 40),
                'age': age
            }
            session.add(ValueBattingStat(**value_batting))
            
            # Advanced batting stats
            advanced_batting = {
                'player_id': player.id,
                'season': year,
                'team': team,
                'pa': batting_stats['pa'],
                'roba': round(random.uniform(0.280, 0.420), 3),
                'rbat_plus': random.randint(80, 130),
                'babip': round(random.uniform(0.250, 0.350), 3),
                'iso': round(random.uniform(0.100, 0.300), 3),
                'hr_pct': round(random.uniform(1.0, 8.0), 1),
                'so_pct': round(random.uniform(10.0, 30.0), 1),
                'bb_pct': round(random.uniform(5.0, 15.0), 1),
                'ev': round(random.uniform(85.0, 95.0), 1),
                'hardh_pct': round(random.uniform(25.0, 45.0), 1),
                'ld_pct': round(random.uniform(15.0, 25.0), 1),
                'gb_pct': round(random.uniform(35.0, 55.0), 1),
                'fb_pct': round(random.uniform(25.0, 45.0), 1),
                'gb_fb': round(random.uniform(0.5, 2.0), 1),
                'pull_pct': round(random.uniform(30.0, 50.0), 1),
                'cent_pct': round(random.uniform(20.0, 40.0), 1),
                'oppo_pct': round(random.uniform(15.0, 35.0), 1),
                'wpa': round(random.uniform(-3.0, 3.0), 2),
                'cwpa': round(random.uniform(-0.05, 0.05), 3),
                're24': round(random.uniform(-20.0, 30.0), 1),
                'rs_pct': round(random.uniform(30.0, 70.0), 1),
                'sb_pct': round(random.uniform(60.0, 90.0), 1),
                'xbt_pct': round(random.uniform(30.0, 60.0), 1),
                'age': age
            }
            session.add(AdvancedBattingStat(**advanced_batting))
            
            # Pitching stats for pitchers
            if is_pitcher:
                pitching_stats = generate_realistic_pitching_stats(level, season=year)
                pitching_stats['player_id'] = player.id
                pitching_stats['team'] = team
                pitching_stats['age'] = age
                session.add(StandardPitchingStat(**pitching_stats))
                
                value_pitching = {
                    'player_id': player.id,
                    'season': year,
                    'team': team,
                    'ip': pitching_stats['ip'],
                    'g': pitching_stats['g'],
                    'gs': pitching_stats['gs'],
                    'ra9': round(random.uniform(3.0, 6.0), 2),
                    'fip': round(random.uniform(3.0, 5.5), 2),
                    'wpa': round(random.uniform(-2.0, 2.0), 2),
                    're24': round(random.uniform(-15.0, 20.0), 1),
                    'cwpa': round(random.uniform(-0.03, 0.03), 3),
                    'raa': random.randint(-30, 40),
                    'rrep': random.randint(15, 35),
                    'rar': random.randint(-15, 50),
                    'waa': round(random.uniform(-3.0, 4.0), 1),
                    'war': round(random.uniform(-1.0, 5.0), 1),
                    'bf': pitching_stats['bf'],
                    'age': age,
                    'g': pitching_stats['g'],
                    'gs': pitching_stats['gs']
                }
                session.add(ValuePitchingStat(**value_pitching))
                
                advanced_pitching = {
                    'player_id': player.id,
                    'season': year,
                    'team': team,
                    'ip': pitching_stats['ip'],
                    'k_pct': round(random.uniform(15.0, 30.0), 1),
                    'bb_pct': round(random.uniform(5.0, 12.0), 1),
                    'hr_pct': round(random.uniform(2.0, 8.0), 1),
                    'babip': round(random.uniform(0.250, 0.320), 3),
                    'lob_pct': round(random.uniform(65.0, 85.0), 1),
                    'era_minus': round(random.uniform(70.0, 130.0), 1),
                    'fip_minus': round(random.uniform(70.0, 130.0), 1),
                    'xfip_minus': round(random.uniform(70.0, 130.0), 1),
                    'siera': round(random.uniform(3.0, 5.5), 2),
                    'pli': round(random.uniform(0.8, 1.2), 2),
                    'inli': round(random.uniform(0.8, 1.2), 2),
                    'gmli': round(random.uniform(0.8, 1.2), 2),
                    'exli': round(random.uniform(0.8, 1.2), 2),
                    'wpa': round(random.uniform(-2.0, 2.0), 2),
                    're24': round(random.uniform(-15.0, 20.0), 1),
                    'cwpa': round(random.uniform(-0.03, 0.03), 3),
                    'age': age
                }
                session.add(AdvancedPitchingStat(**advanced_pitching))
            
            # Fielding stats
            fielding_stats = generate_realistic_fielding_stats(level, season=year)
            fielding_stats['player_id'] = player.id
            fielding_stats['team'] = team
            fielding_stats['age'] = age
            session.add(StandardFieldingStat(**fielding_stats))
        else:
            # Minor league players only get standard stats (mapped from register tables)
            batting_stats = generate_realistic_batting_stats(level, season=year)
            batting_stats['player_id'] = player.id
            batting_stats['team'] = team
            batting_stats['age'] = age
            session.add(StandardBattingStat(**batting_stats))
            
            if is_pitcher:
                pitching_stats = generate_realistic_pitching_stats(level, season=year)
                pitching_stats['player_id'] = player.id
                pitching_stats['team'] = team
                pitching_stats['age'] = age
                session.add(StandardPitchingStat(**pitching_stats))
            
            fielding_stats = generate_realistic_fielding_stats(level, season=year)
            fielding_stats['player_id'] = player.id
            fielding_stats['team'] = team
            fielding_stats['age'] = age
            session.add(StandardFieldingStat(**fielding_stats))

def main():
    """Main function to seed the database with multi-level data"""
    print("Starting multi-level data seeding...")
    
    # Clear the database
    clear_database()
    
    session = SessionLocal()
    
    try:
        # Create 30 players for each level
        levels = ['MLB', 'AAA', 'AA', 'A+', 'A', 'Rk']
        player_id = 1
        
        for level in levels:
            print(f"Creating 30 {level} players...")
            for i in range(30):
                create_player_with_stats(session, level, player_id)
                player_id += 1
                if (i + 1) % 10 == 0:
                    print(f"  Created {i + 1}/30 {level} players")
        
        # Commit all changes
        session.commit()
        
        # Print summary
        total_players = session.query(Player).count()
        mlb_players = session.query(Player).filter_by(level='MLB').count()
        aaa_players = session.query(Player).filter_by(level='AAA').count()
        aa_players = session.query(Player).filter_by(level='AA').count()
        a_plus_players = session.query(Player).filter_by(level='A+').count()
        a_players = session.query(Player).filter_by(level='A').count()
        rk_players = session.query(Player).filter_by(level='Rk').count()
        
        print(f"\nDatabase seeding complete!")
        print(f"Total players: {total_players}")
        print(f"MLB players: {mlb_players}")
        print(f"AAA players: {aaa_players}")
        print(f"AA players: {aa_players}")
        print(f"A+ players: {a_plus_players}")
        print(f"A players: {a_players}")
        print(f"Rk players: {rk_players}")
        
        # Print some sample players
        print(f"\nSample players by level:")
        for level in levels:
            player = session.query(Player).filter_by(level=level).first()
            if player:
                print(f"  {level}: {player.full_name} ({player.team})")
        
    except Exception as e:
        print(f"Error during seeding: {e}")
        session.rollback()
        raise
    finally:
        session.close()

if __name__ == '__main__':
    main() 