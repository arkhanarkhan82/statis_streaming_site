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
# >>> ADD THIS LINE BELOW <<<
OUTPUT_DIR = '.' 
# ---------------------------

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
# 3. NEW LOGIC: PORTS FROM JS (INDEX.HTML)
# ==============================================================================

def normalize(s):
    if not s: return ""
    # JS: s.toLowerCase().replace(/[^a-z0-9]+/g, "").trim()
    return re.sub(r'[^a-z0-9]+', '', str(s).lower()).strip()

def extract_teams(match):
    """
    Port of extractTeams(match) from JS.
    Modifies match dict in place.
    """
    title = match.get('title') or ""
    parts = [p.strip() for p in title.split(":")]

    if len(parts) >= 2:
        match['league'] = parts[0]
        match['_leagueSource'] = "title"
        title = parts[-1] # Take the last part as the actual title
    
    # Store clean title back
    match['title_clean'] = title

    teams = match.get('teams', {})
    home_name = teams.get('home', {}).get('name')
    away_name = teams.get('away', {}).get('name')

    if home_name or away_name:
        return # Teams already exist

    # Regex for "vs" or "v" or "vs."
    vs_match = re.search(r'(.+?)\s+vs\.?\s+(.+)', title, re.IGNORECASE)
    if vs_match:
        match['teams'] = {
            'home': {'name': vs_match.group(1).strip(), 'badge': ''},
            'away': {'name': vs_match.group(2).strip(), 'badge': ''}
        }
    else:
        match['teams'] = {
            'home': {'name': '', 'badge': ''},
            'away': {'name': '', 'badge': ''}
        }

def resolve_league(match):
    """
    Port of resolveLeague(match) from JS.
    """
    teams = match.get('teams', {})
    home = teams.get('home', {}).get('name')
    away = teams.get('away', {}).get('name')
    
    # 1. Try to find league by teams in LEAGUE_MAP
    if home and away:
        h_norm = normalize(home)
        a_norm = normalize(away)
        
        for league, team_list in LEAGUE_MAP.items():
            # Normalize team list for comparison
            normalized_list = [normalize(t) for t in team_list] if isinstance(team_list, list) else []
            if h_norm in normalized_list and a_norm in normalized_list:
                match['league'] = league
                match['_leagueSource'] = "map"
                return

    # 2. Try to find league by Title (Strict)
    title = match.get('title_clean') or match.get('title') or ""
    title_lower = title.lower()
    
    for league in LEAGUE_MAP.keys():
        if league.lower() in title_lower:
            match['league'] = league
            match['_leagueSource'] = "title"
            return

    # 3. Loose Title Match
    if not home and not away and not match.get('league'):
        for league in LEAGUE_MAP.keys():
            if league.lower() in title_lower:
                match['league'] = league
                match['_leagueSource'] = "map-title"
                return

    # 4. Existing API Source
    if match.get('league'):
        if not match.get('_leagueSource'): match['_leagueSource'] = "api"
        return

    # Fallback
    match['league'] = ""
    match['_leagueSource'] = "unknown"

def teams_match(a, b):
    """
    Port of teamsMatch(a, b) from JS.
    a and b are dicts with {home, away}.
    """
    if not a or not b: return False
    
    ah = normalize(a.get('home'))
    aa = normalize(a.get('away'))
    bh = normalize(b.get('home'))
    ba = normalize(b.get('away'))
    
    return (ah == bh and aa == ba) or (ah == ba and aa == bh)

def titles_match(t1, t2):
    """
    Port of titlesMatch(t1, t2) from JS.
    """
    if not t1 or not t2: return False
    
    stop_words = {"in","at","the","vs","on","day","match"}
    
    w1 = set(w for w in t1.lower().split() if w not in stop_words)
    w2 = set(w for w in t2.lower().split() if w not in stop_words)
    
    common = w1.intersection(w2)
    return len(common) >= 2

def merge_matches(streamed_list, adstrim_list):
    """
    Port of mergeMatches(streamed, adstrim) from JS.
    """
    TIME_WINDOW_MS = 20 * 60 * 1000
    used_adstrim_indices = set()
    merged = []
    
    for sm in streamed_list:
        found_am = None
        
        # Raw Timestamp from Streamed is usually in seconds or ms? 
        # API says 'date' (unix seconds). Let's convert to MS for comparison.
        sm_date = sm.get('date', 0)
        sm_ms = sm_date * 1000 if sm_date < 10000000000 else sm_date
        
        sm_sport = normalize(sm.get('category'))
        
        sm_teams = sm.get('teams', {})
        sm_h_name = sm_teams.get('home', {}).get('name')
        sm_a_name = sm_teams.get('away', {}).get('name')
        
        for i, am in enumerate(adstrim_list):
            if i in used_adstrim_indices: continue
            
            # Time Check
            am_ts = am.get('timestamp', 0)
            am_ms = am_ts * 1000 if am_ts < 10000000000 else am_ts
            
            if abs(sm_ms - am_ms) > TIME_WINDOW_MS: continue
            
            # Sport Check
            am_sport = normalize(am.get('sport'))
            if sm_sport and am_sport and sm_sport != am_sport: continue
            
            # Match Logic
            am_h = am.get('home_team')
            am_a = am.get('away_team')
            
            matched = False
            
            if sm_h_name or sm_a_name or am_h or am_a:
                # Teams Present -> Use teamsMatch
                t1 = {'home': sm_h_name, 'away': sm_a_name}
                t2 = {'home': am_h, 'away': am_a}
                if teams_match(t1, t2):
                    matched = True
            else:
                # Teams Missing -> Use titlesMatch
                t1_title = sm.get('title_clean') or sm.get('title')
                t2_title = am.get('title')
                if titles_match(t1_title, t2_title):
                    matched = True
            
            if matched:
                found_am = am
                used_adstrim_indices.add(i)
                break # Stop looking for this streamed match
        
        merged.append({'sm': sm, 'am': found_am})
        
    # Add remaining Adstrim
    for i, am in enumerate(adstrim_list):
        if i not in used_adstrim_indices:
            merged.append({'sm': None, 'am': am})
            
    return merged

# ==============================================================================
# 4. DATA FETCHING & PROCESSING ENGINE
# ==============================================================================

def get_stream_details(source, sid):
    """
    Fetches detailed stream info (embeds, language, hd) from Streamed API.
    Returns list of stream objects.
    """
    try:
        url = f"{NODE_A_ENDPOINT}/stream/{source}/{sid}"
        r = requests.get(url, headers=HEADERS, timeout=3)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return []

def fetch_and_process():
    print(" > Fetching APIs...")
    
    # 1. Fetch RAW
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        print(f"   - Streamed Raw: {len(res_a)}")
    except Exception as e:
        print(f"   ! Streamed Failed: {e}")
        res_a = []

    try:
        res_b_json = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
        res_b = res_b_json.get('data', [])
        print(f"   - Adstrim Raw: {len(res_b)}")
    except Exception as e:
        print(f"   ! Adstrim Failed: {e}")
        res_b = []

    # 2. Process Streamed (Extract Teams, Resolve League)
    # We do this IN PLACE before merging
    valid_streamed = []
    
    # 2a. Prepare threading for stream details
    stream_detail_jobs = {}
    
    with ThreadPoolExecutor(max_workers=15) as executor:
        for m in res_a:
            extract_teams(m)
            resolve_league(m)
            
            # Filter Logic: Keep it valid? 
            # In index.html logic, we keep everything.
            
            # Queue Stream Details Fetch
            m['_streamEmbeds'] = {} # Initialize container
            if m.get('sources'):
                for src in m['sources']:
                    s_source = src.get('source')
                    s_id = src.get('id')
                    future = executor.submit(get_stream_details, s_source, s_id)
                    stream_detail_jobs[future] = (m, s_source)
            
            valid_streamed.append(m)
        
        # Collect Stream Details
        print(f" > Fetching inner stream details for {len(stream_detail_jobs)} sources...")
        for future in as_completed(stream_detail_jobs):
            match_obj, src_name = stream_detail_jobs[future]
            try:
                details = future.result()
                if details:
                    # Store exactly as in JS logic: dict key = source name
                    match_obj['_streamEmbeds'][src_name] = details
                    
                    # Calculate total viewers for this match
                    current_v = match_obj.get('_totalViewers', 0)
                    for d in details:
                        current_v += d.get('viewers', 0)
                    match_obj['_totalViewers'] = current_v
            except:
                pass

    # 3. Merge
    print(" > Merging matches...")
    merged_raw = merge_matches(valid_streamed, res_b)
    
    final_list = []
    
    for item in merged_raw:
        sm = item['sm']
        am = item['am']
        
        # --- CONSTRUCT FINAL OBJECT ---
        
        # 1. Teams
        home = ""
        away = ""
        
        if sm:
            home = sm.get('teams', {}).get('home', {}).get('name')
            away = sm.get('teams', {}).get('away', {}).get('name')
        
        # Fallback to Adstrim if empty
        if not home and am: home = am.get('home_team')
        if not away and am: away = am.get('away_team')
        
        # 2. Title
        # JS Logic: sm.title || am.title || joined teams
        title = ""
        if sm: title = sm.get('title')
        if not title and am: title = am.get('title')
        if not title and home and away: title = f"{home} vs {away}"
        
        # 3. League
        # JS Logic: if both match, use am.league. Else sm.league || am.league || category || sport
        league = ""
        sm_l = sm.get('league') if sm else ""
        am_l = am.get('league') if am else ""
        
        if sm_l and am_l and normalize(sm_l) == normalize(am_l):
            league = am_l
        else:
            league = sm_l or am_l
            if not league:
                league = sm.get('category') if sm else (am.get('sport') if am else "")
                
        # 4. Sport
        sport = ""
        if sm: sport = sm.get('category')
        if not sport and am: sport = am.get('sport')
        if not sport: sport = "General"
        
        # 5. Timing
        # Prefer Streamed date, else Adstrim timestamp
        ts = 0
        if sm and sm.get('date'):
            ts = sm['date']
            if ts < 10000000000: ts *= 1000
        elif am and am.get('timestamp'):
            ts = am['timestamp']
            if ts < 10000000000: ts *= 1000
            
        # 6. Streams
        # Combine sm._streamEmbeds and am.channels
        streams = []
        
        # From Streamed
        if sm and '_streamEmbeds' in sm:
            for src_key, details_list in sm['_streamEmbeds'].items():
                for d in details_list:
                    streams.append({
                        'source': 'streamed',
                        'type': src_key,
                        'name': f"{src_key} {d.get('streamNo','')}",
                        'url': d.get('embedUrl'), # Use embedUrl specifically
                        'hd': d.get('hd', False),
                        'lang': d.get('language', '')
                    })
        
        # From Adstrim
        if am and am.get('channels'):
            for ch in am['channels']:
                # JS: embedUrl: `https://topembed.pw/channel/${c.name}`
                streams.append({
                    'source': 'adstrim',
                    'name': ch.get('name'),
                    'url': f"{TOPEMBED_BASE}{ch.get('name')}",
                    'hd': False,
                    'lang': ''
                })

        # 7. Images Meta (For Downloader)
        img_meta = {
            'home_name': home,
            'away_name': away,
            'league_name': league,
            'sm_home_badge': sm.get('teams', {}).get('home', {}).get('badge') if sm else None,
            'sm_away_badge': sm.get('teams', {}).get('away', {}).get('badge') if sm else None,
            'am_home_img': am.get('home_team_image') if am else None,
            'am_away_img': am.get('away_team_image') if am else None,
            'am_home_dict': am.get('home_team_images') if am else None,
            'am_away_dict': am.get('away_team_images') if am else None,
            'am_league_img': am.get('league_image') or am.get('league_images') if am else None
        }

        # 8. Status & Scoring
        now_ms = time.time() * 1000
        viewers = sm.get('_totalViewers', 0) if sm else 0
        duration = int(am.get('duration')) if am and am.get('duration') else SPORT_DURATIONS.get('default', 130)
        end_time = ts + (duration * 60 * 1000)
        # --- FILTER: REMOVE EXPIRED MATCHES ---
        if now_ms > end_time and viewers == 0:
            continue
        # --------------------------------------
        
        is_live = False
        status_text = ""
        
        # Determine Live
        if viewers > 0: is_live = True
        elif ts <= now_ms <= end_time: is_live = True
        
        # Calculate Status Text
        if is_live:
            diff = now_ms - ts
            if diff < 0: mins = 0
            else: mins = int(diff / 60000)
            h, m = divmod(mins, 60)
            status_text = f"{h}h {m:02d}'" if h > 0 else f"{m}'"
        else:
            diff = ts - now_ms
            if diff < 0: status_text = "Starting"
            else:
                secs = int(diff / 1000)
                d = secs // 86400
                h = (secs % 86400) // 3600
                m = (secs % 3600) // 60
                p = []
                if d > 0: p.append(f"{d}d")
                if d > 0 or h > 0: p.append(f"{h}h")
                p.append(f"{m}m")
                status_text = " ".join(p)

        # Generate ID
        # SEO Friendly ID
        h_s = slugify(home)
        a_s = slugify(away)
        base = f"{h_s}-vs-{a_s}" if a_s else h_s
        if not base: base = slugify(title)
        
        # Unique Hash
        uid_raw = f"{ts}-{home}-{away}"
        uid = hashlib.md5(uid_raw.encode()).hexdigest()
        seo_id = f"{base}-{uid[:8]}"
        
        # Clean Names
        def clean_name(n):
            if not n or n == 'TBA': return "TBA"
            return n.replace('_', ' ').strip()
        
        home = clean_name(home)
        away = clean_name(away)
        
        # SCORING (For Sorting)
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
                base = 5 * 10**18 if is_boosted else 0
                score = base + (admin_score * 10**15) + viewers
        else:
            base = 5 * 10**18 if is_boosted else 0
            score = base + (admin_score * 10**15) - ts

        final_list.append({
            'id': seo_id,
            'home': home, 'away': away,
            'title': title, # Backup title
            'league': league, 'sport': sport,
            'timestamp': ts,
            'is_live': is_live,
            'status_text': status_text,
            'viewers': viewers,
            'streams': streams,
            'score': score,
            'is_single': (not away or away == "TBA"),
            '_img_meta': img_meta
        })

    return final_list

# ==============================================================================
# 5. IMAGE CHECKER & DOWNLOADER (60x60 WebP)
# ==============================================================================
def run_image_downloader(matches):
    print(" > Checking for new images (Resize 60x60 WebP)...")
    
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
        if not os.path.exists(d): os.makedirs(d, exist_ok=True)

    def process_and_save(url, save_path):
        try:
            h = {'User-Agent': 'Mozilla/5.0'}
            r = requests.get(url, headers=h, timeout=5)
            if r.status_code == 200:
                img = Image.open(BytesIO(r.content))
                
                # --- REQUIREMENT: Resize to 60x60 ---
                img = img.resize((60, 60), Image.Resampling.LANCZOS)
                
                # --- REQUIREMENT: Convert to WEBP ---
                img.save(save_path, 'WEBP', quality=90)
                return True
        except Exception:
            pass
        return False

    for m in matches:
        meta = m.get('_img_meta', {})
        
        # 1. PROCESS HOME TEAM
        h_name = m['home']
        if h_name and h_name != 'TBA' and h_name not in img_map['teams']:
            success = False
            
            # Try Streamed (Priority)
            if meta.get('sm_home_badge'):
                url = f"https://streamed.pk/api/images/badge/{meta['sm_home_badge']}.webp"
                fname = f"assets/logos/streamed/{slugify(h_name)}.webp"
                if process_and_save(url, fname):
                    img_map['teams'][h_name] = fname
                    success = True
                    updated = True
            
            # Try Adstrim
            if not success:
                url = meta.get('am_home_img')
                # Check dict
                if not url and meta.get('am_home_dict'):
                    d = meta['am_home_dict']
                    if isinstance(d, dict): url = d.get('sofascore') or d.get('flashscore')
                
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
            if meta.get('sm_away_badge'):
                url = f"https://streamed.pk/api/images/badge/{meta['sm_away_badge']}.webp"
                fname = f"assets/logos/streamed/{slugify(a_name)}.webp"
                if process_and_save(url, fname):
                    img_map['teams'][a_name] = fname
                    success = True
                    updated = True
            
            # Try Adstrim
            if not success:
                url = meta.get('am_away_img')
                if not url and meta.get('am_away_dict'):
                    d = meta['am_away_dict']
                    if isinstance(d, dict): url = d.get('sofascore') or d.get('flashscore')
                
                if url:
                    fname = f"assets/logos/upstreams/{slugify(a_name)}.webp"
                    if process_and_save(url, fname):
                        img_map['teams'][a_name] = fname
                        updated = True

        # 3. PROCESS LEAGUE
        l_name = m['league']
        if l_name and l_name not in img_map['leagues']:
            url = meta.get('am_league_img')
            if url:
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
# 6. HTML RENDERERS
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

    # Handle Missing Teams -> Show Title
    if m['home'] == "TBA" and m['away'] == "TBA" and m['title']:
        teams_html = f'<div class="team-name" style="justify-content:center; font-weight:600;">{m["title"]}</div>'
    else:
        teams_html = render_team(m["home"])
        if not m['is_single']: teams_html += render_team(m["away"])

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    
    svg_icon = '<svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>'
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')">{svg_icon} Link</button>'

    btn = ""
    diff = (m['timestamp'] - time.time()*1000) / 60000
    
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
    # Note: LEAGUE_MAP is global now, but we can pass config's REVERSE Map if needed. 
    # For now passing empty to not break JS, or rebuild reverse map if frontend needs it.
    html = html.replace('{{JS_LEAGUE_MAP}}', '{}') 
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
# 7. BUILDERS
# ==============================================================================
def build_homepage(matches):
    print(" > Injecting matches into Homepage...")
    
    # 1. Read the EXISTING index.html (Created by build_site.py)
    if not os.path.exists('index.html'):
        print(" ! Error: index.html not found. Run build_site.py first.")
        return
        
    with open('index.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 2. Filter Matches
    live_matches = sorted([m for m in matches if m['is_live']], key=lambda x: x.get('score',0), reverse=True)
    
    now_ms = time.time() * 1000
    one_day = 24 * 60 * 60 * 1000
    
    upcoming_full = [m for m in matches if not m['is_live']]
    upcoming_full.sort(key=lambda x: x.get('score',0), reverse=True)
    
    used_ids = set(m['id'] for m in live_matches)

    # 3. Generate HTML Fragments (Only Content)
    
    # Live Section
    live_html = render_container(live_matches, THEME.get('text_live_section_title', 'Trending Live'), '🔴', None, True)

    # Wildcard or Top 5
    wc_cat = THEME.get('wildcard_category', '').lower()
    wc_active = len(wc_cat) > 2
    wc_html = ""
    top5_html = ""

    if wc_active:
        wc_m = [m for m in upcoming_full if wc_cat in m['league'].lower() or wc_cat in m['sport'].lower()]
        for m in wc_m: used_ids.add(m['id'])
        wc_html = render_container(wc_m, THEME.get('text_wildcard_title', 'Featured'), '🔥', None)
    else:
        top5 = []
        used_leagues = set()
        for m in upcoming_full:
            if len(top5) >= 5: break
            if m['id'] in used_ids or (m['timestamp'] - now_ms >= one_day): continue
            
            # Simple diversity check
            l_key = m['league'] or m['sport']
            if l_key in used_leagues: continue
            
            top5.append(m)
            used_ids.add(m['id'])
            used_leagues.add(l_key)
        top5_html = render_container(top5, THEME.get('text_top_upcoming_title', 'Top Upcoming'), '📅', None)

    # Grouped Section
    grouped_html = ""
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
            grouped_html += render_container(grp, key, icon, link)

    # 4. INJECTION (Regex Replace)
    # We look for the specific ID containers and replace ONLY their inner content
    
    # Inject Live
    if live_html:
        html = re.sub(r'(<div id="live-section-container"[^>]*>).*?(</div>)', f'\\1{live_html}\\2', html, flags=re.DOTALL)
        # Ensure wrapper is visible
        html = html.replace('id="live-content-wrapper" style="display:none;"', 'id="live-content-wrapper"') 
    else:
        html = re.sub(r'(<div id="live-section-container"[^>]*>).*?(</div>)', '\\1\\2', html, flags=re.DOTALL)
        # Hide wrapper if empty
        html = html.replace('id="live-content-wrapper"', 'id="live-content-wrapper" style="display:none;"')

    # Inject Wildcard
    html = re.sub(r'(<div id="wildcard-section-container"[^>]*>).*?(</div>)', f'\\1{wc_html}\\2', html, flags=re.DOTALL)
    
    # Inject Top 5
    html = re.sub(r'(<div id="top5-section-container"[^>]*>).*?(</div>)', f'\\1{top5_html}\\2', html, flags=re.DOTALL)
    
    # Inject Grouped
    html = re.sub(r'(<div id="grouped-section-container"[^>]*>).*?(</div>)', f'\\1{grouped_html}\\2', html, flags=re.DOTALL)

    # Remove Skeletons (CSS logic usually handles this, but good to clean up)
    html = re.sub(r'<div id="live-sk-head".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="live-skeleton".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="upcoming-skeleton".*?</div>', '', html, flags=re.DOTALL)

    # Update Schema (Optional but recommended for SEO freshness)
    schema_data = {
        "@context": "https://schema.org", "@type": "ItemList",
        "itemListElement": [{
            "@type": "SportsEvent", 
            "name": f"{m['home']} vs {m['away']}" if not m['is_single'] else m['home'],
            "startDate": datetime.fromtimestamp(m['timestamp']/1000).isoformat(),
            "url": f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
        } for m in (live_matches + upcoming_full)[:20]]
    }
    # Regex to find the schema script and replace it
    html = re.sub(r'(<script type="application/ld\+json">).*?(</script>)', f'\\1{json.dumps(schema_data)}\\2', html, flags=re.DOTALL)

    # 5. Save
    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_watch_page(matches):
    print(" > Injecting matches into Watch Page...")
    target_file = 'watch/index.html'
    
    # 1. Check if file exists (Created by build_site.py)
    if not os.path.exists(target_file):
        print(f" ! Watch page not found at {target_file}")
        return

    # 2. Read File
    with open(target_file, 'r', encoding='utf-8') as f:
        html = f.read()

    # 3. Prepare injection data
    # We inject the full list so the JS frontend can handle routing/display
    data_string = f"window.MATCH_DATA = {json.dumps(matches)};"

    # 4. Regex Injection
    # This regex looks for EITHER:
    # A) The initial placeholder comment: // {{INJECTED_MATCH_DATA}}
    # B) OR An existing variable assignment: window.MATCH_DATA = [...];
    # This ensures it works immediately after build_site.py AND on subsequent updates.
    pattern = r'(//\s*\{\{INJECTED_MATCH_DATA\}\}|window\.MATCH_DATA\s*=\s*\[.*?\];)'
    
    if re.search(pattern, html, flags=re.DOTALL):
        html = re.sub(pattern, data_string, html, flags=re.DOTALL)
        
        # 5. Save
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
        
        # 1. Check if file exists (Created by build_site.py)
        if not os.path.exists(target_file): 
            continue

        # 2. Filter Matches
        l_matches = [m for m in matches if key.lower() in m['league'].lower() or key.lower() in m['sport'].lower()]
        l_live = sorted([m for m in l_matches if m['is_live']], key=lambda x: x.get('score',0), reverse=True)
        l_upc = [m for m in l_matches if not m['is_live']]
        l_upc.sort(key=lambda x: x['timestamp'])

        # 3. Read File
        with open(target_file, 'r', encoding='utf-8') as f:
            html = f.read()

        # 4. Inject LIVE Section
        if l_live:
            live_content = render_container(l_live, f"Live {key}", "🔴", None, True)
            # Replace inner content of #live-list
            html = re.sub(r'(<div id="live-list"[^>]*>).*?(</div>)', f'\\1{live_content}\\2', html, flags=re.DOTALL)
            # Show the section container
            html = html.replace('id="live-section" style="display:none;"', 'id="live-section"')
        else:
            # Empty the list
            html = re.sub(r'(<div id="live-list"[^>]*>).*?(</div>)', '\\1\\2', html, flags=re.DOTALL)
            # Hide the section container
            html = html.replace('id="live-section"', 'id="live-section" style="display:none;"')

        # 5. Inject UPCOMING Section
        # Matches <div id="schedule-list">...</div>
        rows_html = "".join([render_match_row(m, key) for m in l_upc]) if l_upc else '<div class="match-row" style="justify-content:center;">No upcoming matches found.</div>'
        html = re.sub(r'(<div id="schedule-list"[^>]*>).*?(</div>)', f'\\1{rows_html}\\2', html, flags=re.DOTALL)

        # 6. Save
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
