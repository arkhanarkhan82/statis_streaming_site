import json
import os
import re
import shutil

# ==========================================
# 1. CONFIGURATION
# ==========================================
CONFIG_PATH = 'data/config.json'
TEMPLATE_MASTER = 'assets/master_template.html'
TEMPLATE_WATCH = 'assets/watch_template.html'
TEMPLATE_LEAGUE = 'assets/league_template.html'
TEMPLATE_PAGE = 'assets/page_template.html'
OUTPUT_DIR = '.' 

# ==========================================
# 2. UTILS
# ==========================================
def load_json(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f: return json.load(f)
    return {}

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

def slugify(text):
    if not text: return ""
    clean = str(text).lower()
    clean = re.sub(r"[^\w\s-]", "", clean)
    clean = re.sub(r"\s+", "-", clean)
    return clean.strip("-")

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

# ==========================================
# 3. THEME ENGINE
# ==========================================
def apply_theme(html, config, page_data=None):
    if page_data is None: page_data = {}
    THEME = config.get('theme', {})
    SETTINGS = config.get('site_settings', {})
    MENUS = config.get('menus', {})
    
    # 1. Variable Map
    vars = {
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
        
        'header_bg': 'THEME_HEADER_BG', 'header_text_color': 'THEME_HEADER_TEXT_COLOR',
        'header_link_active_color': 'THEME_HEADER_LINK_ACTIVE_COLOR',
        'header_link_hover_color': 'THEME_HEADER_LINK_HOVER_COLOR',
        'header_highlight_color': 'THEME_HEADER_HIGHLIGHT_COLOR',
        'header_border_bottom': 'THEME_HEADER_BORDER_BOTTOM',
        'logo_p1_color': 'THEME_LOGO_P1_COLOR', 'logo_p2_color': 'THEME_LOGO_P2_COLOR',
        'logo_image_size': 'THEME_LOGO_IMAGE_SIZE',
        
        'hero_h1_color': 'THEME_HERO_H1_COLOR', 'hero_intro_color': 'THEME_HERO_INTRO_COLOR',
        'hero_pill_bg': 'THEME_HERO_PILL_BG', 'hero_pill_text': 'THEME_HERO_PILL_TEXT',
        'hero_pill_hover_bg': 'THEME_HERO_PILL_HOVER_BG', 'hero_pill_hover_text': 'THEME_HERO_PILL_HOVER_TEXT',
        'text_sys_status': 'THEME_TEXT_SYS_STATUS',
        
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
        'match_row_btn_copy_link_color': 'THEME_MATCH_ROW_BTN_COPY_LINK_COLOR',

        'footer_bg_start': 'THEME_FOOTER_BG_START', 'footer_bg_end': 'THEME_FOOTER_BG_END',
        'footer_border_top': 'THEME_FOOTER_BORDER_TOP', 'footer_link_color': 'THEME_FOOTER_LINK_COLOR',
        'footer_link_hover_color': 'THEME_FOOTER_LINK_HOVER_COLOR',
        'footer_copyright_color': 'THEME_FOOTER_COPYRIGHT_COLOR',
        'footer_desc_color': 'THEME_FOOTER_DESC_COLOR',
        'footer_heading_color': 'THEME_FOOTER_HEADING_COLOR',
        
        'article_bg': 'THEME_ARTICLE_BG', 'article_text': 'THEME_ARTICLE_TEXT',
        'article_line_height': 'THEME_ARTICLE_LINE_HEIGHT', 'article_bullet_color': 'THEME_ARTICLE_BULLET_COLOR',
        'article_link_color': 'THEME_ARTICLE_LINK_COLOR', 'article_h2_color': 'THEME_ARTICLE_H2_COLOR',
        'article_h2_border_color': 'THEME_ARTICLE_H2_BORDER', 'article_h3_color': 'THEME_ARTICLE_H3_COLOR',
        'article_h4_color': 'THEME_ARTICLE_H4_COLOR',
        
        'social_sidebar_bg': 'THEME_SOCIAL_SIDEBAR_BG', 'social_sidebar_border': 'THEME_SOCIAL_SIDEBAR_BORDER',
        'social_btn_bg': 'THEME_SOCIAL_BTN_BG', 'social_btn_color': 'THEME_SOCIAL_BTN_COLOR',
        'mobile_footer_bg': 'THEME_MOBILE_FOOTER_BG', 'mobile_footer_border_top': 'THEME_MOBILE_FOOTER_BORDER_TOP',
        
        'back_to_top_bg': 'THEME_BACK_TO_TOP_BG', 'back_to_top_icon_color': 'THEME_BACK_TO_TOP_ICON_COLOR',
        'sys_status_bg_color': 'THEME_SYS_STATUS_BG_COLOR', 'sys_status_border_color': 'THEME_SYS_STATUS_BORDER',
        'sys_status_text_color': 'THEME_SYS_STATUS_TEXT_COLOR', 'sys_status_dot_color': 'THEME_SYS_STATUS_DOT_COLOR',
        'sys_status_radius': 'THEME_SYS_STATUS_RADIUS', 'section_logo_size': 'THEME_SECTION_LOGO_SIZE',
        
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
        'watch_server_text': 'THEME_WATCH_SERVER_TEXT',
        
        'league_card_bg': 'THEME_LEAGUE_CARD_BG', 'league_card_text': 'THEME_LEAGUE_CARD_TEXT',
        'league_card_border_color': 'THEME_LEAGUE_CARD_BORDER', 'league_card_radius': 'THEME_LEAGUE_CARD_RADIUS',
        'league_card_hover_bg': 'THEME_LEAGUE_CARD_HOVER_BG', 'league_card_hover_text': 'THEME_LEAGUE_CARD_HOVER_TEXT',
        'league_card_hover_border_color': 'THEME_LEAGUE_CARD_HOVER_BORDER'
    }

    # Apply Variable Replacements
    for json_key, tpl_key in vars.items():
        val = THEME.get(json_key, '')
        if 'radius' in json_key or 'size' in json_key or 'width' in json_key: val = ensure_unit(val)
        if json_key == 'sys_status_bg_color':
            op = THEME.get('sys_status_bg_opacity', '0.1')
            if THEME.get('sys_status_bg_transparent'): val = 'transparent'
            else: val = hex_to_rgba(val, op)
        if json_key == 'chat_overlay_bg':
             val = hex_to_rgba(THEME.get('chat_overlay_bg', '#000000'), THEME.get('chat_overlay_opacity', '0.9'))
             html = html.replace('{{THEME_CHAT_OVERLAY_BG_FINAL}}', val)
        if 'border_color' in json_key and 'league' in json_key: 
             w = ensure_unit(THEME.get('league_card_border_width', '1'))
             val = f"{w} solid {val}"

        html = html.replace(f'{{{{{tpl_key}}}}}', str(val))

    # Apply Borders
    for sec in ['live', 'upcoming', 'wildcard', 'leagues', 'grouped', 'league_upcoming']:
        w = ensure_unit(THEME.get(f'sec_border_{sec}_width', '1'))
        c = THEME.get(f'sec_border_{sec}_color', '#334155')
        html = html.replace(f'{{{{THEME_SEC_BORDER_{sec.upper()}}}}}', f'{w} solid {c}')

    # Apply Text Labels
    html = html.replace('{{TEXT_LIVE_SECTION_TITLE}}', THEME.get('text_live_section_title', 'Trending Live'))
    html = html.replace('{{TEXT_UPCOMING_TITLE}}', THEME.get('text_top_upcoming_title', 'Upcoming Matches'))
    html = html.replace('{{TEXT_SHOW_MORE}}', THEME.get('text_show_more', 'Show More'))
    html = html.replace('{{TEXT_WATCH_BTN}}', THEME.get('text_watch_btn', 'WATCH'))
    html = html.replace('{{TEXT_HD_BADGE}}', THEME.get('text_hd_badge', 'HD'))
    html = html.replace('{{TEXT_SECTION_LINK}}', THEME.get('text_section_link', 'View All'))
    html = html.replace('{{TEXT_SECTION_PREFIX}}', THEME.get('text_section_prefix', 'Upcoming'))
    
    # Hero Layout Logic
    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    b_w = ensure_unit(THEME.get('hero_box_border_width', '1'))
    b_c = THEME.get('hero_box_border_color', '#333')
    
    bg_style = THEME.get('hero_bg_style', 'solid')
    if bg_style == 'solid': bg_css = f"background: {THEME.get('hero_bg_solid')};"
    elif bg_style == 'gradient': bg_css = f"background: radial-gradient(circle at top, {THEME.get('hero_gradient_start')} 0%, {THEME.get('hero_gradient_end')} 100%);"
    elif bg_style == 'image': bg_css = f"background: url('{THEME.get('hero_bg_image_url')}'); background-size: cover;"
    else: bg_css = "background: transparent;"

    if mode == 'box':
        outer_style = "padding: 40px 15px;"
        inner_style = f"max-width: {box_w}; margin: 0 auto; {bg_css} padding: 30px; border-radius: var(--border-radius-base); border: {b_w} solid {b_c};"
    else:
        outer_style = f"{bg_css} padding: 40px 15px 15px 15px;"
        inner_style = "max-width: var(--container-max-width); margin: 0 auto;"

    html = html.replace('{{HERO_OUTER_STYLE}}', outer_style)
    html = html.replace('{{HERO_INNER_STYLE}}', inner_style)
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', THEME.get('hero_content_align', 'center'))
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if THEME.get('hero_content_align')=='center' else 'flex-start')
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if THEME.get('hero_content_align')=='center' else 'flex-start')
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if THEME.get('hero_content_align')=='center' else '0')
    html = html.replace('{{DISPLAY_HERO}}', THEME.get('display_hero', 'block'))
    html = html.replace('{{HERO_MENU_DISPLAY}}', THEME.get('hero_menu_visible', 'flex'))
    html = html.replace('{{WILDCARD_CATEGORY}}', THEME.get('wildcard_category', ''))
    html = html.replace('{{TEXT_WILDCARD_TITLE}}', THEME.get('text_wildcard_title', ''))
    html = html.replace('{{THEME_TEXT_SYS_STATUS}}', THEME.get('text_sys_status', 'System Status: Online'))
    html = html.replace('{{THEME_SYS_STATUS_DISPLAY}}', 'inline-flex' if THEME.get('sys_status_visible') else 'none')

    # Socials & Colors
    html = html.replace('{{THEME_SOCIAL_TELEGRAM_COLOR}}', THEME.get('social_telegram_color', '#0088cc'))
    html = html.replace('{{THEME_SOCIAL_WHATSAPP_COLOR}}', THEME.get('social_whatsapp_color', '#25D366'))
    html = html.replace('{{THEME_SOCIAL_REDDIT_COLOR}}', THEME.get('social_reddit_color', '#FF4500'))
    html = html.replace('{{THEME_SOCIAL_TWITTER_COLOR}}', THEME.get('social_twitter_color', '#1DA1F2'))
    html = html.replace('{{THEME_SOCIAL_DESKTOP_TOP}}', THEME.get('social_desktop_top', '50%'))
    html = html.replace('{{THEME_SOCIAL_DESKTOP_SCALE}}', THEME.get('social_desktop_scale', '1.0'))
    html = html.replace('{{THEME_MOBILE_FOOTER_HEIGHT}}', THEME.get('mobile_footer_height', '60px'))

    # Watch Page Specifics
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

    # Watch Ads & SEO (from config.watch_settings)
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    html = html.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))

    # Branding & SEO
    p1 = SETTINGS.get('title_part_1', 'Stream')
    p2 = SETTINGS.get('title_part_2', 'East')
    site_name = f"{p1}{p2}"
    
    logo_html = f'<div class="logo-text">{p1}<span>{p2}</span></div>'
    if SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SETTINGS.get("logo_url")}" class="logo-img"> {logo_html}'
        html = html.replace('{{LOGO_PRELOAD}}', f'<link rel="preload" as="image" href="{SETTINGS.get("logo_url")}">')
    else:
        html = html.replace('{{LOGO_PRELOAD}}', '')

    html = html.replace('{{LOGO_HTML}}', logo_html)
    config['_generated_logo_html'] = logo_html # Store for Footer
    
    html = html.replace('{{SITE_NAME}}', site_name)
    html = html.replace('{{DOMAIN}}', SETTINGS.get('domain', 'example.com'))
    html = html.replace('{{CANONICAL_URL}}', page_data.get('canonical_url', f"https://{SETTINGS.get('domain', 'example.com')}/"))
    html = html.replace('{{FAVICON}}', SETTINGS.get('favicon_url', ''))
    html = html.replace('{{OG_IMAGE}}', SETTINGS.get('logo_url', ''))
    html = html.replace('{{OG_MIME}}', 'image/png')
    
    html = html.replace('{{META_TITLE}}', page_data.get('meta_title', site_name))
    html = html.replace('{{META_DESC}}', page_data.get('meta_desc', ''))
    html = html.replace('{{META_KEYWORDS}}', f'<meta name="keywords" content="{page_data.get("meta_keywords","")}">' if page_data.get("meta_keywords") else '')
    html = html.replace('{{THEME_META_COLOR}}', THEME.get('header_bg', '#000000'))
    html = html.replace('{{SCHEMA_BLOCK}}', '') 

    # Content Replacement with SAFETY CHECKS
    html = html.replace('{{H1_TITLE}}', page_data.get('h1_title') or site_name)
    html = html.replace('{{H1_ALIGN}}', page_data.get('h1_align') or 'left')
    html = html.replace('{{HERO_TEXT}}', page_data.get('hero_text') or '')
    html = html.replace('{{ARTICLE_CONTENT}}', page_data.get('article') or '')
    
    # Menus
    html = html.replace('{{HEADER_MENU}}', build_menu_html(MENUS.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(MENUS.get('hero', []), 'hero'))
    
    # Footer Links (Static + Auto Leagues)
    f_leagues = []
    country = SETTINGS.get('target_country', 'US')
    prio = config.get('sport_priorities', {}).get(country, {})
    for k, v in prio.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{slugify(k)}-streams/"})
    
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))
    
    # Footer Grid (requires config with logo html)
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config)) 
    html = html.replace('{{FOOTER_COPYRIGHT}}', SETTINGS.get('footer_copyright', ''))
    
    # Static Params
    html = html.replace('{{PARAM_LIVE}}', SETTINGS.get('param_live', 'stream'))
    html = html.replace('{{PARAM_INFO}}', SETTINGS.get('param_info', 'info'))
    html = html.replace('{{TARGET_COUNTRY}}', country)

    return html

# ==========================================
# 4. MAIN BUILD PROCESS
# ==========================================
def main():
    print("--- 🔨 Building Site Structure ---")
    config = load_json(CONFIG_PATH)
    if not config: return

    # 1. BUILD HOMEPAGE (index.html)
    print(" > Building Index...")
    with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: master_tpl = f.read()
    
    p_home = next((p for p in config.get('pages',[]) if p.get('slug')=='home'), {})
    home_html = apply_theme(master_tpl, config, {
        'meta_title': p_home.get('meta_title'),
        'meta_desc': p_home.get('meta_desc'),
        'h1_title': p_home.get('title'),
        'h1_align': p_home.get('h1_align'),
        'hero_text': p_home.get('meta_desc'),
        'article': p_home.get('content'),
        'canonical_url': f"https://{config['site_settings']['domain']}/"
    })
    
    with open('index.html', 'w', encoding='utf-8') as f: f.write(home_html)

    # 2. BUILD WATCH PAGE (watch/index.html)
    print(" > Building Watch Page...")
    with open(TEMPLATE_WATCH, 'r', encoding='utf-8') as f: watch_tpl = f.read()
    
    # Apply theme variables to watch template
    watch_html = apply_theme(watch_tpl, config, {})
    
    # Ensure directory exists
    os.makedirs('watch', exist_ok=True)
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(watch_html)

    # 3. BUILD LEAGUE PAGES (Skeletons)
    print(" > Building League Skeletons...")
    with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f: league_tpl = f.read()
    
    country = config['site_settings'].get('target_country', 'US')
    prio = config.get('sport_priorities', {}).get(country, {})
    articles = config.get('articles', {})
    
    for key, settings in prio.items():
        if key.startswith('_') or not settings.get('hasLink'): continue
        
        slug = slugify(key) + "-streams"
        
        # Metadata logic
        is_league = settings.get('isLeague', False)
        tpl_art = articles.get('league') if is_league else articles.get('sport')
        
        def rep(txt):
            if not txt: return ""
            return txt.replace('{{NAME}}', key).replace('{{YEAR}}', '2025').replace('{{DOMAIN}}', config['site_settings']['domain'])

        p_data = {
            'meta_title': rep(articles.get('league_h1', f"Watch {key} Live")),
            'h1_title': rep(articles.get('league_h1', f"Watch {key} Live")),
            'hero_text': rep(articles.get('league_intro', '')),
            'article': rep(tpl_art),
            'canonical_url': f"https://{config['site_settings']['domain']}/{slug}/"
        }
        
        html = apply_theme(league_tpl, config, p_data)
        
        # Inject League Specifics (Placeholders)
        html = html.replace('{{PAGE_FILTER}}', key)
        html = html.replace('{{LEAGUE_ARTICLE}}', p_data['article'])
        html = html.replace('{{TEXT_LIVE_SECTION_TITLE}}', rep(articles.get('league_live_title', f"Live {key}")))
        html = html.replace('{{TEXT_UPCOMING_TITLE}}', rep(articles.get('league_upcoming_title', f"Upcoming {key}")))
        
        out = os.path.join(OUTPUT_DIR, slug)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)

    # 4. BUILD STATIC PAGES (About, Contact, etc)
    print(" > Building Static Pages...")
    if os.path.exists(TEMPLATE_PAGE):
        with open(TEMPLATE_PAGE, 'r', encoding='utf-8') as f: page_tpl = f.read()
        
        for p in config.get('pages', []):
            if p.get('slug') == 'home' or p.get('layout') == 'watch': continue
            
            p_data = {
                'meta_title': p.get('meta_title', p['title']),
                'meta_desc': p.get('meta_desc', ''),
                'h1_title': p.get('title'),
                'h1_align': p.get('h1_align', 'left'),
                'hero_text': '', 
                'article': p.get('content', ''),
                'canonical_url': f"https://{config['site_settings']['domain']}/{p['slug']}/"
            }
            
            html = apply_theme(page_tpl, config, p_data)
            
            out = os.path.join(OUTPUT_DIR, p['slug'])
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)

    print("✅ Structure Build Complete.")

if __name__ == "__main__":
    main()
