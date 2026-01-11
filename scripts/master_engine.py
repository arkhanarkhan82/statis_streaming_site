import os
import json
import requests
import hashlib
import time
import re
import shutil
from datetime import datetime
from PIL import Image
from io import BytesIO

# ==========================================
# 1. CONFIGURATION & PATHS
# ==========================================
CONFIG_PATH = 'data/config.json'
LEAGUE_MAP_PATH = 'assets/data/league_map.json'
IMAGE_MAP_PATH = 'assets/data/image_map.json'

TEMPLATE_MASTER = 'assets/master_template.html'
TEMPLATE_WATCH = 'assets/watch_template.html'
TEMPLATE_LEAGUE = 'assets/league_template.html'
TEMPLATE_PAGE = 'assets/page_template.html'

# Output Paths
OUTPUT_DIR = '.' # Root
ASSETS_DIR = 'assets/logos'

# API Endpoints
NODE_A_ENDPOINT = 'https://streamed.pk/api'
ADSTRIM_ENDPOINT = 'https://beta.adstrim.ru/api/events'
STREAMED_IMG_BASE = "https://streamed.pk/api/images/badge/"

# Request Headers
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Fixes for generic API names
NAME_FIXES = {
    "icehockey": "Ice Hockey", "fieldhockey": "Field Hockey",
    "tabletennis": "Table Tennis", "americanfootball": "American Football",
    "australianfootball": "AFL", "basketball": "Basketball",
    "football": "Soccer", "soccer": "Soccer", "baseball": "Baseball",
    "fighting": "Fighting", "mma": "MMA", "boxing": "Boxing",
    "motorsport": "Motorsport", "golf": "Golf"
}

# ==========================================
# 2. DATA LOADING & SAVING
# ==========================================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving {path}: {e}")

# Load Initial Data
config = load_json(CONFIG_PATH)
league_map = load_json(LEAGUE_MAP_PATH)
image_map = load_json(IMAGE_MAP_PATH)

# Admin Settings
SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')

# Reverse League Map for Fast Lookup (Team Slug -> League Name)
# Logic: If Team A is in "NBA" list, map["team-a"] = "NBA"
REVERSE_LEAGUE_MAP = {}
for l_name, teams in league_map.items():
    for t in teams:
        REVERSE_LEAGUE_MAP[t] = l_name

# ==========================================
# 3. HELPER FUNCTIONS
# ==========================================
def slugify(text):
    if not text: return ""
    clean = str(text).lower()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"\s+", "-", clean)
    return clean.strip("-")

def unslugify(slug):
    return slug.replace('-', ' ').title()

def generate_match_id(sport, start_unix, home, away):
    """
    Replicates Node.js crypto.createHash('md5') logic EXACTLY.
    Format: sport-YYYY-MM-DD-homevaway
    """
    date = datetime.fromtimestamp(start_unix / 1000)
    date_key = date.strftime('%Y-%m-%d')
    
    def clean_for_id(s):
        s = (s or '').lower()
        s = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs)\b', '', s)
        return re.sub(r'[^a-z0-9]', '', s)

    teams = sorted([clean_for_id(home), clean_for_id(away)])
    raw_key = f"{sport.lower()}-{date_key}-{teams[0]}v{teams[1]}"
    return hashlib.md5(raw_key.encode('utf-8')).hexdigest()

def normalize_time(ts):
    # Ensure MS
    if ts < 10000000000: return ts * 1000
    return ts

def format_display_time(unix_ms):
    """Generates '12:30 PM ET' or 'GMT' based on country"""
    is_uk = TARGET_COUNTRY == 'UK'
    dt = datetime.fromtimestamp(unix_ms / 1000)
    # Note: Python runs on UTC servers usually.
    # Simple formatting (For advanced TZ, external libs needed, but keeping it standard lib for now)
    # We will output UTC time formatted string, client browser usually handles 'new Date()' better,
    # but for Static HTML, we want a rough string.
    time_str = dt.strftime('%I:%M %p') # 02:30 PM
    date_str = dt.strftime('%b %d')    # Jan 01
    
    # Simple Logic: Actions usually run UTC.
    # If US, subtract 5 hours (EST). If UK, add 0/1 (GMT).
    # Ideally, we rely on the timestamp for JS, but for text:
    return { "time": time_str, "date": date_str, "iso": dt.isoformat() }

# ==========================================
# 4. CORE LOGIC: RESOLUTION & CLEANING
# ==========================================
def smart_resolve(raw_match):
    """
    The BRAIN of the operation.
    Determines correct League, Home Name, Away Name using 3-Level Logic.
    """
    raw_home = raw_match.get('home_team') or 'TBA'
    raw_away = raw_match.get('away_team') or 'TBA'
    raw_league = raw_match.get('league') or raw_match.get('category') or "General"
    
    h_slug = slugify(raw_home)
    a_slug = slugify(raw_away)
    
    final_league = "General"
    final_home = raw_home
    final_away = raw_away
    source_method = "API"

    # --- LEVEL 1: STRICT MAP CHECK ---
    # Check if BOTH teams exist in the same league in our map
    if h_slug in REVERSE_LEAGUE_MAP and a_slug in REVERSE_LEAGUE_MAP:
        if REVERSE_LEAGUE_MAP[h_slug] == REVERSE_LEAGUE_MAP[a_slug]:
            final_league = REVERSE_LEAGUE_MAP[h_slug]
            source_method = "MapStrict"
    
    # --- LEVEL 2: COLON PREFIX CHECK ---
    # Example: "NBA: Lakers"
    if source_method == "API" and ':' in raw_home:
        parts = raw_home.split(':')
        candidate_league = parts[0].strip()
        candidate_team = parts[1].strip()
        
        # Validation: League name usually 2-20 chars
        if 1 < len(candidate_league) < 25 and len(candidate_team) > 0:
            final_league = candidate_league
            final_home = candidate_team
            source_method = "ColonSplit"

    # --- LEVEL 3: API FALLBACK ---
    if source_method == "API":
        # Clean API league name
        l_clean = raw_league.strip()
        l_key = l_clean.lower().replace(' ', '')
        final_league = NAME_FIXES.get(l_key, l_clean)

    # --- CLEANING TEAM NAMES ---
    # Regardless of method, ensure Home/Away doesn't contain the League Name prefix
    def clean_name(name, league):
        if not name or name == 'TBA': return 'TBA'
        # Remove League Prefix (Case Insensitive)
        if league:
            pattern = re.compile(re.escape(league) + r'[:\s-]*', re.IGNORECASE)
            name = pattern.sub('', name)
        # Remove Common US Prefixes
        name = re.sub(r'^(NBA|NFL|NHL|MLB|UFC|AFL)[:\s-]*', '', name, flags=re.IGNORECASE)
        return name.strip()

    final_home = clean_name(final_home, final_league)
    final_away = clean_name(final_away, final_league)
    
    # Determine Sport
    raw_sport = (raw_match.get('sport') or "General").lower()
    final_sport = final_league # Default sport to league name initially
    
    # Map Common Sports
    if "soccer" in raw_sport or "football" in raw_sport: final_sport = "Soccer"
    elif "basket" in raw_sport: final_sport = "Basketball"
    elif "base" in raw_sport: final_sport = "Baseball"
    elif "hock" in raw_sport: final_sport = "Ice Hockey"
    elif "nfl" in raw_sport or "american" in raw_sport: final_sport = "American Football"
    
    # If League is known in Config Priority, use that key as Sport/Category for grouping
    # But usually we keep Sport generic (Soccer) and League specific (Premier League)
    
    return {
        "league": final_league,
        "home": final_home,
        "away": final_away,
        "sport": final_sport.title()
    }

def calculate_score(match_data):
    """
    Uses Admin Panel Config (PRIORITY_SETTINGS) to score matches.
    """
    score = 0
    league = match_data['league']
    sport = match_data['sport']
    
    # 1. Boost List (Highest)
    boost_txt = str(PRIORITY_SETTINGS.get('_BOOST', '')).lower()
    boost_list = [x.strip() for x in boost_txt.split(',') if x.strip()]
    
    if any(b in league.lower() or b in sport.lower() for b in boost_list):
        score += 2000
        
    # 2. Explicit Priority Score
    # Check League
    if league in PRIORITY_SETTINGS:
        score += (PRIORITY_SETTINGS[league].get('score', 0) * 10)
    # Check Sport
    elif sport in PRIORITY_SETTINGS:
        score += (PRIORITY_SETTINGS[sport].get('score', 0))
        
    # 3. Live Bonus
    if match_data['is_live']:
        score += 5000
        score += (match_data.get('live_viewers', 0) / 10)
        
    # 4. Time Proximity (Upcoming)
    else:
        diff = (match_data['timestamp'] - time.time()*1000) / 3600000 # Hours
        if diff < 24:
            score += (24 - diff) # Higher score for closer games
            
    return score

# ==========================================
# 5. ASSET RESOLUTION
# ==========================================
def resolve_and_fetch_logo(team_name, image_payload=None):
    """
    Checks if logo exists in image_map. If not, fetches from provided payload.
    """
    if not team_name or team_name == 'TBA': return None
    
    # 1. Check Map
    if team_name in image_map['teams']:
        return image_map['teams'][team_name]
    
    # 2. If no map, but we have payload (from Streamed/Adstrim), fetch it
    if image_payload:
        slug = slugify(team_name)
        filename = f"{slug}.webp"
        save_path = os.path.join(ASSETS_DIR, 'streamed', filename)
        
        # Ensure dir exists
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        # Download logic
        urls = []
        if isinstance(image_payload, str): urls = [image_payload]
        elif isinstance(image_payload, dict): urls = list(image_payload.values())
        
        for url in urls:
            if not url.startswith('http'): url = f"{STREAMED_IMG_BASE}{url}.webp"
            try:
                r = requests.get(url, headers=HEADERS, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    if img.mode != 'RGBA': img = img.convert('RGBA')
                    img = img.resize((60, 60), Image.Resampling.LANCZOS)
                    img.save(save_path, "WEBP", quality=90)
                    
                    # Update Map
                    rel_path = f"/assets/logos/streamed/{filename}"
                    image_map['teams'][team_name] = rel_path
                    return rel_path
            except:
                continue
                
    return None

# ==========================================
# 6. HTML GENERATION (The Factory)
# ==========================================
def render_match_row(m, context="home"):
    """
    Generates HTML string for a single match row.
    Replicates 'createMatchRow' from app.js via Python f-strings.
    """
    is_live = m['is_live']
    
    # Time Column
    if is_live:
        status = m.get('status_text', 'Now')
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{status}</span>'
        row_class = "match-row live"
    else:
        ft = format_display_time(m['timestamp'])
        time_html = f'<span class="time-main">{ft["time"]}</span><span class="time-sub">{ft["date"]}</span>'
        row_class = "match-row"

    # Logo Helper
    def get_logo_html(name):
        url = image_map['teams'].get(name)
        if url:
            if not url.startswith('http'): url = f"https://{DOMAIN}{url}" if url.startswith('/') else f"https://{DOMAIN}/{url}"
            return f'<div class="logo-box"><img src="{url}" class="t-img" alt="{name}" loading="lazy" width="20" height="20"></div>'
        else:
            # Fallback letter logo
            color = "#334155" # Default gray
            initial = name[0] if name else "?"
            return f'<div class="logo-box"><span class="t-logo" style="background:{color}">{initial}</span></div>'

    # Teams HTML
    if m['is_single_event']:
        teams_html = f'<div class="team-name">{get_logo_html(m["home"])} {m["home"]}</div>'
    else:
        teams_html = f'<div class="team-name">{get_logo_html(m["home"])} {m["home"]}</div>' \
                     f'<div class="team-name">{get_logo_html(m["away"])} {m["away"]}</div>'

    # Meta/Status HTML
    if is_live:
        v = m.get('live_viewers', 0)
        v_txt = f"👀 {(v/1000):.1f}k 🔥" if v > 1000 else "⚡ Stable"
        meta_html = f'<div class="meta-top">{v_txt}</div>'
    else:
        meta_html = f'<div style="display:flex; flex-direction:column; align-items:flex-end;">' \
                    f'<span style="font-size:0.55rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; margin-bottom:2px;">Starts in</span>' \
                    f'<span class="meta-top" style="color:var(--accent-gold); font-size:0.75rem;">{m["status_text"]}</span></div>'

    # Action Button HTML
    # We use param_live for live, param_info for upcoming
    p_live = SITE_SETTINGS.get('param_live', 'stream')
    p_info = SITE_SETTINGS.get('param_info', 'info')
    
    # Watch Page URL
    if is_live:
        btn_action = f"window.location.href='/watch/?{p_live}={m['id']}'"
        btn_cls = "btn-watch"
        btn_txt = "WATCH"
        btn_icon = '<span class="hd-badge">HD</span>'
    else:
        # Check if starting within 30 mins
        diff_mins = (m['timestamp'] - time.time()*1000) / 60000
        if diff_mins <= 30:
            btn_action = f"window.location.href='/watch/?{p_info}={m['id']}'"
            btn_cls = "btn-watch"
            btn_txt = "WATCH"
            btn_icon = '<span class="hd-badge">HD</span>'
        else:
            # Notify Button (Static HTML representation)
            btn_action = "this.classList.add('active');this.innerText='✓ Set';"
            btn_cls = "btn-notify"
            btn_txt = "🔔 Notify"
            btn_icon = ""

    action_html = f"""
        <button onclick="{btn_action}" class="{btn_cls}">{btn_txt} {btn_icon}</button>
        <button class="btn-copy-link" onclick="copyText('https://{DOMAIN}/watch/?{p_info}={m['id']}')">
            <svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> Link
        </button>
    """

    # Final Row Assembly
    tag = m['league'].upper()
    return f"""
    <div class="{row_class}">
        <div class="col-time">{time_html}</div>
        <div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div>
        <div class="col-meta">{meta_html}</div>
        <div class="col-action">{action_html}</div>
    </div>
    """

def render_section(title, matches, is_league=False):
    if not matches: return ""
    
    rows = "".join([render_match_row(m) for m in matches])
    
    # Resolve Icon
    icon = "🏆"
    if title in image_map.get('leagues', {}):
        url = image_map['leagues'][title]
        if not url.startswith('http'): url = f"https://{DOMAIN}{url}"
        icon_html = f'<img src="{url}" class="sec-logo" alt="{title}" loading="lazy" width="24" height="24">'
    else:
        icon_html = f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span>'

    # Link
    link_html = ""
    if is_league:
        slug = slugify(title) + "-streams"
        link_html = f'<a href="/{slug}/" class="sec-right-link">View All ></a>'

    return f"""
    <div class="section-box" style="margin-bottom:30px;">
        <div class="sec-head">
            <h2 class="sec-title">{icon_html} Upcoming {title}</h2>
            {link_html}
        </div>
        <div>{rows}</div>
    </div>
    """

# ==========================================
# 7. MAIN ENGINE
# ==========================================
def main():
    print("--- 🚀 Starting Master Engine ---")
    start_time = time.time()

    # 1. Fetch Data
    print(" > Fetching External APIs...")
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    active_live_ids = set([m['id'] for m in res_live] if isinstance(res_live, list) else [])
    
    raw_matches = []
    
    # 2. Normalize Streamed.pk
    for item in res_a:
        # Create common structure
        resolved = smart_resolve({
            'home_team': item.get('title', '').split(' vs ')[0] if 'title' in item else item.get('home', 'TBA'),
            'away_team': item.get('title', '').split(' vs ')[1] if 'title' in item and ' vs ' in item['title'] else item.get('away', 'TBA'),
            'league': item.get('league') or item.get('category'),
            'sport': item.get('category')
        })
        
        # Check Images
        h_img = item.get('teams', {}).get('home', {}).get('badge')
        a_img = item.get('teams', {}).get('away', {}).get('badge')
        
        raw_matches.append({
            'src': 'streamed',
            'orig_id': item.get('id'),
            'timestamp': normalize_time(item.get('date', 0)),
            'resolved': resolved,
            'channels': item.get('sources', []),
            'imgs': {'home': h_img, 'away': a_img},
            'is_live': item.get('id') in active_live_ids,
            'viewers': 0 # We skip heavy viewer fetch for static build speed
        })

    # 3. Normalize Adstrim
    if 'data' in res_b:
        for item in res_b['data']:
            resolved = smart_resolve({
                'home_team': item.get('home_team'),
                'away_team': item.get('away_team'),
                'league': item.get('league'),
                'sport': item.get('sport')
            })
            
            # Streams
            chans = []
            if item.get('channels'):
                for c in item['channels']:
                    chans.append({'source': 'adstrim', 'id': c.get('name'), 'type': 'embed', 'url': f"https://topembed.pw/channel/{c.get('name')}"})

            raw_matches.append({
                'src': 'adstrim',
                'orig_id': item.get('id'),
                'timestamp': normalize_time(item.get('timestamp', 0)),
                'resolved': resolved,
                'channels': chans,
                'imgs': {'home': None, 'away': None}, # Adstrim images usually unreliable url
                'is_live': False, # Adstrim doesn't tell us easily
                'viewers': 0
            })

    # 4. De-Duplicate & Finalize
    final_matches = []
    seen_ids = set()
    
    print(f" > Processing {len(raw_matches)} raw items...")
    
    for m in raw_matches:
        # Generate SEO ID
        uid = generate_match_id(m['resolved']['sport'], m['timestamp'], m['resolved']['home'], m['resolved']['away'])
        
        if uid in seen_ids:
            # Merge Logic (Append channels to existing)
            existing = next((x for x in final_matches if x['id'] == uid), None)
            if existing:
                # Add unique channels
                existing_urls = set(c.get('url') or c.get('id') for c in existing['stream_channels'])
                for c in m['channels']:
                    c_url = c.get('url') or c.get('id')
                    if c_url not in existing_urls:
                        existing['stream_channels'].append({
                            'name': f"Server {len(existing['stream_channels'])+1}",
                            'url': c.get('url') if c.get('url') else f"https://streamed.pk/player?id={c['id']}" # Fallback
                        })
            continue
            
        seen_ids.add(uid)
        
        # Resolve Images (Auto-Update Map)
        if m['imgs']['home']: resolve_and_fetch_logo(m['resolved']['home'], m['imgs']['home'])
        if m['imgs']['away']: resolve_and_fetch_logo(m['resolved']['away'], m['imgs']['away'])
        
        # Calc Priority
        is_single = m['resolved']['away'] == 'TBA' or not m['resolved']['away']
        
        match_obj = {
            'id': uid,
            'originalId': m['orig_id'], # needed for legacy watch links
            'home': m['resolved']['home'],
            'away': m['resolved']['away'],
            'league': m['resolved']['league'],
            'sport': m['resolved']['sport'],
            'timestamp': m['timestamp'],
            'is_live': m['is_live'],
            'is_single_event': is_single,
            'status_text': getStatusText(m['timestamp'], m['is_live']),
            'stream_channels': [{ 'name': 'Main', 'url': c.get('url') or f"https://streamed.pk/player?id={c['id']}" } for c in m['channels']],
            'live_viewers': m['viewers']
        }
        
        # Calculate Score
        match_obj['priority_score'] = calculate_score(match_obj)
        final_matches.append(match_obj)

    # Save Updated Image Map
    save_json(IMAGE_MAP_PATH, image_map)

    # Sort Global List
    final_matches.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # ==========================================
    # 8. BUCKETING & INJECTION
    # ==========================================
    print(" > Generating HTML Content...")
    
    live_matches = [m for m in final_matches if m['is_live']]
    upcoming_matches = [m for m in final_matches if not m['is_live']]
    
    # 1. LIVE SECTION HTML
    live_html = ""
    if live_matches:
        rows = "".join([render_match_row(m, "live") for m in live_matches])
        title = config['theme'].get('text_live_section_title', 'Trending Live')
        live_html = f"""
        <div id="live-section">
            <div class="sec-head"><h2 class="sec-title"><div class="live-dot"></div> {title}</h2></div>
            <div id="trending-list" class="match-list">{rows}</div>
        </div>
        """
    
    # 2. TOP UPCOMING HTML
    wildcard = config['theme'].get('wildcard_category', '')
    wc_html = ""
    top_html = ""
    
    if wildcard:
        # Wildcard Mode
        wc_matches = [m for m in upcoming_matches if wildcard.lower() in m['league'].lower()]
        if wc_matches:
            wc_rows = "".join([render_match_row(m) for m in wc_matches])
            wc_html = f"""<div id="wildcard-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">🔥 {wildcard}</h2></div>{wc_rows}</div></div>"""
    
    # Standard Top 5
    top5 = upcoming_matches[:5]
    if top5:
        top_rows = "".join([render_match_row(m) for m in top5])
        title = config['theme'].get('text_top_upcoming_title', 'Top Upcoming')
        top_html = f"""<div id="top-upcoming-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">📅 {title}</h2></div>{top_rows}</div></div>"""

    # 3. GROUPED HTML
    grouped_html = ""
    # Group by priorities in Config
    used_ids = set([m['id'] for m in live_matches] + [m['id'] for m in top5])
    
    # Iterate priorities
    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or settings.get('isHidden'): continue
        
        # Find matches for this league/sport
        group_matches = []
        for m in upcoming_matches:
            if m['id'] in used_ids: continue
            if key.lower() in m['league'].lower() or key.lower() in m['sport'].lower():
                group_matches.append(m)
                used_ids.add(m['id'])
        
        if group_matches:
            is_league = settings.get('isLeague', False)
            grouped_html += render_section(key, group_matches, is_league)

    # ==========================================
    # 9. WRITE FILES
    # ==========================================
    print(" > Writing Static Files...")
    
    # A. MASTER HOME
    with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f:
        html = f.read()
    
    # Basic Replacements (Config)
    # Note: We rely on build_site.py or similar to handle the heavy CSS variable injection usually.
    # But since this REPLACES build_site.py data injection, we need to ensure placeholders exist.
    # Assuming the Template already has placeholders or empty divs.
    
    # INJECTION STRATEGY:
    # We replace the *entire* innerHTML of specific containers if possible, 
    # OR we replace custom placeholders like {{INJECT_LIVE}} if we added them.
    # Based on your prompt, you want match data injected "directly".
    # I will replace the specific div IDs with the content.
    
    def inject_id(html, div_id, content):
        # Regex to find <div id="X">...</div> and replace content
        # Simplified: Replace the placeholder comment or empty div content
        # For robustness, let's assume we replace the inner content of the known containers.
        # But regex on HTML is flaky. Better to replace known placeholders.
        # However, to support your existing template, we will replace the loading skeletons/empty divs.
        
        # Hack: Replace the closing > of the opening tag with > + content + <style>#skeleton...{display:none}</style>
        # A cleaner way given your template:
        # Your template has: <div id="live-section">...</div>
        # We constructed 'live_html' as the WHOLE div. So we replace the template's placeholder div with ours.
        
        pattern = f'<div id="{div_id}"[^>]*>.*?</div>'
        # We need dotall to match newlines
        return re.sub(pattern, content, html, flags=re.DOTALL) if content else re.sub(pattern, '', html, flags=re.DOTALL)

    # Actually, simpler strategy: In the template, put {{LIVE_SECTION}} etc.
    # But since I can't edit your template in this response, I will assume 
    # we replace the specific hardcoded strings found in your provided `master_template.html`.
    
    # 1. Live Section Replacement
    # In template: <div id="live-section"> ... </div>
    # My generated live_html includes <div id="live-section">...</div>
    # So we replace the entire block.
    if live_html:
        html = re.sub(r'<div id="live-section">.*?<!-- 3. TOP 5 UPCOMING -->', f'{live_html}\n<!-- 3. TOP 5 UPCOMING -->', html, flags=re.DOTALL)
    else:
        # Hide live section if empty
        html = html.replace('<div id="live-section">', '<div id="live-section" style="display:none;">')

    # 2. Upcoming
    if wildcard:
        html = re.sub(r'<div id="wildcard-container">.*?</div>', wc_html, html, flags=re.DOTALL)
    else:
        html = re.sub(r'<div id="top-upcoming-container">.*?</div>', top_html, html, flags=re.DOTALL)

    # 3. Grouped
    html = re.sub(r'<div id="grouped-container">.*?</div>', grouped_html, html, flags=re.DOTALL)

    # 4. Remove JS Loaders
    html = html.replace('loadMatches();', '// Matches Injected Static')
    
    # 5. Save Home
    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

    # B. WATCH PAGE (Hybrid Injection)
    # We load the template, inject the JSON payload, save as watch/index.html
    with open(TEMPLATE_WATCH, 'r', encoding='utf-8') as f:
        w_html = f.read()
    
    # Convert Match List to Minimal JSON for Client
    # Client needs: id, home, away, league, sport, timestamp, is_live, status_text, stream_channels
    min_matches = []
    for m in final_matches:
        min_matches.append({
            'id': m['id'],
            'home': m['home'],
            'away': m['away'],
            'league': m['league'],
            'sport': m['sport'],
            'startTimeUnix': m['timestamp'],
            'is_live': m['is_live'],
            'status_text': m['status_text'],
            'stream_channels': m['stream_channels'],
            'live_viewers': m['live_viewers'],
            'isSingleEvent': m['is_single_event']
        })
    
    json_dump = json.dumps(min_matches)
    
    # Inject into Watch Template
    # We look for the <script> block and prepend the data
    w_html = w_html.replace('<script>', f'<script>\nwindow.MATCH_DATA = {json_dump};\n')
    
    # Remove API call in watch template (simple string replace of the init function)
    # In watch_template: const res = await fetch...
    # We replace the 'init' function body essentially, or just logic inside it.
    # To keep it safe without rewriting the whole JS in python:
    # We just make sure the `API_URL` variable is empty so it triggers a fallback, 
    # OR we modify the JS to check `window.MATCH_DATA` first.
    # *Assumption*: You will update `watch_template.html` separately to use `window.MATCH_DATA`.
    
    os.makedirs('watch', exist_ok=True)
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(w_html)

    # C. LEAGUE PAGES
    # Iterate Priorities, filter matches, generate page
    print(" > Building League Pages...")
    with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f:
        l_tpl_base = f.read()

    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or not settings.get('hasLink'): continue
        
        # Filter Matches
        l_matches = [m for m in final_matches if key.lower() in m['league'].lower()]
        if not l_matches: continue
        
        slug = slugify(key) + "-streams"
        
        # Generate Rows
        l_live = [m for m in l_matches if m['is_live']]
        l_upc = [m for m in l_matches if not m['is_live']]
        
        l_live_html = "".join([render_match_row(m, "live") for m in l_live])
        l_upc_html = "".join([render_match_row(m) for m in l_upc])
        
        # Inject
        pg = l_tpl_base
        pg = pg.replace('{{PAGE_FILTER}}', key)
        pg = re.sub(r'<div id="live-list">.*?</div>', f'<div id="live-list">{l_live_html}</div>', pg, flags=re.DOTALL)
        if l_live_html: pg = pg.replace('style="display:none;"', '') # Show live section
        
        pg = re.sub(r'<div id="schedule-list".*?>.*?</div>', f'<div id="schedule-list">{l_upc_html}</div>', pg, flags=re.DOTALL)
        pg = pg.replace('loadMatches();', '// Static Loaded')
        
        # Save
        l_dir = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(l_dir, exist_ok=True)
        with open(os.path.join(l_dir, 'index.html'), 'w', encoding='utf-8') as f: f.write(pg)

    print(f"--- ✅ Build Complete in {time.time() - start_time:.2f}s ---")

def getStatusText(ts, is_live):
    if is_live: return "LIVE"
    diff = (ts - time.time()*1000) / 60000
    if diff < 60: return f"In {int(diff)}m"
    hours = diff / 60
    if hours < 24: return f"In {int(hours)}h"
    days = hours / 24
    return f"In {int(days)}d"

if __name__ == "__main__":
    main()
