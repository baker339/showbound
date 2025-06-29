import requests
from bs4 import BeautifulSoup, Comment
import time
import os
import re
import bs4

BASE_URL = "https://www.baseball-reference.com"
AFFILIATES_URL = f"{BASE_URL}/register/affiliate.cgi?year=2025"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '../player_url_lists')
LEVELS = ['MLB', 'AAA', 'AA', 'A+', 'A', 'Rk', 'UNKNOWN']

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_soup(url):
    resp = requests.get(url, headers=HEADERS)
    print(f"[DEBUG] GET {url} -> {resp.status_code}")
    resp.raise_for_status()
    time.sleep(2)  # Lowered sleep time
    return BeautifulSoup(resp.text, 'html.parser')

def get_player_type_and_overview(register_url):
    soup = get_soup(register_url)
    # Check for overview link
    overview_url = None
    for a in soup.find_all('a', href=True):
        if not isinstance(a, bs4.element.Tag):
            continue
        href = a.get('href', None)
        if isinstance(href, str) and href.startswith('/players/') and a.get_text(strip=True).endswith('Overview'):
            overview_url = BASE_URL + str(href)
            break
    # Check team in bio
    meta_div = soup.find('div', id='meta')
    team_type = None
    if meta_div:
        for p in meta_div.find_all('p'):
            strong = p.find('strong')
            if strong and 'Team' in strong.get_text(strip=True):
                value = p.get_text(strip=True)
                if '(majors)' in value:
                    team_type = 'majors'
                elif '(minors)' in value:
                    team_type = 'minors'
    # Parse Standard Roster table for highest level
    highest_level = None
    teams_table = soup.find('table', id='standard_roster')
    if not teams_table:
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if 'standard_roster' in comment:
                comment_soup = BeautifulSoup(comment, 'html.parser')
                teams_table = comment_soup.find('table', id='standard_roster')
                if teams_table:
                    break
    if teams_table:
        levels = set()
        for row in teams_table.find_all('tr'):
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if len(cells) >= 5:
                lvl = cells[4]  # Level column
                if lvl:
                    levels.add(lvl)
        order = ['MLB', 'AAA', 'AA', 'A+', 'A', 'Rk', 'FRk']
        for lvl in order:
            if lvl in levels:
                highest_level = lvl
                break
    return team_type, overview_url, highest_level

def extract_player_links_from_div(soup, div_id):
    links = set()
    div = soup.find('div', id=div_id)
    if div:
        table = div.find('table')
        if table:
            player_links = table.find_all('a', href=True)
            for a in player_links:
                href = a.get('href', '')
                if href.startswith('/register/player.fcgi'):
                    links.add(BASE_URL + href)
    return links

def extract_player_links_from_comments(soup, div_id):
    links = set()
    comments = soup.find_all(string=lambda text: isinstance(text, Comment))
    for comment in comments:
        if div_id in comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            links.update(extract_player_links_from_div(comment_soup, div_id))
    return links

def extract_all_player_links(team_soup):
    all_links = set()
    for div_id in ['div_team_batting', 'div_team_pitching']:
        links = extract_player_links_from_div(team_soup, div_id)
        if not links:
            links = extract_player_links_from_comments(team_soup, div_id)
        all_links.update(links)
    return all_links

def categorize_player_by_level(register_url):
    try:
        team_type, overview_url, highest_level = get_player_type_and_overview(register_url)
        print(f"    [PLAYER] {register_url}")
        print(f"      [TYPE] {team_type} [LEVEL] {highest_level}")
        if team_type == 'majors' and overview_url:
            return 'MLB', overview_url
        elif highest_level == 'MLB':
            return 'MLB', overview_url if overview_url else register_url
        elif highest_level == 'AAA':
            return 'AAA', register_url
        elif highest_level == 'AA':
            return 'AA', register_url
        elif highest_level == 'A+':
            return 'A+', register_url
        elif highest_level == 'A':
            return 'A', register_url
        elif highest_level in ['Rk', 'FRk']:
            return 'Rk', register_url
        else:
            if team_type == 'majors':
                return 'MLB', overview_url if overview_url else register_url
            else:
                return 'AAA', register_url
    except Exception as e:
        print(f"      [ERROR] {e}")
        return 'UNKNOWN', register_url

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    aff_soup = get_soup(AFFILIATES_URL)
    aff_table = aff_soup.find('table', id='affiliates')
    team_links = []
    if aff_table:
        for row in aff_table.find_all('tr'):
            th = row.find('th', {'data-stat': 'franch_name'})
            if th:
                a = th.find('a', href=True)
                if a and a['href'].startswith('/register/affiliate.cgi?id='):
                    team_links.append(BASE_URL + a['href'])
    print(f"[DEBUG] Found {len(team_links)} team links.")
    categorized_players = {level: set() for level in LEVELS}
    for team_url in team_links:
        print(f"[TEAM] {team_url}")
        team_soup = get_soup(team_url)
        player_links = extract_all_player_links(team_soup)
        print(f"  [DEBUG] Found {len(player_links)} player links on team page.")
        for register_url in player_links:
            level, final_url = categorize_player_by_level(register_url)
            categorized_players[level].add(final_url)
            time.sleep(2)  # Lowered sleep time
        time.sleep(2)
    # Write to separate files
    for level, urls in categorized_players.items():
        if urls:
            filename = os.path.join(OUTPUT_DIR, f'{level.lower()}_player_urls.txt')
            with open(filename, 'w') as f:
                for url in sorted(urls):
                    f.write(url + '\n')
            print(f"[OUTPUT] {len(urls)} {level} players written to {filename}")
    print("\n[SUMMARY] Player categorization:")
    for level, urls in categorized_players.items():
        if urls:
            print(f"  {level}: {len(urls)} players")

if __name__ == '__main__':
    main() 