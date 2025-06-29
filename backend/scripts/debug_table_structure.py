#!/usr/bin/env python3

import requests
from bs4 import BeautifulSoup, Comment
import time

BASE_URL = "https://www.baseball-reference.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def get_soup(url):
    resp = requests.get(url, headers=HEADERS)
    print(f"[DEBUG] GET {url} -> {resp.status_code}")
    resp.raise_for_status()
    time.sleep(5)
    return BeautifulSoup(resp.text, 'html.parser')

def main():
    # Test with one player URL
    player_url = "https://www.baseball-reference.com/register/player.fcgi?id=rosari000nai"
    
    print(f"[PLAYER] {player_url}")
    soup = get_soup(player_url)
    
    # Look for standard_roster table in main HTML
    table = soup.find('table', id='standard_roster')
    if table:
        print("[DEBUG] Found standard_roster table in main HTML")
    else:
        print("[DEBUG] standard_roster table not found in main HTML")
        
        # Check in HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))
        found_in_comments = False
        for comment in comments:
            if 'standard_roster' in comment:
                print("[DEBUG] Found standard_roster in HTML comment")
                comment_soup = BeautifulSoup(comment, 'html.parser')
                table = comment_soup.find('table', id='standard_roster')
                if table:
                    found_in_comments = True
                    print("[DEBUG] Successfully extracted standard_roster table from comment")
                    break
        
        if not found_in_comments:
            print("[DEBUG] standard_roster table not found in comments either")
    
    # Show all table IDs on the page (main HTML)
    all_tables = soup.find_all('table')
    table_ids = [table.get('id', 'NO_ID') for table in all_tables]
    print(f"[DEBUG] All table IDs found in main HTML: {table_ids}")
    
    # Show all table IDs in comments
    all_comment_table_ids = []
    for comment in comments:
        if '<table' in comment:
            comment_soup = BeautifulSoup(comment, 'html.parser')
            comment_tables = comment_soup.find_all('table')
            for table in comment_tables:
                table_id = table.get('id', 'NO_ID')
                if table_id not in all_comment_table_ids:
                    all_comment_table_ids.append(table_id)
    
    if all_comment_table_ids:
        print(f"[DEBUG] All table IDs found in comments: {all_comment_table_ids}")

if __name__ == '__main__':
    main() 