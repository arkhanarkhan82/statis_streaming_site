import json
import os
import re

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
LEAGUE_MAP_PATH = 'assets/data/league_map.json' 
IMAGE_MAP_PATH = 'assets/data/image_map.json'
TEMPLATE_PATH = 'assets/master_template.html'
WATCH_TEMPLATE_PATH = 'assets/watch_template.html'
LEAGUE_TEMPLATE_PATH = 'assets/league_template.html'
PAGE_TEMPLATE_PATH = 'assets/page_template.html'
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

# ==========================================
# 2. UTILS
# ==========================================
def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f: 
                return json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ Warning: {path} contains invalid JSON. Returning empty dict.")
            return {}
    return {}

def normalize_key(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def ensure_unit(val, unit='px'):
    s_val = str(val).strip()
    if not s_val: return f"0{unit}"
    if s_val.isdigit(): return f"{s_val}{unit}"
    return s_val

def build_menu_html(menu_items, section):
    html = ""
    for item in menu_items:
        title = item.get('title', 'Link')
        url = item.get('url', '#')
        
        if section == 'header':
            css_class = ' class="highlighted"' if item.get('highlight') else ''
            html += f'<a href="{url}"{css_class}>{title}</a>'
        elif section == 'footer_leagues':
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
            html += f'<a href="{url}" class="league-card"><span class="l-icon">{icon}</span><span>{title}</span></a>'
        elif section == 'hero':
            html += f'<a href="{url}" class="cat-pill">{title}</a>'
        elif section == 'footer_static':
             html += f'<a href="{url}" class="f-link">{title}</a>'
        else:
            html += f'<a href="{url}">{title}</a>'
    return html

# ==========================================
# 3. PAGE RENDERER
# ==========================================
def build_footer_grid(config):
    t = config.get('theme', {})
    s = config.get('site_settings', {})
    m = config.get('menus', {})
    
    cols = str(t.get('footer_columns', '2'))
    show_disclaimer = t.get('footer_show_disclaimer', True)
    
    # 1. Define Content Blocks
    # Block: Brand
    brand_html = f"""
    <div class="f-brand">
        {config.get('_generated_logo_html', '')} 
    </div>
    """
    
    # Block: Disclaimer
    disc_text = s.get('footer_disclaimer', '')
    disc_html = f'<div class="f-desc">{disc_text}</div>' if show_disclaimer else ''
    
    # Block: Brand + Disclaimer (Combined)
    brand_disc_html = f"""
    <div class="f-brand">
        {config.get('_generated_logo_html', '')}
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
def render_page(template, config, page_data, theme_override=None):
    s = config.get('site_settings', {})
    # MERGE LOGIC: Use Base Theme as default, then overwrite with League Theme
    base_theme = config.get('theme', {}).copy()
    if theme_override:
        base_theme.update(theme_override)
    t = base_theme
    
    m = config.get('menus', {})
    
    html = template
    
    # --- THEME DEFAULTS ---
    defaults = {
        'brand_primary': '#D00000', 'brand_dark': '#8a0000', 'accent_gold': '#FFD700', 'status_green': '#22c55e',
        'bg_body': '#050505', 'bg_panel': '#1e293b', 'bg_glass': 'rgba(30, 41, 59, 0.7)',
        'text_main': '#f1f5f9', 'text_muted': '#94a3b8', 'border_color': '#334155', 'scrollbar_thumb_color': '#475569',
        'font_family_base': 'system-ui, -apple-system, sans-serif', 'font_family_headings': 'inherit',
        'base_font_size': '14px', 'base_line_height': '1.5',
        'league_card_bg': 'rgba(30, 41, 59, 0.5)',
        'league_card_text': '#f1f5f9',
        'static_h1_color': '#f1f5f9',
        'static_h1_align': 'left',
        'league_card_border_width': '1', 
        'league_card_border_color': '#334155',
        'league_card_radius': '6',
        'static_h1_border_width': '1', 
        'static_h1_border_color': '#334155',
        'sys_status_visible': True,
        'sys_status_text_color': '#22c55e',
        'sys_status_bg_color': 'rgba(34, 197, 94, 0.1)',
        'sys_status_border_color': 'rgba(34, 197, 94, 0.2)',
        'sys_status_border_width': '1',
        'sys_status_radius': '20',
        'sys_status_dot_color': '#22c55e',
        'sys_status_dot_size': '8',
        'league_card_hover_bg': '#1e293b',
        'league_card_hover_text': '#ffffff',
        'league_card_hover_border_color': '#D00000',
        'container_max_width': '1100px', 'border_radius_base': '6px', 'button_border_radius': '4px',
        'header_max_width': '1100px', 'hero_pill_radius': '50px', 'card_shadow': '0 4px 6px -1px rgba(0,0,0,0.1)',
        'header_bg': 'rgba(5, 5, 5, 0.8)', 'header_text_color': '#f1f5f9', 'header_link_active_color': '#D00000',
        'header_border_bottom': '1px solid #334155', 'logo_p1_color': '#f1f5f9', 'logo_p2_color': '#D00000',
        'logo_image_size': '40px', 'header_layout': 'standard', 'header_icon_pos': 'left',
        'header_link_hover_color': '#ffffff', 'header_highlight_color': '#FFD700', 'header_highlight_hover': '#ffea70',
        'hero_bg_style': 'solid', 'hero_bg_solid': '#1a0505', 'hero_gradient_start': '#1a0505', 'hero_gradient_end': '#000000',
        'hero_h1_color': '#ffffff', 'hero_intro_color': '#94a3b8',
        'hero_pill_bg': 'rgba(255,255,255,0.05)', 'hero_pill_text': '#f1f5f9', 'hero_pill_border': 'rgba(255,255,255,0.1)',
        'hero_pill_hover_bg': '#D00000', 'hero_pill_hover_text': '#ffffff', 'hero_pill_hover_border': '#D00000',
        'hero_layout_mode': 'full', 'hero_content_align': 'center', 'hero_menu_visible': 'flex',
        'hero_box_width': '1000px', 'hero_border_width': '1', 'hero_border_color': '#334155',
        'hero_border_top': False, 'hero_border_left': False, 'hero_border_right': False,
        'text_sys_status': 'System Status: Online',
        'hero_main_border_pos': 'themeHeroMainBorderPos', 'hero_main_border_width': 'themeHeroMainBorderWidth',
        'hero_main_border_color': 'themeHeroMainBorderColor', 'hero_box_border_width': '1', 'hero_box_border_color': '#334155',
        'hero_border_bottom_box': False,
        'footer_columns': '2',
        # ... existing defaults ...
        'watch_sidebar_swap': False,
        'watch_show_ad1': True, 'watch_show_discord': True, 'watch_show_ad2': True,
        'watch_discord_order': 'middle',
        'chat_header_bg': 'rgba(0,0,0,0.4)', 'chat_header_text': '#ffffff',
        'chat_dot_color': '#22c55e', 'chat_dot_size': '6px',
        'chat_overlay_bg': 'rgba(15, 23, 42, 0.6)', 'chat_input_bg': '#000000',
        'chat_input_text': '#ffffff',
        'watch_table_head_bg': 'rgba(255,255,255,0.03)', 'watch_table_body_bg': '#1e293b',
        'watch_table_border': '#334155', 'watch_table_radius': '6px',
        'watch_team_color': '#ffffff', 'watch_vs_color': 'rgba(255,255,255,0.1)',
        'watch_team_size': '1.4rem', 'watch_vs_size': '2rem',
        'watch_btn_bg': '#D00000', 'watch_btn_text': '#ffffff',
        'watch_btn_disabled_bg': '#1e293b', 'watch_btn_disabled_text': '#94a3b8',
        'watch_info_btn_bg': '#1e293b', 'watch_info_btn_text': '#ffffff',
        'watch_server_active_bg': '#D00000', 'watch_server_text': '#94a3b8',
        'watch_discord_title': 'Join Discord', 'watch_discord_btn_text': 'Join',
        'chat_header_title': 'Live Chat', 'chat_join_btn_text': 'Join Room',
        'watch_btn_label': 'Watch Live Stream', 'watch_btn_disabled_label': 'Stream Starts Soon',
        'watch_info_btn_label': 'View Match Info',
        'sec_border_live_width': '1', 'sec_border_live_color': '#334155',
        'sec_border_upcoming_width': '1', 'sec_border_upcoming_color': '#334155',
        'sec_border_wildcard_width': '1', 'sec_border_wildcard_color': '#334155',
        'sec_border_leagues_width': '1', 'sec_border_leagues_color': '#334155',
        'sec_border_grouped_width': '1', 'sec_border_grouped_color': '#334155',
        'match_row_bg': '#1e293b', 'match_row_border': '#334155', 
        'match_row_live_border_left': '4px solid #22c55e', 'match_row_live_bg_start': 'rgba(34, 197, 94, 0.1)',
        'match_row_live_bg_end': 'transparent', 'match_row_hover_border': '#D00000', 'match_row_hover_transform': 'translateY(-2px)',
        'match_row_hover_bg': '#1e293b', 'match_row_time_main_color': '#f1f5f9', 'match_row_time_sub_color': '#94a3b8',
        'match_row_live_text_color': '#22c55e', 'match_row_league_tag_color': '#94a3b8', 'match_row_team_name_color': '#f1f5f9',
        'match_row_btn_watch_bg': '#D00000', 'match_row_btn_watch_text': '#ffffff', 
        'match_row_btn_watch_hover_bg': '#b91c1c', 'match_row_btn_watch_hover_transform': 'scale(1.05)',
        'match_row_hd_badge_bg': 'rgba(0,0,0,0.3)', 'match_row_hd_badge_border': 'rgba(255,255,255,0.2)', 'match_row_hd_badge_text': '#facc15',
        'match_row_btn_notify_bg': 'transparent', 'match_row_btn_notify_border': '#334155', 'match_row_btn_notify_text': '#94a3b8',
        'match_row_btn_notify_active_bg': '#22c55e', 'match_row_btn_notify_active_border': '#22c55e', 'match_row_btn_notify_active_text': '#ffffff',
        'match_row_btn_copy_link_color': '#64748b', 'match_row_btn_copy_link_hover_color': '#D00000',
        'footer_bg_start': '#0f172a', 'footer_bg_end': '#020617', 'footer_border_top': '1px solid #334155',
        'footer_heading_color': '#94a3b8', 'footer_link_color': '#64748b', 'footer_link_hover_color': '#f1f5f9',
        'footer_link_hover_transform': 'translateX(5px)', 'footer_copyright_color': '#475569', 'footer_desc_color': '#64748b',
        'social_sidebar_bg': 'rgba(15, 23, 42, 0.8)', 'social_sidebar_border': '#334155', 'social_sidebar_shadow': '0 4px 10px rgba(0,0,0,0.3)',
        'social_btn_bg': 'rgba(30, 41, 59, 0.8)', 'social_btn_border': '#334155', 'social_btn_color': '#94a3b8',
        'social_btn_hover_bg': '#1e293b', 'social_btn_hover_border': '#D00000', 'social_btn_hover_transform': 'translateX(5px)',
        'social_count_color': '#64748b', 'mobile_footer_bg': 'rgba(5, 5, 5, 0.9)', 'mobile_footer_border_top': '1px solid #334155',
        'mobile_footer_shadow': '0 -4px 10px rgba(0,0,0,0.5)', 'copy_toast_bg': '#22c55e', 'copy_toast_text': '#ffffff', 'copy_toast_border': '#16a34a',
        'back_to_top_bg': '#D00000', 'back_to_top_icon_color': '#ffffff', 'back_to_top_shadow': '0 4px 10px rgba(208,0,0,0.4)',
        'sys_status_dot_color': '#22c55e', 'sys_status_bg': 'rgba(34, 197, 94, 0.1)', 'sys_status_border': 'rgba(34, 197, 94, 0.2)', 'sys_status_text': '#22c55e',
        'skeleton_gradient_start': '#1e293b', 'skeleton_gradient_mid': '#334155', 'skeleton_gradient_end': '#1e293b', 'skeleton_border_color': '#334155',
        'text_wildcard_title': '', 'text_top_upcoming_title': '', 'logo_image_shadow_color': 'rgba(208, 0, 0, 0.3)',
        'button_shadow_color': 'rgba(0,0,0,0.2)', 'show_more_btn_bg': '#1e293b', 'show_more_btn_border': '#334155', 'show_more_btn_text': '#94a3b8',
        'show_more_btn_hover_bg': '#D00000', 'show_more_btn_hover_border': '#D00000', 'show_more_btn_hover_text': '#ffffff',
        'league_card_bg': 'rgba(30, 41, 59, 0.5)', 'league_card_border': '#334155', 'league_card_text': '#f1f5f9',
        'league_card_hover_bg': '#1e293b', 'league_card_hover_border': '#D00000', 'footer_brand_color': '#ffffff',
        'mobile_footer_btn_active_bg': 'rgba(255,255,255,0.1)', 'social_telegram_color': '#0088cc', 'social_whatsapp_color': '#25D366',
        'social_reddit_color': '#FF4500', 'social_twitter_color': '#1DA1F2', 'social_btn_hover_shadow_color': 'rgba(0,0,0,0.3)',
        'footer_grid_columns': '1fr 1fr', 'footer_text_align_mobile': 'left', 'footer_grid_columns_desktop': '1fr 1fr 1fr',
        'footer_text_align_desktop': 'left', 'footer_last_col_align_desktop': 'right', 'social_desktop_top': '50%', 'social_desktop_left': '0',
        'social_desktop_scale': '1.0', 'mobile_footer_height': '60px', 'show_more_btn_radius': '30px', 'back_to_top_radius': '50%',
        'back_to_top_size': '40px', 'section_logo_size': '24px', 'text_live_section_title': 'Trending Live',
        'text_show_more': 'Show More', 'text_watch_btn': 'WATCH', 'text_hd_badge': 'HD', 'text_section_link': 'View All',
        'wildcard_category': '', 'text_section_prefix': 'Upcoming',
        'sec_border_league_upcoming_width': '1', 'sec_border_league_upcoming_color': '#334155',
        'article_bg': 'transparent', 'article_text': '#94a3b8', 'article_line_height': '1.6',
        'article_bullet_color': '#D00000', 'article_link_color': '#D00000',
        'article_h2_color': '#f1f5f9', 'article_h2_border_width': '0', 'article_h2_border_color': '#334155',
        'article_h3_color': '#f1f5f9', 'article_h4_color': '#cbd5e1'
    }

    theme = {}
    for k, v in defaults.items():
        val = t.get(k)
        if k in ['border_radius_base', 'container_max_width', 'base_font_size', 'logo_image_size', 'button_border_radius', 
                 'show_more_btn_radius', 'back_to_top_size', 'header_max_width', 'section_logo_size', 'hero_pill_radius', 'hero_box_width', 'hero_box_border_width', 'hero_main_border_width']:
            if val: val = ensure_unit(val, 'px')
        # Fix: Allow False (boolean) to override True (default), but treat empty strings as missing
        theme[k] = val if val is not None and val != "" else v

    def make_border(w, c): return f"{ensure_unit(w, 'px')} solid {c}"
    theme['sec_border_live'] = make_border(theme.get('sec_border_live_width'), theme.get('sec_border_live_color'))
    theme['sec_border_upcoming'] = make_border(theme.get('sec_border_upcoming_width'), theme.get('sec_border_upcoming_color'))
    theme['sec_border_wildcard'] = make_border(theme.get('sec_border_wildcard_width'), theme.get('sec_border_wildcard_color'))
    theme['sec_border_leagues'] = make_border(theme.get('sec_border_leagues_width'), theme.get('sec_border_leagues_color'))
    theme['sec_border_grouped'] = make_border(theme.get('sec_border_grouped_width'), theme.get('sec_border_grouped_color'))
    theme['article_h2_border'] = make_border(theme.get('article_h2_border_width'), theme.get('article_h2_border_color'))
    theme['sec_border_league_upcoming'] = make_border(theme.get('sec_border_league_upcoming_width'), theme.get('sec_border_league_upcoming_color'))
    theme['league_card_border'] = make_border(theme.get('league_card_border_width'), theme.get('league_card_border_color'))
    theme['league_card_hover_border'] = make_border(theme.get('league_card_border_width'), theme.get('league_card_hover_border_color'))
    theme['static_h1_border'] = make_border(theme.get('static_h1_border_width'), theme.get('static_h1_border_color'))
    theme['sys_status_border'] = make_border(theme.get('sys_status_border_width'), theme.get('sys_status_border_color'))
    # ... existing processing ...
    theme['chat_dot_size'] = ensure_unit(theme.get('chat_dot_size'), 'px')
    theme['watch_table_radius'] = ensure_unit(theme.get('watch_table_radius'), 'px')
    
    # Opacity for Chat Overlay
    chat_op = theme.get('chat_overlay_opacity', '0.9')
    chat_ov_hex = theme.get('chat_overlay_bg', '#0f172a')
    theme['chat_overlay_bg_final'] = hex_to_rgba(chat_ov_hex, chat_op)
     # === NEW CODE ADDED HERE ===
    s_bg_hex = theme.get('sys_status_bg_color', '#22c55e') 
    s_bg_op = theme.get('sys_status_bg_opacity', '0.1')
    s_bg_trans = theme.get('sys_status_bg_transparent', False)

    if s_bg_trans is True or str(s_bg_trans).lower() == 'true':
        theme['sys_status_bg_color'] = 'transparent'
    else:
        theme['sys_status_bg_color'] = hex_to_rgba(s_bg_hex, s_bg_op)
    # ===========================
    theme['sys_status_radius'] = ensure_unit(theme.get('sys_status_radius'), 'px')
    theme['sys_status_dot_size'] = ensure_unit(theme.get('sys_status_dot_size'), 'px')
    is_visible = theme.get('sys_status_visible')
    if is_visible is None: is_visible = True # Default True
    theme['sys_status_display'] = 'inline-flex' if is_visible else 'none'
    
    # 2. ENSURE RADIUS HAS UNIT
    theme['league_card_radius'] = ensure_unit(theme.get('league_card_radius'), 'px')

    for key, val in theme.items():
        if isinstance(val, bool):
            val = str(val).lower()
        html = html.replace(f"{{{{THEME_{key.upper()}}}}}", str(val))
        grid_cols = str(theme.get('footer_columns', '2'))
    html = html.replace('{{THEME_FOOTER_COLS}}', f'repeat({grid_cols}, 1fr)')

    # --- LAYOUT/HERO LOGIC ---
    h_layout = theme.get('header_layout', 'standard')
    h_icon = theme.get('header_icon_pos', 'left')
    header_class = f"h-layout-{h_layout}"
    if h_layout == 'center': header_class += f" h-icon-{h_icon}"
    html = html.replace('{{HEADER_CLASSES}}', header_class)

    hero_style = theme.get('hero_bg_style', 'solid')
    hero_css = ""
    if hero_style == 'gradient':
        hero_css = f"background: radial-gradient(circle at top, {theme.get('hero_gradient_start')} 0%, {theme.get('hero_gradient_end')} 100%);"
    elif hero_style == 'image':
        hero_css = f"background: linear-gradient(rgba(0,0,0,{theme.get('hero_bg_image_overlay_opacity')}), rgba(0,0,0,{theme.get('hero_bg_image_overlay_opacity')})), url('{theme.get('hero_bg_image_url')}'); background-size: cover; background-position: center;"
    elif hero_style == 'transparent':
        hero_css = "background: transparent;"
    else:
        hero_css = f"background: {theme.get('hero_bg_solid')};"

    align = theme.get('hero_content_align', 'center')
    align_items = 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end')
    intro_margin = '0 auto' if align == 'center' else ('0' if align == 'left' else '0 0 0 auto')
    menu_justify = align_items

    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', align)
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', align_items)
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', intro_margin)
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', menu_justify)

    h_mode = theme.get('hero_layout_mode', 'full')
    box_b_str = f"{ensure_unit(theme.get('hero_box_border_width'), 'px')} solid {theme.get('hero_box_border_color')}"
    box_border_css = ""
    if theme.get('hero_border_top'): box_border_css += f"border-top: {box_b_str}; "
    if theme.get('hero_border_bottom_box'): box_border_css += f"border-bottom: {box_b_str}; "
    if theme.get('hero_border_left'): box_border_css += f"border-left: {box_b_str}; "
    if theme.get('hero_border_right'): box_border_css += f"border-right: {box_b_str}; "

    main_pos = theme.get('hero_main_border_pos', 'full')
    main_border_str = f"border-bottom: {ensure_unit(theme.get('hero_main_border_width'), 'px')} solid {theme.get('hero_main_border_color')};" if main_pos != 'none' else ""

    hero_outer_style = ""
    hero_inner_style = ""
    if h_mode == 'box':
        hero_outer_style = f"background: transparent; padding: 40px 15px;"
        if main_pos == 'full': hero_outer_style += f" {main_border_str}"
        hero_inner_style = f"{hero_css} max-width: {ensure_unit(theme.get('hero_box_width'))}; margin: 0 auto; padding: 30px; border-radius: var(--border-radius-base); {box_border_css}"
        if main_pos == 'box': hero_inner_style += f" {main_border_str}"
    else:
        hero_outer_style = f"{hero_css} padding: 40px 15px 15px 15px;"
        if main_pos == 'full': hero_outer_style += f" {main_border_str}"
        hero_inner_style = "max-width: var(--container-max-width); margin: 0 auto;"

    html = html.replace('{{HERO_OUTER_STYLE}}', hero_outer_style)
    html = html.replace('{{HERO_INNER_STYLE}}', hero_inner_style)
    html = html.replace('{{HERO_MENU_DISPLAY}}', theme.get('hero_menu_visible', 'flex'))
    html = html.replace('{{JS_THEME_CONFIG}}', json.dumps(theme))
    html = html.replace('{{WILDCARD_CATEGORY}}', theme.get('wildcard_category', ''))
    
    # Text Replacements
    html = html.replace('{{TEXT_LIVE_SECTION_TITLE}}', theme.get('text_live_section_title', 'Trending Live'))
    html = html.replace('{{TEXT_SHOW_MORE}}', theme.get('text_show_more', 'Show More'))
    html = html.replace('{{TEXT_WATCH_BTN}}', theme.get('text_watch_btn', 'WATCH'))
    html = html.replace('{{TEXT_HD_BADGE}}', theme.get('text_hd_badge', 'HD'))
    html = html.replace('{{TEXT_SECTION_LINK}}', theme.get('text_section_link', 'View All'))
    html = html.replace('{{TEXT_SECTION_PREFIX}}', theme.get('text_section_prefix', 'Upcoming'))
    html = html.replace('{{TEXT_WILDCARD_TITLE}}', theme.get('text_wildcard_title', ''))
    html = html.replace('{{THEME_TEXT_SYS_STATUS}}', theme.get('text_sys_status', 'System Status: Online'))
    html = html.replace('{{TEXT_TOP_UPCOMING_TITLE}}', theme.get('text_top_upcoming_title', ''))

    html = html.replace('{{BRAND_PRIMARY}}', theme.get('brand_primary'))
    html = html.replace('{{API_URL}}', s.get('api_url', ''))
    country = s.get('target_country', 'US')
    html = html.replace('{{TARGET_COUNTRY}}', country)
    html = html.replace('lang="en"', f'lang="en-GB"' if country == 'UK' else 'lang="en-US"')
    
    p1 = s.get('title_part_1', 'Stream')
    p2 = s.get('title_part_2', 'East')
    site_name = f"{p1}{p2}"
    html = html.replace('{{SITE_NAME}}', site_name)
    domain = s.get('domain', 'example.com')
    
    # Logo Logic
    og_image = s.get('logo_url', '') or ""
    if og_image and not og_image.startswith('http'): og_image = f"https://{domain.rstrip('/')}/{og_image.lstrip('/')}"
    og_mime = "image/png"
    if og_image.lower().endswith('.webp'): og_mime = "image/webp"
    elif og_image.lower().endswith(('.jpg', '.jpeg')): og_mime = "image/jpeg"
    
    html = html.replace('{{OG_IMAGE}}', og_image)
    html = html.replace('{{OG_MIME}}', og_mime)
    logo_html = f'<div class="logo-text">{p1}<span>{p2}</span></div>'
    if s.get('logo_url'): logo_html = f'<img src="{s.get("logo_url")}" class="logo-img" alt="{site_name} Logo" fetchpriority="high"> {logo_html}'
    config['_generated_logo_html'] = logo_html      # <--- FIX: Remove spaces to align with 'if'
    html = html.replace('{{LOGO_HTML}}', logo_html)
    html = html.replace('{{DOMAIN}}', domain)
    p_live = s.get('param_live', 'stream')
    p_info = s.get('param_info', 'info')
    
    html = html.replace('{{PARAM_LIVE}}', p_live)
    html = html.replace('{{PARAM_INFO}}', p_info)
    html = html.replace('{{FAVICON}}', s.get('favicon_url', ''))

    html = html.replace('{{HEADER_MENU}}', build_menu_html(m.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(m.get('hero', []), 'hero'))
    
    auto_footer_leagues = []
    priorities = config.get('sport_priorities', {}).get(country, {})
    if priorities:
        for name, data in sorted([item for item in priorities.items() if not item[0].startswith('_')], key=lambda x: x[1].get('score', 0), reverse=True):
            if data.get('hasLink'): auto_footer_leagues.append({'title': name, 'url': f'/{normalize_key(name)}-streams/'})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(auto_footer_leagues, 'footer_leagues'))

    html = html.replace('{{FOOTER_COPYRIGHT}}', s.get('footer_copyright', f"&copy; 2025 {domain}"))
    
    # <--- FIX: Add indentation to this whole block
    temp_config = config.copy()
    if theme_override:
        temp_config['theme'] = config.get('theme', {}).copy()
        temp_config['theme'].update(theme_override)

    # 2. Build the Grid
    footer_grid_html = build_footer_grid(temp_config)
    html = html.replace('{{FOOTER_GRID_CONTENT}}', footer_grid_html)
    # <--- End of fix

    layout = page_data.get('layout', 'page')
    if layout == 'watch':
        html = html.replace('{{META_TITLE}}', '').replace('{{META_DESC}}', '').replace('<link rel="canonical" href="{{CANONICAL_URL}}">', '')
        html = html.replace('{{H1_TITLE}}', '').replace('{{HERO_TEXT}}', '').replace('{{DISPLAY_HERO}}', 'none')
        html = html.replace('</head>', '<style>.hero, #live-section, #upcoming-container { display: none !important; }</style></head>')
    else:
        html = html.replace('{{META_TITLE}}', page_data.get('meta_title') or f"{site_name} - {page_data.get('title')}")
        html = html.replace('{{META_DESC}}', page_data.get('meta_desc', ''))
        html = html.replace('{{H1_TITLE}}', page_data.get('title', ''))
        default_align = theme.get('static_h1_align', 'left') 
        html = html.replace('{{H1_ALIGN}}', page_data.get('h1_align') or default_align)
        html = html.replace('{{HERO_TEXT}}', page_data.get('hero_text') or page_data.get('meta_desc', ''))
        canon = page_data.get('canonical_url', '') or (f"https://{domain}/{page_data.get('slug')}/" if page_data.get('slug') != 'home' else f"https://{domain}/")
        html = html.replace('{{CANONICAL_URL}}', canon)

    html = html.replace('{{META_KEYWORDS}}', f'<meta name="keywords" content="{page_data.get("meta_keywords")}">' if page_data.get('meta_keywords') else '')
    
    # FIX: Allow 'league' layout to show Hero and Match Sections
    if layout in ['home', 'league']: 
        html = html.replace('{{DISPLAY_HERO}}', theme.get('display_hero', 'block'))
    elif layout != 'watch': 
        # Only hide sections for static pages (About, Contact, etc.)
        html = html.replace('{{DISPLAY_HERO}}', 'none')
        html = html.replace('</head>', '<style>#live-section, #upcoming-container { display: none !important; }</style></head>')

    html = html.replace('{{ARTICLE_CONTENT}}', page_data.get('content', ''))

    # --- INJECTIONS (OPTIMIZED) ---
    html = html.replace('{{JS_PRIORITIES}}', json.dumps(priorities))
    
    social_data = config.get('social_sharing', {})
    js_social = {"excluded": [x.strip() for x in social_data.get('excluded_pages', '').split(',') if x.strip()], "counts": social_data.get('counts', {})}
    html = re.sub(r'const SHARE_CONFIG = \{.*?\};', f'const SHARE_CONFIG = {json.dumps(js_social)};', html, flags=re.DOTALL)

    # 1. LOAD LEAGUE MAP
    league_map_data = load_json(LEAGUE_MAP_PATH)
    
    # 2. CREATE REVERSE MAP (Team -> League) SERVER SIDE
    reverse_map = {}
    if league_map_data:
        for league_name, teams in league_map_data.items():
            for team in teams:
                # Store as key: team-slug, value: League Name
                reverse_map[team] = league_name
    
    # Inject the REVERSED map instead of the raw map
    html = html.replace('{{JS_LEAGUE_MAP}}', json.dumps(reverse_map))
    html = html.replace('{{JS_IMAGE_MAP}}', json.dumps(load_json(IMAGE_MAP_PATH)))

    # --- STATIC SCHEMAS ---
    schemas = []
    page_schemas = page_data.get('schemas', {})
    org_id = f"https://{domain}/#organization"
    website_id = f"https://{domain}/#website"
    
    if page_schemas.get('org'):
        schemas.append({"@context": "https://schema.org", "@type": "Organization", "@id": org_id, "name": site_name, "url": f"https://{domain}/", "logo": {"@type": "ImageObject", "url": og_image, "width": 512, "height": 512}})
    if page_schemas.get('website'):
        schemas.append({"@context": "https://schema.org", "@type": "WebSite", "@id": website_id, "url": f"https://{domain}/", "name": site_name, "publisher": {"@id": org_id}})
    if page_schemas.get('about'):
        # Add indentation here vvv
        schemas.append({
            "@context": "https://schema.org",
            "@type": "AboutPage",
            "@id": f"{canon}#webpage",
            "url": canon,
            "name": page_data.get('title'),
            "description": page_data.get('meta_desc'),
            "isPartOf": {"@id": website_id},
            # STACKING MAGIC: Explicitly link this page to the Organization Entity
            "about": {"@id": org_id}, 
            "mainEntity": {"@id": org_id},
            "primaryImageOfPage": {
                "@type": "ImageObject",
                "url": og_image
            }
        })
    if page_data.get('slug') == 'home':
        schemas.append({"@context": "https://schema.org", "@type": "CollectionPage", "@id": f"https://{domain}/#webpage", "url": f"https://{domain}/", "name": page_data.get('meta_title'), "description": page_data.get('meta_desc'), "isPartOf": {"@id": website_id}, "about": {"@id": org_id}, "mainEntity": {"@id": f"https://{domain}/#matchlist"}})
    if page_schemas.get('faq'):
        valid_faqs = [{"@type": "Question", "name": i.get('q'), "acceptedAnswer": {"@type": "Answer", "text": i.get('a')}} for i in page_schemas.get('faq_list', []) if i.get('q') and i.get('a')]
        if valid_faqs: schemas.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": valid_faqs})
            # FIX: Entity Stacking Schema for League Pages
    if page_data.get('layout') == 'league':
        # 1. Breadcrumb
        schemas.append({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"https://{domain}/"},
                {"@type": "ListItem", "position": 2, "name": page_data.get('title'), "item": page_data.get('canonical_url')}
            ]
        })
        # 2. CollectionPage (The Entity Page)
        schemas.append({
            "@context": "https://schema.org", "@type": "CollectionPage",
            "@id": f"{page_data.get('canonical_url')}#webpage",
            "url": page_data.get('canonical_url'),
            "name": page_data.get('title'),
            "isPartOf": {"@id": website_id},
            "about": {"@type": "SportsEvent", "name": f"{page_data.get('title')}"},
            # THIS WAS MISSING: Connects Page to the Dynamic List
            "mainEntity": {"@id": f"{page_data.get('canonical_url')}#events"} 
        })

    html = html.replace('{{SCHEMA_BLOCK}}', f'<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": schemas}, indent=2)}</script>' if schemas else '')
    html = html.replace('{{LOGO_PRELOAD}}', f'<link rel="preload" as="image" href="{s.get("logo_url")}" fetchpriority="high">' if s.get('logo_url') else '')
    html = html.replace('{{HEADER_CLASSES}}', '').replace('{{MAIN_CONTAINER_CLASSES}}', '').replace('{{FOOTER_CLASSES}}', '')

    return html

# ==========================================
# 4. MAIN BUILD PROCESS
# ==========================================
def build_site():
    print("--- 🔨 Starting Build Process ---")
    config = load_json(CONFIG_PATH)
    if not config: 
        print("❌ Config not found!")
        return

    try:
        with open(TEMPLATE_PATH, 'r', encoding='utf-8') as f: master_template_content = f.read()
        with open(WATCH_TEMPLATE_PATH, 'r', encoding='utf-8') as f: watch_template_content = f.read()
        
        # ADD THIS: Load Page Template
        page_template_content = master_template_content # Fallback
        if os.path.exists(PAGE_TEMPLATE_PATH):
            with open(PAGE_TEMPLATE_PATH, 'r', encoding='utf-8') as f: page_template_content = f.read()
            
    except FileNotFoundError:
        print("❌ Template file not found")
        return

    print("📄 Building Pages...")
    
    # Get Theme Contexts
    theme_page_conf = config.get('theme_page', {}) # Get Static Context
    if not theme_page_conf: theme_page_conf = config.get('theme', {})

    # NEW: Load Watch Theme Config
    theme_watch_conf = config.get('theme_watch', {})
    if not theme_watch_conf: theme_watch_conf = config.get('theme', {})

    for page in config.get('pages', []):
        slug = page.get('slug')
        if not slug: continue
        
        layout = page.get('layout')
        
        final_template = master_template_content
        active_theme_override = None

        # ... inside the loop ...
        if layout == 'watch':
            final_template = watch_template_content
            active_theme_override = theme_watch_conf 
            
            # INJECT WATCH CONFIG
            w_conf = config.get('watch_settings', {})
            final_template = final_template.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
            final_template = final_template.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
            final_template = final_template.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
            final_template = final_template.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
            final_template = final_template.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
            final_template = final_template.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
            
            # NEW: Inject SEO Templates into JS Variables
            # We use distinct placeholders so we don't conflict with standard META tags
            final_template = final_template.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}} Live'))
            final_template = final_template.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', 'Watch {{HOME}} vs {{AWAY}} live stream online.'))

            # Fallback for the static page load (before JS runs)
            page['meta_title'] = "Watch Live Sports"
            page['meta_desc'] = "Live sports streaming coverage."
        # ... rest of loop
        elif layout == 'page':
            final_template = page_template_content
            active_theme_override = theme_page_conf # Apply Static Context
        
        # Render
        final_html = render_page(final_template, config, page, theme_override=active_theme_override)
        
        out_dir = os.path.join(OUTPUT_DIR, slug) if slug != 'home' else OUTPUT_DIR
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(final_html)
    
    # ==========================================
    # 5. BUILD LEAGUE PAGES
    # ==========================================
    print("🏆 Building League Pages...")
    
    league_template_content = None
    if os.path.exists(LEAGUE_TEMPLATE_PATH):
        with open(LEAGUE_TEMPLATE_PATH, 'r', encoding='utf-8') as f:
            league_template_content = f.read()
    
    if league_template_content:
        target_country = config.get('site_settings', {}).get('target_country', 'US')
        priorities = config.get('sport_priorities', {}).get(target_country, {})
        articles = config.get('articles', {})
        
        # Get League Theme or fallback
        theme_league = config.get('theme_league', {})
        if not theme_league: theme_league = config.get('theme', {})

        domain = config.get('site_settings', {}).get('domain', 'example.com')

        # Templates from Admin
        tpl_h1 = articles.get('league_h1', 'Watch {{NAME}} Live Streams')
        tpl_intro = articles.get('league_intro', 'Best free {{NAME}} streams online.')
        tpl_live_title = articles.get('league_live_title', 'Live {{NAME}} Matches')
        tpl_upcoming_title = articles.get('league_upcoming_title', 'Upcoming {{NAME}} Schedule')

        for name, data in priorities.items():
            if name.startswith('_') or not data.get('hasLink'): continue
            
            slug = normalize_key(name) + "-streams"
            is_league = data.get('isLeague', False)
            
            # Entity Intelligence (Parent Sport)
            parent_sport = LEAGUE_PARENT_MAP.get(name)
            if not parent_sport:
                lower_name = name.lower()
                if "football" in lower_name or "soccer" in lower_name: parent_sport = "Soccer"
                elif "basket" in lower_name: parent_sport = "Basketball"
                elif "fight" in lower_name: parent_sport = "Combat Sports"
                elif "racing" in lower_name or "motor" in lower_name: parent_sport = "Motorsport"
                else: parent_sport = name

            # 1. Prepare Variables
            vars_map = {'{{NAME}}': name, '{{SPORT}}': parent_sport, '{{YEAR}}': "2025", '{{DOMAIN}}': config['site_settings']['domain']}
            
            def replace_vars(text, v_map):
                if not text: return ""
                for k, v in v_map.items():
                    text = text.replace(k, v)
                return text

            # 2. Define Content & TITLES (Fixes Title Issue)
            p_h1 = replace_vars(articles.get('league_h1', 'Watch {{NAME}} Live'), vars_map)
            p_intro = replace_vars(articles.get('league_intro', ''), vars_map)
            
            # Process Section Titles (NEW FIX)
            sec_live = replace_vars(articles.get('league_live_title', 'Live {{NAME}}'), vars_map)
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
                'schemas': {'org': True, 'website': True}
            }

            # 4. Render
            html = render_page(league_template_content, config, page_data, theme_override=theme_league)
            
            # 5. Injections (Fixes Placeholder Issue)
            html = html.replace('{{PAGE_FILTER}}', name)
            html = html.replace('{{LEAGUE_ARTICLE}}', final_art)
            html = html.replace('{{TEXT_LIVE_SECTION_TITLE}}', sec_live) # Inject Processed Title
            html = html.replace('{{TEXT_UPCOMING_TITLE}}', sec_upc)      # Inject Processed Title
            html = html.replace('{{HERO_PILLS}}', build_menu_html(config.get('menus', {}).get('hero', []), 'hero'))
            
            # 6. Write File
            out_dir = os.path.join(OUTPUT_DIR, slug)
            os.makedirs(out_dir, exist_ok=True)
            with open(os.path.join(out_dir, 'index.html'), 'w', encoding='utf-8') as f:
                f.write(html)
            
            print(f"   -> Built: {slug} (Filter: {name})")

    print("✅ Build Complete.")

if __name__ == "__main__":
    build_site()
