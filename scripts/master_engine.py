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
        try: with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_json(path, data):
    try: with open(path, 'w', encoding='utf-8') as f: json.dump(data, f, indent=2)
    except: pass

config = load_json(CONFIG_PATH)
image_map = load_json(IMAGE_MAP_PATH)
league_map = load_json(LEAGUE_MAP_PATH)

SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')

REVERSE_LEAGUE_MAP = {}
for l_name, teams in league_map.items():
    for t in teams: REVERSE_LEAGUE_MAP[t] = l_name

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
# 3. CORE LOGIC
# ==========================================
def smart_resolve(raw_match):
    raw_home = raw_match.get('home_team') or 'TBA'
    raw_away = raw_match.get('away_team') or 'TBA'
    raw_league = raw_match.get('league') or raw_match.get('category') or "General"
    
    h_slug = slugify(raw_home)
    a_slug = slugify(raw_away)
    
    final_league = "General"
    source_method = "API"

    if h_slug in REVERSE_LEAGUE_MAP and a_slug in REVERSE_LEAGUE_MAP:
        if REVERSE_LEAGUE_MAP[h_slug] == REVERSE_LEAGUE_MAP[a_slug]:
            final_league = REVERSE_LEAGUE_MAP[h_slug]
            source_method = "MapStrict"
    
    if source_method == "API" and ':' in raw_home:
        parts = raw_home.split(':')
        if len(parts) > 1 and 1 < len(parts[0].strip()) < 25:
            final_league = parts[0].strip()
            raw_home = parts[1].strip() # Auto clean home for next step
            source_method = "ColonSplit"

    if source_method == "API":
        l_key = raw_league.lower().replace(' ', '')
        final_league = NAME_FIXES.get(l_key, raw_league.strip())

    def clean_name(name, league):
        if not name or name == 'TBA': return 'TBA'
        if league: name = re.sub(re.escape(league) + r'[:\s-]*', '', name, flags=re.IGNORECASE)
        return re.sub(r'^(NBA|NFL|NHL|MLB|UFC|AFL)[:\s-]*', '', name, flags=re.IGNORECASE).strip()

    final_home = clean_name(raw_home, final_league)
    final_away = clean_name(raw_away, final_league)
    
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

def resolve_and_fetch_logo(team_name, image_payload=None):
    if not team_name or team_name == 'TBA': return None
    if team_name in image_map['teams']: return image_map['teams'][team_name]
    if image_payload:
        slug = slugify(team_name)
        filename = f"{slug}.webp"
        save_path = os.path.join(ASSETS_DIR, 'streamed', filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        urls = [image_payload] if isinstance(image_payload, str) else list(image_payload.values())
        for url in urls:
            if not url.startswith('http'): url = f"{STREAMED_IMG_BASE}{url}.webp"
            try:
                r = requests.get(url, headers=HEADERS, timeout=5)
                if r.status_code == 200:
                    img = Image.open(BytesIO(r.content))
                    if img.mode != 'RGBA': img = img.convert('RGBA')
                    img.save(save_path, "WEBP")
                    rel = f"/assets/logos/streamed/{filename}"
                    image_map['teams'][team_name] = rel
                    return rel
            except: continue
    return None

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
        return f'<div class="logo-box"><span class="t-logo" style="background:#333">{name[0] if name else "?"}</span></div>'

    if m['is_single_event']:
        teams_html = f'<div class="team-name">{get_logo(m["home"])} {m["home"]}</div>'
    else:
        teams_html = f'<div class="team-name">{get_logo(m["home"])} {m["home"]}</div><div class="team-name">{get_logo(m["away"])} {m["away"]}</div>'

    p_live = SITE_SETTINGS.get('param_live', 'stream')
    p_info = SITE_SETTINGS.get('param_info', 'info')
    
    if is_live:
        btn = f'<button onclick="window.location.href=\'/watch/?{p_live}={m["id"]}\'" class="btn-watch">WATCH <span class="hd-badge">HD</span></button>'
    else:
        diff = (m['timestamp'] - time.time()*1000) / 60000
        if diff <= 30: btn = f'<button onclick="window.location.href=\'/watch/?{p_info}={m["id"]}\'" class="btn-watch">WATCH <span class="hd-badge">HD</span></button>'
        else: btn = '<button class="btn-notify">🔔 Notify</button>'

    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{m["league"].upper()}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}</div></div>'

def render_section_content(matches):
    if not matches: return ""
    return "".join([render_match_row(m) for m in matches])

# ==========================================
# 4. MAIN INJECTOR
# ==========================================
def main():
    print("--- 🚀 Master Engine: Fetch & Inject ---")
    
    # 1. Fetch & Normalize
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"❌ API Error: {e}"); return

    active_live_ids = set([m['id'] for m in res_live] if isinstance(res_live, list) else [])
    raw_matches = []

    # Streamed
    for item in res_a:
        resolved = smart_resolve({
            'home_team': item.get('title', '').split(' vs ')[0] if 'title' in item else item.get('home', 'TBA'),
            'away_team': item.get('title', '').split(' vs ')[1] if 'title' in item and ' vs ' in item['title'] else item.get('away', 'TBA'),
            'league': item.get('league') or item.get('category'),
            'sport': item.get('category')
        })
        raw_matches.append({
            'src': 'streamed', 'orig_id': item.get('id'), 'timestamp': normalize_time(item.get('date', 0)),
            'resolved': resolved, 'channels': item.get('sources', []),
            'imgs': {'home': item.get('teams',{}).get('home',{}).get('badge'), 'away': item.get('teams',{}).get('away',{}).get('badge')},
            'is_live': item.get('id') in active_live_ids, 'viewers': 0
        })

    # Adstrim
    if 'data' in res_b:
        for item in res_b['data']:
            resolved = smart_resolve({ 'home_team': item.get('home_team'), 'away_team': item.get('away_team'), 'league': item.get('league'), 'sport': item.get('sport') })
            chans = [{'source': 'adstrim', 'id': c.get('name'), 'type': 'embed', 'url': f"https://topembed.pw/channel/{c.get('name')}"} for c in item.get('channels',[])]
            raw_matches.append({
                'src': 'adstrim', 'orig_id': item.get('id'), 'timestamp': normalize_time(item.get('timestamp', 0)),
                'resolved': resolved, 'channels': chans,
                'imgs': {'home': None, 'away': None}, 'is_live': False, 'viewers': 0
            })

    # Finalize
    final_matches = []
    seen_ids = set()
    
    for m in raw_matches:
        uid = generate_match_id(m['resolved']['sport'], m['timestamp'], m['resolved']['home'], m['resolved']['away'])
        if uid in seen_ids:
            existing = next((x for x in final_matches if x['id'] == uid), None)
            if existing:
                urls = set(c.get('url') for c in existing['stream_channels'])
                for c in m['channels']:
                    if c.get('url') not in urls: existing['stream_channels'].append({'name': f"Server {len(existing['stream_channels'])+1}", 'url': c.get('url') or f"https://streamed.pk/player?id={c['id']}"})
            continue
        
        seen_ids.add(uid)
        if m['imgs']['home']: resolve_and_fetch_logo(m['resolved']['home'], m['imgs']['home'])
        if m['imgs']['away']: resolve_and_fetch_logo(m['resolved']['away'], m['imgs']['away'])
        
        obj = {
            'id': uid, 'originalId': m['orig_id'],
            'home': m['resolved']['home'], 'away': m['resolved']['away'],
            'league': m['resolved']['league'], 'sport': m['resolved']['sport'],
            'timestamp': m['timestamp'], 'is_live': m['is_live'],
            'is_single_event': (not m['resolved']['away'] or m['resolved']['away']=='TBA'),
            'status_text': getStatusText(m['timestamp'], m['is_live']),
            'stream_channels': [{'name': 'Main', 'url': c.get('url') or f"https://streamed.pk/player?id={c['id']}"} for c in m['channels']],
            'live_viewers': m['viewers']
        }
        obj['priority_score'] = calculate_score(obj)
        final_matches.append(obj)

    save_json(IMAGE_MAP_PATH, image_map)
    final_matches.sort(key=lambda x: x['priority_score'], reverse=True)

    # 2. INJECT INTO HOME (index.html)
    if os.path.exists('index.html'):
        with open('index.html', 'r', encoding='utf-8') as f: html = f.read()
        
        # Categorize
        live = [m for m in final_matches if m['is_live']]
        upcoming = [m for m in final_matches if not m['is_live']]
        
        # Replace Live
        live_rows = render_section_content(live)
        if live_rows:
            html = re.sub(r'<div id="live-list".*?>.*?</div>', f'<div id="live-list">{live_rows}</div>', html, flags=re.DOTALL)
            html = html.replace('style="display:none;"', '') # Unhide
        else:
            # If no live matches, ensure it's hidden or empty
            html = re.sub(r'<div id="live-list".*?>.*?</div>', '<div id="live-list"></div>', html, flags=re.DOTALL)
            if 'id="live-section"' in html:
                html = html.replace('<div id="live-section">', '<div id="live-section" style="display:none;">')

        # Replace Top 5
        top5 = upcoming[:5]
        html = re.sub(r'<div id="top-upcoming-container".*?>.*?</div>', f'<div id="top-upcoming-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">📅 Upcoming</h2></div>{render_section_content(top5)}</div></div>', html, flags=re.DOTALL)

        # Replace Grouped
        grouped_html = ""
        used_ids = set([m['id'] for m in live] + [m['id'] for m in top5])
        for key, settings in PRIORITY_SETTINGS.items():
            if key.startswith('_') or settings.get('isHidden'): continue
            grp = [m for m in upcoming if m['id'] not in used_ids and (key.lower() in m['league'].lower() or key.lower() in m['sport'].lower())]
            if grp:
                for m in grp: used_ids.add(m['id'])
                slug = slugify(key) + "-streams"
                link = f'<a href="/{slug}/" class="sec-right-link">View All ></a>' if settings.get('hasLink') else ''
                grouped_html += f'<div class="section-box"><div class="sec-head"><h2 class="sec-title">🏆 {key}</h2>{link}</div>{render_section_content(grp)}</div>'
        
        html = re.sub(r'<div id="grouped-container".*?>.*?</div>', f'<div id="grouped-container">{grouped_html}</div>', html, flags=re.DOTALL)
        
        with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

    # 3. INJECT INTO WATCH (watch/index.html)
    if os.path.exists('watch/index.html'):
        with open('watch/index.html', 'r', encoding='utf-8') as f: w_html = f.read()
        min_matches = [{
            'id': m['id'], 'home': m['home'], 'away': m['away'], 'league': m['league'], 'sport': m['sport'],
            'startTimeUnix': m['timestamp'], 'is_live': m['is_live'], 'status_text': m['status_text'],
            'stream_channels': m['stream_channels'], 'live_viewers': m['live_viewers'], 
            'isSingleEvent': m['is_single_event'], 'originalId': m['originalId']
        } for m in final_matches]
        
        # Replace JS Variable
        # Look for window.MATCH_DATA = ...; or inject if not found (using a marker like <script>)
        # Robust method: Replace the specific line we put in build_site.py
        # But if build_site injects "window.MATCH_DATA = [];", we replace that.
        # Actually, simpler to regex replace the script block or just the variable assignment.
        
        # NOTE: In build_site.py, I didn't explicitly put window.MATCH_DATA = [] because I assumed Python handles it.
        # Let's assume build_site puts: window.MATCH_DATA = [];
        
        # If build_site put a placeholder, we use that. 
        # Strategy: Replace the first <script> tag content if it's our data block, 
        # OR just search for a known string.
        # Let's assume we search for the specific variable name.
        if "window.MATCH_DATA =" in w_html:
             w_html = re.sub(r'window\.MATCH_DATA\s*=\s*\[.*?\];', f'window.MATCH_DATA = {json.dumps(min_matches)};', w_html, flags=re.DOTALL)
        else:
             # Fallback: inject after <script>
             w_html = w_html.replace('<script>', f'<script>window.MATCH_DATA = {json.dumps(min_matches)};')
             
        with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(w_html)

    # 4. INJECT INTO LEAGUES
    # Iterate known league folders
    for key, settings in PRIORITY_SETTINGS.items():
        slug = slugify(key) + "-streams"
        path = os.path.join(OUTPUT_DIR, slug, 'index.html')
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f: l_html = f.read()
            
            l_matches = [m for m in final_matches if key.lower() in m['league'].lower()]
            l_live = [m for m in l_matches if m['is_live']]
            l_upc = [m for m in l_matches if not m['is_live']]
            
            live_rows = render_section_content(l_live)
            upc_rows = render_section_content(l_upc)
            
            l_html = re.sub(r'<div id="live-list".*?>.*?</div>', f'<div id="live-list">{live_rows}</div>', l_html, flags=re.DOTALL)
            if live_rows: l_html = l_html.replace('style="display:none;"', '')
            
            l_html = re.sub(r'<div id="schedule-list".*?>.*?</div>', f'<div id="schedule-list">{upc_rows}</div>', l_html, flags=re.DOTALL)
            
            with open(path, 'w', encoding='utf-8') as f: f.write(l_html)

    print("✅ Data Injection Complete.")

if __name__ == "__main__":
    main()
