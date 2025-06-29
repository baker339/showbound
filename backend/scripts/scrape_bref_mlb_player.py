import requests
from bs4 import BeautifulSoup, Tag
import time
import json

player_urls = [
    # MLB main pages (famous players)
    "https://www.baseball-reference.com/players/b/bettsmo01.shtml",  # Mookie Betts
    "https://www.baseball-reference.com/players/t/troutmi01.shtml",  # Mike Trout
    "https://www.baseball-reference.com/players/j/judgaar01.shtml",  # Aaron Judge
    "https://www.baseball-reference.com/players/s/sotogu01.shtml",  # Juan Soto
    "https://www.baseball-reference.com/players/o/otaan01.shtml",    # Shohei Ohtani
    "https://www.baseball-reference.com/players/a/acunaro01.shtml",  # Ronald Acuña Jr.
    "https://www.baseball-reference.com/players/f/freemfr01.shtml",  # Freddie Freeman
    "https://www.baseball-reference.com/players/a/altuvjo01.shtml",  # Jose Altuve
    "https://www.baseball-reference.com/players/c/correal01.shtml",  # Carlos Correa
    "https://www.baseball-reference.com/players/b/bogeexa01.shtml",  # Xander Bogaerts
    "https://www.baseball-reference.com/players/d/deverra01.shtml",  # Rafael Devers
    "https://www.baseball-reference.com/players/r/ramirjo01.shtml",  # Jose Ramirez
    "https://www.baseball-reference.com/players/b/bryankr01.shtml",  # Kris Bryant
    "https://www.baseball-reference.com/players/h/harpebr03.shtml",  # Bryce Harper
    "https://www.baseball-reference.com/players/t/turnetr01.shtml",  # Trea Turner
    "https://www.baseball-reference.com/players/m/machama01.shtml",  # Manny Machado
    "https://www.baseball-reference.com/players/s/seageco01.shtml",  # Corey Seager
    "https://www.baseball-reference.com/players/b/bichette01.shtml", # Bo Bichette
    "https://www.baseball-reference.com/players/v/vladigu01.shtml", # Vladimir Guerrero Jr.
    "https://www.baseball-reference.com/players/r/realmjt01.shtml",  # J.T. Realmuto
    # Register pages (less famous, prospects, or non-MLB)
    "https://www.baseball-reference.com/register/player.fcgi?id=croche000gar",  # Garret Crochet
    "https://www.baseball-reference.com/register/player.fcgi?id=greenea01aar",  # Aaron Greene
    "https://www.baseball-reference.com/register/player.fcgi?id=adams-000jos",  # Josh Adams
    "https://www.baseball-reference.com/register/player.fcgi?id=smith-002joh",  # John Smith
    "https://www.baseball-reference.com/register/player.fcgi?id=rodrig001jul",  # Julio Rodriguez (prospect)
    "https://www.baseball-reference.com/register/player.fcgi?id=lewis-000ky",  # Kyle Lewis
    "https://www.baseball-reference.com/register/player.fcgi?id=martin001aus",  # Austin Martin
    "https://www.baseball-reference.com/register/player.fcgi?id=torres001gle",  # Gleyber Torres (prospect)
    "https://www.baseball-reference.com/register/player.fcgi?id=adell-000jo",  # Jo Adell
    "https://www.baseball-reference.com/register/player.fcgi?id=abrams000cj",  # CJ Abrams
]

def print_bio_and_tables(player_url):
    print(f"\nFetching player page: {player_url}")
    time.sleep(2)  # Rate limiting
    resp = requests.get(player_url)
    soup = BeautifulSoup(resp.text, 'html.parser')
    player_data = {"source_url": player_url, "bio": {}, "tables": []}

    # Bio extraction from div#info > div#meta
    info_div = soup.find('div', id='info')
    meta_div = info_div.find('div', id='meta') if isinstance(info_div, Tag) else None
    if isinstance(meta_div, Tag):
        for p in meta_div.find_all('p'):
            if not isinstance(p, Tag):
                continue
            strong = p.find('strong')
            if strong:
                label = strong.get_text(strip=True)
                value = p.get_text(strip=True).replace(label, '').strip(': ').strip()
                player_data["bio"][label] = value
            else:
                text = p.get_text(strip=True)
                if text:
                    player_data["bio"][text] = ""
    # Table extraction
    for table_container in soup.find_all('div', class_='table_container'):
        if not isinstance(table_container, Tag):
            continue
        table = table_container.find('table')
        if not isinstance(table, Tag):
            continue
        caption = table.find('caption')
        caption_text = caption.get_text(strip=True) if isinstance(caption, Tag) else 'No Caption'
        headers = [th.get_text(strip=True) for th in table.find_all('th')]
        rows = []
        for row in table.find_all('tr')[1:]:
            if not isinstance(row, Tag):
                continue
            cols = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if cols:
                rows.append(cols)
        player_data["tables"].append({
            "caption": caption_text,
            "headers": headers,
            "rows": rows
        })
    return player_data

all_players_data = []
for i, url in enumerate(player_urls):
    print(f"\n--- [{i+1}/{len(player_urls)}] ---")
    try:
        pdata = print_bio_and_tables(url)
        all_players_data.append(pdata)
    except Exception as e:
        print(f"Error scraping {url}: {e}")

with open("scraped_players.json", "w") as f:
    json.dump(all_players_data, f, indent=2)

print("\nDone. Data saved to scraped_players.json") 