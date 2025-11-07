import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys

# ... (URL a TARGET_STATS zůstávají stejné)
URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = ["BR Quads Wins", "BR Duo Quads Wins"]
OUTPUT_FILE = "wins_data.json"

def get_wins():
    print(f"Stahuji data z: {URL}")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status() 
    except requests.RequestException as e:
        print(f"Chyba při stahování URL: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    total_wins = 0
    found_stats = 0
    
    for stat_name in TARGET_STATS:
        # 1. Najdeme název statistiky (jako v předchozí verzi)
        name_element = soup.find('div', class_='stats-card__title', string=lambda t: t and stat_name.lower() in t.lower())
        
        if name_element:
            # 2. Najdeme rodičovskou kartu (stat-card)
            card = name_element.find_parent('div', class_='stats-card')
            
            if card:
                # 3. Nový, přesnější selektor pro hodnotu:
                # Hledáme span s třídou 'stat-value' a vnořeným span.truncate
                stat_value_element = card.select_one('span.stat-value span.truncate')
                
                if stat_value_element:
                    # Získání hodnoty a úprava
                    stat_value_str = stat_value_element.text.strip().replace(',', '')
                    
                    try:
                        wins = int(stat_value_str)
                        total_wins += wins
                        found_stats += 1
                        print(f"Nalezeno: {stat_name} = {wins}")
                    except ValueError:
                        print(f"Varování: Hodnota pro '{stat_name}' není platné číslo: '{stat_value_str}'", file=sys.stderr)
                else:
                    # Původní fallback selektor (pokud by se změnila ta nová struktura)
                    fallback_value_element = card.select_one('div.stats-card__value')
                    if fallback_value_element:
                         stat_value_str = fallback_value_element.text.strip().replace(',', '')
                         try:
                            wins = int(stat_value_str)
                            total_wins += wins
                            found_stats += 1
                            print(f"Nalezeno (Fallback): {stat_name} = {wins}")
                         except ValueError:
                            print(f"Varování: Hodnota pro '{stat_name}' není platné číslo (Fallback): '{stat_value_str}'", file=sys.stderr)
                    else:
                        print(f"Varování: Nalezen název '{stat_name}', ale nedaří se najít hodnotu (nový ani starý selektor).", file=sys.stderr)
            else:
                print(f"Varování: Nedaří se najít rodičovskou kartu ('stats-card') pro '{stat_name}'.", file=sys.stderr)
        else:
            print(f"Varování: Statistiky '{stat_name}' nebyly na stránce nalezeny.", file=sys.stderr)
            
    if found_stats != len(TARGET_STATS):
        print(f"Upozornění: Podařilo se najít pouze {found_stats} z {len(TARGET_STATS)} cílových statistik. Součet může být neúplný.", file=sys.stderr)

    return total_wins

# ... (Funkce main() zůstává beze změny)
def main():
    wins = get_wins()
    
    if wins is not None:
        data = {
            "total_wins": wins,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False) 
            print(f"Data úspěšně uložena do {OUTPUT_FILE}: Total Wins = {wins}")
        except IOError as e:
            print(f"Chyba při ukládání souboru {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("Skript selhal při získávání dat. JSON nebyl aktualizován.")

if __name__ == "__main__":
    main()
