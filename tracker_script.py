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
            
            # 1. Zvýšit celkový timeout pro všechny operace na 60 sekund
            page.set_default_timeout(60000) 
            
            # Přejít na stránku se sníženou náročností čekání, jen na základní obsah (domcontentloaded)
            print(f"Naviguji na {URL} s wait_until=domcontentloaded a timeoutem 60s...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # NOVÉ ČEKÁNÍ: Dáme 20 sekund na spuštění JavaScriptu a vykreslení statistik
            print("Čekám 20 sekund na vykreslení JavaScriptu...")
            page.wait_for_timeout(20000) # Čekání 20000 ms
            
            # Důležité: Počkat na načtení klíčového elementu, abychom zkontrolovali, že se vykreslil
            print("Čekám na element div.stats-card...")
            # Ponecháme kratší timeout pro tento element, jelikož by se měl objevit po 20s
            page.wait_for_selector('div.stats-card', timeout=15000) 
            
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
    
    # Parsovací logika
    for stat_name, wins_key in TARGET_STATS.items():
        current_wins = 0
        
        name_element = soup.find('div', class_='stats-card__title', 
                                 string=lambda t: t and stat_name.lower() in t.lower())
        
        if name_element:
            card = name_element.find_parent('div', class_='stats-card')
            
            if card:
                # Přesný selektor pro hodnotu: span.stat-value vnořený span.truncate
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
