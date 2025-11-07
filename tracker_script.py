import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import sys

# 1. URL a cílové statistiky
URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = ["BR Quads Wins", "BR Duo Quads Wins"]
OUTPUT_FILE = "wins_data.json"

def get_wins():
    """Stáhne web, parsuje BR Quads Wins a BR Duo Quads Wins a vrátí jejich součet."""
    print(f"Stahuji data z: {URL}")
    
    # Hlavičky pro simulaci běžného prohlížeče
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(URL, headers=headers, timeout=15)
        response.raise_for_status() # Vyvolá HTTPError pro špatné kódy (4xx nebo 5xx)
    except requests.RequestException as e:
        print(f"Chyba při stahování URL: {e}", file=sys.stderr)
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    total_wins = 0
    found_stats = 0
    
    # Robustnější hledání statistik: 
    # Hledáme div s třídou 'stats-card__title', který obsahuje cílový text.
    
    for stat_name in TARGET_STATS:
        # Hledáme element 'div' s třídou 'stats-card__title', který má ve svém textu název statistiky
        name_element = soup.find('div', class_='stats-card__title', string=lambda t: t and stat_name.lower() in t.lower())
        
        if name_element:
            # Hodnota je obvykle v sousedním divu, nebo jako sourozenec k názvu, 
            # ale nejspolehlivější je jít k rodičovské 'card' a tam hledat hodnotu.
            card = name_element.find_parent('div', class_='stats-card')
            
            if card:
                # Najdi hodnotu v divu s třídou 'stats-card__value' uvnitř dané karty
                stat_value_element = card.select_one('div.stats-card__value')
                
                if stat_value_element:
                    # Ostranění čárky pro správný převod na číslo (např. '1,500' -> '1500')
                    stat_value_str = stat_value_element.text.strip().replace(',', '')
                    
                    try:
                        wins = int(stat_value_str)
                        total_wins += wins
                        found_stats += 1
                        print(f"Nalezeno: {stat_name} = {wins}")
                    except ValueError:
                        print(f"Varování: Hodnota pro '{stat_name}' není platné číslo: '{stat_value_str}'", file=sys.stderr)
                else:
                    print(f"Varování: Nalezen název '{stat_name}', ale nedaří se najít jeho hodnotu ('stats-card__value').", file=sys.stderr)
            else:
                print(f"Varování: Nedaří se najít rodičovskou kartu ('stats-card') pro '{stat_name}'.", file=sys.stderr)
        else:
            print(f"Varování: Statistiky '{stat_name}' nebyly na stránce nalezeny.", file=sys.stderr)
            
    if found_stats != len(TARGET_STATS):
        print(f"Upozornění: Podařilo se najít pouze {found_stats} z {len(TARGET_STATS)} cílových statistik. Součet může být neúplný.", file=sys.stderr)

    # Vrátí součet, i když je 0 (pokud by se nic nenašlo)
    return total_wins

def main():
    wins = get_wins()
    
    # Kontrola, zda se data podařilo získat (není None, vrací se None při HTTP chybě)
    if wins is not None:
        # Vytvoření JSONu
        data = {
            "total_wins": wins,
            "last_updated": datetime.now().isoformat()
        }
        
        # Uložení JSONu
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                # Použijeme ensure_ascii=False pro správné české znaky, pokud by byly potřeba
                json.dump(data, f, indent=4, ensure_ascii=False) 
            print(f"Data úspěšně uložena do {OUTPUT_FILE}: Total Wins = {wins}")
        except IOError as e:
            print(f"Chyba při ukládání souboru {OUTPUT_FILE}: {e}", file=sys.stderr)
    else:
        # Pokud se nepodařilo získat data, nebudeme přepisovat JSON, aby zůstaly staré hodnoty
        print("Skript selhal při získávání dat. JSON nebyl aktualizován.")


if __name__ == "__main__":
    main()
