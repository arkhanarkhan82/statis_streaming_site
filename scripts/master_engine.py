import os
import json
import requests
import hashlib
import time
import re
import urllib.parse
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
from io import BytesIO

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================
CONFIG_PATH = 'data/config.json'
IMAGE_MAP_PATH = 'assets/data/image_map.json'
LEAGUE_MAP_PATH = 'assets/data/league_map.json'
TEMPLATE_MASTER = 'assets/master_template.html'
TEMPLATE_WATCH = 'assets/watch_template.html'
TEMPLATE_LEAGUE = 'assets/league_template.html'
OUTPUT_DIR = '.' 

# API ENDPOINTS
NODE_A_ENDPOINT = 'https://streamed.pk/api'
ADSTRIM_ENDPOINT = 'https://beta.adstrim.ru/api/events'
TOPEMBED_BASE = 'https://topembed.pw/channel/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://streamed.su/'
}

# Match Duration Defaults (Minutes)
SPORT_DURATIONS = {
    'cricket': 480, 'baseball': 210, 'american football': 200, 
    'basketball': 170, 'ice hockey': 170, 'tennis': 180, 'golf': 300,
    'soccer': 125, 'rugby': 125, 'fight': 180, 'boxing': 180, 'mma': 180,
    'default': 130
}

# Sport Mapping
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

# ==============================================================================
# 2. UTILITIES & LOADERS
# ==============================================================================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def ensure_unit(val, unit='px'):
    if val is None: return f"0{unit}"
    s_val = str(val).strip()
    if not s_val: return f"0{unit}"
    if s_val.isdigit(): return f"{s_val}{unit}"
    return s_val

def hex_to_rgba(hex_code, opacity):
    if not hex_code or not hex_code.startswith('#'): return hex_code
    hex_code = hex_code.lstrip('#')
    try:
        if len(hex_code) == 3: hex_code = ''.join([c*2 for c in hex_code])
        r = int(hex_code[0:2], 16)
        g = int(hex_code[2:4], 16)
        b = int(hex_code[4:6], 16)
        return f"rgba({r}, {g}, {b}, {opacity})"
    except:
        return hex_code

# Load Configs
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

# Build Reverse League Map
REVERSE_LEAGUE_MAP = {}
league_data = load_json(LEAGUE_MAP_PATH)
if league_data:
    for league_name, teams_list in league_data.items():
        if isinstance(teams_list, list):
            for team_slug in teams_list:
                REVERSE_LEAGUE_MAP[team_slug.lower().strip()] = league_name

# ==============================================================================
# 3. TEXT & DATA NORMALIZATION
# ==============================================================================
def slugify(text):
    if not text: return ""
    text = re.sub(r'[^\w\s-]', '', str(text).lower())
    return re.sub(r'[-\s]+', '-', text).strip("-")

def clean_team_name(name):
    if not name or name == 'TBA': return "TBA"
    clean = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs)\b', '', name, flags=re.IGNORECASE)
    clean = clean.replace('_', ' ').strip()
    return clean

def tokenize_name(text):
    if not text: return set()
    clean = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs|at|united|city|real|inter|ac|sv)\b', '', text.lower())
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return set(w for w in clean.split() if len(w) > 2)

def normalize_sport(sport_raw, league_raw=""):
    s = (sport_raw or "").lower().strip()
    l = (league_raw or "").lower().strip()
    if 'nfl' in l or 'college football' in l: return 'American Football'
    if 'nba' in l: return 'Basketball'
    if 'nhl' in l: return 'Ice Hockey'
    if 'ufc' in l: return 'MMA'
    if 'f1' in l or 'formula' in l: return 'Formula 1'
    return SPORT_MAPPING.get(s, s.title() if s else "General")

def get_display_time(unix_ms):
    utc_dt = datetime.fromtimestamp(unix_ms / 1000, tz=timezone.utc)
    if TARGET_COUNTRY == 'UK':
        local_dt = utc_dt
        time_str = local_dt.strftime('%H:%M GMT')
        date_str = local_dt.strftime('%d %b')
    else:
        local_dt = utc_dt - timedelta(hours=5)
        time_str = local_dt.strftime('%I:%M %p ET')
        date_str = local_dt.strftime('%b %d')
    return { "time": time_str, "date": date_str }

def get_status_text(ts, is_live):
    if is_live: return "LIVE"
    now_ms = time.time() * 1000
    diff_min = (ts - now_ms) / 60000
    
    if diff_min < 0: return "Started" 
    if diff_min < 60: return f"In {int(diff_min)}m"
    h = diff_min / 60
    if h < 24: return f"In {int(h)}h"
    return f"In {int(h/24)}d"

def get_logo(name, type_key):
    path = image_map[type_key].get(name)
    if path: 
        if not path.startswith('http') and not path.startswith('/'): path = f"/{path}"
        return path
    c = ['#e53935','#d81b60','#8e24aa','#5e35b1','#3949ab','#1e88e5','#039be5','#00897b','#43a047','#7cb342','#c0ca33','#fdd835','#fb8c00'][(sum(map(ord, name)) if name else 0)%13]
    letter = name[0] if name else "?"
    return f"fallback:{c}:{letter}" 

def generate_seo_id(home, away, original_id):
    h = slugify(home)
    a = slugify(away) if away and away != "TBA" else ""
    base = f"{h}-vs-{a}" if a else h
    return f"{base}-{original_id}"

# ==============================================================================
# 4. CORE LOGIC: RESOLUTION & MATCHING
# ==============================================================================
def resolve_match_identity(raw_match):
    raw_home = raw_match.get('home_raw') or ''
    raw_away = raw_match.get('away_raw') or ''
    raw_title = raw_match.get('title_raw') or ''
    
    home = clean_team_name(raw_home)
    away = clean_team_name(raw_away)
    
    # --- PARSING FIX: Parse Title if Home/Away are invalid (TBA) ---
    if (not home or home == "TBA" or home == "") and raw_title:
        # Regex to find ' vs ' or ' v ' or ' - ' (case insensitive)
        split_parts = re.split(r'\s+(?:vs|v)\s+', raw_title, flags=re.IGNORECASE, maxsplit=1)
        
        if len(split_parts) == 2:
            home = clean_team_name(split_parts[0])
            away = clean_team_name(split_parts[1])
        else:
            home = clean_team_name(raw_title)

    # Secondary check: If Home is valid but Away is TBA, check title again
    if (not away or away == "TBA") and raw_title and home and home != "TBA":
         split_parts = re.split(r'\s+(?:vs|v)\s+', raw_title, flags=re.IGNORECASE, maxsplit=1)
         if len(split_parts) == 2:
             if clean_team_name(split_parts[0]) == home:
                 away = clean_team_name(split_parts[1])
    # -------------------------------------------------
    
    is_single = (not away or away == "TBA" or away == "")
    league_name = None
    
    # Check Colon in name
    if ":" in home:
        parts = home.split(":", 1)
        if len(parts) == 2:
            lc = parts[0].strip()
            if len(lc) > 2 and not any(char.isdigit() for char in lc):
                league_name = lc
                home = clean_team_name(parts[1])
    
    # Reverse Map Lookup
    h_slug = slugify(home)
    if h_slug in REVERSE_LEAGUE_MAP:
        league_name = REVERSE_LEAGUE_MAP[h_slug]
    
    if not is_single:
        a_slug = slugify(away)
        if a_slug in REVERSE_LEAGUE_MAP:
            if not league_name: league_name = REVERSE_LEAGUE_MAP[a_slug]

    # Fallback to Adstrim
    if not league_name and raw_match.get('adstrim_league'):
        league_name = raw_match['adstrim_league']
        
    # Fallback to Sport
    if not league_name or league_name.lower() in ["other", "general"]:
        league_name = normalize_sport(raw_match.get('sport_raw'), "")

    sport = normalize_sport(raw_match.get('sport_raw'), league_name)

    return { "home": home, "away": away, "league": league_name, "sport": sport, "is_single": is_single }

def is_fuzzy_match(m1, m2):
    if abs(m1['timestamp'] - m2['timestamp']) > 20 * 60 * 1000: return False
    
    t1_h = tokenize_name(m1['home'])
    t2_h = tokenize_name(m2['home'])
    
    if not t1_h.isdisjoint(t2_h):
        if m1['is_single'] or m2['is_single']: return True
        t1_a = tokenize_name(m1['away'])
        t2_a = tokenize_name(m2['away'])
        if not t1_a.isdisjoint(t2_a): return True
        
    return False

# ==============================================================================
# 5. DATA FETCHING & PROCESSING ENGINE
# ==============================================================================
def get_viewers(stream_info):
    url, src, sid = stream_info
    try:
        r = requests.get(f"{NODE_A_ENDPOINT}/stream/{src}/{sid}", headers=HEADERS, timeout=2)
        if r.status_code == 200:
            d = r.json()
            data = d[0] if isinstance(d, list) and d else d
            return data.get('viewers', 0)
    except: pass
    return 0

def fetch_and_merge():
    print(" > Fetching APIs...")
    matches = []
    
    res_a = []
    res_live = []
    res_b = {'data': []}

    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        print(f"   - Streamed All: {len(res_a)} raw items")
    except Exception as e: print(f"   ! Streamed All Failed: {e}")

    try:
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        print(f"   - Streamed Live: {len(res_live)} raw items")
    except Exception as e: print(f"   ! Streamed Live Failed: {e}")

    try:
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
        count_b = len(res_b.get('data', [])) if res_b else 0
        print(f"   - Adstrim: {count_b} raw items")
    except Exception as e: print(f"   ! Adstrim Failed: {e}")

    active_live_ids = set()
    if isinstance(res_live, list):
        for m in res_live: 
            if m.get('id'): active_live_ids.add(m.get('id'))

    viewers_to_check = []

    # 1. STREAMED PROCESSING (Node A)
    for item in res_a:
        raw_ts = item.get('date') or 0
        timestamp = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
        
        # --- NEW: Capture Image Metadata from Streamed ---
        teams = item.get('teams', {})
        home_badge = teams.get('home', {}).get('badge')
        away_badge = teams.get('away', {}).get('badge')
        
        resolved = resolve_match_identity({
            'home_raw': item.get('home') or item.get('home_team'),
            'away_raw': item.get('away') or item.get('away_team'),
            'title_raw': item.get('title'),
            'sport_raw': item.get('category'),
            'adstrim_league': None 
        })
        
        date_str = datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
        uid = hashlib.md5(f"{resolved['sport']}-{date_str}-{resolved['home']}".encode()).hexdigest()
        is_live = item.get('id') in active_live_ids
        
        matches.append({
            '_uid': uid,
            'original_id': item.get('id'),
            'home': resolved['home'], 'away': resolved['away'],
            'league': resolved['league'], 'sport': resolved['sport'],
            'timestamp': timestamp, 'is_live': is_live,
            'is_single': resolved['is_single'],
            'streams': item.get('sources', []),
            'duration': None, 'live_viewers': 0,
            
            # STORE IMAGE DATA FOR DOWNLOADER
            '_img_meta': {
                'source': 'streamed',
                'home_id': home_badge,
                'away_id': away_badge,
                'poster': item.get('poster')
            }
        })
        
        if is_live and item.get('sources'):
            src = item['sources'][0]
            viewers_to_check.append((len(matches)-1, (None, src.get('source'), src.get('id'))))

    # 2. VIEWERS CHECK
    if viewers_to_check:
        print(f" > Checking viewers for {len(viewers_to_check)} matches...")
        with ThreadPoolExecutor(max_workers=10) as ex:
            future_map = {ex.submit(get_viewers, m[1]): m[0] for m in viewers_to_check}
            for fut in as_completed(future_map):
                idx = future_map[fut]
                try: matches[idx]['live_viewers'] = fut.result()
                except: pass

    # 3. ADSTRIM MERGE (Node B)
    if 'data' in res_b:
        for item in res_b['data']:
            raw_ts = item.get('timestamp') or 0
            ts = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
            
            resolved = resolve_match_identity({
                'home_raw': item.get('home_team'),
                'away_raw': item.get('away_team'),
                'sport_raw': item.get('sport'),
                'adstrim_league': item.get('league')
            })
            
            ad_streams = []
            if item.get('channels'):
                for ch in item['channels']:
                    ad_streams.append({
                        'source': 'adstrim', 
                        'id': ch.get('name'), 
                        'name': ch.get('name'), 
                        'url': f"{TOPEMBED_BASE}{ch.get('name')}"
                    })

            # Fuzzy Match
            matched_idx = -1
            candidate = {'timestamp': ts, 'home': resolved['home'], 'away': resolved['away'], 'is_single': resolved['is_single']}
            
            for i, m in enumerate(matches):
                if is_fuzzy_match(m, candidate):
                    matched_idx = i
                    break
            
            if matched_idx > -1:
                # MERGE DETECTED
                target = matches[matched_idx]
                
                # Update names if existing was TBA
                if (target['home'] == 'TBA' or target['home'] == '') and resolved['home'] != 'TBA':
                    target['home'] = resolved['home']
                if (target['away'] == 'TBA' or target['away'] == '') and resolved['away'] != 'TBA':
                    target['away'] = resolved['away']
                
                # Merge Streams
                existing_urls = set(s.get('url') or s.get('id') for s in target['streams'])
                for s in ad_streams:
                    if s['id'] not in existing_urls: target['streams'].append(s)
                
                if item.get('duration'): target['duration'] = item.get('duration')
                
                # --- LEAGUE FIX: Use Adstrim League if currently generic ---
                cur_l = target['league'].lower()
                cur_s = target['sport'].lower()
                if resolved['league'] and ("general" in cur_l or "other" in cur_l or cur_l == cur_s):
                    target['league'] = resolved['league']
                
                # MERGE IMAGE DATA
                if '_img_meta' in target:
                    target['_img_meta']['adstrim_home'] = item.get('home_team_image')
                    target['_img_meta']['adstrim_away'] = item.get('away_team_image')
                    target['_img_meta']['adstrim_league'] = item.get('league_image')
                    target['_img_meta']['adstrim_home_dict'] = item.get('home_team_images')
                    target['_img_meta']['adstrim_away_dict'] = item.get('away_team_images')

            else:
                # ADD NEW
                date_str = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d')
                uid = hashlib.md5(f"{resolved['sport']}-{date_str}-{resolved['home']}".encode()).hexdigest()
                
                matches.append({
                    '_uid': uid,
                    'original_id': f"ad_{item.get('id')}",
                    'home': resolved['home'], 'away': resolved['away'],
                    'league': resolved['league'], 'sport': resolved['sport'],
                    'timestamp': ts, 'is_live': False,
                    'is_single': resolved['is_single'],
                    'streams': ad_streams,
                    'duration': item.get('duration'),
                    'live_viewers': 0,
                    
                    # STORE IMAGE DATA
                    '_img_meta': {
                        'source': 'adstrim',
                        'adstrim_home': item.get('home_team_image'),
                        'adstrim_away': item.get('away_team_image'),
                        'adstrim_league': item.get('league_image'),
                        'adstrim_home_dict': item.get('home_team_images'),
                        'adstrim_away_dict': item.get('away_team_images')
                    }
                })

    # 4. FINAL PROCESSING
    final_list = []
    now = time.time() * 1000
    
    print(f" > Raw matches before filtering: {len(matches)}")
    
    for m in matches:
        dur_mins = m.get('duration')
        if not dur_mins:
            s_low = m['sport'].lower()
            dur_mins = SPORT_DURATIONS.get('default')
            for k, v in SPORT_DURATIONS.items():
                if k in s_low: dur_mins = v; break
        
        try: dur_mins = int(dur_mins)
        except: dur_mins = 130
        
        end_time = m['timestamp'] + (dur_mins * 60 * 1000)
        is_finished = now > end_time
        has_viewers = m['live_viewers'] > 0
        
        if is_finished and not has_viewers: continue
            
        m['is_live'] = m['is_live'] or has_viewers or (m['timestamp'] <= now <= end_time)
        m['status_text'] = get_status_text(m['timestamp'], m['is_live'])
        m['id'] = generate_seo_id(m['home'], m['away'], m['original_id'])
        
        # --- SCORING LOGIC ---
        score = 0
        l_low = m['league'].lower()
        
        if m['is_live']: score += 10000 + m['live_viewers']

        if '_BOOST' in PRIORITY_SETTINGS:
            boosts = [x.strip().lower() for x in PRIORITY_SETTINGS['_BOOST'].split(',')]
            if any(b in l_low for b in boosts): score += 2000
            
        # PENALTY: Downgrade 'TBA' names
        if m['home'] == "TBA" or m['away'] == "TBA":
            score -= 5000
            
        # BOOST: Give Adstrim/Merged matches a nudge
        if str(m['original_id']).startswith('ad_') or len(m['streams']) > 1:
            score += 500

        m['score'] = score
        final_list.append(m)
        
    return final_list

# ==============================================================================
# 6. HTML RENDERERS
# ==============================================================================
def render_match_row(m, section_title=""):
    is_live = m['is_live']
    row_class = "match-row live" if is_live else "match-row"
    
    if is_live:
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{m.get("status_text")}</span>'
        v = m.get("live_viewers", 0)
        v_str = f"{v/1000:.1f}k" if v >= 1000 else str(v)
        meta_html = f'<div class="meta-top">👀 {v_str}</div>'
    else:
        ft = get_display_time(m['timestamp'])
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

    teams_html = render_team(m["home"])
    if not m['is_single']: teams_html += render_team(m["away"])

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    
    svg_icon = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>'
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')">{svg_icon} Link</button>'

    btn = ""
    diff = (m['timestamp'] - time.time()*1000) / 60000
    
    # Use standard <a href> tag
    if is_live or diff <= 30:
        btn = f'<a href="{info_url}" class="btn-watch">{THEME.get("text_watch_btn","WATCH")} <span class="hd-badge">{THEME.get("text_hd_badge","HD")}</span></a>'
    else:
        btn = '<button class="btn-notify">🔔 Notify</button>'

    tag = m['league'].upper()
    if section_title and section_title.lower() in m['league'].lower():
        tag = m['sport'].upper()

    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}{copy_btn}</div></div>'

def render_container(matches, title, icon=None, link=None, is_live_section=False):
    if not matches: return ""
    
    img_html = ""
    if icon:
        if icon.startswith('http') or icon.startswith('/'):
            img_html = f'<img src="{icon}" class="sec-logo"> '
        else:
            img_html = f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span> '
    
    link_html = f'<a href="{link}" class="sec-right-link">{THEME.get("text_section_link","View All")} ></a>' if link else ''
    header = f'<div class="sec-head"><h2 class="sec-title">{img_html}{title}</h2>{link_html}</div>'

    rows_html = ""
    hidden_html = ""
    
    if is_live_section and len(matches) > 5:
        visible = matches[:5]
        hidden = matches[5:]
        rows_html = "".join([render_match_row(m, title) for m in visible])
        hidden_rows = "".join([render_match_row(m, title) for m in hidden])
        
        btn_id = f"btn-{int(time.time()*1000)}"
        div_id = f"hide-{int(time.time()*1000)}"
        
        hidden_html = f'''
        <button id="{btn_id}" class="show-more-btn" onclick="toggleHidden('{div_id}', this)">{THEME.get("text_show_more","Show More")} ({len(hidden)}) ▼</button>
        <div id="{div_id}" class="match-list" style="display:none; margin-top:10px;">{hidden_rows}</div>
        '''
    else:
        rows_html = "".join([render_match_row(m, title) for m in matches])

    return f'<div class="section-box">{header}<div class="match-list">{rows_html}</div>{hidden_html}</div>'

# ==============================================================================
# 7. TEMPLATE INJECTION
# ==============================================================================
def apply_theme_to_template(html, page_data=None):
    if page_data is None: page_data = {}
    
    def make_border(w, c): return f"{ensure_unit(THEME.get(w,'1'))} solid {THEME.get(c,'#333')}"
    THEME['sec_border_live'] = make_border('sec_border_live_width', 'sec_border_live_color')
    THEME['sec_border_upcoming'] = make_border('sec_border_upcoming_width', 'sec_border_upcoming_color')
    THEME['sec_border_wildcard'] = make_border('sec_border_wildcard_width', 'sec_border_wildcard_color')
    THEME['sec_border_leagues'] = make_border('sec_border_leagues_width', 'sec_border_leagues_color')
    THEME['sec_border_grouped'] = make_border('sec_border_grouped_width', 'sec_border_grouped_color')
    THEME['sys_status_border'] = make_border('sys_status_border_width', 'sys_status_border_color')
    
    for k in ['logo_image_size', 'border_radius_base', 'container_max_width', 'header_max_width', 'hero_pill_radius', 'button_border_radius', 'section_logo_size', 'sys_status_radius', 'sys_status_dot_size', 'league_card_radius', 'hero_box_width']:
        if k in THEME: THEME[k] = ensure_unit(THEME[k])

    s_bg_hex = THEME.get('sys_status_bg_color', '#22c55e')
    s_bg_op = THEME.get('sys_status_bg_opacity', '0.1')
    THEME['sys_status_bg_color'] = 'transparent' if str(THEME.get('sys_status_bg_transparent')).lower() == 'true' else hex_to_rgba(s_bg_hex, s_bg_op)
    THEME['sys_status_display'] = 'inline-flex' if THEME.get('sys_status_visible', True) else 'none'

    replacements = {
        'META_TITLE': page_data.get('meta_title', ''),
        'META_DESC': page_data.get('meta_desc', ''),
        'H1_TITLE': page_data.get('h1_title', ''),
        'H1_ALIGN': page_data.get('h1_align', 'left'),
        'HERO_TEXT': page_data.get('hero_text', ''),
        'ARTICLE_CONTENT': page_data.get('article', ''),
        'SITE_NAME': f"{SITE_SETTINGS.get('title_part_1','')}{SITE_SETTINGS.get('title_part_2','')}",
        'CANONICAL_URL': page_data.get('canonical_url', f"https://{DOMAIN}/"),
        'FAVICON': SITE_SETTINGS.get('favicon_url', ''),
        'OG_IMAGE': SITE_SETTINGS.get('logo_url', ''),
        'LOGO_PRELOAD': f'<link rel="preload" as="image" href="{SITE_SETTINGS.get("logo_url")}">' if SITE_SETTINGS.get('logo_url') else '',
        'API_URL': SITE_SETTINGS.get('api_url', ''),
        'TARGET_COUNTRY': TARGET_COUNTRY,
        'PARAM_LIVE': PARAM_LIVE,
        'PARAM_INFO': PARAM_INFO,
        'DOMAIN': DOMAIN,
        
        'TEXT_LIVE_SECTION_TITLE': THEME.get('text_live_section_title', 'Trending Live'),
        'TEXT_WILDCARD_TITLE': THEME.get('text_wildcard_title', ''),
        'TEXT_TOP_UPCOMING_TITLE': THEME.get('text_top_upcoming_title', 'Top Upcoming'),
        'TEXT_UPCOMING_TITLE': page_data.get('upcoming_title', 'Upcoming Matches'),
        'TEXT_SHOW_MORE': THEME.get('text_show_more', 'Show More'),
        'TEXT_WATCH_BTN': THEME.get('text_watch_btn', 'WATCH'),
        'TEXT_HD_BADGE': THEME.get('text_hd_badge', 'HD'),
        'TEXT_SECTION_LINK': THEME.get('text_section_link', 'View All'),
        'TEXT_SECTION_PREFIX': THEME.get('text_section_prefix', 'Upcoming'),
        'WILDCARD_CATEGORY': THEME.get('wildcard_category', ''),
        'PAGE_FILTER': page_data.get('page_filter', '')
    }

    for k, v in THEME.items(): html = html.replace(f"{{{{THEME_{k.upper()}}}}}", str(v))
    for k, v in replacements.items(): html = html.replace(f"{{{{{k}}}}}", str(v))

    html = html.replace('{{HEADER_MENU}}', build_menu_html(config.get('menus',{}).get('header',[]), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(config.get('menus',{}).get('hero',[]), 'hero'))
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config, THEME))
    html = html.replace('{{FOOTER_COPYRIGHT}}', SITE_SETTINGS.get('footer_copyright',''))
    
    logo_size = THEME.get('logo_image_size', '40px')
    logo_html = f'<div class="logo-text" style="color:{THEME.get("logo_p1_color")};">{SITE_SETTINGS.get("title_part_1")}<span style="color:{THEME.get("logo_p2_color")};">{SITE_SETTINGS.get("title_part_2")}</span></div>'
    if SITE_SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SITE_SETTINGS.get("logo_url")}" class="logo-img" style="width:{logo_size}; height:{logo_size}; object-fit:cover; border-radius:6px; box-shadow: 0 0 10px {THEME.get("logo_image_shadow_color","rgba(0,0,0,0)")}"> {logo_html}'
    html = html.replace('{{LOGO_HTML}}', logo_html)

    h_layout = THEME.get('header_layout', 'standard')
    h_icon = THEME.get('header_icon_pos', 'left')
    html = html.replace('{{HEADER_CLASSES}}', f"h-layout-{h_layout}{' h-icon-'+h_icon if h_layout=='center' else ''}")
    html = html.replace('{{FOOTER_CLASSES}}', '')

    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    hero_bg = f"background: {THEME.get('hero_bg_solid')};"
    h_style = THEME.get('hero_bg_style', 'solid')
    if h_style == 'gradient': hero_bg = f"background: radial-gradient(circle at top, {THEME.get('hero_gradient_start')} 0%, {THEME.get('hero_gradient_end')} 100%);"
    elif h_style == 'image': hero_bg = f"background: linear-gradient(rgba(0,0,0,{THEME.get('hero_bg_image_overlay_opacity')}), rgba(0,0,0,{THEME.get('hero_bg_image_overlay_opacity')})), url('{THEME.get('hero_bg_image_url')}'); background-size: cover;"
    elif h_style == 'transparent': hero_bg = "background: transparent;"

    box_b_str = f"{ensure_unit(THEME.get('hero_box_border_width', '1'))} solid {THEME.get('hero_box_border_color')}"
    box_css = ""
    if THEME.get('hero_border_top'): box_css += f"border-top: {box_b_str}; "
    if THEME.get('hero_border_bottom_box'): box_css += f"border-bottom: {box_b_str}; "
    if THEME.get('hero_border_left'): box_css += f"border-left: {box_b_str}; "
    if THEME.get('hero_border_right'): box_css += f"border-right: {box_b_str}; "

    main_pos = THEME.get('hero_main_border_pos', 'full')
    main_border = f"border-bottom: {ensure_unit(THEME.get('hero_main_border_width'))} solid {THEME.get('hero_main_border_color')};" if main_pos != 'none' else ""

    if mode == 'box':
        html = html.replace('{{HERO_OUTER_STYLE}}', f"background: transparent; padding: 40px 15px; {' '+main_border if main_pos=='full' else ''}")
        html = html.replace('{{HERO_INNER_STYLE}}', f"{hero_bg} max-width: {box_w}; margin: 0 auto; padding: 30px; border-radius: {ensure_unit(THEME.get('border_radius_base'))}; {box_css} {' '+main_border if main_pos=='box' else ''}")
    else:
        html = html.replace('{{HERO_OUTER_STYLE}}', f"{hero_bg} padding: 40px 15px; {' '+main_border if main_pos=='full' else ''}")
        html = html.replace('{{HERO_INNER_STYLE}}', f"max-width: {ensure_unit(THEME.get('container_max_width'))}; margin: 0 auto;")

    align = THEME.get('hero_content_align', 'center')
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', align)
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if align == 'center' else ('0' if align == 'left' else '0 0 0 auto'))
    html = html.replace('{{HERO_MENU_DISPLAY}}', THEME.get('hero_menu_visible', 'flex'))
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    html = html.replace('{{DISPLAY_HERO}}', THEME.get('display_hero', 'block'))

    html = html.replace('{{JS_THEME_CONFIG}}', json.dumps(THEME))
    html = html.replace('{{JS_PRIORITIES}}', json.dumps(PRIORITY_SETTINGS))
    html = html.replace('{{JS_LEAGUE_MAP}}', json.dumps(REVERSE_LEAGUE_MAP))
    html = html.replace('{{JS_IMAGE_MAP}}', json.dumps(image_map))
    
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    html = html.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))
    
    html = html.replace('{{LEAGUE_ARTICLE}}', '')
    html = html.replace('{{SCHEMA_BLOCK}}', '')
    
    f_leagues = []
    for k, v in PRIORITY_SETTINGS.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{slugify(k)}-streams/"})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))

    return html

def build_menu_html(menu_items, section):
    html = ""
    for item in menu_items:
        title = item.get('title', 'Link')
        url = item.get('url', '#')
        if section == 'header': html += f'<a href="{url}" class="{ "highlighted" if item.get("highlight") else "" }">{title}</a>'
        elif section == 'hero': html += f'<a href="{url}" class="cat-pill">{title}</a>'
        elif section == 'footer_leagues': html += f'<a href="{url}" class="league-card"><span class="l-icon">🏆</span><span>{title}</span></a>'
        elif section == 'footer_static': html += f'<a href="{url}" class="f-link">{title}</a>'
    return html

def build_footer_grid(config, active_theme):
    return f'<div class="footer-grid cols-{active_theme.get("footer_columns","2")}"><div class="f-brand">Brand</div><div>Menu</div></div>'

# ==============================================================================
# 8. BUILDERS
# ==============================================================================
def build_homepage(matches):
    print(" > Building Homepage...")
    try:
        with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: tpl = f.read()
    except: return

    live_matches = sorted([m for m in matches if m['is_live']], key=lambda x: (x.get('score',0)), reverse=True)
    upcoming = [m for m in matches if not m['is_live']]
    upcoming.sort(key=lambda x: x['timestamp'])

    used_ids = set(m['id'] for m in live_matches)

    live_html = render_container(live_matches, THEME.get('text_live_section_title'), '🔴', None, True)

    wc_cat = THEME.get('wildcard_category', '').lower()
    wc_active = len(wc_cat) > 2
    wc_html = ""
    top5_html = ""

    if wc_active:
        wc_m = [m for m in upcoming if wc_cat in m['league'].lower() or wc_cat in m['sport'].lower()]
        for m in wc_m: used_ids.add(m['id'])
        wc_html = render_container(wc_m, THEME.get('text_wildcard_title'), '🔥', None)
    else:
        top5 = []
        for m in upcoming:
            if m['id'] not in used_ids and len(top5) < 5:
                top5.append(m)
                used_ids.add(m['id'])
        top5_html = render_container(top5, THEME.get('text_top_upcoming_title'), '📅', None)

    grouped_html = ""
    now_ms = time.time() * 1000
    one_day = 24 * 60 * 60 * 1000
    
    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or settings.get('isHidden'): continue
        
        grp = [m for m in upcoming if m['id'] not in used_ids and 
               (key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()) and 
               (m['timestamp'] - now_ms < one_day)]
        
        if grp:
            grp = grp[:5]
            for m in grp: used_ids.add(m['id'])
            logo = get_logo(key, 'leagues')
            icon = logo if not logo.startswith('fallback') else '🏆'
            link = f"/{slugify(key)}-streams/" if settings.get('hasLink') else None
            grouped_html += render_container(grp, key, icon, link)

    other_matches = [m for m in upcoming if m['id'] not in used_ids and (m['timestamp'] - now_ms < one_day)]
    if other_matches:
        grouped_html += render_container(other_matches[:10], "Upcoming Other", "⚽", None)

    home_data = next((p for p in config.get('pages', []) if p['slug'] == 'home'), {})
    html = apply_theme_to_template(tpl, home_data)
    
    # Clean Skeletons
    html = re.sub(r'<div id="live-sk-head".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="live-skeleton".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="upcoming-skeleton".*?</div>', '', html, flags=re.DOTALL)
    html = html.replace('style="display:none;"', '')
    html = html.replace('<div id="live-content-wrapper" style="display:none;">', '<div id="live-content-wrapper">')

    # UPDATED IDS for Injection
    if live_html:
        html = re.sub(r'<div id="live-section-container".*?</div>', f'<div id="live-section-container">{live_html}</div>', html, flags=re.DOTALL)
    else:
        html = re.sub(r'<div id="live-section-container".*?</div>', '<div id="live-section-container" style="display:none"></div>', html, flags=re.DOTALL)

    html = re.sub(r'<div id="wildcard-section-container".*?</div>', f'<div id="wildcard-section-container">{wc_html}</div>' if wc_html else '<div id="wildcard-section-container" style="display:none"></div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="top5-section-container".*?</div>', f'<div id="top5-section-container">{top5_html}</div>' if top5_html else '<div id="top5-section-container" style="display:none"></div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="grouped-section-container".*?</div>', f'<div id="grouped-section-container">{grouped_html}</div>' if grouped_html else '<div id="grouped-section-container" style="display:none"></div>', html, flags=re.DOTALL)

    schema = json.dumps({
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListElement": [{
            "@type": "SportsEvent", "name": f"{m['home']} vs {m['away']}" if not m['is_single'] else m['home'],
            "startDate": datetime.fromtimestamp(m['timestamp']/1000).isoformat(),
            "url": f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
        } for m in (live_matches + upcoming)[:20]]
    })
    html = html.replace('{{SCHEMA_BLOCK}}', f'<script type="application/ld+json">{schema}</script>')

    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_watch_page(matches):
    if not os.path.exists('watch/index.html'): return
    with open('watch/index.html', 'r', encoding='utf-8') as f: html = f.read()
    html = html.replace('// {{INJECTED_MATCH_DATA}}', f'window.MATCH_DATA = {json.dumps(matches)};')
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_leagues(matches):
    for key in PRIORITY_SETTINGS:
        slug = slugify(key) + "-streams"
        path = f"{slug}/index.html"
        if os.path.exists(path):
            l_matches = [m for m in matches if key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()]
            l_live = sorted([m for m in l_matches if m['is_live']], key=lambda x: x.get('score',0), reverse=True)
            l_upc = [m for m in l_matches if not m['is_live']]
            l_upc.sort(key=lambda x: x['timestamp'])
            
            live_html = render_container(l_live, f"Live {key}", "🔴", None, True)
            upc_html = render_container(l_upc, f"Upcoming {key}", "📅", None)
            
            with open(path, 'r', encoding='utf-8') as f: l_html = f.read()
            l_html = re.sub(r'<div id="live-list">.*?</div>', f'<div id="live-list">{live_html}</div>', l_html, flags=re.DOTALL)
            l_html = re.sub(r'<div id="schedule-list">.*?</div>', f'<div id="schedule-list">{upc_html}</div>', l_html, flags=re.DOTALL)
            
            display_style = 'block' if l_live else 'none'
            l_html = re.sub(r'id="live-section" style="display:.*?"', f'id="live-section" style="display:{display_style}"', l_html)
            
            with open(path, 'w', encoding='utf-8') as f: f.write(l_html)
            print(f" > Updated {slug}")

# ==============================================================================
# 10. IMAGE DOWNLOADER & PROCESSOR
# ==============================================================================
def run_image_downloader(matches):
    print(" > Checking for new images...")
    
    # Reload map to get latest state
    img_map = load_json(IMAGE_MAP_PATH)
    if 'teams' not in img_map: img_map['teams'] = {}
    if 'leagues' not in img_map: img_map['leagues'] = {}
    
    updated = False
    
    # Ensure directories exist
    dirs = [
        'assets/logos/streamed', 
        'assets/logos/upstreams', 
        'assets/logos/leagues'
    ]
    for d in dirs:
        if not os.path.exists(d): os.makedirs(d)

    def process_and_save(url, save_path):
        try:
            # Fake headers to avoid 403s on some CDNs
            h = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=h, timeout=5)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                
                # Resize to 60x60
                img = img.resize((60, 60), Image.Resampling.LANCZOS)
                
                # Save as WebP
                img.save(save_path, 'WEBP', quality=90)
                return True
        except Exception as e:
            pass
        return False

    for m in matches:
        meta = m.get('_img_meta', {})
        
        # 1. PROCESS HOME TEAM
        h_name = m['home']
        if h_name and h_name != 'TBA' and h_name not in img_map['teams']:
            success = False
            
            # Try Streamed (Priority: Cleanest)
            if meta.get('home_id'):
                url = f"https://streamed.pk/api/images/badge/{meta['home_id']}.webp"
                fname = f"assets/logos/streamed/{slugify(h_name)}.webp"
                if process_and_save(url, fname):
                    img_map['teams'][h_name] = fname
                    success = True
                    updated = True
            
            # Try Adstrim (Fallback)
            if not success and (meta.get('adstrim_home') or meta.get('adstrim_home_dict')):
                url = meta.get('adstrim_home')
                if meta.get('adstrim_home_dict') and isinstance(meta['adstrim_home_dict'], dict):
                    url = meta['adstrim_home_dict'].get('sofascore') or url
                
                if url:
                    fname = f"assets/logos/upstreams/{slugify(h_name)}.webp"
                    if process_and_save(url, fname):
                        img_map['teams'][h_name] = fname
                        updated = True

        # 2. PROCESS AWAY TEAM
        a_name = m['away']
        if a_name and a_name != 'TBA' and a_name not in img_map['teams']:
            success = False
            
            # Try Streamed
            if meta.get('away_id'):
                url = f"https://streamed.pk/api/images/badge/{meta['away_id']}.webp"
                fname = f"assets/logos/streamed/{slugify(a_name)}.webp"
                if process_and_save(url, fname):
                    img_map['teams'][a_name] = fname
                    success = True
                    updated = True
            
            # Try Adstrim
            if not success and (meta.get('adstrim_away') or meta.get('adstrim_away_dict')):
                url = meta.get('adstrim_away')
                if meta.get('adstrim_away_dict') and isinstance(meta['adstrim_away_dict'], dict):
                    url = meta['adstrim_away_dict'].get('sofascore') or url
                
                if url:
                    fname = f"assets/logos/upstreams/{slugify(a_name)}.webp"
                    if process_and_save(url, fname):
                        img_map['teams'][a_name] = fname
                        updated = True

        # 3. PROCESS LEAGUE
        l_name = m['league']
        if l_name and l_name != m['sport'] and l_name not in img_map['leagues']:
            if meta.get('adstrim_league'):
                url = meta.get('adstrim_league')
                fname = f"assets/logos/leagues/{slugify(l_name)}.webp"
                if process_and_save(url, fname):
                    img_map['leagues'][l_name] = fname
                    updated = True

    if updated:
        print(" > Saving updated image map...")
        with open(IMAGE_MAP_PATH, 'w', encoding='utf-8') as f:
            json.dump(img_map, f, indent=4)
    else:
        print(" > No new images to download.")

# ==============================================================================
# 9. MAIN EXECUTION
# ==============================================================================
def main():
    print("--- 🚀 Master Engine Running ---")
    matches = fetch_and_merge()
    print(f" > Total Valid Matches: {len(matches)}")
    
    build_homepage(matches)
    print(" > Homepage Built.")
    
    inject_watch_page(matches)
    print(" > Watch Data Injected.")
    
    inject_leagues(matches)
    print(" > League Pages Updated.")
    
    run_image_downloader(matches)

if __name__ == "__main__":
    main()
