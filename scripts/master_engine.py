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

OUTPUT_DIR = '.' 
ASSETS_DIR = 'assets/logos'

NODE_A_ENDPOINT = 'https://streamed.pk/api'
ADSTRIM_ENDPOINT = 'https://beta.adstrim.ru/api/events'
STREAMED_IMG_BASE = "https://streamed.pk/api/images/badge/"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

NAME_FIXES = {
    "icehockey": "Ice Hockey", "fieldhockey": "Field Hockey",
    "tabletennis": "Table Tennis", "americanfootball": "American Football",
    "australianfootball": "AFL", "basketball": "Basketball",
    "football": "Soccer", "soccer": "Soccer", "baseball": "Baseball",
    "fighting": "Fighting", "mma": "MMA", "boxing": "Boxing",
    "motorsport": "Motorsport", "golf": "Golf"
}

# ==========================================
# 2. DATA LOADING
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

config = load_json(CONFIG_PATH)
league_map = load_json(LEAGUE_MAP_PATH)
image_map = load_json(IMAGE_MAP_PATH)

SITE_SETTINGS = config.get('site_settings', {})
TARGET_COUNTRY = SITE_SETTINGS.get('target_country', 'US')
PRIORITY_SETTINGS = config.get('sport_priorities', {}).get(TARGET_COUNTRY, {})
DOMAIN = SITE_SETTINGS.get('domain', 'example.com')
THEME = config.get('theme', {})
MENUS = config.get('menus', {})

REVERSE_LEAGUE_MAP = {}
for l_name, teams in league_map.items():
    for t in teams:
        REVERSE_LEAGUE_MAP[t] = l_name

# ==========================================
# 3. UTILS & RENDERING HELPERS (Ported from build_site.py)
# ==========================================
def slugify(text):
    if not text: return ""
    clean = str(text).lower()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"\s+", "-", clean)
    return clean.strip("-")

def unslugify(slug):
    return slug.replace('-', ' ').title()

def ensure_unit(val, unit='px'):
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
    except: return hex_code

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
            icon = "🏆" # Simplified logic for speed
            html += f'<a href="{url}" class="league-card"><span class="l-icon">{icon}</span><span>{title}</span></a>'
        elif section == 'footer_static':
             html += f'<a href="{url}" class="f-link">{title}</a>'
    return html

def build_footer_grid(cfg):
    t = cfg.get('theme', {})
    s = cfg.get('site_settings', {})
    m = cfg.get('menus', {})
    cols = str(t.get('footer_columns', '2'))
    
    # Components
    p1 = s.get('title_part_1', 'Stream')
    p2 = s.get('title_part_2', 'East')
    logo_html = f'<div class="logo-text">{p1}<span>{p2}</span></div>'
    if s.get('logo_url'): logo_html = f'<img src="{s.get("logo_url")}" class="logo-img"> {logo_html}'
    
    brand_html = f'<div class="f-brand">{logo_html}</div>'
    disc_html = f'<div class="f-desc">{s.get("footer_disclaimer", "")}</div>' if t.get('footer_show_disclaimer', True) else ''
    brand_disc_html = f'<div class="f-brand">{logo_html}{disc_html}</div>'
    links_html = f'<div><div class="f-head">Quick Links</div><div class="f-links">{build_menu_html(m.get("footer_static", []), "footer_static")}</div></div>'
    
    # Slots
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

# ==========================================
# 4. THEME & TEMPLATE ENGINE
# ==========================================
def apply_theme_and_content(html, page_data=None):
    """
    Replaces all {{THEME_...}} and {{META_...}} placeholders.
    This restores the visual style from your Admin Panel.
    """
    if page_data is None: page_data = {}
    
    # 1. THEME MAPPING (JSON Key -> Template Placeholder)
    mapping = {
        'brand_primary': 'THEME_BRAND_PRIMARY', 'brand_dark': 'THEME_BRAND_DARK',
        'accent_gold': 'THEME_ACCENT_GOLD', 'status_green': 'THEME_STATUS_GREEN',
        'bg_body': 'THEME_BG_BODY', 'bg_panel': 'THEME_BG_PANEL',
        'text_main': 'THEME_TEXT_MAIN', 'text_muted': 'THEME_TEXT_MUTED',
        'border_color': 'THEME_BORDER_COLOR',
        
        'font_family_base': 'THEME_FONT_FAMILY_BASE',
        'font_family_headings': 'THEME_FONT_FAMILY_HEADINGS',
        'container_max_width': 'THEME_CONTAINER_MAX_WIDTH',
        'header_max_width': 'THEME_HEADER_MAX_WIDTH',
        'border_radius_base': 'THEME_BORDER_RADIUS_BASE',
        'button_border_radius': 'THEME_BUTTON_BORDER_RADIUS',
        'hero_pill_radius': 'THEME_HERO_PILL_RADIUS',
        
        # Header
        'header_bg': 'THEME_HEADER_BG', 'header_text_color': 'THEME_HEADER_TEXT_COLOR',
        'header_link_active_color': 'THEME_HEADER_LINK_ACTIVE_COLOR',
        'header_link_hover_color': 'THEME_HEADER_LINK_HOVER_COLOR',
        'header_highlight_color': 'THEME_HEADER_HIGHLIGHT_COLOR',
        'header_border_bottom': 'THEME_HEADER_BORDER_BOTTOM',
        'logo_p1_color': 'THEME_LOGO_P1_COLOR', 'logo_p2_color': 'THEME_LOGO_P2_COLOR',
        'logo_image_size': 'THEME_LOGO_IMAGE_SIZE',
        
        # Hero
        'hero_h1_color': 'THEME_HERO_H1_COLOR', 'hero_intro_color': 'THEME_HERO_INTRO_COLOR',
        'hero_pill_bg': 'THEME_HERO_PILL_BG', 'hero_pill_text': 'THEME_HERO_PILL_TEXT',
        'hero_pill_hover_bg': 'THEME_HERO_PILL_HOVER_BG', 'hero_pill_hover_text': 'THEME_HERO_PILL_HOVER_TEXT',
        'text_sys_status': 'THEME_TEXT_SYS_STATUS',
        
        # Match Rows
        'match_row_bg': 'THEME_MATCH_ROW_BG', 'match_row_border': 'THEME_MATCH_ROW_BORDER',
        'match_row_live_border_left': 'THEME_MATCH_ROW_LIVE_BORDER_LEFT',
        'match_row_live_bg_start': 'THEME_MATCH_ROW_LIVE_BG_START',
        'match_row_live_bg_end': 'THEME_MATCH_ROW_LIVE_BG_END',
        'match_row_hover_bg': 'THEME_MATCH_ROW_HOVER_BG',
        'match_row_hover_border': 'THEME_MATCH_ROW_HOVER_BORDER',
        'match_row_time_main_color': 'THEME_MATCH_ROW_TIME_MAIN_COLOR',
        'match_row_time_sub_color': 'THEME_MATCH_ROW_TIME_SUB_COLOR',
        'match_row_live_text_color': 'THEME_MATCH_ROW_LIVE_TEXT_COLOR',
        'match_row_team_name_color': 'THEME_MATCH_ROW_TEAM_NAME_COLOR',
        
        'match_row_btn_watch_bg': 'THEME_MATCH_ROW_BTN_WATCH_BG',
        'match_row_btn_watch_text': 'THEME_MATCH_ROW_BTN_WATCH_TEXT',
        'match_row_hd_badge_bg': 'THEME_MATCH_ROW_HD_BADGE_BG',
        'match_row_hd_badge_text': 'THEME_MATCH_ROW_HD_BADGE_TEXT',
        'match_row_btn_notify_bg': 'THEME_MATCH_ROW_BTN_NOTIFY_BG',
        'match_row_btn_notify_border': 'THEME_MATCH_ROW_BTN_NOTIFY_BORDER',
        'match_row_btn_notify_text': 'THEME_MATCH_ROW_BTN_NOTIFY_TEXT',
        
        # Footer
        'footer_bg_start': 'THEME_FOOTER_BG_START', 'footer_bg_end': 'THEME_FOOTER_BG_END',
        'footer_border_top': 'THEME_FOOTER_BORDER_TOP', 'footer_link_color': 'THEME_FOOTER_LINK_COLOR',
        'footer_link_hover_color': 'THEME_FOOTER_LINK_HOVER_COLOR',
        'footer_copyright_color': 'THEME_FOOTER_COPYRIGHT_COLOR',
        'footer_desc_color': 'THEME_FOOTER_DESC_COLOR',
        
        # Article
        'article_bg': 'THEME_ARTICLE_BG', 'article_text': 'THEME_ARTICLE_TEXT',
        'article_line_height': 'THEME_ARTICLE_LINE_HEIGHT', 'article_bullet_color': 'THEME_ARTICLE_BULLET_COLOR',
        'article_link_color': 'THEME_ARTICLE_LINK_COLOR', 'article_h2_color': 'THEME_ARTICLE_H2_COLOR',
        'article_h2_border_color': 'THEME_ARTICLE_H2_BORDER',
        
        # Socials
        'social_sidebar_bg': 'THEME_SOCIAL_SIDEBAR_BG', 'social_sidebar_border': 'THEME_SOCIAL_SIDEBAR_BORDER',
        'social_btn_bg': 'THEME_SOCIAL_BTN_BG', 'social_btn_color': 'THEME_SOCIAL_BTN_COLOR',
        'mobile_footer_bg': 'THEME_MOBILE_FOOTER_BG', 'mobile_footer_border_top': 'THEME_MOBILE_FOOTER_BORDER_TOP',
        
        # Misc
        'back_to_top_bg': 'THEME_BACK_TO_TOP_BG', 'back_to_top_icon_color': 'THEME_BACK_TO_TOP_ICON_COLOR',
        'sys_status_bg_color': 'THEME_SYS_STATUS_BG_COLOR', 'sys_status_border_color': 'THEME_SYS_STATUS_BORDER',
        'sys_status_text_color': 'THEME_SYS_STATUS_TEXT_COLOR', 'sys_status_dot_color': 'THEME_SYS_STATUS_DOT_COLOR',
        'sys_status_radius': 'THEME_SYS_STATUS_RADIUS', 'section_logo_size': 'THEME_SECTION_LOGO_SIZE',
        
        # Watch specific (needed if passed)
        'chat_header_bg': 'THEME_CHAT_HEADER_BG', 'chat_header_text': 'THEME_CHAT_HEADER_TEXT',
        'chat_dot_color': 'THEME_CHAT_DOT_COLOR', 'chat_dot_size': 'THEME_CHAT_DOT_SIZE',
        'chat_input_bg': 'THEME_CHAT_INPUT_BG', 'chat_input_text': 'THEME_CHAT_INPUT_TEXT',
        'watch_table_head_bg': 'THEME_WATCH_TABLE_HEAD_BG', 'watch_table_body_bg': 'THEME_WATCH_TABLE_BODY_BG',
        'watch_table_border': 'THEME_WATCH_TABLE_BORDER', 'watch_table_radius': 'THEME_WATCH_TABLE_RADIUS',
        'watch_team_color': 'THEME_WATCH_TEAM_COLOR', 'watch_vs_color': 'THEME_WATCH_VS_COLOR',
        'watch_team_size': 'THEME_WATCH_TEAM_SIZE', 'watch_vs_size': 'THEME_WATCH_VS_SIZE',
        'watch_btn_bg': 'THEME_WATCH_BTN_BG', 'watch_btn_text': 'THEME_WATCH_BTN_TEXT',
        'watch_btn_disabled_bg': 'THEME_WATCH_BTN_DISABLED_BG', 'watch_btn_disabled_text': 'THEME_WATCH_BTN_DISABLED_TEXT',
        'watch_info_btn_bg': 'THEME_WATCH_INFO_BTN_BG', 'watch_info_btn_text': 'THEME_WATCH_INFO_BTN_TEXT',
        'watch_info_btn_hover': 'THEME_WATCH_INFO_BTN_HOVER', 'watch_server_active_bg': 'THEME_WATCH_SERVER_ACTIVE_BG',
        'watch_server_text': 'THEME_WATCH_SERVER_TEXT'
    }

    # Apply Theme Variables
    for json_key, tpl_key in mapping.items():
        val = THEME.get(json_key, '')
        if 'radius' in json_key or 'size' in json_key or 'width' in json_key: val = ensure_unit(val)
        if json_key == 'sys_status_bg_color':
            # Handle rgba logic for system status
            op = THEME.get('sys_status_bg_opacity', '0.1')
            if THEME.get('sys_status_bg_transparent'): val = 'transparent'
            else: val = hex_to_rgba(val, op)
        if json_key == 'chat_overlay_bg':
             # Handle rgba for chat
             val = hex_to_rgba(THEME.get('chat_overlay_bg', '#000000'), THEME.get('chat_overlay_opacity', '0.9'))
             html = html.replace('{{THEME_CHAT_OVERLAY_BG_FINAL}}', val)

        html = html.replace(f'{{{{{tpl_key}}}}}', str(val))

    # Apply Borders
    for sec in ['live', 'upcoming', 'wildcard', 'leagues', 'grouped', 'league_upcoming']:
        w = ensure_unit(THEME.get(f'sec_border_{sec}_width', '1'))
        c = THEME.get(f'sec_border_{sec}_color', '#334155')
        html = html.replace(f'{{{{THEME_SEC_BORDER_{sec.upper()}}}}}', f'{w} solid {c}')

    # Apply Texts & Logic
    html = html.replace('{{TEXT_LIVE_SECTION_TITLE}}', THEME.get('text_live_section_title', 'Trending Live'))
    html = html.replace('{{TEXT_UPCOMING_TITLE}}', THEME.get('text_top_upcoming_title', 'Upcoming Matches'))
    html = html.replace('{{HERO_MENU_DISPLAY}}', THEME.get('hero_menu_visible', 'flex'))
    
    # Hero Logic
    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    b_w = ensure_unit(THEME.get('hero_box_border_width', '1'))
    b_c = THEME.get('hero_box_border_color', '#333')
    
    outer_style = ""
    inner_style = f"max-width: {box_w if mode=='box' else 'var(--container-max-width)'}; margin: 0 auto;"
    
    bg_style = THEME.get('hero_bg_style', 'solid')
    if bg_style == 'solid': bg_css = f"background: {THEME.get('hero_bg_solid')};"
    elif bg_style == 'gradient': bg_css = f"background: radial-gradient(circle at top, {THEME.get('hero_gradient_start')} 0%, {THEME.get('hero_gradient_end')} 100%);"
    elif bg_style == 'image': bg_css = f"background: url('{THEME.get('hero_bg_image_url')}'); background-size: cover;"
    else: bg_css = "background: transparent;"

    if mode == 'box':
        outer_style = "padding: 40px 15px;"
        inner_style += f" {bg_css} padding: 30px; border-radius: var(--border-radius-base); border: {b_w} solid {b_c};"
    else:
        outer_style = f"{bg_css} padding: 40px 15px 15px 15px;"

    html = html.replace('{{HERO_OUTER_STYLE}}', outer_style)
    html = html.replace('{{HERO_INNER_STYLE}}', inner_style)
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', THEME.get('hero_content_align', 'center'))
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if THEME.get('hero_content_align')=='center' else 'flex-start')
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if THEME.get('hero_content_align')=='center' else 'flex-start')
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if THEME.get('hero_content_align')=='center' else '0')
    html = html.replace('{{DISPLAY_HERO}}', THEME.get('display_hero', 'block'))

    # Socials
    html = html.replace('{{THEME_SOCIAL_TELEGRAM_COLOR}}', THEME.get('social_telegram_color', '#0088cc'))
    html = html.replace('{{THEME_SOCIAL_WHATSAPP_COLOR}}', THEME.get('social_whatsapp_color', '#25D366'))
    html = html.replace('{{THEME_SOCIAL_REDDIT_COLOR}}', THEME.get('social_reddit_color', '#FF4500'))
    html = html.replace('{{THEME_SOCIAL_TWITTER_COLOR}}', THEME.get('social_twitter_color', '#1DA1F2'))
    html = html.replace('{{THEME_SOCIAL_DESKTOP_TOP}}', THEME.get('social_desktop_top', '50%'))
    html = html.replace('{{THEME_SOCIAL_DESKTOP_SCALE}}', THEME.get('social_desktop_scale', '1.0'))
    html = html.replace('{{THEME_MOBILE_FOOTER_HEIGHT}}', THEME.get('mobile_footer_height', '60px'))

    # Watch Configs
    html = html.replace('{{THEME_WATCH_SIDEBAR_SWAP}}', 'true' if THEME.get('watch_sidebar_swap') else 'false')
    html = html.replace('{{THEME_WATCH_SHOW_AD1}}', 'true' if THEME.get('watch_show_ad1') else 'false')
    html = html.replace('{{THEME_WATCH_SHOW_AD2}}', 'true' if THEME.get('watch_show_ad2') else 'false')
    html = html.replace('{{THEME_WATCH_SHOW_DISCORD}}', 'true' if THEME.get('watch_show_discord') else 'false')
    html = html.replace('{{THEME_WATCH_DISCORD_ORDER}}', THEME.get('watch_discord_order', 'middle'))
    html = html.replace('{{THEME_CHAT_JOIN_BTN_TEXT}}', THEME.get('chat_join_btn_text', 'Join Room'))
    html = html.replace('{{THEME_CHAT_HEADER_TITLE}}', THEME.get('chat_header_title', 'Live Chat'))
    html = html.replace('{{THEME_WATCH_DISCORD_TITLE}}', THEME.get('watch_discord_title', 'Join Discord'))
    html = html.replace('{{THEME_WATCH_DISCORD_BTN_TEXT}}', THEME.get('watch_discord_btn_text', 'Join'))
    html = html.replace('{{THEME_WATCH_BTN_LABEL}}', THEME.get('watch_btn_label', 'Watch Live Stream'))
    html = html.replace('{{THEME_WATCH_BTN_DISABLED_LABEL}}', THEME.get('watch_btn_disabled_label', 'Stream Starts Soon'))
    html = html.replace('{{THEME_WATCH_INFO_BTN_LABEL}}', THEME.get('watch_info_btn_label', 'View Match Info'))
    
    # Watch Ads & SEO (Config from config.json -> watch_settings)
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    html = html.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))

    # Site Identity & SEO
    p1 = SITE_SETTINGS.get('title_part_1', 'Stream')
    p2 = SITE_SETTINGS.get('title_part_2', 'East')
    site_name = f"{p1}{p2}"
    logo_html = f'<div class="logo-text">{p1}<span>{p2}</span></div>'
    if SITE_SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SITE_SETTINGS.get("logo_url")}" class="logo-img"> {logo_html}'
        html = html.replace('{{LOGO_PRELOAD}}', f'<link rel="preload" as="image" href="{SITE_SETTINGS.get("logo_url")}">')
    else:
        html = html.replace('{{LOGO_PRELOAD}}', '')

    html = html.replace('{{LOGO_HTML}}', logo_html)
    html = html.replace('{{SITE_NAME}}', site_name)
    html = html.replace('{{DOMAIN}}', DOMAIN)
    html = html.replace('{{CANONICAL_URL}}', page_data.get('canonical_url', f"https://{DOMAIN}/"))
    html = html.replace('{{FAVICON}}', SITE_SETTINGS.get('favicon_url', ''))
    html = html.replace('{{OG_IMAGE}}', SITE_SETTINGS.get('logo_url', ''))
    html = html.replace('{{OG_MIME}}', 'image/png')
    
    html = html.replace('{{META_TITLE}}', page_data.get('meta_title', site_name))
    html = html.replace('{{META_DESC}}', page_data.get('meta_desc', ''))
    html = html.replace('{{META_KEYWORDS}}', f'<meta name="keywords" content="{page_data.get("meta_keywords","")}">' if page_data.get("meta_keywords") else '')
    html = html.replace('{{THEME_META_COLOR}}', THEME.get('header_bg', '#000000'))
    html = html.replace('{{SCHEMA_BLOCK}}', '') # Or inject schema if needed

    # Content Replacements
    html = html.replace('{{H1_TITLE}}', page_data.get('h1_title', site_name))
    html = html.replace('{{HERO_TEXT}}', page_data.get('hero_text', ''))
    html = html.replace('{{ARTICLE_CONTENT}}', page_data.get('article', ''))
    
    # Menus
    html = html.replace('{{HEADER_MENU}}', build_menu_html(MENUS.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(MENUS.get('hero', []), 'hero'))
    
    # Footer Layout
    # Auto-generate footer leagues
    f_leagues = []
    for k, v in PRIORITY_SETTINGS.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{slugify(k)}-streams/"})
    
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config))
    html = html.replace('{{FOOTER_COPYRIGHT}}', SITE_SETTINGS.get('footer_copyright', ''))

    return html

# ==========================================
# 5. CORE LOGIC: MATCH ID & TIME
# ==========================================
def generate_match_id(sport, start_unix, home, away):
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
    if ts < 10000000000: return ts * 1000
    return ts

def getStatusText(ts, is_live):
    if is_live: return "LIVE"
    diff = (ts - time.time()*1000) / 60000
    if diff < 0: return "Started" # Just started
    if diff < 60: return f"In {int(diff)}m"
    hours = diff / 60
    if hours < 24: return f"In {int(hours)}h"
    days = hours / 24
    return f"In {int(days)}d"

def format_display_time(unix_ms):
    # Timezone: Python in Actions is UTC.
    # To roughly match JS user expectation without external pytz lib:
    # US (UTC-5), UK (UTC+0/1). 
    # For now, we display UTC time. Client browser not involved in SSG text.
    # TODO: Add offset logic if strict timezone required.
    dt = datetime.fromtimestamp(unix_ms / 1000)
    time_str = dt.strftime('%I:%M %p') # 02:30 PM
    date_str = dt.strftime('%b %d')    # Jan 01
    return { "time": time_str, "date": date_str, "iso": dt.isoformat() }

# ==========================================
# 6. RESOLUTION LOGIC
# ==========================================
def smart_resolve(raw_match):
    raw_home = raw_match.get('home_team') or 'TBA'
    raw_away = raw_match.get('away_team') or 'TBA'
    raw_league = raw_match.get('league') or raw_match.get('category') or "General"
    
    h_slug = slugify(raw_home)
    a_slug = slugify(raw_away)
    
    final_league = "General"
    final_home = raw_home
    final_away = raw_away
    source_method = "API"

    # LEVEL 1: Map
    if h_slug in REVERSE_LEAGUE_MAP and a_slug in REVERSE_LEAGUE_MAP:
        if REVERSE_LEAGUE_MAP[h_slug] == REVERSE_LEAGUE_MAP[a_slug]:
            final_league = REVERSE_LEAGUE_MAP[h_slug]
            source_method = "MapStrict"
    
    # LEVEL 2: Colon
    if source_method == "API" and ':' in raw_home:
        parts = raw_home.split(':')
        if len(parts) > 1:
            l_cand = parts[0].strip()
            if 1 < len(l_cand) < 25:
                final_league = l_cand
                final_home = parts[1].strip()
                source_method = "ColonSplit"

    # LEVEL 3: API
    if source_method == "API":
        l_key = raw_league.lower().replace(' ', '')
        final_league = NAME_FIXES.get(l_key, raw_league.strip())

    # Clean Names
    def clean_name(name, league):
        if not name or name == 'TBA': return 'TBA'
        if league:
            pattern = re.compile(re.escape(league) + r'[:\s-]*', re.IGNORECASE)
            name = pattern.sub('', name)
        name = re.sub(r'^(NBA|NFL|NHL|MLB|UFC|AFL)[:\s-]*', '', name, flags=re.IGNORECASE)
        return name.strip()

    final_home = clean_name(final_home, final_league)
    final_away = clean_name(final_away, final_league)
    
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
    
    boost_txt = str(PRIORITY_SETTINGS.get('_BOOST', '')).lower()
    boost_list = [x.strip() for x in boost_txt.split(',') if x.strip()]
    
    if any(b in league.lower() or b in sport.lower() for b in boost_list): score += 2000
    if league in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[league].get('score', 0) * 10)
    elif sport in PRIORITY_SETTINGS: score += (PRIORITY_SETTINGS[sport].get('score', 0))
        
    if match_data['is_live']:
        score += 5000
        score += (match_data.get('live_viewers', 0) / 10)
    else:
        diff = (match_data['timestamp'] - time.time()*1000) / 3600000 
        if diff < 24: score += (24 - diff) 
            
    return score

# ==========================================
# 7. ASSETS
# ==========================================
def resolve_and_fetch_logo(team_name, image_payload=None):
    if not team_name or team_name == 'TBA': return None
    if team_name in image_map['teams']: return image_map['teams'][team_name]
    
    if image_payload:
        slug = slugify(team_name)
        filename = f"{slug}.webp"
        save_path = os.path.join(ASSETS_DIR, 'streamed', filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
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
                    rel_path = f"/assets/logos/streamed/{filename}"
                    image_map['teams'][team_name] = rel_path
                    return rel_path
            except: continue
    return None

# ==========================================
# 8. HTML ROW GENERATOR
# ==========================================
def render_match_row(m):
    is_live = m['is_live']
    if is_live:
        status = m.get('status_text', 'Now')
        time_html = f'<span class="live-txt">LIVE</span><span class="time-sub">{status}</span>'
        row_class = "match-row live"
    else:
        ft = format_display_time(m['timestamp'])
        time_html = f'<span class="time-main">{ft["time"]}</span><span class="time-sub">{ft["date"]}</span>'
        row_class = "match-row"

    def get_logo_html(name):
        url = image_map['teams'].get(name)
        if url:
            if not url.startswith('http'): url = f"https://{DOMAIN}{url}" if url.startswith('/') else f"https://{DOMAIN}/{url}"
            return f'<div class="logo-box"><img src="{url}" class="t-img" alt="{name}" loading="lazy" width="20" height="20"></div>'
        else:
            return f'<div class="logo-box"><span class="t-logo" style="background:#334155">{name[0] if name else "?"}</span></div>'

    if m['is_single_event']:
        teams_html = f'<div class="team-name">{get_logo_html(m["home"])} {m["home"]}</div>'
    else:
        teams_html = f'<div class="team-name">{get_logo_html(m["home"])} {m["home"]}</div>' \
                     f'<div class="team-name">{get_logo_html(m["away"])} {m["away"]}</div>'

    if is_live:
        v = m.get('live_viewers', 0)
        v_txt = f"👀 {(v/1000):.1f}k 🔥" if v > 1000 else "⚡ Stable"
        meta_html = f'<div class="meta-top">{v_txt}</div>'
    else:
        meta_html = f'<div style="display:flex; flex-direction:column; align-items:flex-end;">' \
                    f'<span style="font-size:0.55rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; margin-bottom:2px;">Starts in</span>' \
                    f'<span class="meta-top" style="color:var(--accent-gold); font-size:0.75rem;">{m["status_text"]}</span></div>'

    p_live = SITE_SETTINGS.get('param_live', 'stream')
    p_info = SITE_SETTINGS.get('param_info', 'info')
    
    if is_live:
        btn_action = f"window.location.href='/watch/?{p_live}={m['id']}'"
        btn_cls = "btn-watch"
        btn_txt = "WATCH"
        btn_icon = '<span class="hd-badge">HD</span>'
    else:
        diff_mins = (m['timestamp'] - time.time()*1000) / 60000
        if diff_mins <= 30:
            btn_action = f"window.location.href='/watch/?{p_info}={m['id']}'"
            btn_cls = "btn-watch"
            btn_txt = "WATCH"
            btn_icon = '<span class="hd-badge">HD</span>'
        else:
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
    tag = m['league'].upper()
    return f"""<div class="{row_class}"><div class="col-time">{time_html}</div><div class="teams-wrapper"><div class="league-tag">{tag}</div>{teams_html}</div><div class="col-meta">{meta_html}</div><div class="col-action">{action_html}</div></div>"""

def render_section(title, matches, is_league=False):
    if not matches: return ""
    rows = "".join([render_match_row(m) for m in matches])
    icon = "🏆"
    if title in image_map.get('leagues', {}):
        url = image_map['leagues'][title]
        if not url.startswith('http'): url = f"https://{DOMAIN}{url}"
        icon_html = f'<img src="{url}" class="sec-logo" alt="{title}" loading="lazy" width="24" height="24">'
    else:
        icon_html = f'<span style="font-size:1.2rem; margin-right:8px;">{icon}</span>'
    link_html = ""
    if is_league:
        slug = slugify(title) + "-streams"
        link_html = f'<a href="/{slug}/" class="sec-right-link">View All ></a>'
    return f"""<div class="section-box" style="margin-bottom:30px;"><div class="sec-head"><h2 class="sec-title">{icon_html} Upcoming {title}</h2>{link_html}</div><div>{rows}</div></div>"""

# ==========================================
# 9. MAIN EXECUTION
# ==========================================
def main():
    print("--- 🚀 Starting Master Engine ---")
    start_time = time.time()

    # 1. Fetch
    try:
        res_a = requests.get(f"{NODE_A_ENDPOINT}/matches/all", headers=HEADERS, timeout=10).json()
        res_live = requests.get(f"{NODE_A_ENDPOINT}/matches/live", headers=HEADERS, timeout=10).json()
        res_b = requests.get(ADSTRIM_ENDPOINT, headers=HEADERS, timeout=10).json()
    except Exception as e:
        print(f"❌ API Error: {e}")
        return

    active_live_ids = set([m['id'] for m in res_live] if isinstance(res_live, list) else [])
    raw_matches = []
    
    # 2. Normalize Streamed
    for item in res_a:
        resolved = smart_resolve({
            'home_team': item.get('title', '').split(' vs ')[0] if 'title' in item else item.get('home', 'TBA'),
            'away_team': item.get('title', '').split(' vs ')[1] if 'title' in item and ' vs ' in item['title'] else item.get('away', 'TBA'),
            'league': item.get('league') or item.get('category'),
            'sport': item.get('category')
        })
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
            'viewers': 0
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
                'imgs': {'home': None, 'away': None},
                'is_live': False,
                'viewers': 0
            })

    # 4. Finalize
    final_matches = []
    seen_ids = set()
    print(f" > Processing {len(raw_matches)} raw items...")
    
    for m in raw_matches:
        uid = generate_match_id(m['resolved']['sport'], m['timestamp'], m['resolved']['home'], m['resolved']['away'])
        if uid in seen_ids:
            # Merge
            existing = next((x for x in final_matches if x['id'] == uid), None)
            if existing:
                existing_urls = set(c.get('url') or c.get('id') for c in existing['stream_channels'])
                for c in m['channels']:
                    c_url = c.get('url') or c.get('id')
                    if c_url not in existing_urls:
                        existing['stream_channels'].append({
                            'name': f"Server {len(existing['stream_channels'])+1}",
                            'url': c.get('url') if c.get('url') else f"https://streamed.pk/player?id={c['id']}"
                        })
            continue
            
        seen_ids.add(uid)
        if m['imgs']['home']: resolve_and_fetch_logo(m['resolved']['home'], m['imgs']['home'])
        if m['imgs']['away']: resolve_and_fetch_logo(m['resolved']['away'], m['imgs']['away'])
        
        is_single = m['resolved']['away'] == 'TBA' or not m['resolved']['away']
        match_obj = {
            'id': uid,
            'originalId': m['orig_id'],
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
        match_obj['priority_score'] = calculate_score(match_obj)
        final_matches.append(match_obj)

    save_json(IMAGE_MAP_PATH, image_map)
    final_matches.sort(key=lambda x: x['priority_score'], reverse=True)
    
    # ==========================================
    # 5. GENERATE & INJECT
    # ==========================================
    
    # Lists
    live_matches = [m for m in final_matches if m['is_live']]
    upcoming_matches = [m for m in final_matches if not m['is_live']]
    
    # 1. Live
    live_html = ""
    if live_matches:
        rows = "".join([render_match_row(m) for m in live_matches])
        title = THEME.get('text_live_section_title', 'Trending Live')
        live_html = f"""<div id="live-section"><div class="sec-head"><h2 class="sec-title"><div class="live-dot"></div> {title}</h2></div><div id="trending-list" class="match-list">{rows}</div></div>"""
    
    # 2. Upcoming / Wildcard
    wildcard = THEME.get('wildcard_category', '')
    wc_html = ""
    top_html = ""
    
    if wildcard:
        wc_matches = [m for m in upcoming_matches if wildcard.lower() in m['league'].lower()]
        if wc_matches:
            wc_rows = "".join([render_match_row(m) for m in wc_matches])
            wc_html = f"""<div id="wildcard-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">🔥 {wildcard}</h2></div>{wc_rows}</div></div>"""
    
    top5 = upcoming_matches[:5]
    if top5:
        top_rows = "".join([render_match_row(m) for m in top5])
        title = THEME.get('text_top_upcoming_title', 'Top Upcoming')
        top_html = f"""<div id="top-upcoming-container"><div class="section-box"><div class="sec-head"><h2 class="sec-title">📅 {title}</h2></div>{top_rows}</div></div>"""

    # 3. Grouped
    grouped_html = ""
    used_ids = set([m['id'] for m in live_matches] + [m['id'] for m in top5])
    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or settings.get('isHidden'): continue
        group_matches = []
        for m in upcoming_matches:
            if m['id'] in used_ids: continue
            if key.lower() in m['league'].lower() or key.lower() in m['sport'].lower():
                group_matches.append(m)
                used_ids.add(m['id'])
        if group_matches:
            grouped_html += render_section(key, group_matches, settings.get('isLeague', False))

    # ==========================================
    # 6. FILE WRITING
    # ==========================================
    print(" > Writing Files...")
    
    # A. MASTER HOME
    with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: html = f.read()
    
    # NEW: Apply Theme Replacements FIRST
    p_home = next((p for p in config.get('pages',[]) if p.get('slug')=='home'), {})
    html = apply_theme_and_content(html, p_home)
    
    # Inject Matches
    if live_html: html = re.sub(r'<div id="live-section">.*?<!-- 3. TOP 5 UPCOMING -->', f'{live_html}\n<!-- 3. TOP 5 UPCOMING -->', html, flags=re.DOTALL)
    else: html = html.replace('<div id="live-section">', '<div id="live-section" style="display:none;">')
    
    if wildcard: html = re.sub(r'<div id="wildcard-container">.*?</div>', wc_html, html, flags=re.DOTALL)
    else: html = re.sub(r'<div id="top-upcoming-container">.*?</div>', top_html, html, flags=re.DOTALL)
    html = re.sub(r'<div id="grouped-container">.*?</div>', grouped_html, html, flags=re.DOTALL)
    
    with open('index.html', 'w', encoding='utf-8') as f: f.write(html)

    # B. WATCH PAGE
    with open(TEMPLATE_WATCH, 'r', encoding='utf-8') as f: w_html = f.read()
    
    # Apply Theme to Watch
    w_html = apply_theme_and_content(w_html, {}) # No specific page data
    
    min_matches = []
    for m in final_matches:
        min_matches.append({
            'id': m['id'], 'home': m['home'], 'away': m['away'], 'league': m['league'],
            'sport': m['sport'], 'startTimeUnix': m['timestamp'], 'is_live': m['is_live'],
            'status_text': m['status_text'], 'stream_channels': m['stream_channels'],
            'live_viewers': m['live_viewers'], 'isSingleEvent': m['is_single_event'], 'originalId': m['originalId']
        })
    w_html = w_html.replace('<script>', f'<script>\nwindow.MATCH_DATA = {json.dumps(min_matches)};\n')
    os.makedirs('watch', exist_ok=True)
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(w_html)

    # C. LEAGUE PAGES
    print(" > Building League Pages...")
    with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f: l_tpl_base = f.read()
    
    articles = config.get('articles', {})
    
    for key, settings in PRIORITY_SETTINGS.items():
        if key.startswith('_') or not settings.get('hasLink'): continue
        l_matches = [m for m in final_matches if key.lower() in m['league'].lower()]
        if not l_matches: continue
        
        slug = slugify(key) + "-streams"
        l_live = [m for m in l_matches if m['is_live']]
        l_upc = [m for m in l_matches if not m['is_live']]
        l_live_html = "".join([render_match_row(m) for m in l_live])
        l_upc_html = "".join([render_match_row(m) for m in l_upc])
        
        # Prepare Page Data
        is_league = settings.get('isLeague', False)
        tpl_article = articles.get('league') if is_league else articles.get('sport')
        
        # Simple var replacement for metadata
        def repl_vars(txt):
            if not txt: return ""
            return txt.replace('{{NAME}}', key).replace('{{YEAR}}', '2025').replace('{{DOMAIN}}', DOMAIN)

        p_data = {
            'meta_title': repl_vars(articles.get('league_h1', f"Watch {key} Live")),
            'h1_title': repl_vars(articles.get('league_h1', f"Watch {key} Live")),
            'hero_text': repl_vars(articles.get('league_intro', '')),
            'article': repl_vars(tpl_article),
            'canonical_url': f"https://{DOMAIN}/{slug}/"
        }
        
        # Apply Theme First
        pg = apply_theme_and_content(l_tpl_base, p_data)
        
        # Specific League Replacements
        pg = pg.replace('{{PAGE_FILTER}}', key)
        pg = pg.replace('{{TEXT_LIVE_SECTION_TITLE}}', repl_vars(articles.get('league_live_title', f"Live {key}")))
        pg = pg.replace('{{TEXT_UPCOMING_TITLE}}', repl_vars(articles.get('league_upcoming_title', f"Upcoming {key}")))
        pg = pg.replace('{{LEAGUE_ARTICLE}}', p_data['article'])
        
        pg = re.sub(r'<div id="live-list".*?>.*?</div>', f'<div id="live-list">{l_live_html}</div>', pg, flags=re.DOTALL)
        if l_live_html: pg = pg.replace('style="display:none;"', '') 
        pg = re.sub(r'<div id="schedule-list".*?>.*?</div>', f'<div id="schedule-list">{l_upc_html}</div>', pg, flags=re.DOTALL)
        
        l_dir = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(l_dir, exist_ok=True)
        with open(os.path.join(l_dir, 'index.html'), 'w', encoding='utf-8') as f: f.write(pg)

    print(f"--- ✅ Build Complete in {time.time() - start_time:.2f}s ---")

if __name__ == "__main__":
    main()
