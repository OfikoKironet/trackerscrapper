import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys

# ✅ VÁŠ API KLÍČ ZE SCRAPEOPS
SCRAPEOPS_API_KEY = "61dc2fc0-9e66-4ad8-bc59-4f5dc0c42a1c" 

URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = {
    "BR Quads": "br_quads_wins",
    "BR Duos": "br_duo_quads_wins"
}
OUTPUT_FILE = "wins_data.json"

def get_wins_from_api():
    """Použije ScrapeOps API s JS vykreslováním k načtení stránky a vrátí HTML."""
    
    payload = {
        'api_key': SCRAPEOPS_API_KEY,
        'url': URL,
        'bypass': 'js_rendering', 
        'wait_for_selector': 'tr[data-key="BR Quads"]', 
        'timeout': '60000',
    }

    print(f"Volám ScrapeOps API pro stažení {URL}...")
    
    try:
        response = requests.get('https://api.scrapeops.io/v1/scraper/get', params=payload, timeout=90)
        response.raise_for_status() 
        print("API volání úspěšné. Parsuji data...")
        return response.content
        
    except requests.RequestException as e:
        print(f"Kritická chyba při volání ScrapeOps API: {e}", file=sys.stderr)
        return None

def parse_and_save():
    """Získá data z API, parsuje je a uloží do JSONu."""
    
    html_content = get_wins_from_api()
    if not html_content:
        print("Skript selhal při získávání obsahu.")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    results = {} 
    total_wins = 0
    found_stats = 0
    
    for stat_name, wins_key in TARGET_STATS.items():
        current_wins = 0
        row = soup.find('tr', {'data-key': stat_name})
        
        if row:
            td_elements = row.find_all('td')
            
            if len(td_elements) > 2:
                wins_cell = td_elements[2]
                stat_value_element = wins_cell.select_one('span.stat-value span.truncate')
                
                if stat_value_element:
                    stat_value_str = stat_value_element.text.strip().replace(',', '')
                    
                    try:
                        current_wins = int(stat_value_str)
                        total_wins += current_wins
                        results[wins_key] = current_wins
                        found_stats += 1
                        print(f"Nalezeno: {stat_name} = {current_wins}")
                    except ValueError:
                        print(f"Varování: Hodnota pro '{stat_name}' není platné číslo: '{stat_value_str}'", file=sys.stderr)

    results['total_wins'] = total_wins
    results['last_updated'] = datetime.now().isoformat()
    
    if found_stats > 0:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False) 
            print(f"Data úspěšně uložena do {OUTPUT_FILE}: Total Wins = {results['total_wins']}")
        except IOError as e:
            print(f"Chyba při ukládání souboru {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("Skript nenašel žádná data. JSON nebyl aktualizován.")


if __name__ == "__main__":
    parse_and_save()
