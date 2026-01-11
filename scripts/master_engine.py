import os
import json
import requests
import hashlib
import time
import re
from datetime import datetime
from PIL import Image
from io import BytesIO

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
IMAGE_MAP_PATH = 'assets/data/image_map.json'
LEAGUE_MAP_PATH = 'assets/data/league_map.json'
OUTPUT_DIR = '.' 
ASSETS_DIR = 'assets/logos'

NODE_A_ENDPOINT = 'https://streamed.pk/api'
ADSTRIM_ENDPOINT = 'https://beta.adstrim.ru/api/events'
STREAMED_IMG_BASE = "https://streamed.pk/api/images/badge/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

NAME_FIXES = {
    "icehockey": "Ice Hockey", "fieldhockey": "Field Hockey", "tabletennis": "Table Tennis",
    "americanfootball": "American Football", "australianfootball": "AFL", "basketball": "Basketball",
    "football": "Soccer", "soccer": "Soccer", "baseball": "Baseball", "fighting": "Fighting",
    "mma": "MMA", "boxing": "Boxing", "motorsport": "Motorsport", "golf": "Golf"
}

# ==========================================
# 2. UTILS
# ==========================================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except:
        pass

# Load Data
config = load_json(CONFIG_PATH)
image_map = load_json(IMAGE_MAP_PATH)
league_map = load_json(LEAGUE_MAP_PATH)

# Ensure maps exist
if 'teams' not in image_map: image_map['teams'] = {}
if 'leagues' not in image_map: image_map['leagues'] = {}

SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')
THEME = config.get('theme', {})

# Links
PARAM_LIVE = SITE_SETTINGS.get('param_live', 'stream')
PARAM_INFO = SITE_SETTINGS.get('param_info', 'info')

# Build Reverse Map for League Detection (Team Slug -> League Name)
REVERSE_LEAGUE_MAP = {}
for l_name, teams in league_map.items():
    for t in teams: 
        REVERSE_LEAGUE_MAP[t] = l_name

def slugify(text):
    if not text: return ""
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", str(text).lower())).strip("-")

def unslugify(slug):
    return slug.replace('-', ' ').title()

def generate_match_id(sport, start_unix, home, away):
    date = datetime.fromtimestamp(start_unix / 1000)
    date_key = date.strftime('%Y-%m-%d')
    def clean(s): return re.sub(r'[^a-z0-9]', '', re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs)\b', '', (s or '').lower()))
    teams = sorted([clean(home), clean(away)])
    raw = f"{sport.lower()}-{date_key}-{teams[0]}v{teams[1]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def normalize_time(ts):
    return ts * 1000 if ts < 10000000000 else ts

def getStatusText(ts, is_live):
    if is_live: return "LIVE"
    diff = (ts - time.time()*1000) / 60000
    if diff < 0: return "Started"
    if diff < 60: return f"In {int(diff)}m"
    h = diff / 60
    if h < 24: return f"In {int(h)}h"
    return f"In {int(h/24)}d"

def format_display_time(unix_ms):
    dt = datetime.fromtimestamp(unix_ms / 1000)
    return { "time": dt.strftime('%I:%M %p'), "date": dt.strftime('%b %d') }

# ==========================================
# 3. SMART RESOLUTION LOGIC (Your Requirements)
# ==========================================
def smart_resolve(raw_match):
    """
    Determines correct League, Home, Away using Map, Colon Rule, and API fallback.
    """
    raw_home = raw_match.get('home_team') or 'TBA'
    raw_away = raw_match.get('away_team') or 'TBA'
    raw_league = raw_match.get('league') or raw_match.get('category') or "General"
    
    h_slug = slugify(raw_home)
    a_slug = slugify(raw_away)
    
    final_league = "General"
    source_method = "API"

    # RULE 1: STRICT MAP CHECK
    # If both teams are in our league_map.json, we trust the map's league name.
    if h_slug in REVERSE_LEAGUE_MAP and a_slug in REVERSE_LEAGUE_MAP:
        if REVERSE_LEAGUE_MAP[h_slug] == REVERSE_LEAGUE_MAP[a_slug]:
            final_league = REVERSE_LEAGUE_MAP[h_slug]
            source_method = "MapStrict"
    
    # RULE 2: COLON SPLIT (Dynamic)
    # If API says "NBA: Lakers", we split it.
    if source_method == "API" and ':' in raw_home:
        parts = raw_home.split(':')
        if len(parts) > 1:
            candidate_league = parts[0].strip()
            candidate_team = parts[1].strip()
            # Basic validation to ensure it looks like a league
            if 1 < len(candidate_league) < 25 and len(candidate_team) > 0:
                final_league = candidate_league
                raw_home = candidate_team # Update the name for cleanup
                source_method = "ColonSplit"

    # RULE 3: API FALLBACK
    if source_method == "API":
        l_key = raw_league.lower().replace(' ', '')
        final_league = NAME_FIXES.get(l_key, raw_league.strip())

    # CLEANUP NAMES
    # Removes the league name if it's repeated in the team name string
    def clean_name(name, league):
        if not name or name == 'TBA': return 'TBA'
        if league:
            # Case insensitive remove of "LeagueName: " or "LeagueName - "
            name = re.sub(re.escape(league) + r'[:\s-]*', '', name, flags=re.IGNORECASE)
        # Also remove common prefixes
        name = re.sub(r'^(NBA|NFL|NHL|MLB|UFC|AFL)[:\s-]*', '', name, flags=re.IGNORECASE)
        return name.strip()

    final_home = clean_name(raw_home, final_league)
    final_away = clean_name(raw_away, final_league)
    
    # DETERMINE SPORT
    raw_sport = (raw_match.get('sport') or "General").lower()
    final_sport = final_league 
    if "soccer" in raw_sport or "football" in raw_sport: final_sport = "Soccer"
    elif "basket" in raw_sport: final_sport = "Basketball"
    elif "base" in raw_sport: final_sport = "Baseball"
    elif "hock" in raw_sport: final_sport = "Ice Hockey"
    elif "nfl" in raw_sport or "american" in raw_sport: final_sport = "American Football"
    
    return { "league": final_league, "home": final_home, "away": final_away, "sport": final_sport.title() }

def calculate_score(match_data):
    score = 0
    league = match_data['league']
    sport = match_data['sport']
    
    # Check Boost List from Admin
    boost_list = [x.strip() for x in str(PRIORITY_SETTINGS.get('_BOOST', '')).lower().split(',') if x.strip()]
    
    if any(b in league.lower() or b in sport.lower() for b in boost_list): score += 2000
    if league in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[league].get('score', 0) * 10)
    elif sport in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[sport].get('score', 0))
    
    if match_data['is_live']:
        score += 5000 + (match_data.get('live_viewers', 0) / 10)
    else:
        diff = (match_data['timestamp'] - time.time()*1000) / 3600000 
        if diff < 24: score += (24 - diff) 
    return score

# ==========================================
# 4. ASSET PIPELINE (3-Websites Check)
# ==========================================
def resolve_and_fetch_logo(name, type_key, image_payload=None):
    """
    Logic:
    1. Check Local Map (Stop if found)
    2. Check Payloads from Streamed/Upstreams (Stop if found)
    3. (Future) Check TSDB
    """
    if not name or name == 'TBA': return None
    
    # 1. CHECK LOCAL MAP
    if name in image_map[type_key]: 
        return image_map[type_key][name]
    
    slug = slugify(name)
    filename = f"{slug}.webp"
    
    # Determine Folder
    if type_key == 'leagues': subfolder = 'leagues'
    else: subfolder = 'streamed' # Defaulting new teams to streamed folder
    
    save_path = os.path.join(ASSETS_DIR, subfolder, filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)

    # 2. CHECK PAYLOADS (Streamed/Adstrim)
    if image_payload:
        urls = [image_payload] if isinstance(image_payload, str) else list(image_payload)
        for url in urls:
            if not url: continue
            if not url.startswith('http'): url = f"{STREAMED_IMG_BASE}{url}.webp"
            
            try:
                r = requests.get(url, headers=HEADERS, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    if img.mode != 'RGBA': img = img.convert('RGBA')
                    img = img.resize((60, 60), Image.Resampling.LANCZOS)
                    img.save(save_path, "WEBP", quality=90)
                    
                    # Update Map
                    rel_path = f"/assets/logos/{subfolder}/{filename}"
                    image_map[type_key][name] = rel_path
                    return rel_path
            except: continue

    return None

# ==========================================
# 5. HTML ROW GENERATOR
# ==========================================
def render_match_row(m):
    is_live = m['is_live']
    row_class = "match-row live" if is_live else "match-row"
    
    if is_live:
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{m.get("status_text")}</span>'
        meta_html = f'<div class="meta-top">👀 {(m.get("live_viewers",0)/1000):.1f}k</div>'
    else:
        ft = format_display_time(m['timestamp'])
        time_html = f'<span class="time-main">{ft["time"]}</span><span class="time-sub">{ft["date"]}</span>'
        meta_html = f'<div style="display:flex; flex-direction:column; align-items:flex-end;"><span style="font-size:0.55rem; color:var(--text-muted); font-weight:700; text-transform:uppercase;">Starts</span><span class="meta-top" style="color:var(--accent-gold);">{m["status_text"]}</span></div>'

    def get_logo(name):
        url = image_map['teams'].get(name)
        if url: 
            if not url.startswith('http'): url = f"https://{DOMAIN}{url}" if url.startswith('/') else f"https://{DOMAIN}/{url}"
            return f'<div class="logo-box"><img src="{url}" class="t-img" loading="lazy"></div>'
        return f'<div class="logo-box"><span class="t-logo" style="background:#334155">{name[0] if name else "?"}</span></div>'

    if m['is_single_event']:
        teams_html = f'<div class="team-name">{get_logo(m["home"])} {m["home"]}</div>'
    else:
        teams_html = f'<div class="team-name">{get_logo(m["home"])} {m["home"]}</div><div class="team-name">{get_logo(m["away"])} {m["away"]}</div>'
    
    if is_live:
        btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_LIVE}={m["id"]}\'" class="btn-watch">WATCH <span class="hd-badge">HD</span></button>'
    else:
        diff = (m['timestamp'] - time.time()*1000) / 60000
        if diff <= 30:
            btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_INFO}={m["id"]}\'" class="btn-watch">WATCH <span class="hd-badge">HD</span></button>'
        else:
            btn = '<button class="btn-notify">🔔 Notify</button>'

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')"><svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> Link</button>'

    tag = m['league'].upper()
    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}{copy_btn}</div></div>'

def render_section_content(matches):
    if not matches: return ""
    return "".join([render_match_row(m) for m in matches])

# ==========================================
# 6. MAIN PROCESS
# ==========================================
def main():
    print("--- 🚀 Master Engine: Fetch & Inject ---")
    
    # 1. Fetch
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"❌ API Error: {e}"); return

    active_live_ids = set([m['id'] for m in res_live] if isinstance(res_live, list) else [])
    raw_matches = []

    # 2. Parse Streamed
    for item in res_a:
        resolved = smart_resolve({
            'home_team': item.get('title', '').split(' vs ')[0] if 'title' in item else item.get('home', 'TBA'),
            'away_team': item.get('title', '').split(' vs ')[1] if 'title' in item and ' vs ' in item['title'] else item.get('away', 'TBA'),
            'league': item.get('league') or item.get('category'),
            'sport': item.get('category')
        })
        
        # Capture Images for Pipeline
        imgs_home = []
        if item.get('teams', {}).get('home', {}).get('badge'): imgs_home.append(item['teams']['home']['badge'])
        imgs_away = []
        if item.get('teams', {}).get('away', {}).get('badge'): imgs_away.append(item['teams']['away']['badge'])

        raw_matches.append({
            'src': 'streamed', 'orig_id': item.get('id'), 'timestamp': normalize_time(item.get('date', 0)),
            'resolved': resolved, 'channels': item.get('sources', []),
            'img_payload': {'home': imgs_home, 'away': imgs_away, 'league': []},
            'is_live': item.get('id') in active_live_ids, 'viewers': 0
        })

    # 3. Parse Adstrim
    if 'data' in res_b:
        for item in res_b['data']:
            resolved = smart_resolve({ 'home_team': item.get('home_team'), 'away_team': item.get('away_team'), 'league': item.get('league'), 'sport': item.get('sport') })
            chans = [{'source': 'adstrim', 'id': c.get('name'), 'type': 'embed', 'url': f"https://topembed.pw/channel/{c.get('name')}"} for c in item.get('channels',[])]
            
            # Adstrim Images
            imgs_home = [item.get('home_team_image')] if item.get('home_team_image') else []
            imgs_away = [item.get('away_team_image')] if item.get('away_team_image') else []
            imgs_league = [item.get('league_image')] if item.get('league_image') else []

            raw_matches.append({
                'src': 'adstrim', 'orig_id': item.get('id'), 'timestamp': normalize_time(item.get('timestamp', 0)),
                'resolved': resolved, 'channels': chans,
                'img_payload': {'home': imgs_home, 'away': imgs_away, 'league': imgs_league},
                'is_live': False, 'viewers': 0
            })

    # 4. Finalize & Asset Resolution
    final_matches = []
    seen_ids = set()
    
    print(f" > Processing {len(raw_matches)} matches...")
    
    for m in raw_matches:
        uid = generate_match_id(m['resolved']['sport'], m['timestamp'], m['resolved']['home'], m['resolved']['away'])
        
        # --- TRIGGER ASSET CHECK ---
        # Pass the CLEANED name to check/save the logo correctly
        resolve_and_fetch_logo(m['resolved']['home'], 'teams', m['img_payload']['home'])
        resolve_and_fetch_logo(m['resolved']['away'], 'teams', m['img_payload']['away'])
        resolve_and_fetch_logo(m['resolved']['league'], 'leagues', m['img_payload']['league'])
        # ---------------------------

        if uid in seen_ids:
            existing = next((x for x in final_matches if x['id'] == uid), None)
            if existing:
                urls = set(c.get('url') for c in existing['stream_channels'])
                for c in m['channels']:
                    if c.get('url') not in urls: existing['stream_channels'].append({'name': f"Server {len(existing['stream_channels'])+1}", 'url': c.get('url') or f"https://streamed.pk/player?id={c['id']}"})
            continue
        
        seen_ids.add(uid)
        is_single = (not m['resolved']['away'] or m['resolved']['away']=='TBA')
        
        obj = {
            'id': uid, 'originalId': m['orig_id'],
            'home': m['resolved']['home'], 'away': m['resolved']['away'],
            'league': m['resolved']['league'], 'sport': m['resolved']['sport'],
            'timestamp': m['timestamp'], 'is_live': m['is_live'],
            'is_single_event': is_single,
            'status_text': getStatusText(m['timestamp'], m['is_live']),
            'stream_channels': [{'name': 'Main', 'url': c.get('url') or f"https://streamed.pk/player?id={c['id']}"} for c in m['channels']],
            'live_viewers': m['viewers']
        }
        obj['priority_score'] = calculate_score(obj)
        final_matches.append(obj)

    # Save Updated Map (CRITICAL)
    save_json(IMAGE_MAP_PATH, image_map)
    final_matches.sort(key=lambda x: x['priority_score'], reverse=True)

    # 5. INJECT HTML INTO HOME
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f: html = f.read()
        
        live = [m for m in final_matches if m['is_live']]
        upcoming = [m for m in final_matches if not m['is_live']]
        
        live_rows = render_section_content(live)
        if live_rows:
            html = re.sub(r'<div id="live-list".*?>.*?</div>', f'<div id="live-list" class="match-list">{live_rows}</div>', html, flags=re.DOTALL)
            html = html.replace('style="display:none;"', '') 
        else:
            html = re.sub(r'<div id="live-list".*?>.*?</div>', '', html, flags=re.DOTALL)

        # Top 5
        html = re.sub(r'<div id="top-upcoming-container".*?>.*?</div>', f'<div id="top-upcoming-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">📅 Upcoming</h2></div><div>{render_section_content(upcoming[:5])}</div></div>', html, flags=re.DOTALL)
        
        # Grouped
        grouped_html = ""
        used_ids = set([m['id'] for m in live] + [m['id'] for m in upcoming[:5]])
        for key, settings in PRIORITY_SETTINGS.items():
            if key.startswith('_') or settings.get('isHidden'): continue
            grp = [m for m in upcoming if m['id'] not in used_ids and (key.lower() in m['league'].lower() or key.lower() in m['sport'].lower())]
            if grp:
                for m in grp: used_ids.add(m['id'])
                slug = slugify(key) + "-streams"
                link = f'<a href="/{slug}/" class="sec-right-link">View All ></a>' if settings.get('hasLink') else ''
                grouped_html += f'<div class="section-box"><div class="sec-head"><h2 class="sec-title">🏆 {key}</h2>{link}</div><div>{render_section_content(grp)}</div></div>'
        
        html = re.sub(r'<div id="grouped-container".*?>.*?</div>', f'<div id="grouped-container">{grouped_html}</div>', html, flags=re.DOTALL)
        
        with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

    # 6. INJECT WATCH
    if os.path.exists('watch/index.html'):
        with open('watch/index.html', 'r', encoding='utf-8') as f: w_html = f.read()
        min_matches = [{'id':m['id'], 'home':m['home'], 'away':m['away'], 'league':m['league'], 'sport':m['sport'], 'startTimeUnix':m['timestamp'], 'is_live':m['is_live'], 'status_text':m['status_text'], 'stream_channels':m['stream_channels'], 'live_viewers':m['live_viewers'], 'isSingleEvent':m['is_single_event'], 'originalId':m['originalId']} for m in final_matches]
        json_str = json.dumps(min_matches)
        
        # Safe Lambda Replacement
        if "window.MATCH_DATA =" in w_html:
             w_html = re.sub(r'window\.MATCH_DATA\s*=\s*\[.*?\];', lambda match: f'window.MATCH_DATA = {json_str};', w_html, flags=re.DOTALL)
        else:
             w_html = w_html.replace('<script>', f'<script>window.MATCH_DATA = {json_str};')
        with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(w_html)

    # 7. INJECT LEAGUES
    for key, settings in PRIORITY_SETTINGS.items():
        slug = slugify(key) + "-streams"
        path = os.path.join(OUTPUT_DIR, slug, 'index.html')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: l_html = f.read()
            l_matches = [m for m in final_matches if key.lower() in m['league'].lower()]
            live_rows = render_section_content([m for m in l_matches if m['is_live']])
            upc_rows = render_section_content([m for m in l_matches if not m['is_live']])
            if live_rows:
                l_html = re.sub(r'<div id="live-list"[^>]*>.*?</div>', f'<div id="live-list">{live_rows}</div>', l_html, flags=re.DOTALL)
                l_html = l_html.replace('style="display:none;"', '')
            l_html = re.sub(r'<div id="schedule-list"[^>]*>.*?</div>', f'<div id="schedule-list">{upc_rows}</div>', l_html, flags=re.DOTALL)
            with open(path, 'w', encoding='utf-8') as f: f.write(l_html)

    print("✅ Completed.")

if __name__ == "__main__":
    main()
