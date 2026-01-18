import json
import os
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
# Renamed to match the calls in main()
TEMPLATE_MASTER = 'assets/master_template.html' # Fixed variable name
WATCH_TEMPLATE_PATH = 'assets/watch_template.html'
TEMPLATE_LEAGUE = 'assets/league_template.html' # Fixed variable name
TEMPLATE_PAGE = 'assets/page_template.html'     # Fixed variable name
OUTPUT_DIR = '.'
# ==========================================
# SMART ENTITY MAPPING (LEAGUE -> SPORT)
# ==========================================
LEAGUE_PARENT_MAP = {
    # SOCCER
    "Premier League": "Soccer", "La Liga": "Soccer", "Bundesliga": "Soccer", 
    "Serie A": "Soccer", "Ligue 1": "Soccer", "Champions League": "Soccer", 
    "Europa League": "Soccer", "MLS": "Soccer", "Eredivisie": "Soccer",
    "FA Cup": "Soccer", "Carabao Cup": "Soccer", "Copa America": "Soccer",
    "Euro 2024": "Soccer", "World Cup": "Soccer", "Liga MX": "Soccer",
    
    # BASKETBALL
    "NBA": "Basketball", "NCAA": "Basketball", "EuroLeague": "Basketball", 
    "WNBA": "Basketball", "College Basketball": "Basketball",
    
    # AMERICAN FOOTBALL
    "NFL": "American Football", "NCAA Football": "American Football", 
    "College Football": "American Football", "Super Bowl": "American Football",
    "XFL": "American Football", "CFL": "American Football",
    
    # FIGHTING
    "UFC": "MMA", "Bellator": "MMA", "PFL": "MMA", "Boxing": "Boxing",
    "WWE": "Pro Wrestling", "AEW": "Pro Wrestling",
    
    # MOTORSPORTS
    "F1": "Formula 1", "Formula 1": "Motorsport", "NASCAR": "Motorsport", 
    "MotoGP": "Motorsport", "IndyCar": "Motorsport",
    
    # OTHERS
    "MLB": "Baseball", "NHL": "Ice Hockey", "AFL": "Australian Rules Football",
    "NRL": "Rugby", "Rugby Union": "Rugby", "Six Nations": "Rugby",
    "Cricket": "Cricket", "IPL": "Cricket", "Big Bash": "Cricket",
    "Tennis": "Tennis", "Wimbledon": "Tennis", "US Open": "Tennis",
    "Golf": "Golf", "PGA Tour": "Golf", "LIV Golf": "Golf",
    "Darts": "Darts", "Snooker": "Snooker"
}

# ==========================================
# 2. UTILS
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
            # Restore Emoji Logic
            icon = "🏆"
            t_low = title.lower()
            if "soccer" in t_low or "premier" in t_low or "liga" in t_low: icon = "⚽"
            elif "nba" in t_low or "basket" in t_low: icon = "🏀"
            elif "nfl" in t_low or "football" in t_low: icon = "🏈"
            elif "mlb" in t_low or "baseball" in t_low: icon = "⚾"
            elif "ufc" in t_low or "boxing" in t_low: icon = "🥊"
            elif "f1" in t_low or "motor" in t_low: icon = "🏎️"
            elif "cricket" in t_low: icon = "🏏"
            elif "rugby" in t_low: icon = "🏉"
            elif "tennis" in t_low: icon = "🎾"
            elif "golf" in t_low: icon = "⛳"
            elif "hockey" in t_low or "nhl" in t_low: icon = "🏒"
            
            # Use specific CSS class for styling
            html += f'<a href="{url}" class="league-card"><span class="l-icon">{icon}</span><span>{title}</span></a>'
        elif section == 'footer_static':
             html += f'<a href="{url}" class="f-link">{title}</a>'
    return html

def build_footer_grid(config, logo_html):
    t = config.get('theme', {})
    s = config.get('site_settings', {})
    m = config.get('menus', {})
    
    cols = str(t.get('footer_columns', '2'))
    show_disclaimer = t.get('footer_show_disclaimer', True)
    
    # 1. Define Content Blocks
    # Block: Brand (Uses the passed logo_html directly)
    brand_html = f"""
    <div class="f-brand">
        {logo_html} 
    </div>
    """
    
    # Block: Disclaimer
    disc_text = s.get('footer_disclaimer', '')
    disc_html = f'<div class="f-desc">{disc_text}</div>' if show_disclaimer else ''
    
    # Block: Brand + Disclaimer (Combined)
    brand_disc_html = f"""
    <div class="f-brand">
        {logo_html}
        {disc_html}
    </div>
    """
    
    # Block: Menu
    links_html = f"""
    <div>
        <div class="f-head">Quick Links</div>
        <div class="f-links">{build_menu_html(m.get('footer_static', []), 'footer_static')}</div>
    </div>
    """
    
    # 2. Get Slot Selections
    slot1_type = t.get('footer_slot_1', 'brand_disclaimer')
    slot2_type = t.get('footer_slot_2', 'menu')
    slot3_type = t.get('footer_slot_3', 'empty')
    
    # 3. Helper to pick content
    def get_content(type_key):
        if type_key == 'brand': return brand_html
        if type_key == 'disclaimer': return disc_html
        if type_key == 'brand_disclaimer': return brand_disc_html
        if type_key == 'menu': return links_html
        return '<div></div>'

    # 4. Construct Grid HTML
    html = f'<div class="footer-grid cols-{cols}">'
    html += get_content(slot1_type)
    html += get_content(slot2_type)
    if cols == '3':
        html += get_content(slot3_type)
    html += '</div>'
    
    return html

# ==========================================
# 3. THEME ENGINE
# ==========================================
def render_page(template, config, page_data, theme_override=None):
    s = config.get('site_settings', {})
    base_theme = config.get('theme', {}).copy()
    
    # Merge Theme Override (League/Page specific)
    if theme_override:
        base_theme.update(theme_override)
    t = base_theme
    
    m = config.get('menus', {})
    html = template
    # FIX: Remap Admin keys (desktop) to Template keys (desk) if they exist
    if 'social_desktop_top' in t: t['social_desk_top'] = t.pop('social_desktop_top')
    if 'social_desktop_left' in t: t['social_desk_left'] = t.pop('social_desktop_left')
    if 'social_desktop_scale' in t: t['social_desk_scale'] = t.pop('social_desktop_scale')
    
    # --- COMPREHENSIVE THEME DEFAULTS (Restoring Lost Features) ---
    defaults = {
        # 1. Colors & Base
        'brand_primary': '#D00000', 'brand_dark': '#8a0000', 'accent_gold': '#FFD700', 'status_green': '#22c55e',
        'bg_body': '#050505', 'bg_panel': '#1e293b', 'bg_glass': 'rgba(30, 41, 59, 0.7)',
        'text_main': '#f1f5f9', 'text_muted': '#94a3b8', 'border_color': '#334155', 'scrollbar_thumb_color': '#475569',
        
        # 2. Typography & Layout
        'font_family_base': 'system-ui, -apple-system, sans-serif', 'font_family_headings': 'inherit',
        'base_font_size': '14px', 'base_line_height': '1.5',
        'container_max_width': '1100px', 'header_max_width': '1100px',
        'border_radius_base': '6px', 'button_border_radius': '4px', 'hero_pill_radius': '50px',
        
        # 3. Header & Logo
        'header_bg': 'rgba(5, 5, 5, 0.8)', 'header_text_color': '#f1f5f9', 
        'header_link_active_color': '#D00000', 'header_link_hover_color': '#ffffff',
        'header_highlight_color': '#FFD700', 'header_highlight_hover': '#ffea70',
        'header_border_bottom': '1px solid #334155', 'header_layout': 'standard', 'header_icon_pos': 'left',
        'logo_p1_color': '#f1f5f9', 'logo_p2_color': '#D00000', 'logo_image_size': '40px',
        'logo_image_shadow_color': 'rgba(208, 0, 0, 0.3)', # RESTORED

        # 4. Hero Section
        'hero_bg_style': 'solid', 'hero_bg_solid': '#1a0505', 
        'hero_gradient_start': '#1a0505', 'hero_gradient_end': '#000000',
        'hero_bg_image_url': '', 'hero_bg_image_overlay_opacity': '0.7',
        'hero_h1_color': '#ffffff', 'hero_intro_color': '#94a3b8',
        'hero_pill_bg': 'rgba(255,255,255,0.05)', 'hero_pill_text': '#f1f5f9', 'hero_pill_border': 'rgba(255,255,255,0.1)',
        'hero_pill_hover_bg': '#D00000', 'hero_pill_hover_text': '#ffffff', 'hero_pill_hover_border': '#D00000',
        'hero_layout_mode': 'full', 'hero_content_align': 'center', 'hero_menu_visible': 'flex',
        'hero_box_width': '1000px', 'hero_box_border_width': '1', 'hero_box_border_color': '#334155',
        'hero_border_top': False, 'hero_border_left': False, 'hero_border_right': False, 'hero_border_bottom_box': False,
        'hero_main_border_pos': 'full', 'hero_main_border_width': '1', 'hero_main_border_color': '#334155',
        'display_hero': 'block',
        
        # 5. Footer
        'footer_columns': '2', 'footer_bg_start': '#0f172a', 'footer_bg_end': '#020617', 
        'footer_border_top': '1px solid #334155', 'footer_heading_color': '#94a3b8', 
        'footer_link_color': '#64748b', 'footer_link_hover_color': '#f1f5f9',
        'footer_link_hover_transform': 'translateX(5px)',
        'footer_copyright_color': '#475569', 'footer_desc_color': '#64748b', 'footer_brand_color': '#ffffff', # RESTORED
        'footer_text_align_desktop': 'left', # RESTORED
        
        # 6. League Cards (Footer & Page)
        'league_card_bg': 'rgba(30, 41, 59, 0.5)', 'league_card_text': '#f1f5f9',
        'league_card_border_width': '1', 'league_card_border_color': '#334155', 'league_card_radius': '6',
        'league_card_hover_bg': '#1e293b', 'league_card_hover_text': '#ffffff', 'league_card_hover_border_color': '#D00000',

        # 7. Static Page Elements
        'static_h1_color': '#f1f5f9', 'static_h1_align': 'left',
        'static_h1_border_width': '1', 'static_h1_border_color': '#334155',
        
        # 8. System Status Pill
        'sys_status_visible': True, 'text_sys_status': 'System Status: Online',
        'sys_status_text_color': '#22c55e', 'sys_status_dot_color': '#22c55e', 
        'sys_status_bg_color': 'rgba(34, 197, 94, 0.1)', 'sys_status_border_color': 'rgba(34, 197, 94, 0.2)',
        'sys_status_border_width': '1', 'sys_status_radius': '20', 'sys_status_dot_size': '8',

        # 9. Watch Page & Chat
        'watch_sidebar_swap': False, 'watch_show_ad1': True, 'watch_show_discord': True, 'watch_show_ad2': True,
        'watch_discord_order': 'middle', 'watch_discord_title': 'Join Discord', 'watch_discord_btn_text': 'Join',
        'chat_header_bg': 'rgba(0,0,0,0.4)', 'chat_header_text': '#ffffff', 'chat_header_title': 'Live Chat',
        'chat_dot_color': '#22c55e', 'chat_dot_size': '6px', 'chat_join_btn_text': 'Join Room',
        'chat_overlay_bg': 'rgba(15, 23, 42, 0.6)', 'chat_input_bg': '#000000', 'chat_input_text': '#ffffff',
        
        'watch_table_head_bg': 'rgba(255,255,255,0.03)', 'watch_table_body_bg': '#1e293b',
        'watch_table_border': '#334155', 'watch_table_radius': '6',
        'watch_team_color': '#ffffff', 'watch_vs_color': 'rgba(255,255,255,0.1)',
        'watch_team_size': '1.4rem', 'watch_vs_size': '2rem',
        
        'watch_btn_bg': '#D00000', 'watch_btn_text': '#ffffff', 'watch_btn_label': 'Watch Live Stream',
        'watch_btn_disabled_bg': '#1e293b', 'watch_btn_disabled_text': '#94a3b8', 'watch_btn_disabled_label': 'Stream Starts Soon',
        'watch_info_btn_bg': '#1e293b', 'watch_info_btn_text': '#ffffff', 'watch_info_btn_hover': '#334155', 'watch_info_btn_label': 'View Match Info',
        'watch_server_active_bg': '#D00000', 'watch_server_text': '#94a3b8',

        # 10. Socials & Floating
        'social_sidebar_bg': 'rgba(15, 23, 42, 0.8)', 'social_sidebar_border': '#334155', 'social_sidebar_shadow': '0 4px 10px rgba(0,0,0,0.3)',
        'social_btn_bg': 'rgba(30, 41, 59, 0.8)', 'social_btn_border': '#334155', 'social_btn_color': '#94a3b8',
        'social_btn_hover_bg': '#1e293b', 'social_btn_hover_border': '#D00000', 
        'social_btn_hover_transform': 'translateX(5px)', 'social_btn_hover_shadow_color': 'rgba(0,0,0,0.3)', # RESTORED
        'social_count_color': '#64748b', 
        # FIX: Renamed keys to match CSS template placeholders (desk vs desktop)
        'social_desk_top': '50%', 'social_desk_left': '0', 'social_desk_scale': '1.0',
        'social_telegram_color': '#0088cc', 'social_whatsapp_color': '#25D366', 
        'social_reddit_color': '#FF4500', 'social_twitter_color': '#1DA1F2',
        
        'mobile_footer_bg': 'rgba(5, 5, 5, 0.9)', 'mobile_footer_border_top': '1px solid #334155',
        'mobile_footer_shadow': '0 -4px 10px rgba(0,0,0,0.5)', 'mobile_footer_height': '60px',
        'mobile_footer_btn_active_bg': 'rgba(255,255,255,0.1)', # RESTORED
        
        'copy_toast_bg': '#22c55e', 'copy_toast_text': '#ffffff', 'copy_toast_border': '#16a34a',
        'back_to_top_bg': '#D00000', 'back_to_top_icon_color': '#ffffff', 'back_to_top_shadow': '0 4px 10px rgba(0,0,0,0.3)',
        'back_to_top_radius': '50%', 'back_to_top_size': '40px',

        # 11. Borders & Skeletons
        'sec_border_live_width': '1', 'sec_border_live_color': '#334155',
        'sec_border_upcoming_width': '1', 'sec_border_upcoming_color': '#334155',
        'sec_border_wildcard_width': '1', 'sec_border_wildcard_color': '#334155',
        'sec_border_leagues_width': '1', 'sec_border_leagues_color': '#334155',
        'sec_border_grouped_width': '1', 'sec_border_grouped_color': '#334155',
        'sec_border_league_upcoming_width': '1', 'sec_border_league_upcoming_color': '#334155',
        
        'skeleton_gradient_start': '#1e293b', 'skeleton_gradient_mid': '#334155', 'skeleton_gradient_end': '#1e293b', # RESTORED
        'skeleton_border_color': '#334155',
        'social_sidebar_bg': 'rgba(15, 23, 42, 0.8)',
        'social_sidebar_border': '#334155',
        'social_sidebar_shadow': '0 4px 10px rgba(0,0,0,0.3)',
        'social_btn_bg': 'rgba(30, 41, 59, 0.8)',
        'social_btn_border': '#334155',
        'social_btn_color': '#94a3b8',
        'social_btn_hover_bg': '#1e293b',
        'social_btn_hover_border': '#D00000',
        'social_btn_hover_transform': 'translateX(5px)',
        'social_count_color': '#64748b',
        'mobile_footer_bg': 'rgba(5, 5, 5, 0.9)',
        'mobile_footer_border_top': '1px solid #334155',
        'mobile_footer_shadow': '0 -4px 10px rgba(0,0,0,0.5)',
        'mobile_footer_height': '60px',
        
        # League Cards
        'league_card_bg': 'rgba(30, 41, 59, 0.5)',
        'league_card_text': '#f1f5f9',
        'league_card_border_width': '1',
        'league_card_border_color': '#334155',
        'league_card_radius': '6',
        'league_card_hover_bg': '#1e293b',
        'league_card_hover_text': '#ffffff',
        'league_card_hover_border_color': '#D00000',

        # 12. Match Row (Static Styling)
        'match_row_bg': '#1e293b', 'match_row_border': '#334155', 
        'match_row_live_border_left': '4px solid #22c55e', 'match_row_live_bg_start': 'rgba(34, 197, 94, 0.1)',
        'match_row_live_bg_end': 'transparent', 'match_row_hover_border': '#D00000', 
        'match_row_hover_bg': '#1e293b', 'match_row_hover_transform': 'translateY(-2px)',
        'match_row_time_main_color': '#f1f5f9', 'match_row_time_sub_color': '#94a3b8',
        'match_row_live_text_color': '#22c55e', 'match_row_league_tag_color': '#94a3b8', 'match_row_team_name_color': '#f1f5f9',
        
        'match_row_btn_watch_bg': '#D00000', 'match_row_btn_watch_text': '#ffffff', 
        'match_row_btn_watch_hover_bg': '#b91c1c', 'match_row_btn_watch_hover_transform': 'scale(1.05)',
        'match_row_hd_badge_bg': 'rgba(0,0,0,0.3)', 'match_row_hd_badge_border': 'rgba(255,255,255,0.2)', 'match_row_hd_badge_text': '#facc15',
        'match_row_btn_notify_bg': 'transparent', 'match_row_btn_notify_border': '#334155', 'match_row_btn_notify_text': '#94a3b8',
        'match_row_btn_notify_active_bg': '#22c55e', 'match_row_btn_notify_active_border': '#22c55e', 'match_row_btn_notify_active_text': '#ffffff',
        'match_row_btn_copy_link_color': '#64748b', 'match_row_btn_copy_link_hover_color': '#D00000',
        
        'show_more_btn_bg': '#1e293b', 'show_more_btn_border': '#334155', 'show_more_btn_text': '#94a3b8',
        'show_more_btn_radius': '30px', 
        'show_more_btn_hover_bg': '#D00000', 'show_more_btn_hover_border': '#D00000', 'show_more_btn_hover_text': '#ffffff',
        
        'button_shadow_color': 'rgba(0,0,0,0.2)', 'card_shadow': '0 4px 6px -1px rgba(0,0,0,0.1)', # RESTORED
        'section_logo_size': '24px',

        # 13. Article Styling
        'article_bg': 'transparent', 'article_text': '#94a3b8', 'article_line_height': '1.6',
        'article_bullet_color': '#D00000', 'article_link_color': '#D00000',
        'article_h2_color': '#f1f5f9', 'article_h2_border_width': '0', 'article_h2_border_color': '#334155',
        'article_h3_color': '#f1f5f9', 'article_h4_color': '#cbd5e1'
    }

    # Populate theme dictionary from defaults + config override
    theme = {}
    for k, v in defaults.items():
        val = t.get(k)
        if k in ['border_radius_base', 'container_max_width', 'base_font_size', 'logo_image_size', 'button_border_radius', 
                 'show_more_btn_radius', 'back_to_top_size', 'header_max_width', 'section_logo_size', 'hero_pill_radius', 'hero_box_width', 'hero_box_border_width', 'hero_main_border_width',
                 'league_card_radius', 'sys_status_radius', 'sys_status_dot_size', 'watch_table_radius', 'chat_dot_size']:
            if val: val = ensure_unit(val, 'px')
        theme[k] = val if val is not None and val != "" else v

    # --- BORDER LOGIC ---
    def make_border(w, c): return f"{ensure_unit(w, 'px')} solid {c}"
    theme['sec_border_live'] = make_border(theme.get('sec_border_live_width'), theme.get('sec_border_live_color'))
    theme['sec_border_upcoming'] = make_border(theme.get('sec_border_upcoming_width'), theme.get('sec_border_upcoming_color'))
    theme['sec_border_wildcard'] = make_border(theme.get('sec_border_wildcard_width'), theme.get('sec_border_wildcard_color'))
    theme['sec_border_leagues'] = make_border(theme.get('sec_border_leagues_width'), theme.get('sec_border_leagues_color'))
    theme['sec_border_grouped'] = make_border(theme.get('sec_border_grouped_width'), theme.get('sec_border_grouped_color'))
    theme['sec_border_league_upcoming'] = make_border(theme.get('sec_border_league_upcoming_width'), theme.get('sec_border_league_upcoming_color'))
    
    theme['article_h2_border'] = make_border(theme.get('article_h2_border_width'), theme.get('article_h2_border_color'))
    theme['article_h3_border'] = make_border(theme.get('article_h3_border_width'), theme.get('article_h3_border_color'))
    theme['article_h4_border'] = make_border(theme.get('article_h4_border_width'), theme.get('article_h4_border_color'))
    
    theme['league_card_border'] = make_border(theme.get('league_card_border_width'), theme.get('league_card_border_color'))
    theme['league_card_hover_border'] = make_border(theme.get('league_card_border_width'), theme.get('league_card_hover_border_color'))
    theme['static_h1_border'] = make_border(theme.get('static_h1_border_width'), theme.get('static_h1_border_color'))
    theme['sys_status_border'] = make_border(theme.get('sys_status_border_width'), theme.get('sys_status_border_color'))

    # --- COLOR TRANSFORMATIONS ---
    chat_op = theme.get('chat_overlay_opacity', '0.9')
    chat_hex = theme.get('chat_overlay_bg', '#0f172a')
    theme['chat_overlay_bg_final'] = hex_to_rgba(chat_hex, chat_op)

    s_bg_hex = theme.get('sys_status_bg_color', '#22c55e')
    s_bg_op = theme.get('sys_status_bg_opacity', '0.1')
    if str(theme.get('sys_status_bg_transparent', False)).lower() == 'true':
        theme['sys_status_bg_color'] = 'transparent'
    else:
        theme['sys_status_bg_color'] = hex_to_rgba(s_bg_hex, s_bg_op)

    # ROBUST VISIBILITY CHECK
    # Handles boolean True/False and string "true"/"false" from JSON
    raw_vis = theme.get('sys_status_visible', True)
    is_visible = True
    if str(raw_vis).lower() == 'false':
        is_visible = False
    elif raw_vis is False:
        is_visible = False
        
    theme['sys_status_display'] = 'inline-flex' if is_visible else 'none'
    # Calculate values first to ensure fallbacks
    h1_text = page_data.get('h1_title') or page_data.get('title') or ""
    hero_txt = page_data.get('hero_text') or page_data.get('meta_desc') or ""
    # --- ADD THIS LINE TO DEFINE SITE NAME ---
    full_site_name = f"{s.get('title_part_1', 'Stream')}{s.get('title_part_2', 'East')}".strip()

    # --- TEXT REPLACEMENTS ---
    replacements = {
        'META_TITLE': page_data.get('meta_title', ''),
        'META_DESC': page_data.get('meta_desc', ''),
        'META_KEYWORDS': f'<meta name="keywords" content="{page_data.get("meta_keywords")}">' if page_data.get("meta_keywords") else '', # <--- ADDED
        'H1_TITLE': h1_text, # Updated
        'H1_ALIGN': page_data.get('h1_align', theme.get('static_h1_align', 'left')),
        'HERO_TEXT': hero_txt, # Updated
        # --- ADD THIS LINE HERE ---
        'SITE_NAME': full_site_name,
        'FAVICON': s.get('favicon_url', '/favicon.ico'),
        'CANONICAL_URL': page_data.get('canonical_url', ''), # This cleans the raw shortcode
        'FOOTER_COPYRIGHT': s.get('footer_copyright', ''),
        'THEME_TEXT_SYS_STATUS': theme.get('text_sys_status', 'System Status: Online'),
        'LOGO_PRELOAD': f'<link rel="preload" as="image" href="{s.get("logo_url")}" fetchpriority="high">' if s.get('logo_url') else '',
        'API_URL': s.get('api_url', ''),
        'TARGET_COUNTRY': s.get('target_country', 'US'),
        'PARAM_LIVE': s.get('param_live', 'stream'),
        'PARAM_INFO': s.get('param_info', 'info'),
        'DOMAIN': s.get('domain', ''),
        # --- ADD THESE LINES TO FIX THE ISSUE ---
        'THEME_META_COLOR': theme.get('brand_primary', '#D00000'),
        'OG_IMAGE': s.get('logo_url', ''),
        'OG_MIME': 'image/png', # Default fallback for Open Graph
        
        'TEXT_SHOW_MORE': theme.get('text_show_more', 'Show More'),
        'TEXT_WATCH_BTN': theme.get('text_watch_btn', 'WATCH'),
        'TEXT_HD_BADGE': theme.get('text_hd_badge', 'HD'),
        'TEXT_SECTION_LINK': theme.get('text_section_link', 'View All'),
        'TEXT_SECTION_PREFIX': theme.get('text_section_prefix', 'Upcoming'),
        'WILDCARD_CATEGORY': theme.get('wildcard_category', ''),
        'PAGE_FILTER': page_data.get('page_filter', ''),
        
        # NOTE: Dynamic Match Section Titles (Live, Wildcard, Top 5) are removed from here.
        # They will be injected by master_engine.py.
        # However, for League/Sport pages, we still need the "Upcoming" title as that header is outside the injection zone.
        'TEXT_UPCOMING_TITLE': page_data.get('upcoming_title', 'Upcoming Matches')
    }
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    
    # --- UPDATED: Dual Article & Meta System ---
    
    # 1. Meta Templates (Versus & Single)
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))
    
    html = html.replace('{{JS_WATCH_TITLE_SINGLE_TPL}}', w_conf.get('meta_title_single', 'Watch {{VS}}'))
    html = html.replace('{{JS_WATCH_DESC_SINGLE_TPL}}', w_conf.get('meta_desc_single', ''))

    # 2. Article Templates (Inject both into hidden containers)
    # The frontend JS will grab the correct content from these IDs
    article_vs = w_conf.get('article', '')
    article_single = w_conf.get('article_single', '')

    combined_articles = f"""
    <div id="article-content-vs" style="display:none;">{article_vs}</div>
    <div id="article-content-single" style="display:none;">{article_single}</div>
    """
    html = html.replace('{{WATCH_ARTICLE}}', combined_articles)

    # 3. Supabase Config
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))

    # --- ARTICLE CONTENT LOGIC (Existing Page/League Logic) ---
    raw_content = page_data.get('content') or page_data.get('article') or ''
    
    if not raw_content or raw_content.strip() == "":
        # If content is empty, try to remove the container to avoid empty spacing
        html = html.replace('<div class="seo-article">{{ARTICLE_CONTENT}}</div>', '')
        html = html.replace('<article class="seo-article">\n            {{LEAGUE_ARTICLE}}\n        </article>', '')
        # Fallback cleanup
        html = html.replace('{{ARTICLE_CONTENT}}', '') 
        html = html.replace('{{LEAGUE_ARTICLE}}', '')
    else:
        html = html.replace('{{ARTICLE_CONTENT}}', raw_content)

    # Inject Theme Variables
    # Inject Theme Variables (With JS Boolean Safety)
    for k, v in theme.items():
        placeholder = f"{{{{THEME_{k.upper()}}}}}"
        
        # Convert Python Booleans to JS lowercase strings
        if v is True: safe_val = "true"
        elif v is False: safe_val = "false"
        elif v is None: safe_val = ""
        else: safe_val = str(v)
        
        html = html.replace(placeholder, safe_val)

    for k, v in replacements.items():
        html = html.replace(f"{{{{{k}}}}}", str(v))

    # --- STRUCTURAL INJECTIONS ---
    html = html.replace('{{HEADER_MENU}}', build_menu_html(m.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(m.get('hero', []), 'hero'))
    
    country = s.get('target_country', 'US')
    prio = config.get('sport_priorities', {}).get(country, {})
    f_leagues = []
    for k, v in prio.items():
        if not k.startswith('_') and v.get('hasLink'):
            # Simple slugify for footer links
            slug = k.lower().replace(' ', '-').replace('^[^a-z0-9]','') + "-streams"
            f_leagues.append({'title': k, 'url': f"/{slug}/"})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))

    # --- LOGO ---
    p1 = s.get('title_part_1', 'Stream')
    p2 = s.get('title_part_2', 'East')
    logo_size = theme.get('logo_image_size', '40px')
    
    logo_html = f'<div class="logo-text" style="color:{theme.get("logo_p1_color")};">{p1}<span style="color:{theme.get("logo_p2_color")};">{p2}</span></div>'
    if s.get('logo_url'): 
        logo_html = f'<img src="{s.get("logo_url")}" class="logo-img" style="width:{logo_size}; height:{logo_size}; object-fit:cover; border-radius:6px; box-shadow: 0 0 10px {theme.get("logo_image_shadow_color")};"> {logo_html}'
        
    config['_generated_logo_html'] = logo_html 
    html = html.replace('{{LOGO_HTML}}', logo_html)
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config, logo_html))

    # --- LAYOUTS ---
    h_layout = theme.get('header_layout', 'standard')
    h_icon = theme.get('header_icon_pos', 'left')
    header_class = f"h-layout-{h_layout}{' h-icon-'+h_icon if h_layout=='center' else ''}"
    html = html.replace('{{HEADER_CLASSES}}', header_class)
    html = html.replace('{{FOOTER_CLASSES}}', '')

    # Hero Logic
    mode = theme.get('hero_layout_mode', 'full')
    box_w = ensure_unit(theme.get('hero_box_width', '1000px'))
    h_style = theme.get('hero_bg_style', 'solid')
    
    if h_style == 'gradient':
        hero_bg = f"background: radial-gradient(circle at top, {theme.get('hero_gradient_start')} 0%, {theme.get('hero_gradient_end')} 100%);"
    elif h_style == 'image':
        hero_bg = f"background: linear-gradient(rgba(0,0,0,{theme.get('hero_bg_image_overlay_opacity')}), rgba(0,0,0,{theme.get('hero_bg_image_overlay_opacity')})), url('{theme.get('hero_bg_image_url')}'); background-size: cover;"
    elif h_style == 'transparent':
        hero_bg = "background: transparent;"
    else:
        hero_bg = f"background: {theme.get('hero_bg_solid')};"

    box_b_str = f"{ensure_unit(theme.get('hero_box_border_width'), 'px')} solid {theme.get('hero_box_border_color')}"
    box_css = ""
    if theme.get('hero_border_top'): box_css += f"border-top: {box_b_str}; "
    if theme.get('hero_border_bottom_box'): box_css += f"border-bottom: {box_b_str}; "
    if theme.get('hero_border_left'): box_css += f"border-left: {box_b_str}; "
    if theme.get('hero_border_right'): box_css += f"border-right: {box_b_str}; "

    main_pos = theme.get('hero_main_border_pos', 'full')
    main_border_str = f"border-bottom: {ensure_unit(theme.get('hero_main_border_width'), 'px')} solid {theme.get('hero_main_border_color')};" if main_pos != 'none' else ""

    if mode == 'box':
        html = html.replace('{{HERO_OUTER_STYLE}}', f"background: transparent; padding: 40px 15px; {' '+main_border_str if main_pos=='full' else ''}")
        html = html.replace('{{HERO_INNER_STYLE}}', f"{hero_bg} max-width: {box_w}; margin: 0 auto; padding: 30px; border-radius: {ensure_unit(theme.get('border_radius_base'))}; {box_css} {' '+main_border_str if main_pos=='box' else ''}")
    else:
        html = html.replace('{{HERO_OUTER_STYLE}}', f"{hero_bg} padding: 40px 15px; {' '+main_border_str if main_pos=='full' else ''}")
        html = html.replace('{{HERO_INNER_STYLE}}', f"max-width: {ensure_unit(theme.get('container_max_width'))}; margin: 0 auto;")

    align = theme.get('hero_content_align', 'center')
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', align)
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if align == 'center' else ('0' if align == 'left' else '0 0 0 auto'))
    html = html.replace('{{HERO_MENU_DISPLAY}}', theme.get('hero_menu_visible', 'flex'))
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    html = html.replace('{{DISPLAY_HERO}}', theme.get('display_hero', 'block'))

    # --- JSON INJECTIONS ---
    html = html.replace('{{JS_THEME_CONFIG}}', json.dumps(theme))
    html = html.replace('{{JS_PRIORITIES}}', json.dumps(prio))
    # --- ADD THIS LINE ---
    html = html.replace('{{JS_SHARE_COUNTS}}', json.dumps(config.get('social_sharing', {})))
    
    l_map = load_json('assets/data/league_map.json')
    reverse_map = {}
    if l_map:
        for l_name, teams in l_map.items():
            for t in teams: reverse_map[t] = l_name
    html = html.replace('{{JS_LEAGUE_MAP}}', json.dumps(reverse_map))
    html = html.replace('{{JS_IMAGE_MAP}}', json.dumps(load_json('assets/data/image_map.json')))

    # --- NEW: HOMEPAGE SCHEMA GENERATION (Static + Dynamic Placeholder) ---
    if page_data.get('slug') == 'home':
        site_url = f"https://{s.get('domain')}/"
        
       # --- SCHEMA GENERATION (GRAPH BASED) ---
    schema_output = ""
    site_url = f"https://{s.get('domain')}/"
    logo_url = f"{site_url.rstrip('/')}{s.get('logo_url')}"
    
    # Page URL logic
    if page_data.get('slug') == 'home':
        current_page_url = site_url
    else:
        current_page_url = f"{site_url.rstrip('/')}/{page_data.get('slug')}/"

    schemas = page_data.get('schemas', {})
    graph_nodes = []

    # 1. Organization Node (Conditional)
    if schemas.get('org'):
        graph_nodes.append({
            "@type": "Organization",
            "@id": f"{site_url}#organization",
            "name": full_site_name,
            "url": site_url,
            "logo": {
                "@type": "ImageObject",
                "url": logo_url,
                "width": 512, 
                "height": 512
            }
        })

    # 2. WebSite Node (Conditional)
    if schemas.get('website'):
        ws_node = {
            "@type": "WebSite",
            "@id": f"{site_url}#website",
            "url": site_url,
            "name": full_site_name
        }
        if schemas.get('org'):
            ws_node["publisher"] = { "@id": f"{site_url}#organization" }
        graph_nodes.append(ws_node)

    # 3. Page Specific Node
    if page_data.get('slug') == 'home':
        # --- HOMEPAGE: CollectionPage ---
        coll_node = {
            "@type": "CollectionPage",
            "@id": f"{site_url}#homepage",
            "url": site_url,
            "name": page_data.get('meta_title', full_site_name),
            "description": page_data.get('meta_desc', ''),
            "mainEntity": { "@id": f"{site_url}#matchlist" }
        }
        if schemas.get('website'): coll_node["isPartOf"] = { "@id": f"{site_url}#website" }
        if schemas.get('org'): coll_node["about"] = { "@id": f"{site_url}#organization" }
        graph_nodes.append(coll_node)

    elif schemas.get('about'):
        # --- INNER PAGE: AboutPage (Exact Structure Requested) ---
        about_node = {
            "@type": "AboutPage",
            "@id": f"{current_page_url}#webpage",
            "url": current_page_url,
            "name": page_data.get('title'),
            "description": page_data.get('meta_desc', ''),
            "primaryImageOfPage": {
                "@type": "ImageObject",
                "url": logo_url
            }
        }
        if schemas.get('website'): about_node["isPartOf"] = { "@id": f"{site_url}#website" }
        if schemas.get('org'): 
            about_node["about"] = { "@id": f"{site_url}#organization" }
            # Explicitly requested mainEntity pointing to Org
            about_node["mainEntity"] = { "@id": f"{site_url}#organization" }
            
        graph_nodes.append(about_node)

    # 4. Output Static Graph FIRST
    if graph_nodes:
        static_schema = { "@context": "https://schema.org", "@graph": graph_nodes }
        schema_output += f'<script type="application/ld+json">{json.dumps(static_schema)}</script>\n'

    # 5. Output Dynamic Placeholder SECOND (Only on Home)
    if page_data.get('slug') == 'home':
        dynamic_placeholder = {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "@id": f"{site_url}#matchlist",
            "itemListElement": []
        }
        schema_output += f'<script id="dynamic-schema-placeholder" type="application/ld+json">{json.dumps(dynamic_placeholder)}</script>\n'

    # 6. FAQ Schema (Always available if data exists)
    if schemas.get('faq') and schemas.get('faq_list'):
        faq_objects = []
        for item in schemas['faq_list']:
            q = item.get('q', '').strip()
            a = item.get('a', '').strip()
            if q and a:
                faq_objects.append({ "@type": "Question", "name": q, "acceptedAnswer": { "@type": "Answer", "text": a } })
        
        if faq_objects:
            faq_schema = { "@context": "https://schema.org", "@type": "FAQPage", "mainEntity": faq_objects }
            schema_output += f'<script type="application/ld+json">{json.dumps(faq_schema)}</script>\n'

    # Final Injection
    html = html.replace('{{SCHEMA_BLOCK}}', schema_output)

    return html

# ==========================================
# 4. MAIN BUILD PROCESS
# ==========================================
def main():
    print("--- 🔨 Building Site Structure ---")
    config = load_json(CONFIG_PATH)
    if not config: 
        print("❌ Config not found!")
        return

    try:
        with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: master_template_content = f.read()
        with open(WATCH_TEMPLATE_PATH, 'r', encoding='utf-8') as f: watch_template_content = f.read()
        
        page_template_content = master_template_content # Fallback
        if os.path.exists(TEMPLATE_PAGE):
            with open(TEMPLATE_PAGE, 'r', encoding='utf-8') as f: page_template_content = f.read()
            
    except FileNotFoundError:
        print("❌ Template file not found")
        return

    print("📄 Building Pages...")
    
    # Get Theme Contexts
    theme_page_conf = config.get('theme_page', {}) 
    if not theme_page_conf: theme_page_conf = config.get('theme', {})

    theme_watch_conf = config.get('theme_watch', {})
    if not theme_watch_conf: theme_watch_conf = config.get('theme', {})

    for page in config.get('pages', []):
        slug = page.get('slug')
        if not slug: continue
        
        layout = page.get('layout')
        
        final_template = master_template_content
        active_theme_override = None

        if layout == 'watch':
            final_template = watch_template_content
            active_theme_override = theme_watch_conf 
            
            # Fallback for the static page load (before JS runs)
            page['meta_title'] = "Watch Live Sports"
            page['meta_desc'] = "Live sports streaming coverage."
        elif layout == 'page':
            final_template = page_template_content
            active_theme_override = theme_page_conf 
            # RESTORED: Full Page Data Construction including Keywords and Schemas
        p_data = {
            'title': page.get('title'),
            'meta_title': page.get('meta_title'),
            'meta_desc': page.get('meta_desc'),
            'meta_keywords': page.get('meta_keywords', ''), # Restored
            'h1_title': page.get('title'),
            'h1_align': page.get('h1_align'),
            'hero_text': page.get('meta_desc'), # Fallback hero text
            'content': page.get('content'),     # This is the Article/Body content
            'article': page.get('content'),     # Alias for compatibility
            'canonical_url': page.get('canonical_url') or (f"https://{config['site_settings']['domain']}/{slug}/" if slug != 'home' else f"https://{config['site_settings']['domain']}/"),
            'slug': slug,
            'layout': layout,
            'schemas': page.get('schemas', {})  # Restored Schema Config
        }
        
        # Render
        final_html = render_page(final_template, config, p_data, theme_override=active_theme_override)
        
        out_dir = os.path.join(OUTPUT_DIR, slug) if slug != 'home' else OUTPUT_DIR
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(final_html)
    
    # ==========================================
    # 5. BUILD LEAGUE PAGES
    # ==========================================
    print("🏆 Building League Pages...")
    
    league_template_content = None
    if os.path.exists(TEMPLATE_LEAGUE):
        with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f:
            league_template_content = f.read()
    
    if league_template_content:
        target_country = config.get('site_settings', {}).get('target_country', 'US')
        priorities = config.get('sport_priorities', {}).get(target_country, {})
        articles = config.get('articles', {})
        
        theme_league = config.get('theme_league', {})
        if not theme_league: theme_league = config.get('theme', {})

        domain = config.get('site_settings', {}).get('domain', 'example.com')

        for name, data in priorities.items():
            if name.startswith('_') or not data.get('hasLink'): continue
            
            slug = name.lower().replace(' ', '-').replace('^[^a-z0-9]','') + "-streams"
            is_league = data.get('isLeague', False)
            # Entity Intelligence (Parent Sport) - RESTORED LOGIC
            parent_sport = LEAGUE_PARENT_MAP.get(name)
            
            if not parent_sport:
                lower_name = name.lower()
                # Enhanced detection logic
                if "ncaa" in lower_name: 
                    if "basket" in lower_name: parent_sport = "Basketball"
                    elif "football" in lower_name: parent_sport = "American Football"
                    else: parent_sport = "College Sports"
                elif "football" in lower_name or "soccer" in lower_name: parent_sport = "Soccer"
                elif "basket" in lower_name: parent_sport = "Basketball"
                elif "fight" in lower_name or "ufc" in lower_name or "boxing" in lower_name or "mma" in lower_name: parent_sport = "Combat Sports"
                elif "racing" in lower_name or "motor" in lower_name or "f1" in lower_name: parent_sport = "Motorsport"
                elif "tennis" in lower_name: parent_sport = "Tennis"
                elif "golf" in lower_name: parent_sport = "Golf"
                elif "rugby" in lower_name: parent_sport = "Rugby"
                elif "cricket" in lower_name: parent_sport = "Cricket"
                elif "hockey" in lower_name or "nhl" in lower_name: parent_sport = "Ice Hockey"
                elif "baseball" in lower_name or "mlb" in lower_name: parent_sport = "Baseball"
                else: parent_sport = name # Absolute fallback

            # Ensure it is a string for replacement
            parent_sport = str(parent_sport)
            # Get Site Title parts
            sett = config.get('site_settings', {})
            site_title_full = f"{sett.get('title_part_1', '')}{sett.get('title_part_2', '')}"
            
            # 1. Prepare Variables
            # 1. Prepare Variables
            vars_map = {
                '{{NAME}}': name, 
                '{{SPORT}}': parent_sport, 
                '{{YEAR}}': "2025", 
                '{{DOMAIN}}': sett.get('domain', ''),
                '{{SITE_TITLE}}': site_title_full  # <--- New Shortcode Added
            }
            
            def replace_vars(text, v_map):
                if not text: return ""
                for k, v in v_map.items():
                    text = text.replace(k, v)
                return text

            # 2. Define Content
            p_h1 = replace_vars(articles.get('league_h1', 'Watch {{NAME}} Live'), vars_map)
            p_intro = replace_vars(articles.get('league_intro', ''), vars_map)
            
            # NOTE: Section titles for Leagues are still relevant as Master Engine uses regex to replace list items,
            # BUT in league_template.html, the header is part of the static HTML block ABOVE the regex target.
            # So we MUST provide this title here.
            sec_upc = replace_vars(articles.get('league_upcoming_title', 'Upcoming {{NAME}}'), vars_map)
            
            raw_art = articles.get('league', '') if is_league else articles.get('sport', '')
            final_art = replace_vars(raw_art, vars_map)

            # 3. PAGE DATA Construction
            page_data = {
                'title': p_h1, 
                'meta_title': p_h1,
                'meta_desc': p_intro, 
                'hero_h1': p_h1, 
                'hero_text': p_intro,
                'canonical_url': f"https://{config['site_settings']['domain']}/{slug}/",
                'slug': slug, 
                'layout': 'league', 
                'content': final_art,
                'meta_keywords': f"{name} stream, watch {name} free, {name} live",
                'schemas': {'org': True, 'website': True},
                'upcoming_title': sec_upc
            }

            # 4. Render
            html = render_page(league_template_content, config, page_data, theme_override=theme_league)
            
            # 5. Injections
            html = html.replace('{{PAGE_FILTER}}', name)
            html = html.replace('{{LEAGUE_ARTICLE}}', final_art)
            # We inject this because it's static in the template
            html = html.replace('{{TEXT_UPCOMING_TITLE}}', sec_upc) 
            html = html.replace('{{HERO_PILLS}}', build_menu_html(config.get('menus', {}).get('hero', []), 'hero'))
            
            # 6. Write File
            out_dir = os.path.join(OUTPUT_DIR, slug)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"   -> Built: {slug} (Filter: {name})")

    print("✅ Build Complete.")

if __name__ == "__main__":
    main()
