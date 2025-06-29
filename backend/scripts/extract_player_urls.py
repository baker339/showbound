import requests
from bs4 import BeautifulSoup
import re
import time

def get_player_urls():
    url = "https://www.baseball-reference.com/players/"
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, 'html.parser')
    
    # Find all links that match player URL pattern
    player_links = []
    
    # Look for links in the player index sections
    for link in soup.find_all('a', href=True):
        href = str(link.get('href', ''))
        # Check if it's a player URL pattern
        if re.match(r'/players/[a-z]/[a-z]+[0-9]{2}\.shtml', href):
            full_url = f"https://www.baseball-reference.com{href}"
            player_name = link.get_text(strip=True)
            # Check if it's bold (active player)
            is_active = link.find_parent('strong') is not None
            player_links.append({
                'name': player_name,
                'url': full_url,
                'active': is_active
            })
    
    return player_links

def main():
    print("Extracting player URLs from Baseball Reference...")
    try:
        players = get_player_urls()
        
        print(f"Found {len(players)} total players")
        active_players = [p for p in players if p['active']]
        print(f"Found {len(active_players)} active players")
        
        # Write URLs to file
        with open('backend/player_urls.txt', 'w') as f:
            for player in active_players[:50]:  # Limit to first 50 active players
                f.write(f"{player['url']}\n")
                print(f"Added: {player['name']} - {player['url']}")
        
        print(f"\nWrote {min(50, len(active_players))} active player URLs to backend/player_urls.txt")
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            print("Rate limited by Baseball Reference. Waiting 60 seconds...")
            time.sleep(60)
            print("Retrying...")
            players = get_player_urls()
            # Continue with the rest of the logic...
        else:
            raise e

if __name__ == '__main__':
    main() 