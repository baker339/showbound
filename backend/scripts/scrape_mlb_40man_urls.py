import requests
from bs4 import BeautifulSoup, Comment, Tag
import time
import os

BASE_URL = "https://www.baseball-reference.com"
TEAMS_URL = f"{BASE_URL}/teams/"
OUTPUT_FILE = "player_url_lists/mlb_40man_player_urls.txt"


def get_soup(url):
    time.sleep(3)  # Be polite, avoid rate limiting
    resp = requests.get(url)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def get_active_team_links():
    soup = get_soup(TEAMS_URL)
    # Find the Active Franchises table by id
    table = soup.find("table", id="active_franchises")
    if not table:
        # Fallback: first table after 'Active Franchises' header
        h2 = soup.find("h2", string="Active Franchises")
        table = h2.find_next("table") if h2 else None
    links = []
    seen = set()
    if not table or not isinstance(table, Tag):
        print("[ERROR] Could not find Active Franchises table.")
        return links
    for row in table.find_all("tr"):
        if not isinstance(row, Tag):
            continue
        a = row.find("a", href=True)
        if a and isinstance(a, Tag) and 'href' in a.attrs:
            href = a['href']
            if isinstance(href, str) and href.startswith("/teams/"):
                parts = href.strip('/').split('/')
                if len(parts) >= 2:
                    team_code = parts[1]
                    if team_code not in seen:
                        links.append(BASE_URL + href)
                        seen.add(team_code)
    return links


def get_most_recent_year_url(team_url):
    soup = get_soup(team_url)
    # Try to find the Franchise History table by id
    table = soup.find("table", id="franchise_years")
    if not table:
        # Sometimes the table is in HTML comments as a div with id='all_franchise_years'
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if not isinstance(comment, str):
                continue
            comment_soup = BeautifulSoup(comment, "html.parser")
            table = comment_soup.find("table", id="franchise_years")
            if table:
                break
    if not table or not isinstance(table, Tag):
        return None
    # Find the first non-header row
    for row in table.find_all("tr"):
        if not isinstance(row, Tag):
            continue
        row_class = row.get("class")
        if isinstance(row_class, list) and "thead" in row_class:
            continue
        year_link = row.find("a", href=True)
        if year_link and isinstance(year_link, Tag) and 'href' in year_link.attrs:
            href = year_link['href']
            if isinstance(href, str) and href.startswith("/teams/"):
                return BASE_URL + href
    return None


def get_40man_player_urls(year_url):
    soup = get_soup(year_url)
    # Try to find the 40-man roster table by id
    table = soup.find("table", id="the40man")
    if not table:
        # Sometimes the table is in HTML comments as a div with id='div_the40man'
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        for comment in comments:
            if not isinstance(comment, str):
                continue
            comment_soup = BeautifulSoup(comment, "html.parser")
            div = comment_soup.find("div", id="div_the40man")
            if div and isinstance(div, Tag):
                table = div.find("table", id="the40man")
                if table:
                    break
    if not table or not isinstance(table, Tag):
        return []
    player_urls = set()
    for a in table.find_all("a", href=True):
        if not isinstance(a, Tag):
            continue
        href = a.get("href")
        if isinstance(href, str) and href.startswith("/players/") and href.endswith(".shtml"):
            player_urls.add(BASE_URL + href)
    return list(player_urls)


def main():
    print("[INFO] Scraping all MLB 40-man roster player URLs...")
    team_links = get_active_team_links()
    print(f"[INFO] Found {len(team_links)} active MLB teams.")
    all_player_urls = set()
    for team_url in team_links:
        print(f"[INFO] Processing team: {team_url}")
        year_url = get_most_recent_year_url(team_url)
        if not year_url:
            print(f"[WARN] Could not find most recent year for {team_url}")
            continue
        print(f"[INFO] Most recent year URL: {year_url}")
        player_urls = get_40man_player_urls(year_url)
        print(f"[INFO] Found {len(player_urls)} player URLs for this team.")
        all_player_urls.update(player_urls)
    print(f"[INFO] Total unique player URLs: {len(all_player_urls)}")
    # Ensure output directory exists
    output_dir = os.path.dirname(OUTPUT_FILE)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    # Write to file, replacing any existing content
    with open(OUTPUT_FILE, "w") as f:
        for url in sorted(all_player_urls):
            f.write(url + "\n")
    print(f"[INFO] Player URLs written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main() 