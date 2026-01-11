import os
import json
import requests
import re
from difflib import get_close_matches

# ==========================================
# 1. CONFIGURATION
# ==========================================
BACKEND_URL = "https://vercelapi-olive.vercel.app/api/sync-nodes?country=us"
DIRS = {
    'tsdb': 'assets/logos/tsdb',
    'streamed': 'assets/logos/streamed',
    'leagues': 'assets/logos/leagues'
}
OUTPUT_FILE = 'assets/data/image_map.json'
FUZZY_CUTOFF = 0.85 

# --- WHITELIST FOR NAME CLEANING ONLY ---
# We use this ONLY to help clean names like "NBA - Celtics".
# We DO NOT use this to filter which teams get mapped.
ALLOWED_LEAGUES_INPUT = """
NFL, NBA, MLB, NHL, College Football, College-Football, College Basketball, College-Basketball, 
NCAAB, NCAAF, NCAA Men, NCAA-Men, NCAA Women, NCAA-Women, Premier League, Premier-League, 
Champions League, Champions-League, MLS, Bundesliga, Serie-A, Serie A, American-Football, American Football, 
Ice Hockey, Ice-Hockey, Championship, Scottish Premiership, Scottish-Premiership, 
Europa League, Europa-League, A League, A-League, A League Men, A League Women, 
Ligue 1, La Liga, Eredivisie, Primeira Liga, Saudi Pro League, F1, UFC, Rugby
"""
VALID_LEAGUES = {x.strip().lower() for x in ALLOWED_LEAGUES_INPUT.split(',') if x.strip()}

# ==========================================
# 2. HELPER FUNCTIONS
# ==========================================
def clean_display_name(name):
    """
    Sanitizer:
    1. PRIORITY RULE: If a colon (:) is found, assume format "League: Team" 
       and strip everything before the first colon.
    2. FALLBACK: Check whitelist for prefixes (e.g. "NBA - Team") if no colon exists.
    """
    if not name: return None
    
    # --- RULE 1: Generic Colon Stripper ---
    # This ensures "A-League: Team A" becomes "Team A" automatically.
    if ':' in name:
        parts = name.split(':', 1)
        if len(parts) > 1:
            cleaned = parts[1].strip()
            if cleaned and len(cleaned) > 1:
                return cleaned

    # --- RULE 2: Whitelist Fallback ---
    lower_name = name.lower()
    for league in VALID_LEAGUES:
        if lower_name.startswith(league):
            remainder = name[len(league):]
            # Remove separator characters (spaces, hyphens) from the start
            clean_remainder = re.sub(r"^[\s-]+", "", remainder)
            if clean_remainder and len(clean_remainder.strip()) > 1:
                return clean_remainder.strip()
    return name.strip()

def make_pretty_name(slug):
    """
    Converts a filename slug back to a human-readable title.
    Ex: "manchester-united" -> "Manchester United"
    """
    return slug.replace('-', ' ').title()

# ==========================================
# 3. MAIN EXECUTION
# ==========================================
def main():
    print("--- Generating Full Image Map ---")

    # 1. Index Local Files (The "Source of Truth")
    slug_to_path = {}
    
    # Load TSDB (Priority 1)
    if os.path.exists(DIRS['tsdb']):
        for f in os.listdir(DIRS['tsdb']):
            if f.endswith('.webp'):
                slug = f.replace('.webp', '')
                slug_to_path[slug] = f"/{DIRS['tsdb']}/{f}"

    # Load Streamed (Priority 2)
    if os.path.exists(DIRS['streamed']):
        for f in os.listdir(DIRS['streamed']):
            if f.endswith('.webp'):
                slug = f.replace('.webp', '')
                if slug not in slug_to_path:
                    slug_to_path[slug] = f"/{DIRS['streamed']}/{f}"

    # Load Leagues
    league_paths = {}
    if os.path.exists(DIRS['leagues']):
        for f in os.listdir(DIRS['leagues']):
            if f.endswith('.webp'):
                slug = f.replace('.webp', '')
                league_paths[slug] = f"/{DIRS['leagues']}/{f}"

    # 2. Build Initial Map from Files
    final_teams = {}
    final_leagues = {}

    for slug, path in slug_to_path.items():
        pretty_key = make_pretty_name(slug)
        final_teams[pretty_key] = path

    for slug, path in league_paths.items():
        pretty_key = make_pretty_name(slug)
        final_leagues[pretty_key] = path

    print(f" > Indexed {len(final_teams)} images from local folders.")

    # 3. Fetch Backend Matches (To map specific API names)
    print(" > Fetching backend matches to map live names...")
    try:
        data = requests.get(BACKEND_URL, timeout=10).json()
        matches = data.get('matches', [])
    except Exception as e:
        print(f"   [!] Backend fetch failed: {e}")
        matches = []

    avail_slugs = list(slug_to_path.keys())

    for m in matches:
        # We NO LONGER check "if league not in whitelist: continue"
        # We process ALL matches.
        league_name = m.get('league')

        # Map Teams
        for t_key in ['home_team', 'away_team']:
            raw_name = m.get(t_key)
            if not raw_name: continue
            
            # A. Clean the name (Handles "A-League: Team A" -> "Team A")
            clean_name = clean_display_name(raw_name)
            
            # B. Generate Slug from Clean Name
            search_slug = "".join([c for c in clean_name.lower() if c.isalnum() or c == '-']).strip('-')
            
            # C. Try to match file
            if search_slug in slug_to_path:
                # Perfect Match
                final_teams[clean_name] = slug_to_path[search_slug]
                # Also Map "Raw Name" (just in case frontend sends raw name)
                if raw_name != clean_name:
                    final_teams[raw_name] = slug_to_path[search_slug]
            else:
                # Fuzzy Match
                fuzzy = get_close_matches(search_slug, avail_slugs, n=1, cutoff=FUZZY_CUTOFF)
                if fuzzy:
                    matched_slug = fuzzy[0]
                    final_teams[clean_name] = slug_to_path[matched_slug]

        # Map League
        if league_name:
            l_slug = "".join([c for c in league_name.lower() if c.isalnum() or c == '-']).strip('-')
            if l_slug in league_paths:
                final_leagues[league_name] = league_paths[l_slug]

    # 4. Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({ "teams": final_teams, "leagues": final_leagues }, f, indent=2)
        
    print(f"--- Map Saved: {len(final_teams)} Teams, {len(final_leagues)} Leagues ---")

if __name__ == "__main__":
    main()
