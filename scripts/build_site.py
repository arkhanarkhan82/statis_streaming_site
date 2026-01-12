import json
import os
import re

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
    logo_html = f'<div class="logo-text">{p1}<span>{p2}</span></div>'
    if s.get('logo_url'): logo_html = f'<img src="{s.get("logo_url")}" class="logo-img"> {logo_html}'
    
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

    # Add specific classes for CSS grid handling
    html = f'<div class="footer-grid cols-{cols}">'
    html += get_content(slots[0])
    html += get_content(slots[1])
    if cols == '3': html += get_content(slots[2])
    html += '</div>'
    return html

# ==========================================
# 3. THEME ENGINE (Restored Full Power)
# ==========================================
def apply_theme(html, config, page_data=None, theme_context='home'):
    if page_data is None: page_data = {}
    
    # 1. MERGE THEME CONTEXT
    # Base Theme -> Context Theme (Home/League/Page/Watch)
    THEME = config.get('theme', {}).copy()
    
    if theme_context == 'league':
        THEME.update(config.get('theme_league', {}))
    elif theme_context == 'page':
        THEME.update(config.get('theme_page', {}))
    elif theme_context == 'watch':
        THEME.update(config.get('theme_watch', {}))

    SETTINGS = config.get('site_settings', {})
    MENUS = config.get('menus', {})
    
    # 2. GENERATE DERIVED VARIABLES (Borders, Colors)
    def make_border(w_key, c_key):
        w = ensure_unit(THEME.get(w_key, '1'))
        c = THEME.get(c_key, '#334155')
        return f"{w} solid {c}"

    THEME['sec_border_live'] = make_border('sec_border_live_width', 'sec_border_live_color')
    THEME['sec_border_upcoming'] = make_border('sec_border_upcoming_width', 'sec_border_upcoming_color')
    THEME['sec_border_wildcard'] = make_border('sec_border_wildcard_width', 'sec_border_wildcard_color')
    THEME['sec_border_leagues'] = make_border('sec_border_leagues_width', 'sec_border_leagues_color')
    THEME['sec_border_grouped'] = make_border('sec_border_grouped_width', 'sec_border_grouped_color')
    THEME['sec_border_league_upcoming'] = make_border('sec_border_league_upcoming_width', 'sec_border_league_upcoming_color')
    
    THEME['article_h2_border'] = make_border('article_h2_border_width', 'article_h2_border_color')
    THEME['article_h3_border'] = make_border('article_h3_border_width', 'article_h3_border_color')
    THEME['article_h4_border'] = make_border('article_h4_border_width', 'article_h4_border_color')
    
    THEME['league_card_border'] = make_border('league_card_border_width', 'league_card_border_color')
    THEME['league_card_hover_border'] = make_border('league_card_border_width', 'league_card_hover_border_color')
    THEME['static_h1_border'] = make_border('static_h1_border_width', 'static_h1_border_color')
    THEME['sys_status_border'] = make_border('sys_status_border_width', 'sys_status_border_color')

    # Chat Overlay Opacity
    chat_op = THEME.get('chat_overlay_opacity', '0.9')
    chat_hex = THEME.get('chat_overlay_bg', '#0f172a')
    THEME['chat_overlay_bg_final'] = hex_to_rgba(chat_hex, chat_op)

    # System Status Background
    s_bg_hex = THEME.get('sys_status_bg_color', '#22c55e')
    s_bg_op = THEME.get('sys_status_bg_opacity', '0.1')
    if str(THEME.get('sys_status_bg_transparent', False)).lower() == 'true':
        THEME['sys_status_bg_color'] = 'transparent'
    else:
        THEME['sys_status_bg_color'] = hex_to_rgba(s_bg_hex, s_bg_op)

    # Visibility Toggles
    THEME['sys_status_display'] = 'inline-flex' if THEME.get('sys_status_visible', True) else 'none'

    # Ensure Units
    for key in ['border_radius_base', 'container_max_width', 'header_max_width', 'hero_pill_radius', 
                'button_border_radius', 'logo_image_size', 'section_logo_size', 
                'sys_status_radius', 'sys_status_dot_size', 'league_card_radius', 
                'watch_table_radius', 'chat_dot_size']:
        if key in THEME: THEME[key] = ensure_unit(THEME[key])

    # 3. TEXT REPLACEMENTS
    replacements = {
        'META_TITLE': page_data.get('meta_title', ''),
        'META_DESC': page_data.get('meta_desc', ''),
        'SITE_NAME': f"{SETTINGS.get('title_part_1','')}{SETTINGS.get('title_part_2','')}",
        'CANONICAL_URL': page_data.get('canonical_url', ''),
        'FAVICON': SETTINGS.get('favicon_url', ''),
        'OG_IMAGE': SETTINGS.get('logo_url', ''),
        'H1_TITLE': page_data.get('h1_title', ''),
        'H1_ALIGN': page_data.get('h1_align', THEME.get('static_h1_align', 'left')),
        'HERO_TEXT': page_data.get('hero_text', ''),
        'ARTICLE_CONTENT': page_data.get('article', ''),
        'FOOTER_COPYRIGHT': SETTINGS.get('footer_copyright', ''),
        'THEME_TEXT_SYS_STATUS': THEME.get('text_sys_status', 'System Status: Online'),
        'LOGO_PRELOAD': f'<link rel="preload" as="image" href="{SETTINGS.get("logo_url")}">' if SETTINGS.get('logo_url') else '',
        'API_URL': SETTINGS.get('api_url', ''),
        'TARGET_COUNTRY': SETTINGS.get('target_country', 'US'),
        'PARAM_LIVE': SETTINGS.get('param_live', 'stream'),
        'PARAM_INFO': SETTINGS.get('param_info', 'info'),
        'DOMAIN': SETTINGS.get('domain', ''),
        
        # Text Labels
        'TEXT_LIVE_SECTION_TITLE': THEME.get('text_live_section_title', 'Trending Live'),
        'TEXT_WILDCARD_TITLE': THEME.get('text_wildcard_title', ''),
        'TEXT_TOP_UPCOMING_TITLE': THEME.get('text_top_upcoming_title', 'Top Upcoming'),
        'TEXT_UPCOMING_TITLE': page_data.get('upcoming_title', 'Upcoming Matches'), # For League Pages
        'TEXT_SHOW_MORE': THEME.get('text_show_more', 'Show More'),
        'TEXT_WATCH_BTN': THEME.get('text_watch_btn', 'WATCH'),
        'TEXT_HD_BADGE': THEME.get('text_hd_badge', 'HD'),
        'TEXT_SECTION_LINK': THEME.get('text_section_link', 'View All'),
        'TEXT_SECTION_PREFIX': THEME.get('text_section_prefix', 'Upcoming'),
        'WILDCARD_CATEGORY': THEME.get('wildcard_category', ''),
        'PAGE_FILTER': page_data.get('page_filter', '')
    }

    # Inject Variables {{THEME_KEY}}
    for k, v in THEME.items():
        placeholder = f"{{{{THEME_{k.upper()}}}}}"
        html = html.replace(placeholder, str(v))

    for k, v in replacements.items():
        html = html.replace(f"{{{{{k}}}}}", str(v))

    # 4. STRUCTURAL INJECTIONS
    html = html.replace('{{HEADER_MENU}}', build_menu_html(MENUS.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(MENUS.get('hero', []), 'hero'))
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config, THEME))
    
    # Auto Leagues Footer
    country = SETTINGS.get('target_country', 'US')
    prio = config.get('sport_priorities', {}).get(country, {})
    f_leagues = []
    for k, v in prio.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{k.lower().replace(' ','-').replace('^[^a-z0-9]','')}-streams/"})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))

    # Logo HTML
    p1 = SETTINGS.get('title_part_1', 'Stream')
    p2 = SETTINGS.get('title_part_2', 'East')
    logo_html = f'<div class="logo-text" style="color:{THEME.get("logo_p1_color")};">{p1}<span style="color:{THEME.get("logo_p2_color")};">{p2}</span></div>'
    if SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SETTINGS.get("logo_url")}" class="logo-img" style="box-shadow: 0 0 10px {THEME.get("logo_image_shadow_color","rgba(0,0,0,0)")}"> {logo_html}'
    html = html.replace('{{LOGO_HTML}}', logo_html)

    # 5. HEADER LAYOUT CLASSES
    h_layout = THEME.get('header_layout', 'standard')
    h_icon = THEME.get('header_icon_pos', 'left')
    header_class = f"h-layout-{h_layout}"
    if h_layout == 'center': header_class += f" h-icon-{h_icon}"
    html = html.replace('{{HEADER_CLASSES}}', header_class)
    html = html.replace('{{FOOTER_CLASSES}}', '') # Reserved for future

    # 6. HERO STYLING (Box vs Full)
    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    
    # Background Logic
    h_style = THEME.get('hero_bg_style', 'solid')
    if h_style == 'gradient':
        hero_bg = f"background: radial-gradient(circle at top, {THEME.get('hero_gradient_start')} 0%, {THEME.get('hero_gradient_end')} 100%);"
    elif h_style == 'image':
        hero_bg = f"background: linear-gradient(rgba(0,0,0,{THEME.get('hero_bg_image_overlay_opacity')}), rgba(0,0,0,{THEME.get('hero_bg_image_overlay_opacity')})), url('{THEME.get('hero_bg_image_url')}'); background-size: cover;"
    elif h_style == 'transparent':
        hero_bg = "background: transparent;"
    else:
        hero_bg = f"background: {THEME.get('hero_bg_solid')};"

    # Box Borders
    box_b_str = f"{ensure_unit(THEME.get('hero_box_border_width', '1'))} solid {THEME.get('hero_box_border_color')}"
    box_border_css = ""
    if THEME.get('hero_border_top'): box_border_css += f"border-top: {box_b_str}; "
    if THEME.get('hero_border_bottom_box'): box_border_css += f"border-bottom: {box_b_str}; "
    if THEME.get('hero_border_left'): box_border_css += f"border-left: {box_b_str}; "
    if THEME.get('hero_border_right'): box_border_css += f"border-right: {box_b_str}; "

    # Main Bottom Border
    main_pos = THEME.get('hero_main_border_pos', 'full')
    main_border_str = f"border-bottom: {ensure_unit(THEME.get('hero_main_border_width'))} solid {THEME.get('hero_main_border_color')};" if main_pos != 'none' else ""

    if mode == 'box':
        hero_outer = f"background: transparent; padding: 40px 15px;"
        if main_pos == 'full': hero_outer += f" {main_border_str}"
        hero_inner = f"{hero_bg} max-width: {box_w}; margin: 0 auto; padding: 30px; border-radius: {ensure_unit(THEME.get('border_radius_base'))}; {box_border_css}"
        if main_pos == 'box': hero_inner += f" {main_border_str}"
    else:
        hero_outer = f"{hero_bg} padding: 40px 15px;"
        if main_pos == 'full': hero_outer += f" {main_border_str}"
        hero_inner = f"max-width: {ensure_unit(THEME.get('container_max_width'))}; margin: 0 auto;"

    html = html.replace('{{HERO_OUTER_STYLE}}', hero_outer)
    html = html.replace('{{HERO_INNER_STYLE}}', hero_inner)

    # Hero Alignment
    align = THEME.get('hero_content_align', 'center')
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', align)
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if align == 'center' else ('0' if align == 'left' else '0 0 0 auto'))
    html = html.replace('{{HERO_MENU_DISPLAY}}', THEME.get('hero_menu_visible', 'flex'))
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if align == 'center' else ('flex-start' if align == 'left' else 'flex-end'))
    
    # Hide Hero if needed (for Pages)
    html = html.replace('{{DISPLAY_HERO}}', THEME.get('display_hero', 'block'))

    # 7. JS INJECTIONS
    html = html.replace('{{JS_THEME_CONFIG}}', json.dumps(THEME))
    html = html.replace('{{JS_PRIORITIES}}', json.dumps(prio))
    
    # Load League Map for JS
    l_map = load_json('assets/data/league_map.json')
    reverse_map = {}
    if l_map:
        for l_name, teams in l_map.items():
            for t in teams: reverse_map[t] = l_name
    html = html.replace('{{JS_LEAGUE_MAP}}', json.dumps(reverse_map))
    html = html.replace('{{JS_IMAGE_MAP}}', json.dumps(load_json('assets/data/image_map.json')))

    # 8. WATCH PAGE SPECIFICS
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    html = html.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))
    
    # Default League Article Placeholder
    html = html.replace('{{LEAGUE_ARTICLE}}', '')
    html = html.replace('{{SCHEMA_BLOCK}}', '')

    return html

# ==========================================
# 4. MAIN BUILD PROCESS
# ==========================================
def main():
    print("--- 🔨 Building Site Structure ---")
    config = load_json(CONFIG_PATH)
    if not config: return

    # 1. BUILD PAGES
    print(" > Building Pages...")
    try:
        with open(TEMPLATE_MASTER, 'r', encoding='utf-8') as f: master_tpl = f.read()
        with open(TEMPLATE_WATCH, 'r', encoding='utf-8') as f: watch_tpl = f.read()
        page_tpl = master_tpl # Fallback
        if os.path.exists(TEMPLATE_PAGE):
            with open(TEMPLATE_PAGE, 'r', encoding='utf-8') as f: page_tpl = f.read()
    except Exception as e:
        print(f"Error loading templates: {e}")
        return

    for page in config.get('pages', []):
        slug = page.get('slug')
        layout = page.get('layout', 'page')
        
        # Decide Template & Context
        if layout == 'home':
            tpl = master_tpl
            ctx = 'home'
        elif layout == 'watch':
            tpl = watch_tpl
            ctx = 'watch'
        else:
            tpl = page_tpl
            ctx = 'page'
        
        # Page Data
        p_data = {
            'meta_title': page.get('meta_title'),
            'meta_desc': page.get('meta_desc'),
            'h1_title': page.get('title'),
            'h1_align': page.get('h1_align'),
            'hero_text': page.get('meta_desc'),
            'article': page.get('content'),
            'canonical_url': f"https://{config['site_settings']['domain']}/{slug}/" if slug != 'home' else f"https://{config['site_settings']['domain']}/"
        }
        
        # Render
        html = apply_theme(tpl, config, p_data, ctx)
        
        # Clean up specific placeholders based on layout
        if layout == 'watch':
            html = html.replace('{{DISPLAY_HERO}}', 'none')
        elif layout == 'page':
            html = html.replace('{{DISPLAY_HERO}}', 'none') # Static pages usually use H1 not Hero
            html = html.replace('</head>', '<style>#live-section, #upcoming-container, #grouped-container { display: none !important; }</style></head>')
        
        # Save
        out = OUTPUT_DIR if slug == 'home' else os.path.join(OUTPUT_DIR, slug)
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)

    # 2. BUILD LEAGUE PAGES
    print(" > Building League Skeletons...")
    if os.path.exists(TEMPLATE_LEAGUE):
        with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f: league_tpl = f.read()
        
        country = config['site_settings'].get('target_country', 'US')
        prio = config.get('sport_priorities', {}).get(country, {})
        articles = config.get('articles', {})
        
        for key, settings in prio.items():
            if key.startswith('_') or not settings.get('hasLink'): continue
            
            slug = key.lower().replace(' ', '-').replace('^[^a-z0-9]','') + "-streams"
            is_league = settings.get('isLeague', False)
            tpl_art = articles.get('league') if is_league else articles.get('sport')
            
            # Simple Variable Replacement for Article
            def rep(txt):
                if not txt: return ""
                return txt.replace('{{NAME}}', key).replace('{{YEAR}}', '2025').replace('{{DOMAIN}}', config['site_settings']['domain'])

            p_data = {
                'meta_title': rep(articles.get('league_h1', f"Watch {key} Live")),
                'h1_title': rep(articles.get('league_h1', f"Watch {key} Live")),
                'hero_text': rep(articles.get('league_intro', '')),
                'article': rep(tpl_art),
                'canonical_url': f"https://{config['site_settings']['domain']}/{slug}/",
                'page_filter': key, # Important for JS to filter matches
                'upcoming_title': rep(articles.get('league_upcoming_title', f"Upcoming {key}"))
            }
            
            html = apply_theme(league_tpl, config, p_data, 'league')
            html = html.replace('{{LEAGUE_ARTICLE}}', p_data['article'])
            
            out = os.path.join(OUTPUT_DIR, slug)
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)

    print("✅ Structure Build Complete.")

if __name__ == "__main__":
    main()
