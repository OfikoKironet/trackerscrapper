import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import os

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
        print(f"Chyba při stahování URL: {e}")
        return None

    soup = BeautifulSoup(response.content, 'html.parser')
    
    total_wins = 0
    found_stats = 0
    
    # 2. Hledání statistik
    # Všechny statistiky jsou v sekcích, které je třeba prohledat
    # Předpokládáme, že struktura je Card > Stat Name + Value
    
    # Selektor pro všechny statistické karty, které jsou na stránce
    stat_cards = soup.select('div.stats-card') 
    
    if not stat_cards:
        print("Chyba: Nebyly nalezeny žádné statistické karty (selektor 'div.stats-card'). Struktura stránky se možná změnila.")
        return None

    for card in stat_cards:
        # Název statistiky je v elementu, který je obvykle první Child
        stat_name_element = card.select_one('div.stats-card__title')
        # Hodnota statistiky je v elementu, který je obvykle druhý Child
        stat_value_element = card.select_one('div.stats-card__value')
        
        if stat_name_element and stat_value_element:
            stat_name = stat_name_element.text.strip()
            
            if stat_name in TARGET_STATS:
                # Ostranění čárky pro správný převod na číslo (např. '1,500' -> '1500')
                stat_value_str = stat_value_element.text.strip().replace(',', '')
                
                try:
                    wins = int(stat_value_str)
                    total_wins += wins
                    found_stats += 1
                    print(f"Nalezeno: {stat_name} = {wins}")
                except ValueError:
                    print(f"Varování: Hodnota pro '{stat_name}' není platné číslo: '{stat_value_str}'")
    
    if found_stats != len(TARGET_STATS):
        print(f"Varování: Podařilo se najít pouze {found_stats} z {len(TARGET_STATS)} cílových statistik. Součet může být neúplný.")
        
    return total_wins

def main():
    wins = get_wins()
    
    if wins is not None:
        # 3. Vytvoření JSONu
        data = {
            "total_wins": wins,
            "br_quads_wins": None, # Můžeš přidat detaily, pokud chceš
            "br_duo_quads_wins": None, # Můžeš přidat detaily, pokud chceš
            "last_updated": datetime.now().isoformat()
        }
        
        # 4. Uložení JSONu
        try:
            with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            print(f"Data úspěšně uložena do {OUTPUT_FILE}: Total Wins = {wins}")
        except IOError as e:
            print(f"Chyba při ukládání souboru {OUTPUT_FILE}: {e}")
    else:
        print("Skript selhal, JSON nebyl vytvořen.")


if __name__ == "__main__":
    main()
