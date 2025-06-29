import requests
from bs4 import BeautifulSoup
import time
import os
import re
import bs4

BASE_URL = "https://www.baseball-reference.com"
AFFILIATES_URL = f"{BASE_URL}/register/affiliates.cgi"
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), '../aaa_player_urls.txt')

# Get all AAA team URLs from the affiliates page
resp = requests.get(AFFILIATES_URL)
soup = BeautifulSoup(resp.text, 'html.parser')
aaa_team_links = []
for a in soup.find_all('a', href=True):
    if not isinstance(a, bs4.element.Tag):
        continue
    row = a.find_parent('tr')
    href = a.get('href', None)
    if isinstance(href, str) and href.startswith('/register/team.cgi') and row and 'AAA' in row.get_text():
        aaa_team_links.append(BASE_URL + href)

player_register_urls = set()
for team_url in aaa_team_links:
    print(f"[AAA TEAM] {team_url}")
    team_resp = requests.get(team_url)
    team_soup = BeautifulSoup(team_resp.text, 'html.parser')
    # Find all player register page links in batting and pitching tables
    for table_id in ['team_batting', 'team_pitching']:
        table = team_soup.find('table', id=table_id)
        if not (table and isinstance(table, bs4.element.Tag)):
            continue
        for a in table.find_all('a', href=True):
            if not isinstance(a, bs4.element.Tag):
                continue
            href = a.get('href', None)
            if isinstance(href, str) and href.startswith('/register/player.fcgi'):
                register_url = BASE_URL + str(href)
                print(f"    [PLAYER REGISTER] {register_url}")
                player_register_urls.add(register_url)
        time.sleep(0.5)
    time.sleep(1)
# Write all unique register URLs to file
with open(OUTPUT_FILE, 'w') as f:
    for url in sorted(player_register_urls):
        f.write(url + '\n')
print(f"Done! {len(player_register_urls)} AAA player register URLs written to {OUTPUT_FILE}") 