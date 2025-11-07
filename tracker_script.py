import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys

# 1. URL a cílové statistiky
URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = {
    "BR Quads Wins": "br_quads_wins",
    "BR Duo Quads Wins": "br_duo_quads_wins"
}
OUTPUT_FILE = "wins_data.json"

def get_wins():
    """Stáhne web, parsuje cílové statistiky a vrátí slovník s výsledky."""
    print(f"Stahuji data z: {URL}")
    
    # NOVÉ HLAVIČKY: Detailní User-Agent a další hlavičky pro simulaci Chrome prohlížeče
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'cs-CZ,cs;q=0.8,en-US;q=0.5,en;q=0.3',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status() # Vyvolá HTTPError, pokud kód není 200 (včetně 403)
        print("Stahování úspěšné. Parsuji data...")
    except requests.RequestException as e:
        print(f"Chyba při stahování URL: {e}. Tracker.gg zřejmě blokuje bota.", file=sys.stderr)
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    results = {} 
    total_wins = 0
    found_stats = 0
    
    for stat_name, wins_key in TARGET_STATS.items():
        current_wins = 0
        
        # 1. Hledáme název statistiky: div.stats-card__title obsahující cílový text
        # Hledáme bez ohledu na velikost písmen (lower())
        name_element = soup.find('div', class_='stats-card__title', 
                                 string=lambda t: t and stat_name.lower() in t.lower())
        
        if name_element:
            # 2. Najdeme rodičovskou kartu pro kontext
            card = name_element.find_parent('div', class_='stats-card')
            
            if card:
                # 3. Přesný selektor pro hodnotu: span.stat-value vnořený span.truncate
                # Tento selektor odpovídá HTML struktuře, kterou jsi poslal
                stat_value_element = card.select_one('span.stat-value span.truncate')
                
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
                else:
                    print(f"Varování: Nalezen název '{stat_name}', ale nedaří se najít jeho hodnotu ('span.stat-value span.truncate').", file=sys.stderr)
            else:
                print(f"Varování: Nedaří se najít rodičovskou kartu ('stats-card') pro '{stat_name}'.", file=sys.stderr)
        else:
            print(f"Varování: Statistiky '{stat_name}' nebyly na stránce nalezeny.", file=sys.stderr)

    # Přidání celkového součtu a časové známky
    results['total_wins'] = total_wins
    results['last_updated'] = datetime.now().isoformat()
    
    if found_stats > 0:
        return results
    else:
        # Vracíme None, pokud nebylo nic nalezeno
        return None 

def main():
    results = get_wins()
    
    if results is not None:
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False) 
            print(f"Data úspěšně uložena do {OUTPUT_FILE}: Total Wins = {results['total_wins']}")
        except IOError as e:
            print(f"Chyba při ukládání souboru {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        print("Skript selhal při získávání dat. JSON nebyl aktualizován.")

if __name__ == "__main__":
    main()
