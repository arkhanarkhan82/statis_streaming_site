import os
import json
import requests
import hashlib
import base64
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
# ==============================================================================
# SPORT NAME NORMALIZATION
# ==============================================================================
SPORT_DICTIONARY = {
    "football": "Football",
    "soccer": "Soccer",
    "american-football": "American Football",
    "american football": "American Football",
    "am. football": "American Football",
    "basketball": "Basketball",
    "nba": "Basketball",
    "baseball": "Baseball",
    "mlb": "Baseball",
    "ice-hockey": "Ice Hockey",
    "ice hockey": "Ice Hockey",
    "nhl": "Ice Hockey",
    "hockey": "Ice Hockey",
    "tennis": "Tennis",
    "cricket": "Cricket",
    "rugby": "Rugby",
    "rugby-union": "Rugby Union",
    "rugby-league": "Rugby League",
    "formula-1": "Formula 1",
    "f1": "Formula 1",
    "motorsport": "Motorsport",
    "boxing": "Boxing",
    "mma": "MMA",
    "ufc": "MMA",
    "fighting": "Fighting",
    "golf": "Golf",
    "volleyball": "Volleyball",
    "handball": "Handball",
    "darts": "Darts",
    "snooker": "Snooker",
    "table-tennis": "Table Tennis",
    "badminton": "Badminton",
    "afl": "Aussie Rules"
}

def normalize_sport(raw_name):
    if not raw_name: return "General"
    key = str(raw_name).lower().strip()
    # 1. Check Dictionary
    if key in SPORT_DICTIONARY:
        return SPORT_DICTIONARY[key]
    # 2. Fallback: Replace hyphens and Title Case (e.g. "table-tennis" -> "Table Tennis")
    return key.replace('-', ' ').title()

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

def slugify(text):
    if not text: return ""
    text = re.sub(r'[^\w\s-]', '', str(text).lower())
    return re.sub(r'[-\s]+', '-', text).strip("-")

# Load Configs
config = load_json(CONFIG_PATH)
image_map = load_json(IMAGE_MAP_PATH)
if 'teams' not in image_map: image_map['teams'] = {}
if 'leagues' not in image_map: image_map['leagues'] = {}

LEAGUE_MAP = load_json(LEAGUE_MAP_PATH) # Loaded directly for logic use

SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')
PARAM_LIVE = SITE_SETTINGS.get('param_live', 'stream')
PARAM_INFO = SITE_SETTINGS.get('param_info', 'info')
THEME = config.get('theme', {})

# ==============================================================================
# 3. MATCH PROCESSING LOGIC (PRESERVED EXACTLY)
# ==============================================================================

def normalize(s):
    if not s: return ""
    return re.sub(r'[^a-z0-9]+', '', str(s).lower()).strip()

def extract_teams(match):
    title = match.get('title') or ""
    parts = [p.strip() for p in title.split(":")]
    if len(parts) >= 2:
        match['league'] = parts[0]
        match['_leagueSource'] = "title"
        title = parts[-1]
    match['title_clean'] = title
    teams = match.get('teams') or {}  # Fix: Handle explicit null
    match['teams'] = teams # Ensure match object has safe dict
    
    home_name = teams.get('home', {}).get('name')
    away_name = teams.get('away', {}).get('name')
    if home_name or away_name: return
    vs_match = re.search(r'(.+?)\s+vs\.?\s+(.+)', title, re.IGNORECASE)
    if vs_match:
        match['teams'] = {
            'home': {'name': vs_match.group(1).strip(), 'badge': ''},
            'away': {'name': vs_match.group(2).strip(), 'badge': ''}
        }
    else:
        match['teams'] = {'home': {'name': '', 'badge': ''}, 'away': {'name': '', 'badge': ''}}

def resolve_league(match):
    teams = match.get('teams', {})
    home = teams.get('home', {}).get('name')
    away = teams.get('away', {}).get('name')
    if home and away:
        h_norm = normalize(home)
        a_norm = normalize(away)
        for league, team_list in LEAGUE_MAP.items():
            normalized_list = [normalize(t) for t in team_list] if isinstance(team_list, list) else []
            if h_norm in normalized_list and a_norm in normalized_list:
                match['league'] = league
                match['_leagueSource'] = "map"
                return
    title = match.get('title_clean') or match.get('title') or ""
    title_lower = title.lower()
    for league in LEAGUE_MAP.keys():
        if league.lower() in title_lower:
            match['league'] = league
            match['_leagueSource'] = "title"
            return
    if not home and not away and not match.get('league'):
        for league in LEAGUE_MAP.keys():
            if league.lower() in title_lower:
                match['league'] = league
                match['_leagueSource'] = "map-title"
                return
    if match.get('league'):
        if not match.get('_leagueSource'): match['_leagueSource'] = "api"
        return
    match['league'] = ""
    match['_leagueSource'] = "unknown"

def teams_match(a, b):
    if not a or not b: return False
    ah = normalize(a.get('home'))
    aa = normalize(a.get('away'))
    bh = normalize(b.get('home'))
    ba = normalize(b.get('away'))
    return (ah == bh and aa == ba) or (ah == ba and aa == bh)

def titles_match(t1, t2):
    if not t1 or not t2: return False
    stop_words = {"in","at","the","vs","on","day","match"}
    w1 = set(w for w in t1.lower().split() if w not in stop_words)
    w2 = set(w for w in t2.lower().split() if w not in stop_words)
    common = w1.intersection(w2)
    return len(common) >= 2

def merge_matches(streamed_list, adstrim_list):
    TIME_WINDOW_MS = 20 * 60 * 1000
    used_adstrim_indices = set()
    merged = []
    
    for sm in streamed_list:
        found_am = None
        sm_date = sm.get('date', 0)
        sm_ms = sm_date * 1000 if sm_date < 10000000000 else sm_date
        sm_sport = normalize(sm.get('category'))
        sm_teams = sm.get('teams', {})
        sm_h_name = sm_teams.get('home', {}).get('name')
        sm_a_name = sm_teams.get('away', {}).get('name')
        
        for i, am in enumerate(adstrim_list):
            if i in used_adstrim_indices: continue
            am_ts = am.get('timestamp', 0)
            am_ms = am_ts * 1000 if am_ts < 10000000000 else am_ts
            if abs(sm_ms - am_ms) > TIME_WINDOW_MS: continue
            am_sport = normalize(am.get('sport'))
            if sm_sport and am_sport and sm_sport != am_sport: continue
            am_h = am.get('home_team')
            am_a = am.get('away_team')
            matched = False
            if sm_h_name or sm_a_name or am_h or am_a:
                t1 = {'home': sm_h_name, 'away': sm_a_name}
                t2 = {'home': am_h, 'away': am_a}
                if teams_match(t1, t2): matched = True
            else:
                t1_title = sm.get('title_clean') or sm.get('title')
                t2_title = am.get('title')
                if titles_match(t1_title, t2_title): matched = True
            if matched:
                found_am = am
                used_adstrim_indices.add(i)
                break
        merged.append({'sm': sm, 'am': found_am})
        
    for i, am in enumerate(adstrim_list):
        if i not in used_adstrim_indices:
            merged.append({'sm': None, 'am': am})
    return merged

# ==============================================================================
# 4. DATA FETCHING & PROCESSING ENGINE
# ==============================================================================

def get_stream_details(source, sid):
    try:
        url = f"{NODE_A_ENDPOINT}/stream/{source}/{sid}"
        r = requests.get(url, headers=HEADERS, timeout=3)
        if r.status_code == 200: return r.json()
    except: pass
    return []

def fetch_and_process():
    print(" > Fetching APIs...")
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
    except: res_a = []
    try:
        res_b_json = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
        res_b = res_b_json.get('data', [])
    except: res_b = []

    valid_streamed = []
    stream_detail_jobs = {}
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        for m in res_a:
            extract_teams(m)
            resolve_league(m)
            m['_streamEmbeds'] = {}
            if m.get('sources'):
                for src in m['sources']:
                    s_source = src.get('source')
                    s_id = src.get('id')
                    future = executor.submit(get_stream_details, s_source, s_id)
                    stream_detail_jobs[future] = (m, s_source)
            valid_streamed.append(m)
        
        # Get current time once before the loop
        # Get current time in MILLISECONDS to match the API data
        current_time_ms = time.time() * 1000

        for future in as_completed(stream_detail_jobs):
            match_obj, src_name = stream_detail_jobs[future]
            try:
                details = future.result()
                if details:
                    match_obj['_streamEmbeds'][src_name] = details
                    
                    # Get match start and normalize to milliseconds
                    match_start = match_obj.get('date', 0)
                    match_start_ms = match_start * 1000 if match_start < 10000000000 else match_start
                    
                    # FIX: Compare milliseconds to milliseconds
                    if match_start_ms <= current_time_ms:
                        current_v = match_obj.get('_totalViewers', 0)
                        for d in details: current_v += d.get('viewers', 0)
                        match_obj['_totalViewers'] = current_v
                    
            except: pass

    merged_raw = merge_matches(valid_streamed, res_b)
    final_list = []
    
    for item in merged_raw:
        sm = item['sm']
        am = item['am']
        home = sm.get('teams', {}).get('home', {}).get('name') if sm else (am.get('home_team') if am else "")
        away = sm.get('teams', {}).get('away', {}).get('name') if sm else (am.get('away_team') if am else "")
        if not home and am: home = am.get('home_team')
        if not away and am: away = am.get('away_team')
        
        title = sm.get('title') if sm else ""
        if not title and am: title = am.get('title')
        if not title and home and away: title = f"{home} vs {away}"
        
        sm_l = sm.get('league') if sm else ""
        am_l = am.get('league') if am else ""
        league = am_l if (sm_l and am_l and normalize(sm_l) == normalize(am_l)) else (sm_l or am_l)
        
        raw_sport = sm.get('category') if sm else (am.get('sport') if am else "General")
        if not league: league = raw_sport
        
        # FIX: Normalize Sport Name using Dictionary
        sport = normalize_sport(raw_sport)
        
        ts = 0
        if sm and sm.get('date'): ts = sm['date']
        elif am and am.get('timestamp'): ts = am['timestamp']
        if ts < 10000000000: ts *= 1000
            
        streams = []
        if sm and '_streamEmbeds' in sm:
            for src_key, details_list in sm['_streamEmbeds'].items():
                for d in details_list:
                    raw_url = d.get('embedUrl', '')
                    # ENCODE URL TO BASE64
                    enc_url = base64.b64encode(raw_url.encode('utf-8')).decode('utf-8') if raw_url else ""
                    
                    streams.append({'source': 'streamed', 'type': src_key, 'name': f"{src_key} {d.get('streamNo','')}", 'url': enc_url, 'hd': d.get('hd', False), 'lang': d.get('language', '')})
                    
        if am and am.get('channels'):
            for ch in am['channels']:
                raw_url = f"{TOPEMBED_BASE}{ch.get('name')}"
                # ENCODE URL TO BASE64
                enc_url = base64.b64encode(raw_url.encode('utf-8')).decode('utf-8')
                
                streams.append({'source': 'adstrim', 'name': ch.get('name'), 'url': enc_url, 'hd': False, 'lang': ''})

        img_meta = {
            'home_name': home, 'away_name': away, 'league_name': league,
            'sm_home_badge': sm.get('teams', {}).get('home', {}).get('badge') if sm else None,
            'sm_away_badge': sm.get('teams', {}).get('away', {}).get('badge') if sm else None,
            'am_home_img': am.get('home_team_image') if am else None,
            'am_away_img': am.get('away_team_image') if am else None,
            'am_home_dict': am.get('home_team_images') if am else None,
            'am_away_dict': am.get('away_team_images') if am else None,
            'am_league_img': am.get('league_image') or am.get('league_images') if am else None
        }

        now_ms = time.time() * 1000
        viewers = sm.get('_totalViewers', 0) if sm else 0
        duration = int(am.get('duration')) if am and am.get('duration') else SPORT_DURATIONS.get('default', 130)
        end_time = ts + (duration * 60 * 1000)
        if now_ms > end_time and viewers == 0: continue
        
        is_live = False
        status_text = ""
        if viewers > 0: is_live = True
        elif ts <= now_ms <= end_time: is_live = True
        
        if is_live:
            diff = now_ms - ts
            mins = int(diff / 60000) if diff > 0 else 0
            h, m_val = divmod(mins, 60)
            status_text = f"{h}h {m_val:02d}'" if h > 0 else f"{m_val}'"
        else:
            diff = ts - now_ms
            if diff < 0: status_text = "Starting"
            else:
                secs = int(diff / 1000)
                d_val = secs // 86400
                h_val = (secs % 86400) // 3600
                m_val = (secs % 3600) // 60
                p = []
                if d_val > 0: p.append(f"{d_val}d")
                if d_val > 0 or h_val > 0: p.append(f"{h_val}h")
                p.append(f"{m_val}m")
                status_text = " ".join(p)

        h_s = slugify(home)
        a_s = slugify(away)
        base = f"{h_s}-vs-{a_s}" if a_s else h_s
        if not base: base = slugify(title)
        uid = hashlib.md5(f"{ts}-{home}-{away}".encode()).hexdigest()
        seo_id = f"{base}-{uid[:8]}"
        
        home = (home or "TBA").replace('_', ' ').strip()
        away = (away or "TBA").replace('_', ' ').strip()
        
        score = 0
        l_low = league.lower()
        s_low = sport.lower()
        admin_score = 0
        is_boosted = False
        if '_BOOST' in PRIORITY_SETTINGS:
            boosts = [x.strip().lower() for x in PRIORITY_SETTINGS['_BOOST'].split(',')]
            if any(b in l_low or b in s_low for b in boosts): is_boosted = True

        for k, v in PRIORITY_SETTINGS.items():
            if k.startswith('_'): continue
            if k.lower() in l_low or k.lower() in s_low:
                admin_score = v.get('score', 0)
                break

        if is_live:
            if viewers > 100: score = 10**19 + viewers
            else:
                base_sc = 5 * 10**18 if is_boosted else 0
                score = base_sc + (admin_score * 10**15) + viewers
        else:
            base_sc = 5 * 10**18 if is_boosted else 0
            score = base_sc + (admin_score * 10**15) - ts

        final_list.append({
            'id': seo_id, 'home': home, 'away': away, 'title': title,
            'league': league, 'sport': sport, 'timestamp': ts,
            'is_live': is_live, 'status_text': status_text, 'viewers': viewers,
            'streams': streams, 'score': score, 'is_single': (not away or away == "TBA"),
            '_img_meta': img_meta
        })

    return final_list

# ==============================================================================
# 5. IMAGE CHECKER
# ==============================================================================
def run_image_downloader(matches):
    print(" > Checking for new images...")
    img_map = load_json(IMAGE_MAP_PATH)
    if 'teams' not in img_map: img_map['teams'] = {}
    if 'leagues' not in img_map: img_map['leagues'] = {}
    updated = False
    
    dirs = ['assets/logos/streamed', 'assets/logos/upstreams', 'assets/logos/leagues']
    for d in dirs: os.makedirs(d, exist_ok=True)

    def process_and_save(url, save_path):
        try:
            r = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=5)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                img = img.resize((60, 60), Image.Resampling.LANCZOS)
                img.save(save_path, 'WEBP', quality=90)
                return True
        except: pass
        return False

    for m in matches:
        meta = m.get('_img_meta', {})
        for key, team in [('home', m['home']), ('away', m['away'])]:
            if team and team != 'TBA' and team not in img_map['teams']:
                success = False
                if meta.get(f'sm_{key}_badge'):
                    url = f"https://streamed.pk/api/images/badge/{meta[f'sm_{key}_badge']}.webp"
                    fname = f"assets/logos/streamed/{slugify(team)}.webp"
                    if process_and_save(url, fname): img_map['teams'][team] = fname; success = True; updated = True
                if not success:
                    url = meta.get(f'am_{key}_img')
                    if not url and meta.get(f'am_{key}_dict'):
                        d = meta[f'am_{key}_dict']
                        if isinstance(d, dict): url = d.get('sofascore') or d.get('flashscore')
                    if url:
                        fname = f"assets/logos/upstreams/{slugify(team)}.webp"
                        if process_and_save(url, fname): img_map['teams'][team] = fname; updated = True

        l_name = m['league']
        if l_name and l_name not in img_map['leagues']:
            url = meta.get('am_league_img')
            if url:
                fname = f"assets/logos/leagues/{slugify(l_name)}.webp"
                if process_and_save(url, fname): img_map['leagues'][l_name] = fname; updated = True

    if updated:
        with open(IMAGE_MAP_PATH, 'w', encoding='utf-8') as f: json.dump(img_map, f, indent=4)

# ==============================================================================
# 6. HTML RENDERERS (With Dynamic Editing Logic)
# ==============================================================================
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

def get_logo(name, type_key):
    path = image_map[type_key].get(name)
    if path: 
        if not path.startswith('http') and not path.startswith('/'): path = f"/{path}"
        return path
    c = ['#e53935','#d81b60','#8e24aa','#5e35b1','#3949ab','#1e88e5','#039be5','#00897b','#43a047','#7cb342','#c0ca33','#fdd835','#fb8c00'][(sum(map(ord, name)) if name else 0)%13]
    letter = name[0] if name else "?"
    return f"fallback:{c}:{letter}" 

def render_match_row(m, section_title=""):
    is_live = m['is_live']
    row_class = "match-row live" if is_live else "match-row"
    
    if is_live:
        time_html = f'<span class="live-txt">{m["status_text"]}</span><span class="time-sub">{m["sport"].upper()}</span>'
        v = m.get("viewers", 0)
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
    elif m['home'] == "TBA" and m['away'] == "TBA" and m['title']:
        teams_html = f'<div class="team-name" style="justify-content:center; font-weight:600;">{m["title"]}</div>'

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    
    svg_icon = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>'
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')">{svg_icon} Link</button>'

    btn = ""
    diff = (m['timestamp'] - time.time()*1000) / 60000
    
    # Use Dynamic Text from THEME
    watch_text = THEME.get("text_watch_btn", "WATCH")
    hd_text = THEME.get("text_hd_badge", "HD")
    
    if is_live or diff <= 30:
        btn = f'<a href="{info_url}" class="btn-watch">{watch_text} <span class="hd-badge">{hd_text}</span></a>'
    else:
        btn = '<button class="btn-notify" onclick="handleNotify(this)">🔔 Notify</button>'

    tag = m['league'].upper()
    if section_title and section_title.lower() in m['league'].lower():
        tag = m['sport'].upper()

    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}{copy_btn}</div></div>'

def render_container(matches, title, icon=None, link=None, is_live_section=False, section_id=None):
    if not matches: return ""
    
    # --- DYNAMIC BORDER LOGIC ---
    border_style = ""
    # Map variables (Keys must match config.json exactly)
    t_live = THEME.get('text_live_section_title', 'Trending Live')
    t_wild = THEME.get('text_wildcard_title', 'Featured')
    t_top5 = THEME.get('text_top_upcoming_title', 'Top Upcoming')
    
    if is_live_section or title == t_live:
        w = ensure_unit(THEME.get('sec_border_live_width', '1'))
        c = THEME.get('sec_border_live_color', '#334155')
        border_style = f"border-bottom: {w} solid {c};"
    elif title == t_wild:
        w = ensure_unit(THEME.get('sec_border_wildcard_width', '1'))
        c = THEME.get('sec_border_wildcard_color', '#334155')
        border_style = f"border-bottom: {w} solid {c};"
    elif title == t_top5:
        w = ensure_unit(THEME.get('sec_border_upcoming_width', '1'))
        c = THEME.get('sec_border_upcoming_color', '#334155')
        border_style = f"border-bottom: {w} solid {c};"
    else:
        # Default for Grouped/Leagues
        w = ensure_unit(THEME.get('sec_border_grouped_width', '1'))
        c = THEME.get('sec_border_grouped_color', '#334155')
        border_style = f"border-bottom: {w} solid {c};"

    img_html = ""
    if icon:
        if icon.startswith('http') or icon.startswith('/'):
            img_html = f'<img src="{icon}" class="sec-logo"> '
        else:
            img_html = f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span> '
            
    # --- LOGIC FIXED HERE ---
    right_content = ""
    if is_live_section:
        # 1. Show Live Count
        count = len(matches)
        right_content = f'<span style="font-size:0.8rem; font-weight:700; color:var(--match-row-live-text-color); display:flex; align-items:center; gap:6px;">● {count} Live Events</span>'
    elif link:
        # 2. Show Link (Indentation Fixed)
        link_text = THEME.get("text_section_link", "View All")
        right_content = f'<a href="{link}" class="sec-right-link">{link_text} ></a>'
    
    # Apply border_style inline AND use right_content
    id_attr = f' id="{section_id}"' if section_id else ""
    header = f'<div class="sec-head" style="{border_style}"><h2 class="sec-title"{id_attr}>{img_html}{title}</h2>{right_content}</div>'

    rows_html = ""
    hidden_html = ""
    
    if is_live_section and len(matches) > 5:
        visible = matches[:5]
        hidden = matches[5:]
        rows_html = "".join([render_match_row(m, title) for m in visible])
        hidden_rows = "".join([render_match_row(m, title) for m in hidden])
        
        btn_id = f"btn-{int(time.time()*1000)}"
        div_id = f"hide-{int(time.time()*1000)}"
        btn_text = THEME.get("text_show_more", "Show More")
        
        hidden_html = f'''
        <button id="{btn_id}" class="show-more-btn" onclick="toggleHidden('{div_id}', this)">{btn_text} ({len(hidden)}) ▼</button>
        <div id="{div_id}" class="match-list" style="display:none; margin-top:10px;">{hidden_rows}</div>
        '''
    else:
        rows_html = "".join([render_match_row(m, title) for m in matches])

    return f'<div class="section-box">{header}<div class="match-list">{rows_html}</div>{hidden_html}</div>'

# ==============================================================================
# 7. INJECTORS (Marker Based Safe Injection)
# ==============================================================================

def build_homepage(matches):
    print(" > Injecting matches into Homepage...")
    
    if not os.path.exists('index.html'):
        print(" ! Error: index.html not found. Run build_site.py first.")
        return
        
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    live_matches = sorted([m for m in matches if m['is_live']], key=lambda x: x.get('score',0), reverse=True)
    
    now_ms = time.time() * 1000
    one_day = 24 * 60 * 60 * 1000
    
    upcoming_full = [m for m in matches if not m['is_live']]
    upcoming_full.sort(key=lambda x: x.get('score',0), reverse=True)
    
    used_ids = set(m['id'] for m in live_matches)

    # Use Theme Titles
    live_title = THEME.get('text_live_section_title', 'Trending Live')
    live_html = render_container(live_matches, live_title, '🔴', None, True)

    wc_cat = THEME.get('wildcard_category', '').lower()
    wc_active = len(wc_cat) > 2
    wc_html = ""
    top5_html = ""

    if wc_active:
        wc_m = [m for m in upcoming_full if wc_cat in m['league'].lower() or wc_cat in m['sport'].lower()]
        for m in wc_m: used_ids.add(m['id'])
        wc_title = THEME.get('text_wildcard_title', 'Featured')
        wc_id = THEME.get('id_wildcard', '') # Get ID from config
        wc_html = render_container(wc_m, wc_title, '🔥', None, False, wc_id) # Pass ID
    else:
        top5 = []
        used_leagues = set()
        for m in upcoming_full:
            if len(top5) >= 5: break
            if m['id'] in used_ids or (m['timestamp'] - now_ms >= one_day): continue
            l_key = m['league'] or m['sport']
            if l_key in used_leagues: continue
            top5.append(m)
            used_ids.add(m['id'])
            used_leagues.add(l_key)
        
        top5_title = THEME.get('text_top_upcoming_title', 'Top Upcoming')
        top5_id = THEME.get('id_top_upcoming', '') # Get ID from config
        top5_html = render_container(top5, top5_title, '📅', None, False, top5_id) # Pass ID

    # Grouped Section
    grouped_html = ""
    # 1. Get the prefix from Theme settings
    prefix = THEME.get('text_section_prefix', '').strip()

    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or settings.get('isHidden'): continue
        
        grp = [m for m in upcoming_full if m['id'] not in used_ids and 
               (key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()) and 
               (m['timestamp'] - now_ms < one_day)]
        
        if grp:
            for m in grp: used_ids.add(m['id'])
            logo = get_logo(key, 'leagues')
            icon = logo if not logo.startswith('fallback') else '🏆'
            link = f"/{slugify(key)}-streams/" if settings.get('hasLink') else None
            
            # 2. Apply Prefix to Title (e.g. "Upcoming" + " " + "NFL")
            display_title = f"{prefix} {key}" if prefix else key
            
            grouped_html += render_container(grp, display_title, icon, link)
            # RESTORED: Upcoming Other Section
    if not PRIORITY_SETTINGS.get('_HIDE_OTHERS'):
        # Filter: Not used yet AND starts within 24 hours
        other_matches = [m for m in upcoming_full if m['id'] not in used_ids and (m['timestamp'] - now_ms < one_day)]
        
        if other_matches:
            # Removed limit ([:10]) and removed icon (None)
            grouped_html += render_container(other_matches, "Upcoming Other", "🏆", None)

    # Injection with Markers
    if live_html:
        html = re.sub(r'<!-- LIVE_START -->.*?<!-- LIVE_END -->', f'<!-- LIVE_START -->{live_html}<!-- LIVE_END -->', html, flags=re.DOTALL)
        html = html.replace('id="live-content-wrapper" style="display:none;"', 'id="live-content-wrapper"')
    else:
        html = re.sub(r'<!-- LIVE_START -->.*?<!-- LIVE_END -->', '<!-- LIVE_START --><!-- LIVE_END -->', html, flags=re.DOTALL)
        html = html.replace('id="live-content-wrapper"', 'id="live-content-wrapper" style="display:none;"')

    html = re.sub(r'<!-- WC_START -->.*?<!-- WC_END -->', f'<!-- WC_START -->{wc_html}<!-- WC_END -->', html, flags=re.DOTALL)
    html = re.sub(r'<!-- TOP5_START -->.*?<!-- TOP5_END -->', f'<!-- TOP5_START -->{top5_html}<!-- TOP5_END -->', html, flags=re.DOTALL)
    html = re.sub(r'<!-- GROUPED_START -->.*?<!-- GROUPED_END -->', f'<!-- GROUPED_START -->{grouped_html}<!-- GROUPED_END -->', html, flags=re.DOTALL)

    html = re.sub(r'<div id="live-sk-head".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="live-skeleton".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="upcoming-skeleton".*?</div>', '', html, flags=re.DOTALL)

    # --- DYNAMIC SCHEMA GENERATION (Top 5 Live + Top 15 Upcoming) ---
    schema_matches = live_matches[:5] + upcoming_full[:15]
    list_items = []
    
    site_url = f"https://{DOMAIN}/"
    org_id = f"{site_url}#organization"
    
    # Sports that are Person vs Person
    INDIVIDUAL_SPORTS = ['tennis', 'boxing', 'mma', 'ufc', 'golf', 'darts', 'snooker', 'wrestling', 'table tennis', 'badminton']

    for idx, m in enumerate(schema_matches):
        match_url = f"{site_url}watch/?{PARAM_INFO}={m['id']}"
        event_name = m['title'] if m['is_single'] and m['title'] else f"{m['home']} vs {m['away']}"
        
        # Determine Entity Type based on Sport
        raw_sport = (m['sport'] or "").lower()
        is_individual = any(s in raw_sport for s in INDIVIDUAL_SPORTS)
        entity_type = "Person" if is_individual else "SportsTeam"

        # Base Event Object
        event = {
            "@type": "SportsEvent",
            "name": event_name,
            "description": f"Watch {event_name} live stream. {m['league']}.",
            "startDate": datetime.fromtimestamp(m['timestamp']/1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
            "eventStatus": "https://schema.org/EventLive" if m['is_live'] else "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
            "isAccessibleForFree": True,  # <--- Added
            "url": match_url,
            "image": [f"{site_url.rstrip('/')}{config['site_settings'].get('logo_url')}"],
            "organizer": { "@id": org_id },
            "sport": m['sport']
            # Removed "offers" block
        }

        # Handle Competitors (Team vs Team OR Person vs Person)
        if not m['is_single']:
            # Home
            home_logo = image_map['teams'].get(m['home'])
            home_data = { "@type": entity_type, "name": m['home'] }
            if home_logo: home_data["image"] = f"{site_url.rstrip('/')}/{home_logo}"

            # Away
            away_logo = image_map['teams'].get(m['away'])
            away_data = { "@type": entity_type, "name": m['away'] }
            if away_logo: away_data["image"] = f"{site_url.rstrip('/')}/{away_logo}"

            if is_individual:
                # Individual sports use 'competitor' array
                event["competitor"] = [home_data, away_data]
            else:
                # Team sports use 'homeTeam' and 'awayTeam'
                event["homeTeam"] = home_data
                event["awayTeam"] = away_data
        
        # Add to List Item
        list_items.append({
            "@type": "ListItem",
            "position": idx + 1,
            "item": event
        })

    # Construct the Final Dynamic JSON
    dynamic_schema = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "@id": f"{site_url}#matchlist",
        "itemListElement": list_items
    }

    # TARGETED INJECTION
    pattern = r'(<script id="dynamic-schema-placeholder" type="application/ld\+json">).*?(</script>)'
    
    html = re.sub(
        pattern, 
        lambda match: f"{match.group(1)}{json.dumps(dynamic_schema)}{match.group(2)}", 
        html, 
        flags=re.DOTALL
    )

    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_watch_page(matches):
    print(" > Injecting matches into Watch Page...")
    target_file = 'watch/index.html'
    if not os.path.exists(target_file):
        print(f" ! Watch page not found at {target_file}")
        return

    with open(target_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # --- MODIFICATION: Create a clean copy without _img_meta ---
    clean_matches = []
    for m in matches:
        # Shallow copy the match so we don't affect the original list used by image downloader
        temp_m = m.copy()
        # Remove the raw image metadata from this copy
        temp_m.pop('_img_meta', None)
        clean_matches.append(temp_m)

    data_string = f"window.MATCH_DATA = {json.dumps(clean_matches)};"
    # -----------------------------------------------------------

    pattern = r'(//\s*\{\{INJECTED_MATCH_DATA\}\}|window\.MATCH_DATA\s*=\s*\[.*?\];)'
    
    if re.search(pattern, html, flags=re.DOTALL):
        # Unicode Safe Injection
        html = re.sub(pattern, lambda _: data_string, html, flags=re.DOTALL)
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(html)
        print("   - Watch data updated.")
    else:
        print("   ! Injection marker not found in watch page.")

def inject_leagues(matches):
    print(" > Injecting matches into League Pages...")

    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_'): continue
        
        slug = slugify(key) + "-streams"
        target_file = os.path.join(OUTPUT_DIR, slug, 'index.html')
        
        if not os.path.exists(target_file): 
            continue

        l_matches = [m for m in matches if key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()]
        l_live = sorted([m for m in l_matches if m['is_live']], key=lambda x: x.get('score',0), reverse=True)
        l_upc = [m for m in l_matches if not m['is_live']]
        l_upc.sort(key=lambda x: x['timestamp'])

        with open(target_file, 'r', encoding='utf-8') as f:
            html = f.read()

        # A. Inject League Logo
        logo_url = get_logo(key, 'leagues')
        if logo_url and "fallback" not in logo_url:
            img_tag = f'<img src="{logo_url}" alt="{key}" style="width:28px; height:28px; object-fit:contain; margin-right:8px;">'
            html = re.sub(r'<span id="upcoming-logo-container".*?>.*?</span>', img_tag, html, flags=re.DOTALL)

        # B. Inject Section Border
        w = ensure_unit(THEME.get('sec_border_league_upcoming_width', '1'))
        c = THEME.get('sec_border_league_upcoming_color', '#334155')
        border_style = f'style="border-bottom: {w} solid {c};"'
        html = re.sub(r'(<div id="upcoming-container">\s*<div class="sec-head")', f'\\1 {border_style}', html)

        # C. Inject Match Lists (HTML)
        if l_live:
            live_content = render_container(l_live, f"Live {key}", "🔴", None, True)
            html = re.sub(r'<!-- L_LIVE_START -->.*?<!-- L_LIVE_END -->', f'<!-- L_LIVE_START -->{live_content}<!-- L_LIVE_END -->', html, flags=re.DOTALL)
            html = html.replace('id="live-list" style="display:none;"', 'id="live-list"')
        else:
            html = re.sub(r'<!-- L_LIVE_START -->.*?<!-- L_LIVE_END -->', '<!-- L_LIVE_START --><!-- L_LIVE_END -->', html, flags=re.DOTALL)
            html = html.replace('id="live-list"', 'id="live-list" style="display:none;"')

        rows_html = "".join([render_match_row(m, key) for m in l_upc]) if l_upc else '<div class="match-row" style="justify-content:center;">No upcoming matches found.</div>'
        html = re.sub(r'<!-- L_SCHED_START -->.*?<!-- L_SCHED_END -->', f'<!-- L_SCHED_START -->{rows_html}<!-- L_SCHED_END -->', html, flags=re.DOTALL)

        # D. INJECT DYNAMIC SCHEMA (NEW)
        # Limit: 5 Live + 15 Upcoming (Sorted by time)
        schema_matches = l_live[:5] + l_upc[:15]
        list_items = []
        
        site_url = f"https://{DOMAIN}/"
        page_url = f"{site_url}{slug}/"
        org_id = f"{site_url}#organization"
        INDIVIDUAL_SPORTS = ['tennis', 'boxing', 'mma', 'ufc', 'golf', 'darts', 'snooker', 'wrestling', 'table tennis', 'badminton']

        for idx, m in enumerate(schema_matches):
            match_url = f"{site_url}watch/?{PARAM_INFO}={m['id']}"
            event_name = m['title'] if m['is_single'] and m['title'] else f"{m['home']} vs {m['away']}"
            
            raw_sport = (m['sport'] or "").lower()
            is_individual = any(s in raw_sport for s in INDIVIDUAL_SPORTS)
            entity_type = "Person" if is_individual else "SportsTeam"

            event = {
                "@type": "SportsEvent",
                "name": event_name,
                "description": f"Watch {event_name} live stream. {m['league']}.",
                "startDate": datetime.fromtimestamp(m['timestamp']/1000, timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                "eventStatus": "https://schema.org/EventLive" if m['is_live'] else "https://schema.org/EventScheduled",
                "eventAttendanceMode": "https://schema.org/OnlineEventAttendanceMode",
                "isAccessibleForFree": True,  # <--- Added
                "url": match_url,
                "image": [f"{site_url.rstrip('/')}{config['site_settings'].get('logo_url')}"],
                "organizer": { "@id": org_id },
                "sport": m['sport']
                # Removed "offers" block
            }

            if not m['is_single']:
                home_logo = image_map['teams'].get(m['home'])
                home_data = { "@type": entity_type, "name": m['home'] }
                if home_logo: home_data["image"] = f"{site_url.rstrip('/')}/{home_logo}"

                away_logo = image_map['teams'].get(m['away'])
                away_data = { "@type": entity_type, "name": m['away'] }
                if away_logo: away_data["image"] = f"{site_url.rstrip('/')}/{away_logo}"

                if is_individual:
                    event["competitor"] = [home_data, away_data]
                else:
                    event["homeTeam"] = home_data
                    event["awayTeam"] = away_data
            
            list_items.append({ "@type": "ListItem", "position": idx + 1, "item": event })

        dynamic_schema = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": f"{page_url}#matchlist",
            "itemListElement": list_items
        }

        # Inject into placeholder
        pattern = r'(<script id="dynamic-schema-placeholder" type="application/ld\+json">).*?(</script>)'
        html = re.sub(pattern, lambda match: f"{match.group(1)}{json.dumps(dynamic_schema)}{match.group(2)}", html, flags=re.DOTALL)

        with open(target_file, 'w', encoding='utf-8') as f: f.write(html)
        print(f"   - Updated {slug}")

# ==============================================================================
# 8. MAIN EXECUTION
# ==============================================================================
def main():
    print("--- 🚀 Master Engine Running (Strict Port) ---")
    matches = fetch_and_process()
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
