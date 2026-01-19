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
    'logo_image_shadow_color': 'themeLogoShadow',
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
    'live_dot_color': 'themeLiveDotColor',
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
    'id_wildcard': 'themeIdWildcard',
    'text_top_upcoming_title': 'themeTextTopUpcoming',
    'id_top_upcoming': 'themeIdTopUpcoming',
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
    // ADD THESE LINES:
    'show_more_btn_hover_bg': 'themeShowMoreHoverBg',
    'show_more_btn_hover_text': 'themeShowMoreHoverText',

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
    // ADD THESE NEW LINES:
    'social_sidebar_bg': 'themeSocialSidebarBg',
    'social_sidebar_border': 'themeSocialSidebarBorder',
    'social_btn_bg': 'themeSocialBtnBg',
    'social_btn_border': 'themeSocialBtnBorder',
    'social_btn_hover_bg': 'themeSocialBtnHoverBg',
    'social_btn_hover_border': 'themeSocialBtnHoverBorder',
    'social_count_color': 'themeSocialCountColor',

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
    // FIX: Manually handle Disclaimer Checkbox
    if(document.getElementById('themeFooterShowDisclaimer')) document.getElementById('themeFooterShowDisclaimer').checked = t.footer_show_disclaimer === true;
    if(document.getElementById('val_btnRadius')) document.getElementById('val_btnRadius').innerText = (t.button_border_radius || '4') + 'px';
    if(document.getElementById('val_pillRadius')) document.getElementById('val_pillRadius').innerText = (t.hero_pill_radius || '50') + 'px';
    if(document.getElementById('val_headerWidth')) document.getElementById('val_headerWidth').innerText = (t.header_max_width || '1100') + 'px';
    
    for (const [jsonKey, htmlId] of Object.entries(THEME_FIELDS)) {
        const el = document.getElementById(htmlId);
        if (el) {
            const val = t[jsonKey];
            if (el.type === 'checkbox') {
                el.checked = (val === true);
            } else {
                el.value = (val !== undefined && val !== null) ? val : "";
            }
        }
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
// 1. PROFESSIONAL THEME PRESETS (FULL SUITE)
// ==========================================
const THEME_PRESETS = {
    red: {
        // --- 1. SITE IDENTITY & LAYOUT ---
        font_family_base: "system-ui, -apple-system, sans-serif",
        font_family_headings: "'Inter', system-ui, sans-serif",
        border_radius_base: "4",
        container_max_width: "1200",
        section_logo_size: "24",
        
        // --- 2. GLOBAL PALETTE (High Contrast / Netflix Style) ---
        brand_primary: "#E50914",      // Iconic Broadcast Red
        brand_dark: "#B81D24",         // Deeper Red for hover
        accent_gold: "#FFD700",        // Gold for timers/status
        status_green: "#46d369",       // Success green
        bg_body: "#000000",            // Pure Black (OLED friendly)
        bg_panel: "#141414",           // Dark Gray Panels
        text_main: "#FFFFFF",          // White text
        text_muted: "#B3B3B3",         // Netflix-style muted text
        border_color: "#333333",       // Subtle borders
        scrollbar_thumb_color: "#E50914",

        // --- 3. HEADER (Standard Professional) ---
        header_layout: "standard",
        header_bg: "#000000",
        header_text_color: "#e5e5e5",
        header_link_active_color: "#E50914",
        header_link_hover_color: "#FFFFFF",
        header_highlight_color: "#FFFFFF",
        header_highlight_hover: "#E50914",
        header_max_width: "1200",
        logo_p1_color: "#E50914",
        logo_p2_color: "#FFFFFF",
        logo_image_shadow_color: "#E50914",
        header_border_bottom: "1px solid #333333",
        // ... previous config ...
        show_more_btn_bg: "#151515",
        show_more_btn_text: "#cccccc",
        show_more_btn_radius: "4px",
        show_more_btn_hover_bg: "#E50914", // <--- ADD THIS (Red Hover)
        show_more_btn_hover_text: "#FFFFFF", // <--- ADD THIS
        // --- 12. SOCIAL & FLOATING ---
        social_desktop_top: "50%",
        social_desktop_left: "0",
        social_desktop_scale: "1.0",
        social_sidebar_bg: "#141414",       // Dark Panel
        social_sidebar_border: "#333333",
        social_btn_bg: "#222222",
        social_btn_border: "#333333",
        social_btn_hover_bg: "#E50914",     // Brand Red
        social_btn_hover_border: "#E50914",
        social_count_color: "#808080",
        social_telegram_color: "#0088cc",
        social_whatsapp_color: "#25D366",
        social_reddit_color: "#FF4500",
        social_twitter_color: "#1DA1F2",
        mobile_footer_bg: "#141414",
        // ...

        // --- 4. HERO SECTION (Boxed "Featured" Look) ---
        display_hero: "block",
        hero_layout_mode: "box",
        hero_content_align: "left",
        hero_menu_visible: "flex",
        hero_bg_style: "image", // Uses image or fallback to solid
        hero_bg_solid: "#000000",
        hero_gradient_start: "#000000", 
        hero_gradient_end: "#000000",
        hero_bg_image_overlay_opacity: "0.4",
        hero_h1_color: "#FFFFFF",
        hero_intro_color: "#CCCCCC",
        hero_box_width: "1200px",
        hero_box_border_width: "1",
        hero_box_border_color: "#333333",
        hero_border_bottom_box: true,
        hero_main_border_pos: "none",
        hero_pill_bg: "rgba(255,255,255,0.1)",
        hero_pill_text: "#e5e5e5",
        hero_pill_hover_bg: "#E50914",
        hero_pill_hover_text: "#FFFFFF",
        hero_pill_radius: "4",

        // --- 5. SECTION HEADERS & BORDERS (Visual Hierarchy) ---
        // Live gets a thick red border to pop
        sec_border_live_width: "2",
        sec_border_live_color: "#E50914",
        live_dot_color: "#E50914",
        // Upcoming gets a subtle border
        sec_border_upcoming_width: "1",
        sec_border_upcoming_color: "#333333",
        // Wildcard/Featured gets a brand color accent
        sec_border_wildcard_width: "1",
        sec_border_wildcard_color: "#E50914",
        sec_border_leagues_width: "1",
        sec_border_leagues_color: "#333333",
        sec_border_grouped_width: "1",
        sec_border_grouped_color: "#333333",
        sec_border_league_upcoming_width: "1",
        sec_border_league_upcoming_color: "#333333",

        // --- 6. MATCH ROWS (Clean & Readable) ---
        match_row_bg: "#181818",
        match_row_border: "#333333",
        match_row_hover_bg: "#222222",
        match_row_hover_border: "#E50914",
        match_row_team_name_color: "#FFFFFF",
        match_row_time_main_color: "#B3B3B3",
        match_row_live_bg_start: "rgba(229, 9, 20, 0.15)", // Red tint
        match_row_live_bg_end: "transparent",
        match_row_live_text_color: "#E50914",
        match_row_live_border_left: "4px solid #E50914",
        row_height_mode: "standard",
        match_row_btn_watch_bg: "#E50914",
        match_row_btn_watch_text: "#FFFFFF",

        // --- 7. FOOTER ---
        footer_columns: "3",
        footer_bg_start: "#141414",
        footer_bg_end: "#000000",
        footer_desc_color: "#808080",
        footer_link_color: "#B3B3B3",
        footer_text_align_desktop: "left",
        footer_show_disclaimer: true,
        league_card_bg: "#222222",
        league_card_text: "#FFFFFF",
        league_card_border_width: "1",
        league_card_border_color: "#333333",
        league_card_hover_bg: "#E50914",
        league_card_hover_text: "#FFFFFF",
        league_card_hover_border_color: "#E50914",
        league_card_radius: "4",

        // --- 8. SEO ARTICLE STYLING (Subtle & Clean) ---
        article_bg: "#111111",
        article_text: "#B3B3B3",
        article_line_height: "1.6",
        article_bullet_color: "#E50914",
        article_link_color: "#E50914",
        article_h2_color: "#FFFFFF",
        article_h2_border_width: "1",
        article_h2_border_color: "#333333",
        article_h3_color: "#E5E5E5",
        article_h4_color: "#CCCCCC",

        // --- 9. STATIC PAGES ---
        static_h1_color: "#FFFFFF",
        static_h1_align: "left",
        static_h1_border_width: "2",
        static_h1_border_color: "#E50914",

        // --- 10. SYSTEM STATUS ---
        sys_status_visible: true,
        sys_status_text_color: "#E50914",
        sys_status_bg_color: "#E50914",
        sys_status_bg_opacity: "0.1",
        sys_status_border_color: "#E50914",
        sys_status_border_width: "1",
        sys_status_radius: "4",
        sys_status_dot_color: "#E50914",

        // --- 11. WATCH PAGE ---
        watch_sidebar_swap: false,
        watch_show_ad1: true,
        watch_show_discord: true,
        watch_show_ad2: true,
        chat_header_bg: "#141414",
        chat_header_text: "#E50914",
        watch_table_head_bg: "#181818",
        watch_table_body_bg: "#111111",
        watch_table_border: "#333333",
        watch_team_color: "#FFFFFF",
        watch_vs_color: "#E50914",
        watch_btn_bg: "#E50914",
        watch_btn_text: "#FFFFFF"
    },

    blue: {
        // --- 1. SITE IDENTITY & LAYOUT ---
        font_family_base: "'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
        font_family_headings: "inherit",
        border_radius_base: "8",
        container_max_width: "1400",
        section_logo_size: "28",
        // ...
        show_more_btn_bg: "#1e293b",
        show_more_btn_text: "#cbd5e1",
        show_more_btn_radius: "30px",
        show_more_btn_hover_bg: "#007AFF", // <--- ADD THIS (Blue Hover)
        show_more_btn_hover_text: "#FFFFFF", // <--- ADD THIS
        // ...

        // --- 2. GLOBAL PALETTE (Modern Tech / Sky Style) ---
        brand_primary: "#007AFF",      // Vivid Tech Blue
        brand_dark: "#0051A8",         // Deep Blue
        accent_gold: "#00C7FF",        // Cyan accent for timers
        status_green: "#34C759",       // Apple style green
        bg_body: "#0F172A",            // Slate 900
        bg_panel: "#1E293B",           // Slate 800
        text_main: "#F8FAFC",          // Slate 50
        text_muted: "#94A3B8",         // Slate 400
        border_color: "#334155",       // Slate 700
        scrollbar_thumb_color: "#007AFF",

        // --- 3. HEADER (Glassy & Wide) ---
        header_layout: "standard",
        header_bg: "rgba(15, 23, 42, 0.8)", // Glass effect
        header_text_color: "#94A3B8",
        header_link_active_color: "#007AFF",
        header_link_hover_color: "#FFFFFF",
        header_highlight_color: "#FFFFFF",
        header_highlight_hover: "#00C7FF",
        header_max_width: "1400",
        logo_p1_color: "#F8FAFC",
        logo_p2_color: "#007AFF",
        logo_image_shadow_color: "#007AFF",
        header_border_bottom: "1px solid rgba(51, 65, 85, 0.5)",
        // ... previous config ...
        // --- 12. SOCIAL & FLOATING ---
        social_desktop_top: "50%",
        social_desktop_left: "0",
        social_desktop_scale: "1.0",
        social_sidebar_bg: "rgba(15, 23, 42, 0.9)", // Glassy Blue
        social_sidebar_border: "#334155",
        social_btn_bg: "#1E293B",
        social_btn_border: "#334155",
        social_btn_hover_bg: "#007AFF",     // Brand Blue
        social_btn_hover_border: "#007AFF",
        social_count_color: "#94A3B8",
        social_telegram_color: "#38bdf8",
        social_whatsapp_color: "#4ade80",
        social_reddit_color: "#fb7185",
        social_twitter_color: "#38bdf8",
        mobile_footer_bg: "#0F172A",
        // ...

        // --- 4. HERO SECTION (Full Width Modern) ---
        display_hero: "block",
        hero_layout_mode: "full",
        hero_content_align: "center",
        hero_menu_visible: "flex",
        hero_bg_style: "gradient",
        hero_gradient_start: "#0F172A",
        hero_gradient_end: "#020617",
        hero_h1_color: "#FFFFFF",
        hero_intro_color: "#94A3B8",
        hero_pill_bg: "#1E293B",
        hero_pill_text: "#CBD5E1",
        hero_pill_hover_bg: "#007AFF",
        hero_pill_hover_text: "#FFFFFF",
        hero_pill_radius: "50",
        hero_main_border_pos: "full",
        hero_main_border_width: "1",
        hero_main_border_color: "#334155",

        // --- 5. SECTION HEADERS ---
        sec_border_live_width: "1",
        sec_border_live_color: "#007AFF", // Blue for live here
        sec_border_upcoming_width: "1",
        sec_border_upcoming_color: "#334155",
        sec_border_wildcard_width: "1",
        sec_border_wildcard_color: "#00C7FF",
        sec_border_leagues_width: "1",
        sec_border_leagues_color: "#334155",
        sec_border_grouped_width: "1",
        sec_border_grouped_color: "#334155",
        sec_border_league_upcoming_width: "1",
        sec_border_league_upcoming_color: "#334155",

        // --- 6. MATCH ROWS (Spacious) ---
        match_row_bg: "#1E293B",
        match_row_border: "#334155",
        match_row_hover_bg: "#334155",
        match_row_hover_border: "#007AFF",
        match_row_team_name_color: "#F8FAFC",
        match_row_time_main_color: "#94A3B8",
        match_row_live_bg_start: "rgba(0, 122, 255, 0.15)",
        match_row_live_bg_end: "transparent",
        match_row_live_text_color: "#60A5FA",
        match_row_live_border_left: "4px solid #007AFF",
        live_dot_color: "#007AFF",
        row_height_mode: "spacious", // Airy feel
        match_row_btn_watch_bg: "#007AFF",
        match_row_btn_watch_text: "#FFFFFF",

        // --- 7. FOOTER ---
        footer_columns: "2",
        footer_bg_start: "#1E293B",
        footer_bg_end: "#0F172A",
        footer_desc_color: "#94A3B8",
        footer_link_color: "#64748B",
        footer_text_align_desktop: "center",
        footer_show_disclaimer: false,
        league_card_bg: "#334155",
        league_card_text: "#F8FAFC",
        league_card_border_width: "0",
        league_card_border_color: "transparent",
        league_card_hover_bg: "#007AFF",
        league_card_hover_text: "#FFFFFF",
        league_card_radius: "8",

        // --- 8. SEO ARTICLE ---
        article_bg: "transparent",
        article_text: "#94A3B8",
        article_line_height: "1.7",
        article_bullet_color: "#007AFF",
        article_link_color: "#00C7FF",
        article_h2_color: "#F8FAFC",
        article_h2_border_width: "0",
        article_h2_border_color: "transparent",
        article_h3_color: "#E2E8F0",
        article_h4_color: "#CBD5E1",

        // --- 9. STATIC PAGES ---
        static_h1_color: "#F8FAFC",
        static_h1_align: "center",
        static_h1_border_width: "0",
        static_h1_border_color: "transparent",

        // --- 10. SYSTEM STATUS ---
        sys_status_visible: true,
        sys_status_text_color: "#60A5FA",
        sys_status_bg_color: "#007AFF",
        sys_status_bg_opacity: "0.15",
        sys_status_border_color: "#007AFF",
        sys_status_border_width: "1",
        sys_status_radius: "20",
        sys_status_dot_color: "#60A5FA",

        // --- 11. WATCH PAGE ---
        watch_sidebar_swap: true, // Chat on Left for desktop apps feel
        chat_header_bg: "#1E293B",
        chat_header_text: "#F8FAFC",
        watch_table_head_bg: "#334155",
        watch_table_body_bg: "#1E293B",
        watch_table_border: "#475569",
        watch_team_color: "#F8FAFC",
        watch_vs_color: "#007AFF",
        watch_btn_bg: "#007AFF",
        watch_btn_text: "#FFFFFF"
    },

    green: {
        // --- 1. SITE IDENTITY & LAYOUT ---
        font_family_base: "'Roboto Condensed', 'Segoe UI', sans-serif", // Data-dense font
        font_family_headings: "'Impact', 'Arial Black', sans-serif", // Sporty headlines
        border_radius_base: "0", // Square / Sharp edges
        container_max_width: "1600",
        section_logo_size: "22",
        // ...
        show_more_btn_bg: "#052e16",
        show_more_btn_text: "#86efac",
        show_more_btn_radius: "0px",
        show_more_btn_hover_bg: "#00E676", // <--- ADD THIS (Green Hover)
        show_more_btn_hover_text: "#000000", // <--- ADD THIS
        // ...

        // --- 2. GLOBAL PALETTE (Betting/Stats/Pitch Style) ---
        brand_primary: "#00E676",      // Neon Green
        brand_dark: "#00A854",         // Darker Green
        accent_gold: "#FFEB3B",        // Bright Yellow
        status_green: "#00E676",
        bg_body: "#050505",            // Pitch Black
        bg_panel: "#121212",           // Dark Gray
        text_main: "#EEEEEE",          // Off-white
        text_muted: "#AAAAAA",         // Silver
        border_color: "#2A2A2A",       // Dark borders
        scrollbar_thumb_color: "#00E676",

        // --- 3. HEADER (App Style) ---
        header_layout: "center",       // Mobile-first style
        header_bg: "#080808",
        header_text_color: "#AAAAAA",
        header_link_active_color: "#FFFFFF",
        header_link_hover_color: "#00E676",
        header_highlight_color: "#00E676",
        header_highlight_hover: "#FFFFFF",
        header_max_width: "1600",
        logo_p1_color: "#FFFFFF",
        logo_p2_color: "#00E676",
        logo_image_shadow_color: "#00E676",
        header_border_bottom: "2px solid #00E676", // Techy bottom line
        // ... previous config ...
        // --- 12. SOCIAL & FLOATING ---
        social_desktop_top: "50%",
        social_desktop_left: "0",
        social_desktop_scale: "1.0",
        social_sidebar_bg: "rgba(5, 20, 5, 0.95)", // Deep Green
        social_sidebar_border: "#14532D",
        social_btn_bg: "#1A1A1A",
        social_btn_border: "#14532D",
        social_btn_hover_bg: "#00E676",     // Neon Green
        social_btn_hover_border: "#00E676",
        social_count_color: "#4ade80",
        social_telegram_color: "#00E676",
        social_whatsapp_color: "#00E676",
        social_reddit_color: "#00E676",     // Mono-green look
        social_twitter_color: "#00E676",
        mobile_footer_bg: "#051105",
        // ...

        // --- 4. HERO SECTION (Compact) ---
        display_hero: "block",
        hero_layout_mode: "full",
        hero_content_align: "center",
        hero_menu_visible: "flex",
        hero_bg_style: "gradient",
        hero_gradient_start: "#0A2912", // Dark Forest Green
        hero_gradient_end: "#050505",
        hero_h1_color: "#FFFFFF",
        hero_intro_color: "#AAAAAA",
        hero_pill_bg: "#1A1A1A",
        hero_pill_text: "#CCCCCC",
        hero_pill_hover_bg: "#00E676",
        hero_pill_hover_text: "#000000", // Black text on green pill
        hero_pill_radius: "0",
        hero_main_border_pos: "full",
        hero_main_border_width: "1",
        hero_main_border_color: "#00E676",

        // --- 5. SECTION HEADERS ---
        sec_border_live_width: "1",
        sec_border_live_color: "#00E676",
        sec_border_upcoming_width: "1",
        sec_border_upcoming_color: "#2A2A2A",
        sec_border_wildcard_width: "1",
        sec_border_wildcard_color: "#FFEB3B",
        sec_border_leagues_width: "1",
        sec_border_leagues_color: "#2A2A2A",
        sec_border_grouped_width: "1",
        sec_border_grouped_color: "#2A2A2A",
        sec_border_league_upcoming_width: "1",
        sec_border_league_upcoming_color: "#2A2A2A",

        // --- 6. MATCH ROWS (Compact Data) ---
        match_row_bg: "#121212",
        match_row_border: "#2A2A2A",
        match_row_hover_bg: "#1A1A1A",
        match_row_hover_border: "#00E676",
        match_row_team_name_color: "#FFFFFF",
        match_row_time_main_color: "#AAAAAA",
        match_row_live_bg_start: "#0A2912",
        match_row_live_bg_end: "#121212",
        match_row_live_text_color: "#00E676",
        live_dot_color: "#00E676",
        match_row_live_border_left: "3px solid #00E676",
        row_height_mode: "compact", // High density
        match_row_btn_watch_bg: "#00E676",
        match_row_btn_watch_text: "#000000",

        // --- 7. FOOTER ---
        footer_columns: "3",
        footer_bg_start: "#0A0A0A",
        footer_bg_end: "#000000",
        footer_desc_color: "#888888",
        footer_link_color: "#00E676",
        footer_text_align_desktop: "left",
        footer_show_disclaimer: true,
        league_card_bg: "#1A1A1A",
        league_card_text: "#FFFFFF",
        league_card_border_width: "1",
        league_card_border_color: "#333333",
        league_card_hover_bg: "#00E676",
        league_card_hover_text: "#000000",
        league_card_hover_border_color: "#00E676",
        league_card_radius: "0",

        // --- 8. SEO ARTICLE ---
        article_bg: "#0F0F0F",
        article_text: "#AAAAAA",
        article_line_height: "1.5",
        article_bullet_color: "#00E676",
        article_link_color: "#00E676",
        article_h2_color: "#FFFFFF",
        article_h2_border_width: "1",
        article_h2_border_color: "#00E676",
        article_h3_color: "#DDDDDD",
        article_h4_color: "#CCCCCC",

        // --- 9. STATIC PAGES ---
        static_h1_color: "#FFFFFF",
        static_h1_align: "left",
        static_h1_border_width: "2",
        static_h1_border_color: "#00E676",

        // --- 10. SYSTEM STATUS ---
        sys_status_visible: true,
        sys_status_text_color: "#00E676",
        sys_status_bg_color: "#00E676",
        sys_status_bg_opacity: "0.1",
        sys_status_border_color: "#00E676",
        sys_status_border_width: "1",
        sys_status_radius: "0",
        sys_status_dot_color: "#00E676",

        // --- 11. WATCH PAGE ---
        watch_sidebar_swap: false,
        chat_header_bg: "#0A2912",
        chat_header_text: "#00E676",
        watch_table_head_bg: "#1A1A1A",
        watch_table_body_bg: "#121212",
        watch_table_border: "#333333",
        watch_team_color: "#FFFFFF",
        watch_vs_color: "#00E676",
        watch_btn_bg: "#00E676",
        watch_btn_text: "#000000"
    }
};
// ==========================================
// 2. THE APPLY LOGIC (UPDATED FOR FULL PRESETS)
// ==========================================
window.applyPreset = (presetName) => {
    if(!THEME_PRESETS[presetName]) return;
    const p = THEME_PRESETS[presetName];

    if(!confirm(`Apply ${presetName.toUpperCase()} preset? This will overwrite your current settings.`)) return;

    // Iterate through the JSON keys in the preset
    Object.keys(p).forEach(jsonKey => {
        // Translate JSON key to HTML ID using the mapping
        const htmlId = THEME_FIELDS[jsonKey];
        if (!htmlId) return;

        const el = document.getElementById(htmlId);
        if (el) {
            const val = p[jsonKey];
            
            // Handle Checkboxes (Boolean values)
            if (el.type === 'checkbox') {
                el.checked = (val === true || val === "true");
            } 
            // Handle Standard Inputs
            else {
                el.value = (val !== undefined && val !== null) ? val : "";
            }
        }
    });

    // 2. Refresh Visual Toggles (Layouts, Gradients, etc.)
    if(typeof toggleHeroInputs === 'function') toggleHeroInputs();
    if(typeof toggleHeaderInputs === 'function') toggleHeaderInputs();
    if(typeof toggleHeroBoxSettings === 'function') toggleHeroBoxSettings();
    if(typeof toggleFooterSlots === 'function') toggleFooterSlots();

    // 3. Update Range Sliders Text Displays
    ['themeBorderRadius', 'themeMaxWidth', 'themeSectionLogoSize', 'themeBtnRadius', 
     'themeHeroPillRadius', 'themeLeagueCardBorderWidth', 'themeLeagueCardRadius', 
     'themeSysStatusDotSize', 'themeHeaderWidth'].forEach(id => {
         const el = document.getElementById(id);
         if(!el) return;
         
         // Helper to find the span ID based on your naming convention
         let displayId = "";
         if(id === 'themeLeagueCardBorderWidth') displayId = 'val_lcBorderW';
         else if(id === 'themeLeagueCardRadius') displayId = 'val_lcRadius';
         else if(id === 'themeSysStatusDotSize') displayId = 'val_sysDot';
         else if(id === 'themeHeaderWidth') displayId = 'val_headerWidth';
         else {
             displayId = id.replace('theme','val_')
                           .replace('BorderRadius','borderRadius')
                           .replace('MaxWidth','maxWidth')
                           .replace('SectionLogoSize','secLogo')
                           .replace('BtnRadius','btnRadius')
                           .replace('HeroPillRadius','pillRadius');
         }

         const display = document.getElementById(displayId);
         if(display) display.innerText = el.value + 'px';
    });

    alert(`${presetName.toUpperCase()} preset loaded! Click 'Save' to build.`);
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
        <label style="color:#facc15; font-weight:700;">Rich Snippets</label>
        <label><input type="checkbox" id="schemaOrg" ${p.schemas.org ? 'checked' : ''}> Organization (Entity)</label>
        <label><input type="checkbox" id="schemaWebsite" ${p.schemas.website ? 'checked' : ''}> WebSite (Sitelinks)</label>
        <label><input type="checkbox" id="schemaAbout" ${p.schemas.about ? 'checked' : ''}> About Page (for DMCA/Contact)</label>
        
        <label><input type="checkbox" id="schemaFaq" ${p.schemas.faq ? 'checked' : ''} onchange="toggleFaqEditor(this.checked)"> FAQ Schema</label>
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
    p.schemas.about = document.getElementById('schemaAbout').checked; // Saved
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
    // REPLACE THIS BLOCK INSIDE renderLeagues()
    c.innerHTML = Object.keys(g).sort().map(l => `
        <div class="card">
            <div class="league-card-header">
                <div style="display:flex; align-items:center; gap:10px;">
                    <h3 style="margin:0;">${l}</h3>
                    <button class="btn-icon" onclick="openLeagueMetaModal('${l}')" title="Edit Entity Links" style="font-size:1rem; padding:4px;">🔗</button>
                </div>
                <span>${g[l].length} Teams</span>
            </div>
            <label>Teams</label>
            <textarea class="team-list-editor" rows="6" data-league="${l}">${g[l].join(', ')}</textarea>
        </div>
    `).join('');
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
    const map = {}; 
    document.querySelectorAll('.team-list-editor').forEach(t => { 
        // FIX: Only process elements that actually have a data-league attribute
        // This ignores the Watch Article textareas
        const leagueName = t.getAttribute('data-league');
        if (leagueName && leagueName.trim() !== "") {
            map[leagueName] = t.value.split(',').map(x=>x.trim().toLowerCase().replace(/\s+/g,'-')).filter(x=>x.length>0); 
        }
    });
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
    // Save Watch Settings
    configData.watch_settings = {
        supabase_url: getVal('supaUrl'),
        supabase_key: getVal('supaKey'),
        
        // Versus Match Settings
        meta_title: getVal('watchPageTitle'),
        meta_desc: getVal('watchPageDesc'),
        article: getVal('watchPageArticle'),
        
        // Single Match Settings (NEW)
        meta_title_single: getVal('watchPageTitleSingle'),
        meta_desc_single: getVal('watchPageDescSingle'),
        article_single: getVal('watchPageArticleSingle'),
        
        // Ads
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
// ==========================================
// NEW: LEAGUE METADATA LOGIC
// ==========================================
let currentMetaLeague = null;

window.openLeagueMetaModal = (leagueName) => {
    currentMetaLeague = leagueName;
    document.getElementById('metaModalLeagueName').innerText = leagueName;
    
    // Ensure config container exists
    if(!configData.league_metadata) configData.league_metadata = {};
    
    // Get existing links array and join with comma+newline for easy editing
    const links = configData.league_metadata[leagueName] || [];
    document.getElementById('metaLinksInput').value = links.join(',\n');
    
    document.getElementById('leagueMetaModal').style.display = 'flex';
};

window.saveLeagueMeta = () => {
    if(!currentMetaLeague) return;
    
    const rawText = document.getElementById('metaLinksInput').value;
    
    // Split by comma or newline, trim whitespace, and remove empty strings
    const linkArray = rawText.split(/[\n,]+/).map(s => s.trim()).filter(s => s.length > 0);
    
    if(!configData.league_metadata) configData.league_metadata = {};
    
    if(linkArray.length > 0) {
        configData.league_metadata[currentMetaLeague] = linkArray;
    } else {
        delete configData.league_metadata[currentMetaLeague];
    }
    
    document.getElementById('leagueMetaModal').style.display = 'none';
    
    // Visual Feedback
    const btn = document.querySelector(`button[onclick="openLeagueMetaModal('${currentMetaLeague}')"]`);
    if(btn) {
        btn.style.color = "#22c55e"; // Turn green to show data exists
        setTimeout(() => btn.style.color = "", 2000);
    }
};
