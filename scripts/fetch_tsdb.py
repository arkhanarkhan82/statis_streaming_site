import os
import requests
import urllib.parse
import re
import time
from PIL import Image
from io import BytesIO

# ==========================================
# 1. CONFIGURATION
# ==========================================
API_KEY = "123" # Replace with valid key
BASE_URL = f"https://www.thesportsdb.com/api/v1/json/{API_KEY}"
SAVE_DIR = "assets/logos/tsdb"
REFRESH_DAYS = 60

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

# --- WHITELIST CONFIGURATION ---
ALLOWED_LEAGUES_INPUT = """
NFL, NBA, MLB, NHL, College Football, College-Football, College Basketball, College-Basketball, 
NCAAB, NCAAF, NCAA Men, NCAA-Men, NCAA Women, NCAA-Women, Premier League, Premier-League, 
Champions League, Champions-League, MLS, Bundesliga, Serie-A, Serie A, American Football, 
Ice Hockey, Ice-Hockey, Championship, Scottish Premiership, Scottish-Premiership, 
Europa League, Europa-League, A League, A-League, A League Men, A League Women, 
Ligue 1, La Liga, Eredivisie, Primeira Liga, Saudi Pro League, F1, UFC, Rugby
"""
VALID_LEAGUES = {x.strip().lower() for x in ALLOWED_LEAGUES_INPUT.split(',') if x.strip()}

# Map Display Name -> TSDB Search Query
LEAGUES = {
    "Premier League": "English Premier League",
    "Championship": "English League Championship",
    "Scottish Premiership": "Scottish Premiership",
    "La Liga": "Spanish La Liga",
    "Bundesliga": "German Bundesliga",
    "Serie A": "Italian Serie A",
    "Ligue 1": "French Ligue 1",
    "Eredivisie": "Dutch Eredivisie",
    "Primeira Liga": "Portuguese Primeira Liga",
    "Champions League": "UEFA Champions League",
    "Europa League": "UEFA Europa League",
    "MLS": "American Major League Soccer",
    "Saudi Pro League": "Saudi Arabian Pro League",
    "NBA": "NBA",
    "NFL": "NFL",
    "NHL": "NHL",
    "MLB": "MLB",
    "A League": "Australian A-League",
    "A League Men": "Australian A-League",
    "A League Women": "Australian A-League Women",
    "F1": "Formula 1",
    "UFC": "UFC"
}

# ==========================================
# 2. UTILS
# ==========================================
def slugify(name):
    if not name: return None
    clean = str(name).lower()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"\s+", "-", clean)
    return clean.strip("-")

def should_download(path):
    if not os.path.exists(path): return True
    file_age_days = (time.time() - os.path.getmtime(path)) / (24 * 3600)
    return file_age_days > REFRESH_DAYS

def save_image_optimized(url, save_path):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            img = Image.open(BytesIO(resp.content))
            if img.mode != 'RGBA': img = img.convert('RGBA')
            img = img.resize((60, 60), Image.Resampling.LANCZOS)
            
            temp_buffer = BytesIO()
            img.save(temp_buffer, "WEBP", quality=90, method=6)
            
            with open(save_path, "wb") as f:
                f.write(temp_buffer.getvalue())
            return True
    except: 
        pass
    return False

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    print("--- Starting TSDB Harvester (Image Only) ---")

    for display_name, tsdb_name in LEAGUES.items():
        # Whitelist Check
        if display_name.lower() not in VALID_LEAGUES:
            continue

        print(f" > Checking: {display_name}")
        encoded = urllib.parse.quote(tsdb_name)
        url = f"{BASE_URL}/search_all_teams.php?l={encoded}"
        
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            data = resp.json()
            
            if data and data.get('teams'):
                count = 0
                for t in data['teams']:
                    name = t.get('strTeam')
                    if name:
                        slug = slugify(name)
                        if slug:
                            # Note: NO league_map logic here.
                            
                            # Download Image
                            badge = t.get('strTeamBadge') or t.get('strBadge')
                            if badge:
                                path = os.path.join(SAVE_DIR, f"{slug}.webp")
                                if should_download(path):
                                    if save_image_optimized(badge, path):
                                        count += 1
                
                if count > 0: print(f"   [+] Processed {count} updates.")
            else:
                print(f"   [-] No teams found for {tsdb_name}")

        except Exception as e:
            print(f"   [!] Error: {e}")
        
        time.sleep(1.2)
    
    print("--- TSDB Sync Complete ---")

if __name__ == "__main__":
    main()
