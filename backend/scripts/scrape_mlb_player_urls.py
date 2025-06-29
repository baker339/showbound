import requests
from bs4 import BeautifulSoup
import time
import os
import re
import bs4

BASE_URL = "https://www.baseball-reference.com"
MLB_TEAMS_URL = f"{BASE_URL}/teams/"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../mlb_player_urls.txt')

# Get all MLB team URLs from the teams page
resp = requests.get(MLB_TEAMS_URL)
soup = BeautifulSoup(resp.text, 'html.parser')
team_links = []
for a in soup.select('table#teams_active a[href^="/teams/"]'):
    if not isinstance(a, bs4.element.Tag):
        continue
    href = a.get('href', None)
    if isinstance(href, str) and re.match(r"/teams/[A-Z]{3}/$", href):
        team_links.append(BASE_URL + str(href))

player_overview_urls = set()
for team_url in team_links:
    print(f"[TEAM] {team_url}")
    # Go to the team page, find the current year roster link
    team_resp = requests.get(team_url)
    team_soup = BeautifulSoup(team_resp.text, 'html.parser')
    roster_link = None
    for a in team_soup.find_all('a', href=True):
        if a.get_text(strip=True).lower() == 'roster':
            roster_link = BASE_URL + a['href']
            break
    if not roster_link:
        print(f"  [WARN] No roster link found for {team_url}")
        continue
    # Visit the roster page
    roster_resp = requests.get(roster_link)
    roster_soup = BeautifulSoup(roster_resp.text, 'html.parser')
    # Find all player register page links
    for a in roster_soup.find_all('a', href=True):
        if not isinstance(a, bs4.element.Tag):
            continue
        href = a.get('href', None)
        if isinstance(href, str) and href.startswith('/register/player.fcgi'):
            register_url = BASE_URL + str(href)
            print(f"    [PLAYER REGISTER] {register_url}")
            # Visit the register page
            reg_resp = requests.get(register_url)
            reg_soup = BeautifulSoup(reg_resp.text, 'html.parser')
            # Find the overview page link
            overview_link = None
            for a2 in reg_soup.find_all('a', href=True):
                if not isinstance(a2, bs4.element.Tag):
                    continue
                href2 = a2.get('href', None)
                if isinstance(href2, str) and href2.startswith('/players/') and a2.get_text(strip=True).endswith('Overview'):
                    overview_link = BASE_URL + str(href2)
                    break
            if overview_link:
                print(f"      [OVERVIEW] {overview_link}")
                player_overview_urls.add(overview_link)
            time.sleep(0.5)
    time.sleep(1)
# Write all unique overview URLs to file
with open(OUTPUT_FILE, 'w') as f:
    for url in sorted(player_overview_urls):
        f.write(url + '\n')
print(f"Done! {len(player_overview_urls)} MLB player overview URLs written to {OUTPUT_FILE}") 