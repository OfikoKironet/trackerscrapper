import json
from datetime import datetime
import sys
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# 1. URL a cílové statistiky
URL = "https://tracker.gg/bf6/profile/3186869623/modes"
TARGET_STATS = {
    # Hledáme řádky podle data-key
    "BR Quads": "br_quads_wins",
    "BR Duos": "br_duo_quads_wins"
}
OUTPUT_FILE = "wins_data.json"

def get_wins_with_playwright():
    """Použije Playwright k načtení dynamického obsahu a vrátí HTML."""
    print("Spouštím headless prohlížeč (Playwright) pro získání HTML...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # Zvýšit celkový timeout pro všechny operace na 60 sekund
            page.set_default_timeout(60000) 
            
            # Přejít na stránku se sníženou náročností čekání (domcontentloaded)
            print(f"Naviguji na {URL} s wait_until=domcontentloaded a timeoutem 60s...")
            page.goto(URL, wait_until="domcontentloaded", timeout=60000)
            
            # Dáme 20 sekund na spuštění JavaScriptu a vykreslení tabulky
            print("Čekám 20 sekund na vykreslení JavaScriptu...")
            page.wait_for_timeout(20000) 
            
            # Čekáme na element tr s data-key, což je nejpřesnější selektor
            print("Čekám na řádek tabulky s BR Quads (30s timeout)...")
            page.wait_for_selector('tr[data-key="BR Quads"]', timeout=30000) 
            
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
        print("Skript selhal při získávání obsahu.")
        return

    soup = BeautifulSoup(html_content, 'html.parser')
    
    results = {} 
    total_wins = 0
    found_stats = 0
    
    # Parsovací logika
    for stat_name, wins_key in TARGET_STATS.items():
        current_wins = 0
        
        # 1. Najdeme celou řádku tabulky pomocí atributu data-key
        row = soup.find('tr', {'data-key': stat_name})
        
        if row:
            # 2. Výhry jsou ve TŘETÍ buňce tabulky (index 2)
            # <td> element je druhý po Td s názvem, který je sticky (index 0)
            td_elements = row.find_all('td')
            
            if len(td_elements) > 2:
                # Třetí td obsahuje hodnotu výher (10, 3, atd.)
                wins_cell = td_elements[2]
                
                # 3. Získáme hodnotu uvnitř buňky
                stat_value_element = wins_cell.select_one('span.stat-value span.truncate')
                
                if stat_value_element:
                    stat_value_str = stat_value_element.text.strip().replace(',', '')
                    
                    try:
                        current_wins = int(stat_value_str)
                        total_wins += current_wins
                        results[wins_key] = current_wins
                        found_stats += 1
                        print(f"Nalezeno: {stat_name} = {current_wins} (z td index 2)")
                    except ValueError:
                        print(f"Varování: Hodnota pro '{stat_name}' není platné číslo: '{stat_value_str}'", file=sys.stderr)
                else:
                    print(f"Varování: Nalezen řádek '{stat_name}', ale nedaří se najít hodnotu ('span.stat-value span.truncate').", file=sys.stderr)
            else:
                print(f"Varování: Řádek '{stat_name}' má méně než 3 buňky <td>. Data nebyla nalezena.", file=sys.stderr)
        else:
            print(f"Varování: Řádek tabulky s data-key='{stat_name}' nebyl na stránce nalezen.", file=sys.stderr)

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
