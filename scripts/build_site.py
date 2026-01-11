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

def build_footer_grid(cfg):
    t = cfg.get('theme', {})
    s = cfg.get('site_settings', {})
    m = cfg.get('menus', {})
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

    html = f'<div class="footer-grid" style="display:grid; gap:30px; grid-template-columns: repeat({cols}, 1fr);">'
    html += get_content(slots[0])
    html += get_content(slots[1])
    if cols == '3': html += get_content(slots[2])
    html += '</div>'
    return html

# ==========================================
# 3. THEME ENGINE
# ==========================================
def apply_theme(html, config, page_data=None):
    if page_data is None: page_data = {}
    THEME = config.get('theme', {})
    SETTINGS = config.get('site_settings', {})
    MENUS = config.get('menus', {})
    
    # Generate Variables
    def get_theme_val(key, default=''):
        val = THEME.get(key, default)
        if 'radius' in key or 'size' in key or 'width' in key: return ensure_unit(val)
        return str(val)

    # Basic Text Replacements
    replacements = {
        'META_TITLE': page_data.get('meta_title', ''),
        'META_DESC': page_data.get('meta_desc', ''),
        'SITE_NAME': f"{SETTINGS.get('title_part_1','')}{SETTINGS.get('title_part_2','')}",
        'CANONICAL_URL': page_data.get('canonical_url', ''),
        'FAVICON': SETTINGS.get('favicon_url', ''),
        'OG_IMAGE': SETTINGS.get('logo_url', ''),
        'H1_TITLE': page_data.get('h1_title', ''),
        'HERO_TEXT': page_data.get('hero_text', ''),
        'ARTICLE_CONTENT': page_data.get('article', ''),
        'FOOTER_COPYRIGHT': SETTINGS.get('footer_copyright', ''),
        'THEME_TEXT_SYS_STATUS': THEME.get('text_sys_status', 'System Status: Online'),
        'LOGO_PRELOAD': f'<link rel="preload" as="image" href="{SETTINGS.get("logo_url")}">' if SETTINGS.get('logo_url') else ''
    }

    # Theme CSS Variables Injection
    # We iterate config.theme and replace {{THEME_KEY_UPPER}}
    for k, v in THEME.items():
        placeholder = f"{{{{THEME_{k.upper()}}}}}"
        html = html.replace(placeholder, get_theme_val(k))

    # Apply Manual Replacements
    for k, v in replacements.items():
        html = html.replace(f"{{{{{k}}}}}", v)

    # Menus
    html = html.replace('{{HEADER_MENU}}', build_menu_html(MENUS.get('header', []), 'header'))
    html = html.replace('{{HERO_PILLS}}', build_menu_html(MENUS.get('hero', []), 'hero'))
    
    # Footer Grid & Auto Leagues
    html = html.replace('{{FOOTER_GRID_CONTENT}}', build_footer_grid(config))
    
    # Footer Auto-Leagues (Based on Priority)
    country = SETTINGS.get('target_country', 'US')
    prio = config.get('sport_priorities', {}).get(country, {})
    f_leagues = []
    for k, v in prio.items():
        if not k.startswith('_') and v.get('hasLink'):
            f_leagues.append({'title': k, 'url': f"/{k.lower().replace(' ','-')}-streams/"})
    html = html.replace('{{FOOTER_LEAGUES}}', build_menu_html(f_leagues, 'footer_leagues'))

    # Logo HTML
    p1 = SETTINGS.get('title_part_1', 'Stream')
    p2 = SETTINGS.get('title_part_2', 'East')
    logo_html = f'<div class="logo-text" style="color:{THEME.get("logo_p1_color")};">{p1}<span style="color:{THEME.get("logo_p2_color")};">{p2}</span></div>'
    if SETTINGS.get('logo_url'): 
        logo_html = f'<img src="{SETTINGS.get("logo_url")}" class="logo-img"> {logo_html}'
    html = html.replace('{{LOGO_HTML}}', logo_html)

    # Hero Styling Logic (Box vs Full)
    mode = THEME.get('hero_layout_mode', 'full')
    box_w = ensure_unit(THEME.get('hero_box_width', '1000px'))
    if mode == 'box':
        html = html.replace('{{HERO_OUTER_STYLE}}', 'padding: 40px 15px;')
        html = html.replace('{{HERO_INNER_STYLE}}', f'max-width: {box_w}; margin: 0 auto; background: {THEME.get("hero_bg_solid")}; padding: 30px; border-radius: {ensure_unit(THEME.get("border_radius_base"))};')
    else:
        html = html.replace('{{HERO_OUTER_STYLE}}', f'background: {THEME.get("hero_bg_solid")}; padding: 40px 15px;')
        html = html.replace('{{HERO_INNER_STYLE}}', f'max-width: {ensure_unit(THEME.get("container_max_width"))}; margin: 0 auto;')

    # Hero Alignment
    align = THEME.get('hero_content_align', 'center')
    html = html.replace('{{THEME_HERO_TEXT_ALIGN}}', align)
    html = html.replace('{{THEME_HERO_ALIGN_ITEMS}}', 'center' if align == 'center' else 'flex-start')
    html = html.replace('{{THEME_HERO_MENU_JUSTIFY}}', 'center' if align == 'center' else 'flex-start')
    html = html.replace('{{THEME_HERO_INTRO_MARGIN}}', '0 auto' if align == 'center' else '0')
    html = html.replace('{{HERO_MENU_DISPLAY}}', THEME.get('hero_menu_visible', 'flex'))
    
    # Hide Hero if needed
    html = html.replace('{{DISPLAY_HERO}}', THEME.get('display_hero', 'block'))

    # Watch Page Specifics (Ad placeholders)
    w_conf = config.get('watch_settings', {})
    html = html.replace('{{WATCH_AD_MOBILE}}', w_conf.get('ad_mobile', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_1}}', w_conf.get('ad_sidebar_1', ''))
    html = html.replace('{{WATCH_AD_SIDEBAR_2}}', w_conf.get('ad_sidebar_2', ''))
    html = html.replace('{{WATCH_ARTICLE}}', w_conf.get('article', ''))
    html = html.replace('{{SUPABASE_URL}}', w_conf.get('supabase_url', ''))
    html = html.replace('{{SUPABASE_KEY}}', w_conf.get('supabase_key', ''))
    html = html.replace('{{JS_WATCH_TITLE_TPL}}', w_conf.get('meta_title', 'Watch {{HOME}} vs {{AWAY}}'))
    html = html.replace('{{JS_WATCH_DESC_TPL}}', w_conf.get('meta_desc', ''))
    
    # Params
    html = html.replace('{{PARAM_LIVE}}', SETTINGS.get('param_live', 'stream'))
    html = html.replace('{{PARAM_INFO}}', SETTINGS.get('param_info', 'info'))
    html = html.replace('{{TARGET_COUNTRY}}', country)

    # Empty Schema Block (Master Engine fills specific match schema)
    html = html.replace('{{SCHEMA_BLOCK}}', '') 

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
    
    # Pass Data to Renderer
    home_html = apply_theme(master_tpl, config, {
        'meta_title': p_home.get('meta_title'),
        'meta_desc': p_home.get('meta_desc'),
        'h1_title': p_home.get('title'),
        'hero_text': p_home.get('meta_desc'),
        'article': p_home.get('content'),
        'canonical_url': f"https://{config['site_settings']['domain']}/"
    })
    
    with open('index.html', 'w', encoding='utf-8') as f: f.write(home_html)

    # 2. BUILD WATCH PAGE (watch/index.html)
    print(" > Building Watch Page...")
    with open(TEMPLATE_WATCH, 'r', encoding='utf-8') as f: watch_tpl = f.read()
    watch_html = apply_theme(watch_tpl, config, {})
    os.makedirs('watch', exist_ok=True)
    with open('watch/index.html', 'w', encoding='utf-8') as f: f.write(watch_html)

    # 3. BUILD LEAGUE PAGES (Skeletons)
    print(" > Building League Skeletons...")
    if os.path.exists(TEMPLATE_LEAGUE):
        with open(TEMPLATE_LEAGUE, 'r', encoding='utf-8') as f: league_tpl = f.read()
        
        country = config['site_settings'].get('target_country', 'US')
        prio = config.get('sport_priorities', {}).get(country, {})
        articles = config.get('articles', {})
        
        for key, settings in prio.items():
            if key.startswith('_') or not settings.get('hasLink'): continue
            
            slug = key.lower().replace(' ', '-') + "-streams"
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
            
            # The Engine will look for these IDs to inject specific league matches
            # The structure is already in the template, so we just write it out.
            
            out = os.path.join(OUTPUT_DIR, slug)
            os.makedirs(out, exist_ok=True)
            with open(os.path.join(out, 'index.html'), 'w', encoding='utf-8') as f: f.write(html)

    print("✅ Structure Build Complete.")

if __name__ == "__main__":
    main()
