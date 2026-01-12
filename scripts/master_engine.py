import os
import json
import requests
import hashlib
import time
import re
import urllib.parse
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
IMAGE_MAP_PATH = 'assets/data/image_map.json'
TEMPLATE_MASTER = 'assets/master_template.html' # Now using Source
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

# EXTENSIVE SPORT MAPPING
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
# 2. UTILS & TEMPLATE HELPERS
# ==========================================
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

# --- MENU & FOOTER BUILDERS (From Build Site) ---
def build_menu_html(menu_items, section):
    html = ""
    for item in menu_items:
        title = item.get('title', 'Link')
        url = item.get('url', '#')
        if section == 'header':
            css_class = ' class="highlighted"' if item.get('highlight') else ''
            html += f'<a href="{url}"{css_class}>{title}</a>'
        elif section == 'hero':
            html += f'<a href="{url}" class="cat-pill">{title}</a>'
        elif section == 'footer_leagues':
            html += f'<a href="{url}" class="league-card"><span class="l-icon">🏆</span><span>{title}</span></a>'
        elif section == 'footer_static':
             html += f'<a href="{url}" class="f-link">{title}</a>'
    return html

def build_footer_grid(config, active_theme):
    t = active_theme
    s = config.get('site_settings', {})
    m = config.get('menus', {})
    cols = str(t.get('footer_columns', '2'))
    
    p1 = s.get('title_part_1', 'Stream')
    p2 = s.get('title_part_2', 'East')
    logo_size = ensure_unit(t.get('logo_image_size', '40px'))
    
    logo_html = f'<div class="logo-text" style="color:{t.get("logo_p1_color")};">{p1}<span style="color:{t.get("logo_p2_color")};">{p2}</span></div>'
    if s.get('logo_url'): 
        logo_html = f'<img src="{s.get("logo_url")}" class="logo-img" style="width:{logo_size}; height:{logo_size}; object-fit:cover; border-radius:6px;"> {logo_html}'
    
    brand_html = f'<div class="f-brand">{logo_html}</div>'
    disc_html = f'<div class="f-desc">{s.get("footer_disclaimer", "")}</div>' if t.get('footer_show_disclaimer', True) else ''
    brand_disc_html = f'<div class="f-brand">{logo_html}{disc_html}</div>'
    links_html = f'<div><div class="f-head">Quick Links</div><div class="f-links">{build_menu_html(m.get("footer_static", []), "footer_static")}</div></div>'
    
    slots = [t.get('footer_slot_1', 'brand_disclaimer'), t.get('footer_slot_2', 'menu'), t.get('footer_slot_3', 'empty')]
    
    def get_content(k):
        if k == 'brand': return brand_html
        if k == 'disclaimer': return disc_html
        if k == 'brand_disclaimer': return brand_disc_html
        if k == 'menu': return links_html
        return '<div></div>'

    html = f'<div class="footer-grid cols-{cols}">'
    html += get_content(slots[0])
    html += get_content(slots[1])
    if cols == '3': html += get_content(slots[2])
    html += '</div>'
    return html

# --- THEME APPLIER (Merges Config into Template) ---
def apply_theme_to_template(html, page_data=None):
    if page_data is None: page_data = {}
    
    # 1. Variables Processing
    def make_border(w_key, c_key):
        return f"{ensure_unit(THEME.get(w_key, '1'))} solid {THEME.get(c_key, '#334155')}"

    # Inject calculated vars into THEME dict for replacement
    THEME['sec_border_live'] = make_border('sec_border_live_width', 'sec_border_live_color')
    THEME['sec_border_upcoming'] = make_border('sec_border_upcoming_width', 'sec_border_upcoming_color')
    THEME['sec_border_wildcard'] = make_border('sec_border_wildcard_width', 'sec_border_wildcard_color')
    THEME['sec_border_leagues'] = make_border('sec_border_leagues_width', 'sec_border_leagues_color')
    THEME['sec_border_grouped'] = make_border('sec_border_grouped_width', 'sec_border_grouped_color')
    
    THEME['league_card_border'] = make_border('league_card_border_width', 'league_card_border_color')
    THEME['league_card_hover_border'] = make_border('league_card_border_width', 'league_card_hover_border_color')
    THEME['sys_status_border'] = make_border('sys_status_border_width', 'sys_status_border_color')
    THEME['static_h1_border'] = make_border('static_h1_border_width', 'static_h1_border_color') # Needed if used

    # Unit Enforcement
    for k in ['border_radius_base', 'container_max_width', 'header_max_width', 'hero_pill_radius', 'button_border_radius', 'logo_image_size', 'section_logo_size', 'sys_status_radius', 'sys_status_dot_size', 'league_card_radius']:
        if k in THEME: THEME[k] = ensure_unit(THEME[k])

    s_bg_hex = THEME.get('sys_status_bg_color', '#22c55e')
    s_bg_op = THEME.get('sys_status_bg_opacity', '0.1')
    THEME['sys_status_bg_color'] = 'transparent' if str(THEME.get('sys_status_bg_transparent')).lower() == 'true' else hex_to_rgba(s_bg_hex, s_bg_op)
    THEME['sys_status_display'] = 'inline-flex' if THEME.get('sys_status_visible', True) else 'none'

    # 2. Text Replacements
    replacements = {
        'META_TITLE': page_data.get('meta_title', 'Live Sports Stream'),
        'META_DESC': page_data.get('meta_desc', 'Watch live sports online.'),
        'SITE_NAME': f"{SITE_SETTINGS.get('title_part_1','')}{SITE_SETTINGS.get('title_part_2','')}",
        'CANONICAL_URL': f"https://{DOMAIN}/",
        'FAVICON': SITE_SETTINGS.get('favicon_url', ''),
        'OG_IMAGE': SITE_SETTINGS.get('logo_url', ''),
        'H1_TITLE': page_data.get('h1_title', 'Live Streams'),
        'HERO_TEXT': page_data.get('hero_text', 'Watch your favorite sports live.'),
        'ARTICLE_CONTENT': page_data.get('article', ''),
        'FOOTER_COPYRIGHT': SITE_SETTINGS.get('footer_copyright', ''),
        'THEME_TEXT_SYS_STATUS': THEME.get('text_sys_status', 'System Status: Online'),
        'LOGO_PRELOAD': f'<link rel="preload" as="image" href="{SITE_SETTINGS.get("logo_url")}">' if SITE_SETTINGS.get('logo_url') else '',
        'API_URL': SITE_SETTINGS.get('api_url', ''),
        'TARGET_COUNTRY': TARGET_COUNTRY,
        'PARAM_LIVE': PARAM_LIVE,
        'PARAM_INFO': PARAM_INFO,
        'DOMAIN': DOMAIN,
        
        # Section Titles
        'TEXT_LIVE_SECTION_TITLE': THEME.get('text_live_section_title', 'Trending Live'),
        'TEXT_WILDCARD_TITLE': THEME.get('text_wildcard_title', ''),
        'TEXT_TOP_UPCOMING_TITLE': THEME.get('text_top_upcoming_title', 'Top Upcoming'),
        'TEXT_SHOW_MORE': THEME.get('text_show_more', 'Show More'),
        'TEXT_WATCH_BTN': THEME.get('text_watch_btn', 'WATCH'),
        'TEXT_HD_BADGE': THEME.get('text_hd_badge', 'HD'),
        'TEXT_SECTION_LINK': THEME.get('text_section_link', 'View All'),
        'TEXT_SECTION_PREFIX': THEME.get('text_section_prefix', 'Upcoming'),
        'WILDCARD_CATEGORY': THEME.get('wildcard_category', '')
    }

    # Inject Theme Variables {{THEME_KEY}}
    for k, v in THEME.items():
        html = html.replace(f"{{{{THEME_{k.upper()}}}}}", str(v))

    # Inject Text Vars {{KEY}}
    for k, v in replacements.items():
        html = html.replace(f"{{{{{k}}}}}", str(v))

    # 3. Inject Menus & Footer
    MENUS = config.get('menus', {})
    html = html.replace('{{HEADER_MENU}}', build_menu_html(MENUS.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(MENUS.get('hero', []), 'hero'))
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config, THEME))
    
    # Footer Leagues (From Priority)
    f_leagues = []
    for k, v in PRIORITY_SETTINGS.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{slugify(k)}-streams/"})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))

    # 4. Logo HTML
    p1 = SITE_SETTINGS.get('title_part_1', 'Stream')
    p2 = SITE_SETTINGS.get('title_part_2', 'East')
    logo_size = THEME.get('logo_image_size', '40px')
    logo_html = f'<div class="logo-text" style="color:{THEME.get("logo_p1_color")};">{p1}<span style="color:{THEME.get("logo_p2_color")};">{p2}</span></div>'
    if SITE_SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SITE_SETTINGS.get("logo_url")}" class="logo-img" style="width:{logo_size}; height:{logo_size}; object-fit:cover; border-radius:6px; box-shadow: 0 0 10px {THEME.get("logo_image_shadow_color","rgba(0,0,0,0)")}"> {logo_html}'
    html = html.replace('{{LOGO_HTML}}', logo_html)

    # 5. Header/Hero Classes & Styles
    h_layout = THEME.get('header_layout', 'standard')
    h_icon = THEME.get('header_icon_pos', 'left')
    html = html.replace('{{HEADER_CLASSES}}', f"h-layout-{h_layout}{' h-icon-'+h_icon if h_layout=='center' else ''}")
    html = html.replace('{{FOOTER_CLASSES}}', '')

    # Hero Logic
    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    h_style = THEME.get('hero_bg_style', 'solid')
    
    hero_bg = f"background: {THEME.get('hero_bg_solid')};"
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

    # JS Injections
    html = html.replace('{{JS_THEME_CONFIG}}', json.dumps(THEME))
    html = html.replace('{{JS_PRIORITIES}}', json.dumps(PRIORITY_SETTINGS))
    
    # Reverse Map
    rev_map = {}
    if image_map.get('leagues'):
        l_map = load_json('assets/data/league_map.json') # Load original map for team->league logic
        if l_map:
            for k, v in l_map.items():
                for t in v: rev_map[t] = k
    html = html.replace('{{JS_LEAGUE_MAP}}', json.dumps(rev_map))
    html = html.replace('{{JS_IMAGE_MAP}}', json.dumps(image_map))

    return html

# ==========================================
# 3. NORMALIZATION & MATCHING
# ==========================================
def slugify(text):
    if not text: return ""
    text = re.sub(r'[^\w\s-]', '', str(text).lower())
    return re.sub(r'[-\s]+', '-', text).strip("-")

def normalize_sport(sport_raw, league_raw=""):
    s = (sport_raw or "").lower().strip()
    l = (league_raw or "").lower().strip()
    if 'nfl' in l or 'college football' in l: return 'American Football'
    if 'nba' in l: return 'Basketball'
    if 'nhl' in l: return 'Ice Hockey'
    if 'ufc' in l: return 'MMA'
    if 'f1' in l or 'formula' in l: return 'Formula 1'
    return SPORT_MAPPING.get(s, s.title() if s else "General")

def clean_team_name(name):
    if not name: return "TBA"
    clean = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs)\b', '', name, flags=re.IGNORECASE)
    return clean.replace('_', ' ').strip()

def generate_match_id(sport, start_unix, home, away):
    if not start_unix: start_unix = time.time() * 1000
    # FIX: UTC TIMEZONE for Consistency
    date = datetime.fromtimestamp(start_unix / 1000, tz=timezone.utc)
    date_key = date.strftime('%Y-%m-%d')
    def c(s): return re.sub(r'[^a-z0-9]', '', (s or '').lower())
    teams = sorted([c(home), c(away)])
    raw = f"{sport.lower()}-{date_key}-{teams[0]}v{teams[1]}"
    return hashlib.md5(raw.encode('utf-8')).hexdigest()

def tokenize_name(text):
    if not text: return set()
    clean = re.sub(r'\b(fc|cf|sc|afc|ec|club|v|vs|at|united|city|real|inter)\b', '', text.lower())
    clean = re.sub(r'[^a-z0-9\s]', '', clean)
    return set(w for w in clean.split() if len(w) > 2)

def is_match_fuzzy_same(m_existing, m_candidate):
    diff = abs(m_existing['timestamp'] - m_candidate['timestamp'])
    if diff > 45 * 60 * 1000: return False
    
    t1_home = tokenize_name(m_existing['home'])
    t1_away = tokenize_name(m_existing['away'])
    t2_home = tokenize_name(m_candidate['home'])
    t2_away = tokenize_name(m_candidate['away'])
    
    if (not t1_home.isdisjoint(t2_home)) and (not t1_away.isdisjoint(t2_away)): return True
    return False

def get_logo(name, type_key):
    path = image_map[type_key].get(name)
    if path: 
        if not path.startswith('http') and not path.startswith('/'): path = f"/{path}"
        return path
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
    if m['is_live']: score += 5000 + (m.get('live_viewers', 0) / 10)
    else:
        diff = (m['timestamp'] - time.time()*1000) / 3600000
        if diff < 24: score += (24 - diff)
    return score

# ==========================================
# 4. HTML RENDERERS
# ==========================================
def render_match_row(m):
    is_live = m['is_live']
    row_class = "match-row live" if is_live else "match-row"
    
    if is_live:
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{m.get("status_text")}</span>'
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

    teams_html = render_team(m["home"])
    if not m.get('is_single_event'): teams_html += render_team(m["away"])

    if is_live:
        btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_LIVE}={m["id"]}\'" class="btn-watch">{THEME.get("text_watch_btn","WATCH")} <span class="hd-badge">{THEME.get("text_hd_badge","HD")}</span></button>'
    else:
        diff = (m['timestamp'] - time.time()*1000) / 60000
        btn = f'<button onclick="window.location.href=\'/watch/?{PARAM_INFO}={m["id"]}\'" class="btn-watch">{THEME.get("text_watch_btn","WATCH")} <span class="hd-badge">{THEME.get("text_hd_badge","HD")}</span></button>' if diff <= 30 else '<button class="btn-notify">🔔 Notify</button>'

    info_url = f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}"
    copy_btn = f'<button class="btn-copy-link" onclick="copyText(\'{info_url}\')"><svg viewBox="0 0 24 24" width="12" height="12" fill="currentColor"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg> Link</button>'

    return f'<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{m["league"].upper()}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{btn}{copy_btn}</div></div>'

def render_container(matches, title, icon=None, link=None, is_live_section=False):
    if not matches: return ""
    
    html = ""
    img_html = f'<img src="{icon}" class="sec-logo"> ' if (icon and (icon.startswith('http') or icon.startswith('/'))) else f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span> '
    link_html = f'<a href="{link}" class="sec-right-link">{THEME.get("text_section_link","View All")} ></a>' if link else ''
    header = f'<div class="sec-head"><h2 class="sec-title">{img_html}{title}</h2>{link_html}</div>'

    if is_live_section and len(matches) > 5:
        visible = matches[:5]
        hidden = matches[5:]
        rows = "".join([render_match_row(m) for m in visible])
        hidden_rows = "".join([render_match_row(m) for m in hidden])
        btn_id = f"btn-{int(time.time()*1000)}"
        div_id = f"hide-{int(time.time()*1000)}"
        html = f'{header}<div class="match-list">{rows}</div><button id="{btn_id}" class="show-more-btn" onclick="toggleHidden(\'{div_id}\', this)">{THEME.get("text_show_more","Show More")} ({len(hidden)}) ▼</button><div id="{div_id}" class="match-list" style="display:none; margin-top:10px;">{hidden_rows}</div>'
    else:
        rows = "".join([render_match_row(m) for m in matches])
        html = f'{header}<div class="match-list">{rows}</div>'
        
    return f'<div class="section-box">{html}</div>'

# ==========================================
# 5. DATA FETCHING
# ==========================================
def get_match_viewers(match_stream_info):
    url, source, sid = match_stream_info
    try:
        r = requests.get(f"{NODE_A_ENDPOINT}/stream/{source}/{sid}", headers=HEADERS, timeout=2)
        if r.status_code == 200:
            d = r.json()
            data = d[0] if isinstance(d, list) and d else d
            return data.get('viewers', 0)
    except: pass
    return 0

def fetch_and_process():
    print(" > Fetching data...")
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"API Error: {e}")
        return []

    active_live_ids = set(m.get('id') for m in res_live if m.get('id'))
    data_map = {}
    matches_to_check = []

    # 1. STREAMED.PK
    for item in res_a:
        raw_ts = item.get('date') or 0
        timestamp = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
        home = clean_team_name(item.get('home') or item.get('home_team'))
        away = clean_team_name(item.get('away') or item.get('away_team'))
        raw_l = item.get('league') or "General"
        sport = normalize_sport(item.get('category'), raw_l)
        
        uid = generate_match_id(sport, timestamp, home, away)
        is_live = item.get('id') in active_live_ids
        
        data_map[uid] = {
            'id': uid, 'originalId': item.get('id'),
            'home': home, 'away': away, 'league': raw_l, 'sport': sport,
            'timestamp': timestamp, 'is_live': is_live,
            'is_single_event': not away or away == 'TBA',
            'live_viewers': 0, 'streams': item.get('sources', []),
            'source': 'streamed'
        }
        if is_live and item.get('sources'):
            src = item['sources'][0]
            matches_to_check.append((uid, (None, src.get('source'), src.get('id'))))

    # 2. VIEWERS
    if matches_to_check:
        print(f" > Checking viewers for {len(matches_to_check)} matches...")
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_uid = {executor.submit(get_match_viewers, m[1]): m[0] for m in matches_to_check}
            for future in as_completed(future_to_uid):
                uid = future_to_uid[future]
                try: 
                    v = future.result()
                    if uid in data_map: data_map[uid]['live_viewers'] = v
                except: pass

    # 3. ADSTRIM MERGE (SMART)
    if 'data' in res_b:
        for item in res_b['data']:
            raw_ts = item.get('timestamp') or 0
            ts = raw_ts * 1000 if raw_ts < 10000000000 else raw_ts
            home = clean_team_name(item.get('home_team'))
            away = clean_team_name(item.get('away_team'))
            raw_l = item.get('league') or "General"
            sport = normalize_sport(item.get('sport'), raw_l)
            
            uid = generate_match_id(sport, ts, home, away)
            
            ad_streams = []
            if item.get('channels'):
                for ch in item['channels']:
                    ad_streams.append({'source': 'adstrim', 'id': ch.get('name'), 'name': ch.get('name'), 'url': f"{TOPEMBED_BASE}{ch.get('name')}"})

            # Check for existing (Fuzzy)
            found = data_map.get(uid)
            if not found:
                candidate = {'timestamp': ts, 'home': home, 'away': away}
                for existing in data_map.values():
                    if is_match_fuzzy_same(existing, candidate):
                        found = existing
                        break
            
            if found:
                exist_urls = set(s.get('url') or s.get('id') for s in found['streams'])
                for s in ad_streams:
                    if s['id'] not in exist_urls: found['streams'].append(s)
                if item.get('duration'): found['duration'] = item.get('duration')
            else:
                data_map[uid] = {
                    'id': uid, 'originalId': uid,
                    'home': home, 'away': away, 'league': raw_l, 'sport': sport,
                    'timestamp': ts, 'is_live': False,
                    'is_single_event': not away or away == 'TBA',
                    'live_viewers': 0, 'streams': ad_streams,
                    'source': 'adstrim', 'duration': item.get('duration')
                }

    # 4. FINALIZE
    final = list(data_map.values())
    now = time.time() * 1000
    for m in final:
        dur = m.get('duration')
        if not dur:
            s_low = m['sport'].lower()
            dur = next((v for k,v in SPORT_DURATIONS.items() if k in s_low), 130)
        
        end_time = m['timestamp'] + (int(dur) * 60 * 1000)
        is_time_live = m['timestamp'] <= now <= end_time
        m['is_live'] = m['is_live'] or (m.get('live_viewers',0)>0) or is_time_live
        m['status_text'] = get_status_text(m['timestamp'], m['is_live'])
        m['score'] = calculate_score(m)
        
    final.sort(key=lambda x: x['score'], reverse=True)
    return final

# ==========================================
# 6. INJECTION & BUILD
# ==========================================
def build_homepage(matches):
    print(" > Building Homepage from Template...")
    try:
        with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: tpl = f.read()
    except:
        print("Template not found!")
        return

    # 1. Process Home Page Data
    home_page_data = next((p for p in config.get('pages', []) if p['slug'] == 'home'), {})
    
    # 2. Apply Theme & Structure (Menus, Footer, CSS)
    html = apply_theme_to_template(tpl, {
        'meta_title': home_page_data.get('meta_title', 'Live Sports'),
        'meta_desc': home_page_data.get('meta_desc', ''),
        'h1_title': home_page_data.get('title', 'Live Sports'),
        'h1_align': home_page_data.get('h1_align', 'center'),
        'hero_text': home_page_data.get('meta_desc', '')
    })

    # 3. Generate Sections
    live_matches = sorted([m for m in matches if m['is_live']], key=lambda x: x.get('live_viewers', 0), reverse=True)
    upcoming = [m for m in matches if not m['is_live']]
    
    # Live HTML
    live_html = render_container(
        live_matches, 
        THEME.get('text_live_section_title', 'Trending Live'), 
        '<div class="live-dot" style="width:8px;height:8px;background:#ef4444;border-radius:50%;display:inline-block;margin-right:8px;"></div>', 
        None, True
    )

    # Wildcard / Top 5 HTML
    wc_cat = THEME.get('wildcard_category', '').lower()
    wc_active = len(wc_cat) > 2
    wc_html = ""
    top5_html = ""

    if wc_active:
        wc_m = [m for m in upcoming if wc_cat in (m.get('league') or '').lower() or wc_cat in (m.get('sport') or '').lower()]
        title = THEME.get('text_wildcard_title') or f"{wc_cat.title()} Matches"
        wc_html = render_container(wc_m, title, '🔥', None)
    else:
        top5 = upcoming[:5]
        title = THEME.get('text_top_upcoming_title') or "Top Upcoming"
        top5_html = render_container(top5, title, '📅', None)

    # Grouped HTML
    grouped_html = ""
    used_ids = set([m['id'] for m in live_matches] + [m['id'] for m in (wc_m if wc_active else top5)])
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

    # 4. Inject Content
    # We remove the SKELETONS first since we are providing real data
    html = re.sub(r'<div id="live-skeleton".*?</div>', '', html, flags=re.DOTALL)
    html = re.sub(r'<div id="upcoming-skeleton".*?</div>', '', html, flags=re.DOTALL)
    
    html = html.replace('<div id="live-content-wrapper" style="display:none;">', '<div id="live-content-wrapper">') # Unhide wrapper
    html = re.sub(r'<div id="trending-list".*?</div>', f'<div id="trending-list" class="match-list">{live_html}</div>', html, flags=re.DOTALL)
    
    # If using containers directly (Alternative injection point)
    html = re.sub(r'<div id="live-section">.*?</div>', f'<div id="live-section">{live_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="wildcard-container">.*?</div>', f'<div id="wildcard-container">{wc_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="top-upcoming-container">.*?</div>', f'<div id="top-upcoming-container">{top5_html}</div>', html, flags=re.DOTALL)
    html = re.sub(r'<div id="grouped-container">.*?</div>', f'<div id="grouped-container">{grouped_html}</div>', html, flags=re.DOTALL)

    # 5. Schema
    schema_json = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "itemListElement": [{
            "@type": "SportsEvent",
            "name": f"{m['home']} vs {m['away']}" if not m['is_single_event'] else m['home'],
            "startDate": datetime.fromtimestamp(m['timestamp']/1000).isoformat(),
            "url": f"https://{DOMAIN}/watch/?{PARAM_INFO}={m['id']}",
            "competitor": [{"@type": "SportsTeam", "name": m['home']}, {"@type": "SportsTeam", "name": m['away']}]
        } for m in (live_matches + upcoming)[:20]]
    })
    html = html.replace('{{SCHEMA_BLOCK}}', f'<script type="application/ld+json">{schema_json}</script>')

    # 6. Write to Index
    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_watch_page(matches):
    if not os.path.exists('watch/index.html'): return
    with open('watch/index.html', 'r', encoding='utf-8') as f: html = f.read()
    # Inject Match Data for Client-Side hydration
    json_data = json.dumps(matches)
    html = html.replace('// {{INJECTED_MATCH_DATA}}', f'window.MATCH_DATA = {json_data};')
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(html)

def inject_leagues(matches):
    # This assumes structure already exists from build_site.py or you can adapt to build from template like above
    # For now, keeping legacy injection style for speed
    for key in PRIORITY_SETTINGS:
        slug = slugify(key) + "-streams"
        path = f"{slug}/index.html"
        if os.path.exists(path):
            l_matches = [m for m in matches if key.lower() in (m.get('league') or '').lower() or key.lower() in (m.get('sport') or '').lower()]
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
# 7. MAIN EXECUTION
# ==========================================
def main():
    print("--- 🚀 Master Engine Running ---")
    matches = fetch_and_process()
    print(f" > Processed {len(matches)} matches.")
    
    build_homepage(matches) # Builds index.html from Master Template
    print(" > Homepage Rebuilt.")
    
    inject_watch_page(matches)
    print(" > Watch Page Injected.")
    
    inject_leagues(matches)
    print(" > League Pages Updated.")

if __name__ == "__main__":
    main()
