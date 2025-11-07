import json
from datetime import datetime
import sys
# Import Playwright pro asynchronní spuštění prohlížeče
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 1. URL a cílové statistiky
URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = {
    "BR Quads Wins": "br_quads_wins",
    "BR Duo Quads Wins": "br_duo_quads_wins"
}
OUTPUT_FILE = "wins_data.json"

def get_wins_with_playwright():
    """Použije Playwright k načtení dynamického obsahu a vrátí HTML."""
    print("Spouštím headless prohlížeč (Playwright) pro získání HTML...")
    
    try:
        with sync_playwright() as p:
            # Spustit prohlížeč Chromium (jako skutečný Chrome)
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Nastavíme rozšířený timeout pro pomalejší GitHub Actions runner
            page.set_default_timeout(30000) # 30 sekund
            
            # Přejít na stránku
            page.goto(URL, wait_until="networkidle") 
            
            # Důležité: Počkat na načtení klíčového elementu, abychom zaručili, že JS data jsou viditelná.
            # Předpokládáme, že div.stats-card se objeví, až když se načtou statistiky.
            page.wait_for_selector('div.stats-card') 
            
            # Získat obsah DOM po vykreslení JavaScriptu
            content = page.content()
            
            browser.close()
            print("HTML obsah úspěšně stažen po vykreslení JS.")
            return content

    except Exception as e:
        print(f"Kritická chyba při spouštění Playwright nebo načítání stránky: {e}", file=sys.stderr)
        return None

def parse_and_save():
    """Získá data, parsuje je a uloží do JSONu."""
    
    html_content = get_wins_with_playwright()
    if not html_content:
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    results = {} 
    total_wins = 0
    found_stats = 0
    
    # Standardní parsovací logika (stejná jako dříve, ale nyní pracuje s JS vykresleným HTML)
    for stat_name, wins_key in TARGET_STATS.items():
        current_wins = 0
        
        name_element = soup.find('div', class_='stats-card__title', 
                                 string=lambda t: t and stat_name.lower() in t.lower())
        
        if name_element:
            card = name_element.find_parent('div', class_='stats-card')
            
            if card:
                # Selektor pro hodnotu: span.stat-value vnořený span.truncate
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

    # Uložení výsledků
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
