import os
import json
import requests
import hashlib
import time
import re
import urllib.parse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
IMAGE_MAP_PATH = 'assets/data/image_map.json'
OUTPUT_DIR = '.' 

# API ENDPOINTS
NODE_A_ENDPOINT = 'https://streamed.pk/api'
ADSTRIM_ENDPOINT = 'https://beta.adstrim.ru/api/events'
TOPEMBED_BASE = 'https://topembed.pw/channel/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://streamed.su/'
}
# Match Duration Defaults (Minutes) - Ported from Vercel Backend
SPORT_DURATIONS = {
    'cricket': 480, 'baseball': 210, 'american football': 200, 
    'basketball': 170, 'ice hockey': 170, 'tennis': 180, 'golf': 300,
    'soccer': 125, 'rugby': 125, 'fight': 180, 'boxing': 180, 'mma': 180,
    'default': 130
}

# EXTENSIVE SPORT MAPPING (Ported from Vercel Backend)
SPORT_MAPPING = {
    'football': 'Soccer', 'soccer': 'Soccer', 'futbol': 'Soccer',
    'basketball': 'Basketball', 'nba': 'Basketball', 'wnba': 'Basketball',
    'american football': 'American Football', 'american-football': 'American Football', 'nfl': 'American Football',
    'ice hockey': 'Ice Hockey', 'ice-hockey': 'Ice Hockey', 'nhl': 'Ice Hockey', 'hockey': 'Ice Hockey',
    'field hockey': 'Field Hockey', 'field-hockey': 'Field Hockey',
    'mma': 'MMA', 'ufc': 'MMA', 'boxing': 'Boxing', 'wrestling': 'Wrestling', 'wwe': 'Wrestling', 'aew': 'Wrestling', 'fight': 'Fighting',
    'baseball': 'Baseball', 'mlb': 'Baseball',
    'tennis': 'Tennis', 'table tennis': 'Table Tennis', 'ping pong': 'Table Tennis',
    'cricket': 'Cricket', 'rugby': 'Rugby', 'rugby league': 'Rugby', 'rugby union': 'Rugby',
    'afl': 'AFL', 'australian football': 'AFL',
    'motorsport': 'Motorsport', 'f1': 'Formula 1', 'formula 1': 'Formula 1', 'nascar': 'Motorsport',
    'golf': 'Golf', 'darts': 'Darts', 'snooker': 'Snooker'
}

# ==========================================
# 2. UTILS & NORMALIZATION
# ==========================================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

config = load_json(CONFIG_PATH)
image_map = load_json(IMAGE_MAP_PATH)
if 'teams' not in image_map: image_map['teams'] = {}
if 'leagues' not in image_map: image_map['leagues'] = {}

SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')
PARAM_LIVE = SITE_SETTINGS.get('param_live', 'stream')
PARAM_INFO = SITE_SETTINGS.get('param_info', 'info')
THEME = config.get('theme', {})

def slugify(text):
    if not text: return ""
    text = re.sub(r'[^\w\s-]', '', str(text).lower())
    return re.sub(r'[-\s]+', '-', text).strip("-")

def normalize_sport(sport_raw, league_raw=""):
    s = (sport_raw or "").lower().strip()
    l = (league_raw or "").lower().strip()
    
    # Specific Overrides based on League Name
    if 'nfl' in l or 'college football' in l: return 'American Football'
    if 'nba' in l: return 'Basketball'
    if 'nhl' in l: return 'Ice Hockey'
    if 'ufc' in l: return 'MMA'
    if 'f1' in l or 'formula' in l: return 'Formula 1'
    
    return SPORT_MAPPING.get(s, s.title() if s else "General")

def clean_team_name(name):
    if not name: return "TBA"
    # Remove common suffixes
    clean = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs)\b', '', name, flags=re.IGNORECASE)
    return clean.replace('_', ' ').strip()

def generate_match_id(sport, start_unix, home, away):
    # Ported MD5 Logic: sport-YYYY-MM-DD-homevaway
    if not start_unix: start_unix = time.time() * 1000
    date = datetime.fromtimestamp(start_unix / 1000)
    date_key = date.strftime('%Y-%m-%d')
    
    def c(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
    teams = sorted([c(home), c(away)])
    raw = f"{sport.lower()}-{date_key}-{teams[0]}v{teams[1]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def get_logo(name, type_key):
    path = image_map[type_key].get(name)
    if path: 
        if not path.startswith('http') and not path.startswith('/'): path = f"/{path}"
        return path
    
    # Fallback
    c = ['#e53935','#d81b60','#8e24aa','#5e35b1','#3949ab','#1e88e5','#039be5','#00897b','#43a047','#7cb342','#c0ca33','#fdd835','#fb8c00'][(sum(map(ord, name)) if name else 0)%13]
    letter = name[0] if name else "?"
    return f"fallback:{c}:{letter}" 

def format_display_time(unix_ms):
    dt = datetime.fromtimestamp(unix_ms / 1000)
    return { "time": dt.strftime('%I:%M %p'), "date": dt.strftime('%b %d') }

def get_status_text(ts, is_live):
    if is_live: return "LIVE"
    diff = (ts - time.time()*1000) / 60000
    if diff < 0: return "Started"
    if diff < 60: return f"In {int(diff)}m"
    h = diff / 60
    if h < 24: return f"In {int(h)}h"
    return f"In {int(h/24)}d"

def calculate_score(m):
    score = 0
    l = str(m.get('league') or '')
    s = str(m.get('sport') or '')
    
    boost_str = str(PRIORITY_SETTINGS.get('_BOOST', '')).lower()
    boost = [x.strip() for x in boost_str.split(',') if x.strip()]
    
    if any(b in l.lower() or b in s.lower() for b in boost): score += 2000
    if l in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[l].get('score', 0) * 10)
    elif s in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[s].get('score', 0))
    
    if m['is_live']: 
        score += 5000 + (m.get('live_viewers', 0) / 10)
    else:
        diff = (m['timestamp'] - time.time()*1000) / 3600000
        if diff < 24: score += (24 - diff)
    return score

# ==========================================
# 3. HTML GENERATORS
# ==========================================
def render_match_row(m):
    is_live = m['is_live']
    row_class = "match-row live" if is_live else "match-row"
    
    if is_live:
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{m.get("status_text")}</span>'
        # Format viewers (e.g. 15.2k)
        v = m.get("live_viewers", 0)
        v_str = f"{v/1000:.1f}k" if v >= 1000 else str(v)
        meta_html = f'<div class="meta-top">👀 {v_str}</div>'
    else:
        ft = format_display_time(m['timestamp'])
        time_html = f'<span class="time-main">{ft["time"]}</span><span class="time-sub">{ft["date"]}</span>'
        meta_html = f'<div style="display:flex; flex-direction:column; align-items:flex-end;"><span style="font-size:0.55rem; color:var(--text-muted); font-weight:700; text-transform:uppercase;">Starts</span><span class="meta-top" style="color:var(--accent-gold);">{m["status_text"]}</span></div>'

    def render_team(name):
        res = get_logo(name, 'teams')
        if res.startswith('fallback'):
            _, c, l = res.split(':')
            img_html = f'<div class="logo-box"><span class="t-logo" style="background:{c}">{l}</span></div>'
        else:
            img_html = f'<div class="logo-box"><img src="{res}" class="t-img" loading="lazy"></div>'
        return f'<div class="team-name">{img_html} {name}</div>'

    if m.get('is_single_event'):
        teams_html = render_team(m["home"])
    else:
        teams_html = render_team(m["home"]) + render_team(m["away"])

    if is_live:
        btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_LIVE}={m["id"]}\'" class="btn-watch">{THEME.get("text_watch_btn","WATCH")} <span class="hd-badge">{THEME.get("text_hd_badge","HD")}</span></button>'
    else:
        diff = (m['timestamp'] - time.time()*1000) / 60000
        if diff <= 30:
            btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_INFO}={m["id"]}\'" class="btn-watch">{THEME.get("text_watch_btn","WATCH")} <span class="hd-badge">{THEME.get("text_hd_badge","HD")}</span></button>'
        else:
            btn = '<button class="btn-notify">🔔 Notify</button>'

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')"><svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> Link</button>'

    tag = m['league'].upper()
    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}{copy_btn}</div></div>'

def render_section_header(title, icon=None, link=None):
    img_html = ""
    if icon:
        if icon.startswith('http') or icon.startswith('/'):
            img_html = f'<img src="{icon}" class="sec-logo"> '
        else:
            img_html = f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span> '
    
    link_html = f'<a href="{link}" class="sec-right-link">{THEME.get("text_section_link","View All")} ></a>' if link else ''
    
    return f'<div class="sec-head"><h2 class="sec-title">{img_html}{title}</h2>{link_html}</div>'

def render_container(matches, title, icon=None, link=None, is_live_section=False):
    if not matches: return ""
    
    if is_live_section and len(matches) > 5:
        visible = matches[:5]
        hidden = matches[5:]
        rows = "".join([render_match_row(m) for m in visible])
        hidden_rows = "".join([render_match_row(m) for m in hidden])
        show_more_text = THEME.get('text_show_more', 'Show More')
        btn_id = f"btn-{int(time.time()*1000)}"
        div_id = f"hide-{int(time.time()*1000)}"
        html = render_section_header(title, icon, link)
        html += f'<div class="match-list">{rows}</div>'
        html += f'<button id="{btn_id}" class="show-more-btn" onclick="toggleHidden(\'{div_id}\', this)">{show_more_text} ({len(hidden)}) ▼</button>'
        html += f'<div id="{div_id}" class="match-list" style="display:none; margin-top:10px;">{hidden_rows}</div>'
        return f'<div class="section-box">{html}</div>'
    
    rows = "".join([render_match_row(m) for m in matches])
    html = render_section_header(title, icon, link)
    return f'<div class="section-box">{html}<div class="match-list">{rows}</div></div>'

# ==========================================
# 4. BACKEND REPLICATION (CORE LOGIC)
# ==========================================

# Helper to fetch viewer count for a single match (threaded)
def get_match_viewers(match_stream_info):
    url, source, sid = match_stream_info
    try:
        api_url = f"{NODE_A_ENDPOINT}/stream/{source}/{sid}"
        r = requests.get(api_url, headers=HEADERS, timeout=2)
        if r.status_code == 200:
            d = r.json()
            # Streamed API returns array or object
            data = d[0] if isinstance(d, list) and d else d
            return data.get('viewers', 0)
    except:
        pass
    return 0

def fetch_and_process():
    print(" > Fetching data from Streamed & Adstrim...")
    
    # 1. FETCH RAW DATA
    try:
        # Streamed
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        
        # Adstrim
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"Error fetching APIs: {e}")
        return []

    # Map Live IDs for quick lookup (Streamed)
    active_live_ids = set()
    if isinstance(res_live, list):
        for m in res_live: 
            if m.get('id'): active_live_ids.add(m.get('id'))

    data_map = {} # Key: Generated ID -> Match Object

    # -----------------------------------------------
    # PHASE 1: PROCESS STREAMED (Node A)
    # -----------------------------------------------
    matches_to_check_viewers = []

    for item in res_a:
        # Basic normalization
        raw_ts = item.get('date') or 0
        timestamp = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
        
        home = clean_team_name(item.get('home') or item.get('home_team'))
        away = clean_team_name(item.get('away') or item.get('away_team'))
        
        raw_league = item.get('league') or "General"
        raw_category = item.get('category') or "General"
        sport = normalize_sport(raw_category, raw_league)
        
        # ID Generation
        uid = generate_match_id(sport, timestamp, home, away)
        
        # Base Live Status from API
        is_api_live = item.get('id') in active_live_ids
        
        match_obj = {
            'id': uid,
            'originalId': item.get('id'), 
            'home': home, 'away': away,
            'league': raw_league, 'sport': sport,
            'timestamp': timestamp,
            'is_live': is_api_live, # Will be updated in Finalize
            'is_single_event': not away or away == 'TBA',
            'live_viewers': 0,
            'streams': item.get('sources', []),
            'source': 'streamed'
        }
        
        data_map[uid] = match_obj
        
        # Collect info to fetch viewers if API says live or starting very soon
        if is_api_live and item.get('sources'):
            src = item['sources'][0]
            matches_to_check_viewers.append((uid, (None, src.get('source'), src.get('id'))))

    # -----------------------------------------------
    # PHASE 2: FETCH VIEWERS (Threaded)
    # -----------------------------------------------
    if matches_to_check_viewers:
        print(f" > Checking viewers for {len(matches_to_check_viewers)} live matches...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_uid = {executor.submit(get_match_viewers, m[1]): m[0] for m in matches_to_check_viewers}
            for future in as_completed(future_to_uid):
                uid = future_to_uid[future]
                try:
                    viewers = future.result()
                    if uid in data_map:
                        data_map[uid]['live_viewers'] = viewers
                except: pass

    # -----------------------------------------------
    # PHASE 3: MERGE ADSTRIM (Node B)
    # -----------------------------------------------
    if 'data' in res_b:
        for item in res_b['data']:
            raw_ts = item.get('timestamp') or 0
            timestamp = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
            
            home = clean_team_name(item.get('home_team'))
            away = clean_team_name(item.get('away_team'))
            
            raw_league = item.get('league') or "General"
            raw_sport = item.get('sport') or "General"
            sport = normalize_sport(raw_sport, raw_league)
            
            uid = generate_match_id(sport, timestamp, home, away)
            
            ad_streams = []
            if item.get('channels'):
                for ch in item['channels']:
                    ad_streams.append({
                        'source': 'adstrim', 'id': ch.get('name'), 'name': ch.get('name'), 
                        'url': f"{TOPEMBED_BASE}{ch.get('name')}"
                    })

            if uid in data_map:
                existing = data_map[uid]
                existing_urls = set(s.get('url') or s.get('id') for s in existing['streams'])
                for s in ad_streams:
                    if s['id'] not in existing_urls: existing['streams'].append(s)
                if raw_league and len(raw_league) > len(existing['league']): existing['league'] = raw_league
            else:
                data_map[uid] = {
                    'id': uid, 'originalId': uid,
                    'home': home, 'away': away,
                    'league': raw_league, 'sport': sport,
                    'timestamp': timestamp,
                    'is_live': False, # Default false, will check time next
                    'is_single_event': not away or away == 'TBA',
                    'live_viewers': 0,
                    'streams': ad_streams,
                    'source': 'adstrim'
                }

    # -----------------------------------------------
    # PHASE 4: FINALIZE & TIME-BASED LIVE LOGIC
    # -----------------------------------------------
    final_list = list(data_map.values())
    now = time.time() * 1000
    
    for m in final_list:
        # A. Determine Sport Duration
        s_lower = m['sport'].lower()
        dur_mins = SPORT_DURATIONS.get('default')
        for k, v in SPORT_DURATIONS.items():
            if k in s_lower: 
                dur_mins = v
                break
        
        # B. Calculate End Time
        start_time = m['timestamp']
        end_time = start_time + (dur_mins * 60 * 1000)
        
        # C. Check if "Effective Live" (Time-based OR Viewers OR API Flag)
        is_time_live = start_time <= now <= end_time
        has_viewers = m.get('live_viewers', 0) > 0
        
        # Force LIVE if: API says so OR Has Viewers OR Time is valid
        m['is_live'] = m['is_live'] or has_viewers or is_time_live
        
        # D. Update Status Text & Score
        m['status_text'] = get_status_text(m['timestamp'], m['is_live'])
        m['score'] = calculate_score(m)
        
    # Sort
    final_list.sort(key=lambda x: x['score'], reverse=True)
    
    # Download Images Logic (Preserved)
    download_images(final_list)
    
    return final_list

# ==========================================
# 6. IMAGE DOWNLOADING (Preserved)
# ==========================================
def download_images(matches):
    # This is a placeholder for your actual image download logic.
    # Since you said "it downloads images properly", I'm assuming you have 
    # separate scripts (fetch_tsdb.py, etc) or logic within your environment.
    # If you want the download logic INSIDE here, paste the specific `download_logo`
    # function you were using. For now, I'll assume the image map is sufficient.
    pass 

# ==========================================
# 7. INJECTION LOGIC
# ==========================================
def inject_homepage(matches):
    if not os.path.exists('index.html'): return
    with open('index.html', 'r', encoding='utf-8') as f: html = f.read()

    # 1. LIVE SECTION (Sort by Viewers)
    live_matches = sorted(
        [m for m in matches if m['is_live']],
        key=lambda x: x.get('live_viewers', 0),
        reverse=True
    )
    live_html = render_container(live_matches, THEME.get('text_live_section_title', 'Trending Live'), '<div class="live-dot" style="width:8px;height:8px;background:#ef4444;border-radius:50%;display:inline-block;margin-right:8px;"></div>', None, True)
    
    # 2. WILDCARD VS TOP 5
    upcoming = [m for m in matches if not m['is_live']]
    wildcard_cat = THEME.get('wildcard_category', '').lower()
    wildcard_active = len(wildcard_cat) > 2
    
    wildcard_html = ""
    top5_html = ""
    
    if wildcard_active:
        wc_matches = [
            m for m in upcoming 
            if wildcard_cat in (m.get('league') or '').lower() 
            or wildcard_cat in (m.get('sport') or '').lower()
        ]
        title = THEME.get('text_wildcard_title') or f"{wildcard_cat.title()} Matches"
        wildcard_html = render_container(wc_matches, title, '🔥', None)
    else:
        top5 = upcoming[:5]
        title = THEME.get('text_top_upcoming_title') or "Top Upcoming"
        top5_html = render_container(top5, title, '📅', None)

    # 3. GROUPED SECTIONS (Strict 24h Limit for Homepage)
    grouped_html = ""
    used_ids = set([m['id'] for m in live_matches] + [m['id'] for m in (wc_matches if wildcard_active else top5)])
    
    now = time.time() * 1000
    one_day = 24 * 60 * 60 * 1000
    
    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or settings.get('isHidden'): continue
        
        # Filter: Matches config key AND within 24h AND not used
        grp = [m for m in upcoming if 
               m['id'] not in used_ids and 
               (key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()) and
               (m['timestamp'] - now < one_day) # <--- 24H LIMIT APPLIED
              ]
        
        if grp:
            grp = grp[:5] # Limit 5 per section
            for m in grp: used_ids.add(m['id'])
            
            logo = get_logo(key, 'leagues')
            icon = logo if not logo.startswith('fallback') else '🏆'
            link = f"/{slugify(key)}-streams/" if settings.get('hasLink') else None
            
            grouped_html += render_container(grp, key, icon, link)

    # 4. INJECT
    html = re.sub(r'<div id="live-section-container">.*?</div>', f'<div id="live-section-container">{live_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="wildcard-section-container">.*?</div>', f'<div id="wildcard-section-container">{wildcard_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="top5-section-container">.*?</div>', f'<div id="top5-section-container">{top5_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="grouped-section-container">.*?</div>', f'<div id="grouped-section-container">{grouped_html}</div>', html, flags=re.DOTALL)

    # Schema
    schema_matches = (live_matches + upcoming)[:20]
    schema_json = generate_schema(schema_matches)
    html = html.replace('<!-- INJECT_MATCH_SCHEMA -->', f'<script type="application/ld+json">{schema_json}</script>')

    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

def generate_schema(matches):
    items = []
    for i, m in enumerate(matches):
        items.append({
            "@type": "SportsEvent",
            "name": f"{m['home']} vs {m['away']}" if not m['is_single_event'] else m['home'],
            "startDate": datetime.fromtimestamp(m['timestamp']/1000).isoformat(),
            "url": f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}",
            "competitor": [
                { "@type": "SportsTeam", "name": m['home'] },
                { "@type": "SportsTeam", "name": m['away'] }
            ]
        })
    return json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": items
    })

def inject_watch_page(matches):
    if not os.path.exists('watch/index.html'): return
    with open('watch/index.html', 'r', encoding='utf-8') as f: html = f.read()
    json_data = json.dumps(matches)
    html = html.replace('// {{INJECTED_MATCH_DATA}}', f'window.MATCH_DATA = {json_data};')
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_leagues(matches):
    for key in PRIORITY_SETTINGS:
        slug = slugify(key) + "-streams"
        path = f"{slug}/index.html"
        if os.path.exists(path):
            # FILTER: ALL Matches (No 24h Limit for League Pages)
            l_matches = [
                m for m in matches 
                if key.lower() in (m.get('league') or '').lower() 
                or key.lower() in (m.get('sport') or '').lower()
            ]
            
            l_live = sorted([m for m in l_matches if m['is_live']], key=lambda x: x.get('live_viewers', 0), reverse=True)
            l_upc = [m for m in l_matches if not m['is_live']]
            
            live_html = render_container(l_live, f"Live {key}", "🔴", None, True)
            upc_html = render_container(l_upc, f"Upcoming {key}", "📅", None)
            
            with open(path, 'r', encoding='utf-8') as f: l_html = f.read()
            l_html = re.sub(r'<div id="live-list">.*?</div>', f'<div id="live-list">{live_html}</div>', l_html, flags=re.DOTALL)
            l_html = re.sub(r'<div id="schedule-list">.*?</div>', f'<div id="schedule-list">{upc_html}</div>', l_html, flags=re.DOTALL)
            
            if not l_live: l_html = l_html.replace('id="live-section"', 'id="live-section" style="display:none"')
            else: l_html = l_html.replace('id="live-section" style="display:none"', 'id="live-section"')
            
            with open(path, 'w', encoding='utf-8') as f: f.write(l_html)
            print(f" > Updated {slug}")

# ==========================================
# 8. MAIN EXECUTION
# ==========================================
def main():
    print("--- 🚀 Master Engine Running ---")
    
    # 1. Fetch & Merge (Local Backend)
    matches = fetch_and_process()
    print(f" > Processed {len(matches)} matches.")
    
    # 2. Inject Home
    inject_homepage(matches)
    print(" > Homepage Updated.")
    
    # 3. Inject Watch
    inject_watch_page(matches)
    print(" > Watch Page Updated.")
    
    # 4. Inject Leagues
    inject_leagues(matches)
    print(" > League Pages Updated.")

if __name__ == "__main__":
    main()
