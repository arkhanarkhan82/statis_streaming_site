// ==========================================
// 1. CONFIGURATION
// ==========================================
const REPO_OWNER = 'arkhanarkhan82'; 
const REPO_NAME = 'statis_streaming_site';     
const FILE_PATH = 'data/config.json';
const LEAGUE_FILE_PATH = 'assets/data/league_map.json'; 
const BRANCH = 'main';

// ==========================================
// 2. DEFAULT DATA
// ==========================================
const DEFAULT_PRIORITIES = {
    US: {
        _HIDE_OTHERS: false,
        _BOOST: "Super Bowl, Playoffs, Finals",
        "NFL": { score: 100, isLeague: true, hasLink: true, isHidden: false },
        "NBA": { score: 99, isLeague: true, hasLink: true, isHidden: false },
        "NCAA": { score: 98, isLeague: true, hasLink: true, isHidden: false },
        "MLB": { score: 97, isLeague: true, hasLink: true, isHidden: false },
        "NHL": { score: 96, isLeague: true, hasLink: true, isHidden: false },
        "UFC": { score: 95, isLeague: true, hasLink: true, isHidden: false },
        "Premier League": { score: 90, isLeague: true, hasLink: true, isHidden: false },
        "Champions League": { score: 89, isLeague: true, hasLink: true, isHidden: false },
        "Formula 1": { score: 88, isLeague: true, hasLink: true, isHidden: false },
        "MLS": { score: 87, isLeague: true, hasLink: true, isHidden: false },
        "Africa Cup of Nations": { score: 86, isLeague: true, hasLink: true, isHidden: false },
        "La Liga": { score: 85, isLeague: true, hasLink: true, isHidden: false },
        "Liga MX": { score: 84, isLeague: true, hasLink: false, isHidden: false },
        "Football": { score: 79, isLeague: false, hasLink: false, isHidden: false },
        "Basketball": { score: 78, isLeague: false, hasLink: false, isHidden: false },
        "Baseball": { score: 77, isLeague: false, hasLink: false, isHidden: false },
        "Fighting": { score: 76, isLeague: false, hasLink: false, isHidden: false },
        "Soccer": { score: 60, isLeague: false, hasLink: false, isHidden: false },
        "Tennis": { score: 40, isLeague: false, hasLink: true, isHidden: false },
        "Golf": { score: 30, isLeague: false, hasLink: false, isHidden: false }
    },
    UK: {
        _HIDE_OTHERS: false,
        _BOOST: "Final, Derby",
        "Premier League": { score: 100, isLeague: true, hasLink: true, isHidden: false },
        "Champions League": { score: 99, isLeague: true, hasLink: true, isHidden: false },
        "Championship": { score: 98, isLeague: true, hasLink: true, isHidden: false },
        "Africa Cup of Nations": { score: 97, isLeague: true, hasLink: true, isHidden: false },
        "Scottish Premiership": { score: 96, isLeague: true, hasLink: true, isHidden: false },
        "Europa League": { score: 95, isLeague: true, hasLink: true, isHidden: false },
        "FA Cup": { score: 94, isLeague: true, hasLink: true, isHidden: false },
        "LaLiga": { score: 90, isLeague: true, hasLink: true, isHidden: false },
        "Serie A": { score: 89, isLeague: true, hasLink: true, isHidden: false },
        "Bundesliga": { score: 88, isLeague: true, hasLink: true, isHidden: false },
        "National League": { score: 85, isLeague: true, hasLink: true, isHidden: false },
        "Formula 1": { score: 84, isLeague: true, hasLink: true, isHidden: false },
        "Rugby": { score: 80, isLeague: false, hasLink: true, isHidden: false },
        "Cricket": { score: 79, isLeague: false, hasLink: true, isHidden: false },
        "Darts": { score: 78, isLeague: false, hasLink: true, isHidden: false },
        "Snooker": { score: 77, isLeague: false, hasLink: true, isHidden: false },
        "Boxing": { score: 75, isLeague: false, hasLink: true, isHidden: false },
        "NFL": { score: 70, isLeague: true, hasLink: true, isHidden: false },
        "Soccer": { score: 60, isLeague: false, hasLink: false, isHidden: false }
    }
};

const DEMO_CONFIG = {
    site_settings: {
        title_part_1: "Stream", title_part_2: "East", domain: "streameast.to",
        logo_url: "", target_country: "US"
    },
    social_sharing: {
        counts: { telegram: 1200, whatsapp: 800, reddit: 300, twitter: 500 },
        excluded_pages: "dmca,contact,about,privacy"
    },
    theme: {
        brand_primary: "#D00000", brand_dark: "#8a0000", accent_gold: "#FFD700",
        bg_body: "#050505", font_family_base: "system-ui"
    },
    theme_league: {}, 
articles: { league: "", sport: "", excluded: "" },
    sport_priorities: JSON.parse(JSON.stringify(DEFAULT_PRIORITIES)), 
    menus: { header: [], hero: [], footer_static: [] },
    pages: [
        { id: "p_home", title: "Home", slug: "home", layout: "home", meta_title: "Live Sports", content: "Welcome", schemas: { org: true, website: true } }
    ]
};

// --- MAPPING FOR THEME DESIGNER ---
// JSON Key -> HTML ID
const THEME_FIELDS = {
    // 1. Typography & Base
    'font_family_base': 'themeFontBase',
    'font_family_headings': 'themeFontHeadings',
    'border_radius_base': 'themeBorderRadius',
    'container_max_width': 'themeMaxWidth',
    'static_h1_color': 'themeStaticH1Color',
    'static_h1_align': 'pageH1Align',
    // ... existing fields ...
    'static_h1_border_width': 'themeStaticH1BorderWidth',
    'static_h1_border_color': 'themeStaticH1BorderColor',

    'sys_status_visible': 'themeSysStatusVisible', // Checkbox
    'sys_status_bg_opacity': 'themeSysStatusBgOpacity',
    'sys_status_bg_transparent': 'themeSysStatusBgTransparent',
    
    'sys_status_text_color': 'themeSysStatusText',
    'sys_status_bg_color': 'themeSysStatusBg',
    'sys_status_border_color': 'themeSysStatusBorderColor',
    'sys_status_border_width': 'themeSysStatusBorderWidth',
    'sys_status_radius': 'themeSysStatusRadius',
    'sys_status_dot_color': 'themeSysStatusDotColor',
    'sys_status_dot_size': 'themeSysStatusDotSize',
    // FOOTER LEAGUE CARDS
    'league_card_bg': 'themeLeagueCardBg',
    'league_card_text': 'themeLeagueCardText',
    'league_card_border_color': 'themeLeagueCardBorder',
    'league_card_border_width': 'themeLeagueCardBorderWidth',
    'league_card_radius': 'themeLeagueCardRadius',
    
    'league_card_hover_bg': 'themeLeagueCardHoverBg',
    'league_card_hover_text': 'themeLeagueCardHoverText',
    'league_card_hover_border_color': 'themeLeagueCardHoverBorder',
    
    // 2. Palette
    'brand_primary': 'themeBrandPrimary',
    'brand_dark': 'themeBrandDark',
    'accent_gold': 'themeAccentGold',
    'status_green': 'themeStatusGreen',
    'bg_body': 'themeBgBody',
    'bg_panel': 'themeBgPanel',
    'text_main': 'themeTextMain',
    'text_muted': 'themeTextMuted',
    'border_color': 'themeBorderColor',
    'scrollbar_thumb_color': 'themeScrollThumb',

    // 3. Header
    'header_bg': 'themeHeaderBg',
    'header_text_color': 'themeHeaderText',
    'header_link_active_color': 'themeHeaderActive',
    'header_max_width': 'themeHeaderWidth',
    'logo_p1_color': 'themeLogoP1',
    'logo_p2_color': 'themeLogoP2',
    'header_border_bottom': 'themeHeaderBorderBottom',
    'header_layout': 'themeHeaderLayout',       // NEW
    'header_icon_pos': 'themeHeaderIconPos',    // NEW
    'header_link_hover_color': 'themeHeaderHover', // NEW
    'header_highlight_color': 'themeHeaderHighlightColor',
    'header_highlight_hover': 'themeHeaderHighlightHover',

    // 4. Hero
    'hero_bg_style': 'themeHeroBgStyle',
    'hero_bg_solid': 'themeHeroBgSolid',
    'hero_gradient_start': 'themeHeroGradStart',
    'hero_gradient_end': 'themeHeroGradEnd',
    'hero_bg_image_url': 'themeHeroBgImage',
    'hero_bg_image_overlay_opacity': 'themeHeroOverlayOpacity',
    'hero_h1_color': 'themeHeroH1',
    'hero_intro_color': 'themeHeroIntro',
    'hero_pill_bg': 'themeHeroPillBg',
    'hero_pill_text': 'themeHeroPillText',
    'hero_pill_hover_bg': 'themeHeroPillActiveBg',
    'hero_pill_hover_text': 'themeHeroPillActiveText',
    // ... inside THEME_FIELDS ...
    'hero_border_bottom': 'themeHeroBorderBottom', // NEW
    // ... inside THEME_FIELDS ...
    'hero_layout_mode': 'themeHeroLayoutMode', // full or box
    'hero_content_align': 'themeHeroAlign',    // left, center, right
    'hero_menu_visible': 'themeHeroMenuVisible', // flex or none
    
    'hero_box_width': 'themeHeroBoxWidth',
    
    // Box Borders (Inner)
    'hero_box_border_width': 'themeHeroBoxBorderWidth',
    'hero_box_border_color': 'themeHeroBoxBorderColor',
    'hero_border_top': 'themeHeroBorderTop',         // Checkbox
    'hero_border_bottom_box': 'themeHeroBorderBottomBox', // Checkbox (NEW)
    'hero_border_left': 'themeHeroBorderLeft',       // Checkbox
    'hero_border_right': 'themeHeroBorderRight',     // Checkbox
    'button_border_radius': 'themeBtnRadius',       // For Watch & Notify buttons
    'hero_pill_radius': 'themeHeroPillRadius',      // For Hero Menu Items
    
    // Main Section Border (Outer/Full)
    'hero_main_border_width': 'themeHeroMainBorderWidth', // NEW
    'hero_main_border_color': 'themeHeroMainBorderColor', // NEW
    'hero_main_border_pos': 'themeHeroMainBorderPos',
    'text_sys_status': 'themeTextSysStatus',

    // Section Borders (Width & Color)
    'sec_border_live_width': 'themeLiveBorderWidth',
    'sec_border_live_color': 'themeLiveBorderColor',
    
    'sec_border_upcoming_width': 'themeUpcomingBorderWidth',
    'sec_border_upcoming_color': 'themeUpcomingBorderColor',
    
    'sec_border_wildcard_width': 'themeWildcardBorderWidth',
    'sec_border_wildcard_color': 'themeWildcardBorderColor',
    
    'sec_border_leagues_width': 'themeLeaguesBorderWidth',
    'sec_border_leagues_color': 'themeLeaguesBorderColor',
    'sec_border_grouped_width': 'themeGroupedBorderWidth',
    'sec_border_grouped_color': 'themeGroupedBorderColor',
     // New: League Page Upcoming Border
    'sec_border_league_upcoming_width': 'themeLeagueUpcomingBorderWidth',
    'sec_border_league_upcoming_color': 'themeLeagueUpcomingBorderColor',

    // New: Article Styling
    'article_bg': 'themeArticleBg',
    'article_text': 'themeArticleText',
    'article_line_height': 'themeArticleLineHeight',
    'article_bullet_color': 'themeArticleBullet',
    'article_link_color': 'themeArticleLink',
    
    'article_h2_color': 'themeArticleH2Color',
    'article_h2_border_width': 'themeArticleH2BorderWidth',
    'article_h2_border_color': 'themeArticleH2BorderColor',
    
    'article_h3_color': 'themeArticleH3Color',
    'article_h4_color': 'themeArticleH4Color',

    // 5. Match Rows
    'match_row_bg': 'themeMatchRowBg',
    'match_row_border': 'themeMatchRowBorder',
    'match_row_team_name_color': 'themeMatchTeamColor',
    'match_row_time_main_color': 'themeMatchTimeColor',
    'match_row_live_border_left': 'themeMatchLiveBorder',
    'match_row_live_bg_start': 'themeMatchLiveBgStart',
    'match_row_live_bg_end': 'themeMatchLiveBgEnd',
    'match_row_live_text_color': 'themeMatchLiveText',
    'row_height_mode': 'themeRowHeight',
    'match_row_btn_watch_bg': 'themeBtnWatchBg',
    'match_row_btn_watch_text': 'themeBtnWatchText',

    // 6. Footer
    'footer_bg_start': 'themeFooterBgStart',
    'footer_bg_end': 'themeFooterBgEnd',
    'footer_desc_color': 'themeFooterText',
    'footer_link_color': 'themeFooterLink',
    'footer_text_align_desktop': 'themeFooterAlign',
    
    // NEW LAYOUT FIELDS
    'footer_columns': 'themeFooterCols',
    'footer_show_disclaimer': 'themeFooterShowDisclaimer', // Checkbox
    'footer_slot_1': 'themeFooterSlot1',
    'footer_slot_2': 'themeFooterSlot2',
    'footer_slot_3': 'themeFooterSlot3',

    // --- NEW EXTENDED FIELDS ---
    // Wildcard
    'wildcard_category': 'themeWildcardCat',
    
    // Labels & Text
    'text_live_section_title': 'themeTextLiveTitle',
    'text_wildcard_title': 'themeTextWildcardTitle',       // <--- NEW
    'text_top_upcoming_title': 'themeTextTopUpcoming',
    'text_show_more': 'themeTextShowMore',
    'text_section_link': 'themeTextSectionLink',
    'text_watch_btn': 'themeTextWatch',
    'text_hd_badge': 'themeTextHd',
    'text_section_prefix': 'themeTextSectionPrefix',

    // Hover & Styles
    'match_row_hover_bg': 'themeMatchRowHoverBg',
    'match_row_hover_border': 'themeMatchRowHoverBorder',
    'section_logo_size': 'themeSectionLogoSize',
    'show_more_btn_bg': 'themeShowMoreBg',
    'show_more_btn_border': 'themeShowMoreBorder',
    'show_more_btn_text': 'themeShowMoreText',
    'show_more_btn_radius': 'themeShowMoreRadius',

    // Sticky Share
    'social_desktop_top': 'themeSocialDeskTop',
    'social_desktop_left': 'themeSocialDeskLeft',
    'social_desktop_scale': 'themeSocialDeskScale',
    'mobile_footer_height': 'themeMobFootHeight',
    'social_telegram_color': 'themeSocialTelegram',
    'social_whatsapp_color': 'themeSocialWhatsapp',
    'social_reddit_color': 'themeSocialReddit',
    'social_twitter_color': 'themeSocialTwitter',
    'mobile_footer_bg': 'themeMobFootBg',

    // Back to Top
    'back_to_top_bg': 'themeBttBg',
    'back_to_top_icon_color': 'themeBttIcon',
    'back_to_top_radius': 'themeBttRadius',
    'back_to_top_size': 'themeBttSize',
    
    // Logic Toggles
    'display_hero': 'themeDisplayHero',
    // --- WATCH PAGE SPECIFIC ---
    'watch_sidebar_swap': 'themeWatchSidebarSwap', // Checkbox
    'watch_show_ad1': 'themeWatchShowAd1',         // Checkbox
    'watch_show_discord': 'themeWatchShowDiscord', // Checkbox
    'watch_show_ad2': 'themeWatchShowAd2',         // Checkbox
    'watch_discord_order': 'themeWatchDiscordOrder',
    'watch_discord_title': 'themeWatchDiscordTitle',
    'watch_discord_btn_text': 'themeWatchDiscordBtnText',
    
    'chat_header_title': 'themeWatchChatHeaderTitle',
    'chat_header_bg': 'themeWatchChatHeaderBg',
    'chat_header_text': 'themeWatchChatHeaderText',
    'chat_dot_color': 'themeWatchChatDotColor',
    'chat_dot_size': 'themeWatchChatDotSize',
    'chat_overlay_bg': 'themeWatchChatOverlayBg',
    'chat_overlay_opacity': 'themeWatchChatOverlayOpacity',
    'chat_input_bg': 'themeWatchChatInputBg',
    'chat_input_text': 'themeWatchChatInputText',
    'chat_join_btn_text': 'themeWatchChatJoinBtnText',

    'watch_table_head_bg': 'themeWatchTableHeadBg',
    'watch_table_body_bg': 'themeWatchTableBodyBg',
    'watch_table_border': 'themeWatchTableBorder',
    'watch_table_radius': 'themeWatchTableRadius',
    'watch_team_color': 'themeWatchTeamColor',
    'watch_vs_color': 'themeWatchVsColor',
    'watch_team_size': 'themeWatchTeamSize',
    'watch_vs_size': 'themeWatchVsSize',

    'watch_btn_bg': 'themeWatchBtnBg',
    'watch_btn_text': 'themeWatchBtnText',
    'watch_btn_disabled_bg': 'themeWatchBtnDisabledBg',
    'watch_btn_disabled_text': 'themeWatchBtnDisabledText',
    'watch_btn_label': 'themeWatchBtnLabel',
    'watch_btn_disabled_label': 'themeWatchBtnDisabledLabel',

    'watch_info_btn_bg': 'themeWatchInfoBtnBg',
    'watch_info_btn_hover': 'themeWatchInfoBtnHover',
    'watch_info_btn_text': 'themeWatchInfoBtnText',
    'watch_info_btn_label': 'themeWatchInfoBtnLabel',
    'watch_server_active_bg': 'themeWatchServerActiveBg',
    'watch_server_text': 'themeWatchServerText'
};

let configData = {};
let currentThemeContext = 'home';
let leagueMapData = {}; 
let currentSha = null;
let leagueMapSha = null; 
let currentEditingPageId = null;
let isBuilding = false;

// ==========================================
// 3. INITIALIZATION
// ==========================================
window.addEventListener("DOMContentLoaded", () => {
    // 1. Init Editor
    if(typeof tinymce !== 'undefined') {
        tinymce.init({
            selector: '#pageContentEditor', height: 400, skin: 'oxide-dark', content_css: 'dark',
            setup: (ed) => { ed.on('change', saveEditorContentToMemory); }
        });
    }
    
    // 2. Inject Reset Button for Priorities
    const prioHeader = document.querySelector('#tab-priorities .header-box');
    if(prioHeader && !document.getElementById('resetPrioBtn')) {
        const btn = document.createElement('button');
        btn.id = 'resetPrioBtn';
        btn.className = 'btn-danger';
        btn.innerText = 'Reset to Defaults';
        btn.onclick = resetPriorities;
        prioHeader.appendChild(btn);
    }

    // 3. Auth Check
    const token = localStorage.getItem('gh_token');
    if (!token) document.getElementById('authModal').style.display = 'flex';
    else verifyAndLoad(token);
});

// --- AUTH ---
window.saveToken = async () => {
    const token = document.getElementById('ghToken').value.trim();
    if(token) {
        localStorage.setItem('gh_token', token);
        document.getElementById('authModal').style.display = 'none';
        verifyAndLoad(token);
    }
};

async function verifyAndLoad(token) {
    try {
        const headers = { 'Authorization': `token ${token}` };
        
        const [resConfig, resLeague] = await Promise.all([
            fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}?ref=${BRANCH}`, { headers }),
            fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${LEAGUE_FILE_PATH}?ref=${BRANCH}`, { headers })
        ]);

        if(resConfig.status === 404) {
            configData = JSON.parse(JSON.stringify(DEMO_CONFIG));
        } else {
            const data = await resConfig.json();
            currentSha = data.sha;
            configData = JSON.parse(decodeURIComponent(escape(atob(data.content))));
        }

        if(resLeague.status === 404) {
            leagueMapData = {}; 
        } else {
            const lData = await resLeague.json();
            leagueMapSha = lData.sha;
            leagueMapData = JSON.parse(decodeURIComponent(escape(atob(lData.content))));
        }
        
        // Data Normalization
        if(!configData.pages) configData.pages = DEMO_CONFIG.pages;
        configData.pages.forEach(p => { 
            if(!p.id) p.id = 'p_' + Math.random().toString(36).substr(2, 9); 
            if(!p.schemas) p.schemas = {};
            if(!p.schemas.faq_list) p.schemas.faq_list = [];
        });
        
        if(!configData.sport_priorities) configData.sport_priorities = JSON.parse(JSON.stringify(DEFAULT_PRIORITIES));
        if(!configData.sport_priorities.US) configData.sport_priorities.US = { _HIDE_OTHERS: false, _BOOST: "" };
        if(!configData.sport_priorities.UK) configData.sport_priorities.UK = { _HIDE_OTHERS: false, _BOOST: "" };
        if(!configData.social_sharing) configData.social_sharing = DEMO_CONFIG.social_sharing;
        if(!configData.theme) configData.theme = {};
        if(!configData.theme_page) configData.theme_page = {};

        populateUI();
        startPolling();
    } catch(e) { console.error(e); }
}

// ==========================================
// 4. UI POPULATION
// ==========================================
function populateUI() {
    const s = configData.site_settings || {};
    setVal('apiUrl', s.api_url);
    setVal('titleP1', s.title_part_1);
    setVal('titleP2', s.title_part_2);
    setVal('siteDomain', s.domain);
    setVal('paramLive', s.param_live || 'stream');
    setVal('paramInfo', s.param_info || 'info');
    setVal('logoUrl', s.logo_url);
    setVal('faviconUrl', s.favicon_url);
    setVal('footerCopyright', s.footer_copyright);
    setVal('footerDisclaimer', s.footer_disclaimer);
    setVal('targetCountry', s.target_country || 'US');
    // Populate Watch Settings
    const w = configData.watch_settings || {};
    setVal('supaUrl', w.supabase_url);
    setVal('supaKey', w.supabase_key);
    setVal('watchPageTitle', w.meta_title);
    setVal('watchPageDesc', w.meta_desc);
    setVal('watchPageArticle', w.article);
    // Single (Event) - NEW
    setVal('watchPageTitleSingle', w.meta_title_single);
    setVal('watchPageDescSingle', w.meta_desc_single);
    setVal('watchPageArticleSingle', w.article_single);
    setVal('watchAdMobile', w.ad_mobile);
    setVal('watchAdSidebar1', w.ad_sidebar_1);
    setVal('watchAdSidebar2', w.ad_sidebar_2);

    const soc = configData.social_sharing || { counts: {} };
    setVal('socialTelegram', soc.counts?.telegram || 0);
    setVal('socialWhatsapp', soc.counts?.whatsapp || 0);
    setVal('socialReddit', soc.counts?.reddit || 0);
    setVal('socialTwitter', soc.counts?.twitter || 0);
    setVal('socialExcluded', soc.excluded_pages || "");

    //injectMissingThemeUI(); // Inject new controls before rendering
    renderThemeSettings(); 
    renderPriorities();
    renderMenus();
    renderPageList();
    renderLeagues();
    setVal('tplLeagueArticle', configData.articles?.league || "");
    setVal('tplSportArticle', configData.articles?.sport || "");
    setVal('tplExcludePages', configData.articles?.excluded || "");
    setVal('tplLeagueH1', configData.articles?.league_h1 || "");
    setVal('tplLeagueIntro', configData.articles?.league_intro || "");
    setVal('tplLeagueLiveTitle', configData.articles?.league_live_title || "");
    setVal('tplLeagueUpcomingTitle', configData.articles?.league_upcoming_title || "");
}

// ==========================================
// 5. THEME DESIGNER FUNCTIONS (UPDATED)
// ==========================================
function injectMissingThemeUI() {
    const themeTab = document.getElementById('tab-theme');
    if(!themeTab) return;

    // Clean up old injections
    const existingInput = document.getElementById('themeWildcardCat');
    if (existingInput) {
        const container = existingInput.closest('.grid-3');
        if (container) container.remove();
    }

    const newSection = document.createElement('div');
    newSection.className = 'grid-3';
    newSection.innerHTML = `
        <!-- CARD 1: CONTENT & LOGIC -->
        <div class="card">
            <h3>⚡ Content & Logic</h3>
            <div class="range-wrapper" style="margin-bottom:15px; border-bottom:1px solid #333; padding-bottom:10px;">
                <label style="color:#facc15;">🔥 Wildcard Category</label>
                <input type="text" id="themeWildcardCat" placeholder="e.g. NFL, Premier League">
            </div>

            <h4 style="margin:15px 0 5px 0; font-size:0.8rem; color:#aaa;">Titles</h4>
            <div class="grid-2" style="gap:10px;">
                <div style="grid-column: span 2;"><input type="text" id="themeTextWildcardTitle" placeholder="Wildcard Title"></div>
                <div style="grid-column: span 2;"><input type="text" id="themeTextTopUpcoming" placeholder="Top 5 Title"></div>
                <div><label>Status Text</label><input type="text" id="themeTextSysStatus" placeholder="System Status: Online"></div>
                <div><label>Live</label><input type="text" id="themeTextLiveTitle"></div>
                <div><label>Show More</label><input type="text" id="themeTextShowMore"></div>
                <div><label>Btn</label><input type="text" id="themeTextWatch"></div>
                <div><label>Badge</label><input type="text" id="themeTextHd"></div>
                <div><label>Link</label><input type="text" id="themeTextSectionLink"></div>
                <div><label>Prefix</label><input type="text" id="themeTextSectionPrefix"></div>
            </div>
        </div>

        <!-- CARD 2: STYLING & BORDERS (UPDATED) -->
        <div class="card">
            <h3>🎨 Section Borders</h3>
            <p style="font-size:0.75rem; color:#aaa; margin-bottom:15px;">Customize bottom borders for specific sections.</p>

            <!-- Live -->
            <label>Trending Live</label>
            <div class="input-group">
                <input type="number" id="themeLiveBorderWidth" placeholder="Width (px)" value="1">
                <input type="color" id="themeLiveBorderColor" value="#334155">
            </div>

            <!-- Upcoming -->
            <label>Top 5 Upcoming</label>
            <div class="input-group">
                <input type="number" id="themeUpcomingBorderWidth" placeholder="Width (px)" value="1">
                <input type="color" id="themeUpcomingBorderColor" value="#334155">
            </div>

            <!-- Wildcard -->
            <label>Wildcard Section</label>
            <div class="input-group">
                <input type="number" id="themeWildcardBorderWidth" placeholder="Width (px)" value="1">
                <input type="color" id="themeWildcardBorderColor" value="#334155">
            </div>
            <!-- Grouped Sports (Main List) -->
            <label>Grouped Sports/Leagues</label>
            <div class="input-group">
                <input type="number" id="themeGroupedBorderWidth" placeholder="Width (px)" value="1">
                <input type="color" id="themeGroupedBorderColor" value="#334155">
            </div>

            <!-- Footer Leagues -->
            <label>Footer Popular Leagues</label>
            <div class="input-group">
                <input type="number" id="themeLeaguesBorderWidth" placeholder="Width (px)" value="1">
                <input type="color" id="themeLeaguesBorderColor" value="#334155">
            </div>
            
            <h4 style="margin:15px 0 5px 0; font-size:0.8rem; color:#aaa;">Buttons</h4>
            <div class="color-grid">
                <div><label>Show More BG</label><input type="color" id="themeShowMoreBg"></div>
                <div><label>Text</label><input type="color" id="themeShowMoreText"></div>
            </div>
            <div class="range-wrapper"><label>Radius</label><input type="text" id="themeShowMoreRadius" placeholder="30px"></div>
        </div>

        <!-- CARD 3: FLOATING ELEMENTS -->
        <div class="card">
            <h3>📍 Floating & Extras</h3>
            <h4 style="margin:5px 0 5px 0; font-size:0.8rem; color:#aaa;">Back to Top</h4>
            <div class="color-grid">
                <div><label>BG</label><input type="color" id="themeBttBg"></div>
                <div><label>Icon</label><input type="color" id="themeBttIcon"></div>
            </div>
            
            <h4 style="margin:10px 0 5px 0; font-size:0.8rem; color:#aaa;">Section Logo Size</h4>
             <input type="range" id="themeSectionLogoSize" min="0" max="60" step="1">

            <h4 style="margin:10px 0 5px 0; font-size:0.8rem; color:#aaa;">Social Sidebar</h4>
            <div class="grid-2" style="gap:10px;">
                <div><label>Top</label><input type="text" id="themeSocialDeskTop"></div>
                <div><label>Left</label><input type="text" id="themeSocialDeskLeft"></div>
                <div><label>Scale</label><input type="text" id="themeSocialDeskScale"></div>
            </div>
            <h4 style="margin:10px 0 5px 0; font-size:0.8rem; color:#aaa;">Social Colors</h4>
            <div class="color-grid">
                <div><label>Telegram</label><input type="color" id="themeSocialTelegram"></div>
                <div><label>WhatsApp</label><input type="color" id="themeSocialWhatsapp"></div>
                <div><label>Reddit</label><input type="color" id="themeSocialReddit"></div>
                <div><label>Twitter</label><input type="color" id="themeSocialTwitter"></div>
            </div>
             <h4 style="margin:10px 0 5px 0; font-size:0.8rem; color:#aaa;">Match Hover</h4>
            <div class="color-grid">
                <div><label>Hover BG</label><input type="color" id="themeMatchRowHoverBg"></div>
                <div><label>Hover Border</label><input type="color" id="themeMatchRowHoverBorder"></div>
            </div>
        </div>
    `;
    themeTab.appendChild(newSection);
}

function renderThemeSettings() {
    const t = configData.theme || {};
    // Checkbox Logic for Hero Borders
    if(document.getElementById('themeHeroBorderTop')) document.getElementById('themeHeroBorderTop').checked = t.hero_border_top === true;
    if(document.getElementById('themeHeroBorderBottomBox')) document.getElementById('themeHeroBorderBottomBox').checked = t.hero_border_bottom_box === true; // NEW
    if(document.getElementById('themeHeroBorderLeft')) document.getElementById('themeHeroBorderLeft').checked = t.hero_border_left === true;
    if(document.getElementById('themeHeroBorderRight')) document.getElementById('themeHeroBorderRight').checked = t.hero_border_right === true;
    if(document.getElementById('val_btnRadius')) document.getElementById('val_btnRadius').innerText = (t.button_border_radius || '4') + 'px';
    if(document.getElementById('val_pillRadius')) document.getElementById('val_pillRadius').innerText = (t.hero_pill_radius || '50') + 'px';
    if(document.getElementById('val_headerWidth')) document.getElementById('val_headerWidth').innerText = (t.header_max_width || '1100') + 'px';
    
    for (const [jsonKey, htmlId] of Object.entries(THEME_FIELDS)) {
        if(t[jsonKey]) setVal(htmlId, t[jsonKey]);
    }

    if(document.getElementById('val_borderRadius')) document.getElementById('val_borderRadius').innerText = (t.border_radius_base || '6') + 'px';
    if(document.getElementById('val_maxWidth')) document.getElementById('val_maxWidth').innerText = (t.container_max_width || '1100') + 'px';
    if(document.getElementById('val_secLogo')) document.getElementById('val_secLogo').innerText = (t.section_logo_size || '24') + 'px';

    toggleHeroInputs();
    toggleHeaderInputs();
    toggleHeroBoxSettings();
    toggleFooterSlots();
}
window.toggleHeroBoxSettings = () => {
    const mode = document.getElementById('themeHeroLayoutMode').value;
    const settings = document.getElementById('heroBoxSettings');
    
    // Toggle Box Settings Panel
    settings.style.display = (mode === 'box') ? 'block' : 'none';

    // Toggle Border Placement Options
    const posSelect = document.getElementById('themeHeroMainBorderPos');
    const boxOption = posSelect.querySelector('.opt-box-only');
    
    if (boxOption) {
        if (mode === 'box') {
            boxOption.disabled = false;
            boxOption.innerText = "Match Box Width"; // Visual indicator
        } else {
            boxOption.disabled = true;
            boxOption.innerText = "Match Box Width (Box Layout Only)";
            // Auto-switch to Full if Box was selected but user switched layout
            if (posSelect.value === 'box') posSelect.value = 'full';
        }
    }
};

// Inside admin/app.js

window.toggleHeroInputs = () => {
    const style = document.getElementById('themeHeroBgStyle').value;
    document.getElementById('heroSolidInput').style.display = style === 'solid' ? 'block' : 'none';
    document.getElementById('heroGradientInput').style.display = style === 'gradient' ? 'grid' : 'none';
    document.getElementById('heroImageInput').style.display = style === 'image' ? 'block' : 'none';
    // Transparent triggers none of the above, so inputs remain hidden
};
window.toggleHeaderInputs = () => {
    const layout = document.getElementById('themeHeaderLayout').value;
    // Show Icon Position only if Centered
    const iconGroup = document.getElementById('headerIconPosGroup');
    if(iconGroup) iconGroup.style.display = (layout === 'center') ? 'block' : 'none';
};
window.toggleFooterSlots = () => {
    const cols = document.getElementById('themeFooterCols').value;
    const slot3 = document.getElementById('footerSlot3Group');
    if(slot3) slot3.style.display = (cols === '3') ? 'block' : 'none';
};
// ==========================================
// 1. FIXED THEME PRESETS
// ==========================================
const THEME_PRESETS = {
    red: {
        // --- BASE ---
        themeBrandPrimary: '#D00000',
        themeBrandDark: '#8a0000',
        themeAccentGold: '#FFD700',
        themeStatusGreen: '#00e676',
        themeBgBody: '#050505',
        themeBgPanel: '#0f0f0f',
        themeTextMain: '#ffffff',
        themeTextMuted: '#888888',
        themeBorderColor: '#222222',
        themeScrollThumb: '#333333',

        // --- HEADER ---
        themeHeaderBg: '#050505',
        themeHeaderText: '#aaaaaa',
        themeHeaderActive: '#ffffff',
        themeLogoP1: '#ffffff',
        themeLogoP2: '#D00000',
        themeHeaderBorderBottom: '1px solid var(--border)',

        // --- HERO (Red Gradient) ---
        themeHeroBgStyle: 'gradient',
        themeHeroGradStart: '#2a0505', // Deep Red
        themeHeroGradEnd: '#000000',   // Black
        themeHeroH1: '#ffffff',
        themeHeroIntro: '#999999',
        themeHeroPillBg: '#111111',
        themeHeroPillText: '#cccccc',
        themeHeroPillActiveBg: '#2a0a0a',
        themeHeroPillActiveText: '#ffffff',

        // --- MATCH ROWS ---
        themeMatchRowBg: '#121212',
        themeMatchRowBorder: '#222222',
        themeMatchTeamColor: '#ffffff',
        themeMatchTimeColor: '#888888',

        // --- LIVE ROWS ---
        themeMatchLiveBgStart: '#1a0505',
        themeMatchLiveBgEnd: '#141414',
        themeMatchLiveText: '#D00000',
        themeMatchLiveBorder: '3px solid var(--brand-primary)',

        // --- ELEMENTS ---
        themeBtnWatchBg: '#D00000',
        themeBtnWatchText: '#ffffff',
        themeFooterBgStart: '#0e0e0e',
        themeFooterBgEnd: '#050505',
        themeFooterText: '#64748b',
        themeFooterLink: '#94a3b8',
        themeShowMoreBg: '#151515',
        themeShowMoreText: '#cccccc',
        themeShowMoreBorder: '#333333',
        themeMatchRowHoverBg: '#1a1a1a',
        themeMatchRowHoverBorder: '#444444',
        themeBttBg: '#D00000',
        themeBttIcon: '#ffffff',
        themeMobFootBg: '#0a0a0a'
    },
    blue: {
        // --- BASE ---
        themeBrandPrimary: '#2563EB',
        themeBrandDark: '#1e3a8a',
        themeAccentGold: '#38bdf8',
        themeStatusGreen: '#00e676',
        themeBgBody: '#020617',
        themeBgPanel: '#0f172a',
        themeTextMain: '#f8fafc',
        themeTextMuted: '#94a3b8',
        themeBorderColor: '#1e293b',
        themeScrollThumb: '#334155',

        // --- HEADER ---
        themeHeaderBg: '#020617',
        themeHeaderText: '#94a3b8',
        themeHeaderActive: '#ffffff',
        themeLogoP1: '#f8fafc',
        themeLogoP2: '#2563EB',
        themeHeaderBorderBottom: '1px solid var(--border)',

        // --- HERO (Blue Gradient) ---
        themeHeroBgStyle: 'gradient',
        themeHeroGradStart: '#0f172a', // Deep Blue
        themeHeroGradEnd: '#020617',   // Darker Blue
        themeHeroH1: '#ffffff',
        themeHeroIntro: '#94a3b8',
        themeHeroPillBg: '#1e293b',
        themeHeroPillText: '#cbd5e1',
        themeHeroPillActiveBg: '#172554',
        themeHeroPillActiveText: '#ffffff',

        // --- MATCH ROWS ---
        themeMatchRowBg: '#0f172a',
        themeMatchRowBorder: '#1e293b',
        themeMatchTeamColor: '#f1f5f9',
        themeMatchTimeColor: '#94a3b8',

        // --- LIVE ROWS ---
        themeMatchLiveBgStart: '#172554',
        themeMatchLiveBgEnd: '#0f172a',
        themeMatchLiveText: '#60a5fa',
        themeMatchLiveBorder: '3px solid var(--brand-primary)',

        // --- ELEMENTS ---
        themeBtnWatchBg: '#2563EB',
        themeBtnWatchText: '#ffffff',
        themeFooterBgStart: '#0f172a',
        themeFooterBgEnd: '#020617',
        themeFooterText: '#64748b',
        themeFooterLink: '#94a3b8',
        themeShowMoreBg: '#1e293b',
        themeShowMoreText: '#cbd5e1',
        themeShowMoreBorder: '#334155',
        themeMatchRowHoverBg: '#1e293b',
        themeMatchRowHoverBorder: '#38bdf8',
        themeBttBg: '#2563EB',
        themeBttIcon: '#ffffff',
        themeMobFootBg: '#020617'
    },
    green: {
        // --- BASE ---
        themeBrandPrimary: '#16a34a',
        themeBrandDark: '#14532d',
        themeAccentGold: '#facc15',
        themeStatusGreen: '#22c55e',
        themeBgBody: '#050505',
        themeBgPanel: '#111111',
        themeTextMain: '#ffffff',
        themeTextMuted: '#a3a3a3',
        themeBorderColor: '#262626',
        themeScrollThumb: '#404040',

        // --- HEADER ---
        themeHeaderBg: '#050505',
        themeHeaderText: '#a3a3a3',
        themeHeaderActive: '#ffffff',
        themeLogoP1: '#ffffff',
        themeLogoP2: '#16a34a',
        themeHeaderBorderBottom: '1px solid var(--border)',

        // --- HERO (Green Gradient) ---
        themeHeroBgStyle: 'gradient',
        themeHeroGradStart: '#052e16', // Deep Green
        themeHeroGradEnd: '#000000',
        themeHeroH1: '#ffffff',
        themeHeroIntro: '#a3a3a3',
        themeHeroPillBg: '#262626',
        themeHeroPillText: '#d4d4d4',
        themeHeroPillActiveBg: '#064e3b',
        themeHeroPillActiveText: '#ffffff',

        // --- MATCH ROWS ---
        themeMatchRowBg: '#111111',
        themeMatchRowBorder: '#262626',
        themeMatchTeamColor: '#f5f5f5',
        themeMatchTimeColor: '#737373',

        // --- LIVE ROWS ---
        themeMatchLiveBgStart: '#052e16',
        themeMatchLiveBgEnd: '#111111',
        themeMatchLiveText: '#22c55e',
        themeMatchLiveBorder: '3px solid var(--brand-primary)',

        // --- ELEMENTS ---
        themeBtnWatchBg: '#16a34a',
        themeBtnWatchText: '#ffffff',
        themeFooterBgStart: '#111111',
        themeFooterBgEnd: '#000000',
        themeFooterText: '#737373',
        themeFooterLink: '#a3a3a3',
        themeShowMoreBg: '#171717',
        themeShowMoreText: '#d4d4d4',
        themeShowMoreBorder: '#262626',
        themeMatchRowHoverBg: '#262626',
        themeMatchRowHoverBorder: '#16a34a',
        themeBttBg: '#16a34a',
        themeBttIcon: '#ffffff',
        themeMobFootBg: '#050505'
    }
};
// 2. THE APPLY LOGIC
window.applyPreset = (presetName) => {
    if(!THEME_PRESETS[presetName]) return;
    const p = THEME_PRESETS[presetName];

    if(!confirm(`Apply ${presetName.toUpperCase()} preset? This will overwrite current color settings.`)) return;

    // 1. First, loop through all keys
    Object.keys(p).forEach(id => {
        setVal(id, p[id]);
    });

    // 2. FORCE UPDATE specific gradient fields to be safe
    if(p.themeHeroGradStart) setVal('themeHeroGradStart', p.themeHeroGradStart);
    if(p.themeHeroGradEnd) setVal('themeHeroGradEnd', p.themeHeroGradEnd);

    // 3. Update Visuals
    toggleHeroInputs();
    
    // 4. Update Range Sliders Text (Optional visual polish)
    if(document.getElementById('val_borderRadius')) document.getElementById('val_borderRadius').innerText = getVal('themeBorderRadius') + 'px';

    alert(`${presetName.toUpperCase()} preset loaded! click 'Save' to build.`);
};

// ==========================================
// 6. PRIORITIES & BOOST
// ==========================================
function renderPriorities() {
    const c = getVal('targetCountry') || 'US';
    const container = document.getElementById('priorityListContainer');
    if(document.getElementById('prioLabel')) document.getElementById('prioLabel').innerText = c;
    
    if(!configData.sport_priorities[c]) configData.sport_priorities[c] = { _HIDE_OTHERS: false, _BOOST: "" };
    const isHideOthers = !!configData.sport_priorities[c]._HIDE_OTHERS;
    setVal('prioBoost', configData.sport_priorities[c]._BOOST || "");

    const items = Object.entries(configData.sport_priorities[c])
        .filter(([name]) => name !== '_HIDE_OTHERS' && name !== '_BOOST')
        .map(([name, data]) => ({ name, ...data }))
        .sort((a,b) => b.score - a.score);

    let html = `
        <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); padding: 15px; border-radius: 6px; margin-bottom: 20px;">
            <label style="margin:0; font-weight:700; color:#fca5a5; display:flex; align-items:center; gap:10px;">
                <input type="checkbox" ${isHideOthers ? 'checked' : ''} onchange="toggleHideOthers('${c}', this.checked)"> 
                🚫 Hide all others (Strict Mode)
            </label>
            <p style="margin:5px 0 0 26px; font-size:0.8rem; color:#aaa;">Only listed sports displayed.</p>
        </div>
    `;

    html += items.map(item => `
        <div class="menu-item-row" style="flex-wrap:wrap; opacity: ${item.isHidden ? '0.5' : '1'};">
            <strong style="width:140px; overflow:hidden;">${item.name}</strong>
            <div style="flex:1; display:flex; gap:10px; align-items:center;">
                <label style="margin:0; font-size:0.75rem;"><input type="checkbox" ${item.isLeague?'checked':''} onchange="updatePrioMeta('${c}','${item.name}','isLeague',this.checked)"> League</label>
                <label style="margin:0; font-size:0.75rem;"><input type="checkbox" ${item.hasLink?'checked':''} onchange="updatePrioMeta('${c}','${item.name}','hasLink',this.checked)"> Link</label>
                <label style="margin:0; font-size:0.75rem; color:#ef4444;"><input type="checkbox" ${item.isHidden?'checked':''} onchange="updatePrioMeta('${c}','${item.name}','isHidden',this.checked)"> Hide</label>
                <input type="number" value="${item.score}" onchange="updatePrioMeta('${c}','${item.name}','score',this.value)" style="width:60px; margin:0;">
                <button class="btn-icon" onclick="deletePriority('${c}', '${item.name}')">×</button>
            </div>
        </div>
    `).join('');
    container.innerHTML = html;
}

window.toggleHideOthers = (c, checked) => {
    if(!configData.sport_priorities[c]) configData.sport_priorities[c] = {};
    configData.sport_priorities[c]._HIDE_OTHERS = checked;
};

window.resetPriorities = () => {
    const c = getVal('targetCountry');
    if(!confirm(`Reset priorities for ${c}?`)) return;
    configData.sport_priorities[c] = JSON.parse(JSON.stringify(DEFAULT_PRIORITIES[c] || DEFAULT_PRIORITIES['US']));
    renderPriorities();
};

window.addPriorityRow = () => {
    const c = getVal('targetCountry');
    const name = getVal('newSportName');
    if(name) {
        if(!configData.sport_priorities[c]) configData.sport_priorities[c] = { _HIDE_OTHERS: false, _BOOST: "" };
        const isLikelyLeague = name.toLowerCase().match(/league|nba|nfl/);
        configData.sport_priorities[c][name] = { score: 50, isLeague: !!isLikelyLeague, hasLink: false, isHidden: false };
        setVal('newSportName', '');
        renderPriorities();
    }
};

window.updatePrioMeta = (c, name, key, val) => {
    const item = configData.sport_priorities[c][name];
    if(key === 'score') item.score = parseInt(val);
    else item[key] = val;
    if(key === 'isHidden') renderPriorities();
};

window.deletePriority = (c, name) => {
    if(confirm(`Remove ${name}?`)) {
        delete configData.sport_priorities[c][name];
        renderPriorities();
    }
};

// ==========================================
// 7. PAGES & MENUS (STANDARD)
// ==========================================
function renderPageList() {
    const tbody = document.querySelector('#pagesTable tbody');
    if(!configData.pages) configData.pages = [];
    tbody.innerHTML = configData.pages.map(p => `
        <tr>
            <td><strong>${p.title}</strong></td>
            <td>/${p.slug}</td>
            <td>${p.layout}</td>
            <td>
                <button class="btn-primary" onclick="editPage('${p.id}')">Edit</button>
                ${p.slug !== 'home' ? `<button class="btn-danger" onclick="deletePage('${p.id}')">Del</button>` : ''}
            </td>
        </tr>
    `).join('');
}

window.editPage = (id) => {
    currentEditingPageId = id;
    const p = configData.pages.find(x => x.id === id);
    if(!p) return;
    document.getElementById('pageListView').style.display = 'none';
    document.getElementById('pageEditorView').style.display = 'block';
    document.getElementById('editorPageTitleDisplay').innerText = `Editing: ${p.title}`;
    setVal('pageTitle', p.title);
    setVal('pageH1Align', p.h1_align || 'left');
    setVal('pageSlug', p.slug);
    setVal('pageLayout', p.layout || 'page');
    setVal('pageMetaTitle', p.meta_title);
    setVal('pageMetaDesc', p.meta_desc);
    setVal('pageMetaKeywords', p.meta_keywords); 
    setVal('pageCanonical', p.canonical_url); 
    
    if(!p.schemas) p.schemas = {};
    if(!p.schemas.faq_list) p.schemas.faq_list = [];
    
    document.querySelector('#pageEditorView .checkbox-group').innerHTML = `
        <label style="color:#facc15; font-weight:700;">Static Schemas (SEO)</label>
        <label><input type="checkbox" id="schemaOrg" ${p.schemas.org ? 'checked' : ''}> Organization (The Entity)</label>
        <label><input type="checkbox" id="schemaWebsite" ${p.schemas.website ? 'checked' : ''}> WebSite</label>
        <label><input type="checkbox" id="schemaAbout" ${p.schemas.about ? 'checked' : ''}> About Page (Links to Org)</label> <!-- NEW -->
        <label><input type="checkbox" id="schemaFaq" ${p.schemas.faq ? 'checked' : ''} onchange="toggleFaqEditor(this.checked)"> FAQ</label>
        <div id="faqEditorContainer" style="display:${p.schemas.faq?'block':'none'}; margin-top:10px;">
            <div style="display:flex;justify-content:space-between;"><h4 style="margin:0">FAQ Items</h4><button class="btn-primary" onclick="addFaqItem()">+ Add</button></div>
            <div id="faqList" style="display:flex;flex-direction:column;gap:10px;margin-top:10px;"></div>
        </div>
    `;
    renderFaqItems(p.schemas.faq_list);
    if(tinymce.get('pageContentEditor')) tinymce.get('pageContentEditor').setContent(p.content || '');
    document.getElementById('pageSlug').disabled = (p.slug === 'home');
};

window.toggleFaqEditor = (isChecked) => { document.getElementById('faqEditorContainer').style.display = isChecked ? 'block' : 'none'; };
window.renderFaqItems = (list) => {
    document.getElementById('faqList').innerHTML = list.map((item, idx) => `
        <div style="background:rgba(0,0,0,0.2); padding:10px; border:1px solid #333;">
            <input type="text" class="faq-q" value="${item.q||''}" placeholder="Question" style="font-weight:bold;margin-bottom:5px;">
            <textarea class="faq-a" rows="2" placeholder="Answer" style="margin-bottom:5px;">${item.a||''}</textarea>
            <button class="btn-danger" style="padding:4px 8px;font-size:0.7rem;" onclick="removeFaqItem(${idx})">Remove</button>
        </div>
    `).join('');
};
window.addFaqItem = () => { saveCurrentFaqState(); configData.pages.find(x => x.id === currentEditingPageId).schemas.faq_list.push({ q: "", a: "" }); renderFaqItems(configData.pages.find(x => x.id === currentEditingPageId).schemas.faq_list); };
window.removeFaqItem = (idx) => { saveCurrentFaqState(); configData.pages.find(x => x.id === currentEditingPageId).schemas.faq_list.splice(idx, 1); renderFaqItems(configData.pages.find(x => x.id === currentEditingPageId).schemas.faq_list); };
function saveCurrentFaqState() { 
    if(!currentEditingPageId) return; 
    const p = configData.pages.find(x => x.id === currentEditingPageId); 
    const div = document.getElementById('faqList');
    if(!div) return;
    p.schemas.faq_list = Array.from(div.querySelectorAll('.faq-q')).map((q, i) => ({ q: q.value, a: div.querySelectorAll('.faq-a')[i].value }));
}
window.saveEditorContentToMemory = () => {
    if(!currentEditingPageId) return;
    const p = configData.pages.find(x => x.id === currentEditingPageId);
    p.h1_align = getVal('pageH1Align');
    p.title = getVal('pageTitle'); p.slug = getVal('pageSlug'); p.layout = getVal('pageLayout');
    p.meta_title = getVal('pageMetaTitle'); p.meta_desc = getVal('pageMetaDesc'); p.meta_keywords = getVal('pageMetaKeywords'); p.canonical_url = getVal('pageCanonical');
    p.content = tinymce.get('pageContentEditor').getContent();
    saveCurrentFaqState();
    if(!p.schemas) p.schemas = {};
    p.schemas.org = document.getElementById('schemaOrg').checked;
    p.schemas.website = document.getElementById('schemaWebsite').checked;
    p.schemas.about = document.getElementById('schemaAbout').checked;
    p.schemas.faq = document.getElementById('schemaFaq').checked;
};
window.closePageEditor = () => { saveEditorContentToMemory(); document.getElementById('pageEditorView').style.display = 'none'; document.getElementById('pageListView').style.display = 'block'; renderPageList(); };
window.createNewPage = () => { configData.pages.push({ id: 'p_'+Date.now(), title: "New", slug: "new", layout: "page", content: "", schemas: {org:true} }); renderPageList(); };
window.deletePage = (id) => { if(confirm("Del?")) { configData.pages = configData.pages.filter(p => p.id !== id); renderPageList(); } };

function renderMenus() {
    ['header', 'hero', 'footer_static'].forEach(sec => {
        if(document.getElementById(`menu-${sec}`)) {
            document.getElementById(`menu-${sec}`).innerHTML = (configData.menus[sec]||[]).map((item, idx) => `
                <div class="menu-item-row"><div>${item.highlight?'<span style="color:#facc15">★</span>':''} <strong>${item.title}</strong> <small>(${item.url})</small></div><button class="btn-icon" onclick="deleteMenuItem('${sec}', ${idx})">×</button></div>
            `).join('');
        }
    });
}
window.openMenuModal = (sec) => { 
    document.getElementById('menuTargetSection').value = sec; 
    setVal('menuTitleItem',''); setVal('menuUrlItem',''); 
    const chk = document.getElementById('menuHighlightCheck'); if(chk) chk.parentNode.remove();
    if(sec === 'header') {
        const w = document.createElement('div'); w.innerHTML = `<label style="display:inline-flex;gap:5px;margin-top:10px;"><input type="checkbox" id="menuHighlightCheck"> Highlight</label>`;
        document.querySelector('#menuModal .modal-content').insertBefore(w, document.querySelector('#menuModal .modal-actions'));
    }
    document.getElementById('menuModal').style.display='flex'; 
};
window.saveMenuItem = () => { 
    const sec = document.getElementById('menuTargetSection').value;
    if(!configData.menus[sec]) configData.menus[sec] = [];
    configData.menus[sec].push({ title: getVal('menuTitleItem'), url: getVal('menuUrlItem'), highlight: document.getElementById('menuHighlightCheck')?.checked });
    renderMenus(); document.getElementById('menuModal').style.display = 'none';
};
window.deleteMenuItem = (sec, idx) => { configData.menus[sec].splice(idx, 1); renderMenus(); };

function getGroupedLeagues() { return leagueMapData || {}; }
function renderLeagues() {
    const c = document.getElementById('leaguesContainer'); if(!c) return;
    const g = getGroupedLeagues();
    c.innerHTML = Object.keys(g).sort().map(l => `<div class="card"><div class="league-card-header"><h3>${l}</h3><span>${g[l].length} Teams</span></div><label>Teams</label><textarea class="team-list-editor" rows="6" data-league="${l}">${g[l].join(', ')}</textarea></div>`).join('');
}
window.copyAllLeaguesData = () => {
    let o = ""; for(const [l,t] of Object.entries(getGroupedLeagues())) o+=`LEAGUE: ${l}\nTEAMS: ${t.join(', ')}\n---\n`;
    navigator.clipboard.writeText(o).then(() => alert("Copied!"));
};
window.openLeagueModal = () => document.getElementById('leagueModal').style.display = 'flex';
window.saveNewLeague = () => { 
    const n = document.getElementById('newLeagueNameInput').value.trim(); 
    if(n) { if(!leagueMapData) leagueMapData={}; leagueMapData[n] = ["new"]; renderLeagues(); document.getElementById('leagueModal').style.display='none'; } 
};
function rebuildLeagueMapFromUI() {
    const map = {}; document.querySelectorAll('.team-list-editor').forEach(t => { map[t.getAttribute('data-league')] = t.value.split(',').map(x=>x.trim().toLowerCase().replace(/\s+/g,'-')).filter(x=>x.length>0); });
    return map;
}

// ==========================================
// 10. SAVE
// ==========================================
document.getElementById('saveBtn').onclick = async () => {
    if(isBuilding) return;
    saveEditorContentToMemory(); 
    
    const c = getVal('targetCountry') || 'US';
    if(configData.sport_priorities[c]) configData.sport_priorities[c]._BOOST = getVal('prioBoost');

    configData.site_settings = {
        api_url: getVal('apiUrl'), title_part_1: getVal('titleP1'), title_part_2: getVal('titleP2'),
        domain: getVal('siteDomain'), logo_url: getVal('logoUrl'), favicon_url: getVal('faviconUrl'),
        footer_copyright: getVal('footerCopyright'), footer_disclaimer: getVal('footerDisclaimer'),
        target_country: c,
        param_live: getVal('paramLive') || 'stream',
        param_info: getVal('paramInfo') || 'info'
    };
    configData.social_sharing = {
        counts: { telegram: parseInt(getVal('socialTelegram'))||0, whatsapp: parseInt(getVal('socialWhatsapp'))||0, reddit: parseInt(getVal('socialReddit'))||0, twitter: parseInt(getVal('socialTwitter'))||0 },
        excluded_pages: getVal('socialExcluded')
    };
    
    // === NEW SAVE LOGIC START ===
// 1. Capture whatever is currently on screen to the active context variable
captureThemeState(currentThemeContext);
    // Save Watch Settings
    configData.watch_settings = {
        supabase_url: getVal('supaUrl'),
        supabase_key: getVal('supaKey'),
        meta_title: getVal('watchPageTitle'),
        meta_desc: getVal('watchPageDesc'),
        article: getVal('watchPageArticle'),
        // Single - NEW
        meta_title_single: getVal('watchPageTitleSingle'),
        meta_desc_single: getVal('watchPageDescSingle'),
        article_single: getVal('watchPageArticleSingle'),
        ad_mobile: getVal('watchAdMobile'),
        ad_sidebar_1: getVal('watchAdSidebar1'),
        ad_sidebar_2: getVal('watchAdSidebar2')
    };

// 2. Capture Articles
configData.articles = {
    league: getVal('tplLeagueArticle'),
    sport: getVal('tplSportArticle'),
    excluded: getVal('tplExcludePages'),
    league_h1: getVal('tplLeagueH1'),
    league_intro: getVal('tplLeagueIntro'),
    league_live_title: getVal('tplLeagueLiveTitle'),
    league_upcoming_title: getVal('tplLeagueUpcomingTitle')
};
// === NEW SAVE LOGIC END ===

    if(document.querySelector('.team-list-editor')) leagueMapData = rebuildLeagueMapFromUI();

    document.getElementById('saveBtn').innerText = "Saving..."; document.getElementById('saveBtn').disabled = true;
    const token = localStorage.getItem('gh_token');
    
    try {
        const lContent = btoa(unescape(encodeURIComponent(JSON.stringify(leagueMapData, null, 2))));
        await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${LEAGUE_FILE_PATH}`, {
            method: 'PUT', headers: { 'Authorization': `token ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: "Update League Map", content: lContent, sha: leagueMapSha, branch: BRANCH })
        }).then(r=>r.json()).then(d=>leagueMapSha=d.content.sha);

        const cContent = btoa(unescape(encodeURIComponent(JSON.stringify(configData, null, 2))));
        const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/contents/${FILE_PATH}`, {
            method: 'PUT', headers: { 'Authorization': `token ${token}`, 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: "Update Config", content: cContent, sha: currentSha, branch: BRANCH })
        });

        if(res.ok) {
            const d = await res.json(); currentSha = d.content.sha; startPolling();
        } else {
             alert("Save Config Failed"); document.getElementById('saveBtn').disabled = false;
        }
    } catch(e) { alert("Error: " + e.message); document.getElementById('saveBtn').disabled = false; }
};

function startPolling() {
    isBuilding = true;
    const btn = document.getElementById('saveBtn');
    btn.innerText = "Building..."; btn.disabled = true;
    document.getElementById('buildStatusBox').className = "build-box building";
    document.getElementById('buildStatusText').innerText = "Building...";

    const iv = setInterval(async () => {
        try {
            const res = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/runs?per_page=1`, { headers: { 'Authorization': `token ${localStorage.getItem('gh_token')}` } });
            if (!res.ok) throw new Error();
            const d = await res.json();
            if (!d.workflow_runs || !d.workflow_runs.length) return;
            const run = d.workflow_runs[0];
            if(run.status === 'completed') {
                clearInterval(iv); isBuilding = false;
                btn.disabled = false; btn.innerText = "💾 Save & Build Site";
                document.getElementById('buildStatusText').innerText = run.conclusion === 'success' ? "Live ✅" : "Failed ❌";
                document.getElementById('buildStatusBox').className = `build-box ${run.conclusion}`;
            }
        } catch(e) { clearInterval(iv); isBuilding = false; btn.disabled = false; }
    }, 5000);
}

window.switchTab = (id) => {
    document.querySelectorAll('.tab-content').forEach(e => e.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`tab-${id}`).classList.add('active');
    document.querySelectorAll('.nav-btn').forEach(b => { if(b.onclick.toString().includes(`'${id}'`)) b.classList.add('active'); });
};

function setVal(id, v) { if(document.getElementById(id)) document.getElementById(id).value = v || ""; }
function getVal(id) { return document.getElementById(id)?.value || ""; }
// ==========================================
// NEW: THEME CONTEXT SWITCHER LOGIC
// ==========================================
// Replace the existing switchThemeContext function with this updated version:
window.switchThemeContext = (mode) => {
    captureThemeState(currentThemeContext);
    currentThemeContext = mode;

    document.querySelectorAll('.ctx-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(`ctxBtn-${mode}`).classList.add('active');
    
    // Toggle Control Visibility
    // Toggle Control Visibility
    const staticControls = document.getElementById('staticPageControls');
    const watchControls = document.getElementById('watchThemeControls'); 

    // Static Page Controls logic
    if (staticControls) staticControls.style.display = (mode === 'page') ? 'block' : 'none';
    
    // Watch Controls logic (Show Watch card, BUT KEEP Global cards visible)
    if (mode === 'watch') {
        if(watchControls) watchControls.style.display = 'block';
        document.getElementById('ctxDesc').innerHTML = "Editing specific styles for the <strong>Watch Page</strong> + Global Styles.";
    } else {
        if(watchControls) watchControls.style.display = 'none';
        
        let desc = "Editing global styles.";
        if(mode === 'home') desc = "Editing global styles for the <strong>Homepage</strong>.";
        else if(mode === 'league') desc = "Editing styles for <strong>Inner League Pages</strong> (e.g. /nba-streams/).";
        else if(mode === 'page') desc = "Editing styles for <strong>Static Pages</strong> (About, Contact, etc).";
        document.getElementById('ctxDesc').innerHTML = desc;
    }

    let targetData;
    if (mode === 'home') targetData = configData.theme;
    else if (mode === 'league') targetData = configData.theme_league || {};
    else if (mode === 'page') targetData = configData.theme_page || {};
    else if (mode === 'watch') targetData = configData.theme_watch || {};

    if (!targetData || Object.keys(targetData).length === 0) targetData = configData.theme;
    applyThemeState(targetData);
};

function captureThemeState(mode) {
    if(!configData.theme) configData.theme = {};
    if(!configData.theme_league) configData.theme_league = {};
    // ADD THIS:
    if(!configData.theme_page) configData.theme_page = {};
    if(!configData.theme_watch) configData.theme_watch = {};

    const target = (mode === 'home') ? configData.theme : 
                   (mode === 'league') ? configData.theme_league : 
                   (mode === 'page') ? configData.theme_page : 
                   configData.theme_watch; // Handle 'page' mode
    
    for (const [jsonKey, htmlId] of Object.entries(THEME_FIELDS)) {
        const el = document.getElementById(htmlId);
        if(!el) continue;
        target[jsonKey] = (el.type === 'checkbox') ? el.checked : el.value;
    }
}

function applyThemeState(data) {
    for (const [jsonKey, htmlId] of Object.entries(THEME_FIELDS)) {
        const el = document.getElementById(htmlId);
        if(!el) continue;
        const val = data[jsonKey];
        
        if (el.type === 'checkbox') {
            el.checked = (val === true);
        } else {
            el.value = (val !== undefined && val !== null) ? val : "";
        }
    }
    // Refresh visual toggles
    if(window.toggleHeroInputs) toggleHeroInputs();
    if(window.toggleHeaderInputs) toggleHeaderInputs();
    if(window.toggleHeroBoxSettings) toggleHeroBoxSettings();
    if(document.getElementById('themeSysStatusBgOpacity')) {
    document.getElementById('val_sysBgOp').innerText = document.getElementById('themeSysStatusBgOpacity').value || '0.1';
}
    
    // Refresh Sliders text
    ['themeBorderRadius', 'themeMaxWidth', 'themeSectionLogoSize', 'themeBtnRadius', 'themeHeroPillRadius', 'themeLeagueCardBorderWidth', 'themeLeagueCardRadius', 'themeSysStatusDotSize'].forEach(id => {
         const el = document.getElementById(id);
         
         // CORRECTED LOGIC: Single variable declaration
         const displayId = id === 'themeLeagueCardBorderWidth' ? 'val_lcBorderW' : 
                           id === 'themeLeagueCardRadius' ? 'val_lcRadius' :
                           id === 'themeSysStatusDotSize' ? 'val_sysDot' :
                           id.replace('theme','val_').replace('BorderRadius','borderRadius').replace('MaxWidth','maxWidth').replace('SectionLogoSize','secLogo').replace('BtnRadius','btnRadius').replace('HeroPillRadius','pillRadius');
         
         const display = document.getElementById(displayId);
         if(el && display) display.innerText = el.value + 'px';
    });
}
