import streamlit as st
import streamlit.components.v1 as _stc
from google import genai
from google.genai import types
from openai import OpenAI
import base64, json, io, hmac, time, re
from PIL import Image
from datetime import datetime, timezone

# ══════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════
st.set_page_config(
    page_title="♻️ TriSmart",
    page_icon="♻️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════
# CSS — responsive PC · iOS · iPadOS · Android
# ══════════════════════════════════════════════
# NOTE: Google Fonts @import intentionally removed — it blocks iOS Safari
# rendering on slow connections. We use the native system-ui font stack
# (San Francisco on Apple, Roboto on Android) which loads instantly.
st.markdown("""
<style>
/* ── Base — system font stack, no external @import ── */
html, body, [class*="css"] {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Helvetica Neue", Arial, sans-serif;
    -webkit-text-size-adjust: 100%;
    touch-action: manipulation;
}

/* ── Viewport height: use -webkit-fill-available as iOS fallback ── */
.stApp {
    min-height: 100vh;
    min-height: -webkit-fill-available;
}

/* ── Safe-area insets — iPhone notch, Dynamic Island, home bar ── */
.block-container {
    padding-left:   max(1rem, env(safe-area-inset-left))   !important;
    padding-right:  max(1rem, env(safe-area-inset-right))  !important;
    padding-top:    max(1rem, env(safe-area-inset-top))    !important;
    padding-bottom: max(1rem, env(safe-area-inset-bottom)) !important;
    max-width: 860px !important;
    margin: 0 auto !important;
}

/* ── Hero ── */
.hero-title {
    font-size: clamp(1.6rem, 6vw, 2.4rem);
    font-weight: 700;
    background: linear-gradient(135deg, #00d084, #00a8ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: .2rem;
    line-height: 1.2;
}
.hero-sub {
    text-align: center;
    color: #888;
    font-size: clamp(.85rem, 3vw, 1rem);
    margin-bottom: 1.5rem;
}

/* ── Step badges ── */
.step-badge {
    background: #1e3a2a;
    color: #00d084;
    border-radius: 50%;
    width: 26px; height: 26px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: .8rem;
    margin-right: 6px;
    flex-shrink: 0;
}

/* ── Role badges ── */
.role-badge-admin {
    background: #1a2a4a;
    border: 1px solid #4488ff;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: .75rem;
    color: #88aaff;
}
.role-badge-guest {
    background: #2a2a1a;
    border: 1px solid #aaa;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: .75rem;
    color: #aaa;
}

/* ── Buttons — 48 px minimum tap target (Apple HIG / WCAG 2.5.5) ── */
.stButton > button {
    min-height: 48px;
    font-size: clamp(.9rem, 3vw, 1rem) !important;
    border-radius: 10px !important;
    width: 100%;
    -webkit-tap-highlight-color: transparent;
    -webkit-appearance: none;   /* prevent iOS default button styling */
}

/* ── Radio — larger touch area ── */
.stRadio label {
    font-size: clamp(.85rem, 3vw, 1rem) !important;
    padding: 8px 4px;
    cursor: pointer;
}
.stRadio [data-baseweb="radio"] { padding: 4px 0; }

/* ── Tabs — fill width, scrollable, easy tap ── */
.stTabs [data-baseweb="tab"] {
    font-size: clamp(.85rem, 3vw, 1rem) !important;
    padding: 12px 16px !important;
    flex: 1;
    text-align: center;
    min-height: 48px;
}
.stTabs [data-baseweb="tab-list"] {
    width: 100%;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    flex-wrap: nowrap;
}

/* ── Expander ── */
.stExpander summary {
    font-size: clamp(.85rem, 3vw, 1rem) !important;
    padding: 12px !important;
    min-height: 48px;
    display: flex;
    align-items: center;
}

/* ── Camera input — full width ── */
.stCameraInput, .stCameraInput > div, .stCameraInput video {
    width: 100% !important;
    max-width: 100% !important;
    border-radius: 12px !important;
}

/* ── File uploader — bigger drop zone ── */
.stFileUploader > div { width: 100% !important; }
.stFileUploader [data-testid="stFileUploaderDropzone"] {
    min-height: 80px;
    border-radius: 12px !important;
}

/* ── Text inputs — font-size 16px prevents iOS auto-zoom on focus ── */
.stSelectbox > div, .stTextInput > div > div {
    font-size: clamp(.85rem, 3vw, 1rem) !important;
}
.stTextInput input, .stTextArea textarea, select {
    font-size: 16px !important;
    border-radius: 8px !important;
    -webkit-appearance: none;   /* prevent iOS default input styling */
}

/* ── Checkboxes — bigger tap area ── */
.stCheckbox label {
    min-height: 40px;
    display: flex;
    align-items: center;
    cursor: pointer;
    padding: 4px 0;
}

/* ── Metrics ── */
[data-testid="stMetricValue"] { font-size: 1.4rem !important; }

/* ══ TABLET 768 – 1024 px ══ */
@media (max-width: 1024px) and (min-width: 769px) {
    .block-container { max-width: 720px !important; }
}

/* ══ MOBILE ≤ 768 px ══ */
@media (max-width: 768px) {
    .block-container {
        padding-left:  max(.75rem, env(safe-area-inset-left))  !important;
        padding-right: max(.75rem, env(safe-area-inset-right)) !important;
        max-width: 100% !important;
    }
    .hero-title { font-size: clamp(1.4rem, 7vw, 1.8rem); }

    /* Stack all st.columns vertically */
    [data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }

    .stButton > button { min-height: 52px; font-size: 1rem !important; }
    .result-card { padding: 1rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.2rem !important; }

    /* Sidebar: scrollable overlay — use vh fallback for iOS < 15.4 */
    [data-testid="stSidebar"] {
        overflow-y: auto !important;
        -webkit-overflow-scrolling: touch !important;
        max-height: 100vh !important;
        max-height: -webkit-fill-available !important;
    }
}

/* ══ SMALL PHONE ≤ 480 px ══ */
@media (max-width: 480px) {
    .hero-title { font-size: 1.4rem; }
    .step-badge { width: 22px; height: 22px; font-size: .7rem; }
    .stTabs [data-baseweb="tab"] { padding: 10px 8px !important; font-size: .82rem !important; }
    [data-testid="stMetricValue"] { font-size: 1.1rem !important; }
}

/* ══ LANDSCAPE PHONE ══ */
@media (max-height: 500px) and (orientation: landscape) {
    .hero-title { font-size: 1.2rem; margin-bottom: .1rem; }
    .hero-sub   { margin-bottom: .5rem; }
    .block-container { padding-top: .5rem !important; }
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# LANGUES UI — chargées depuis lang/*.json
# ══════════════════════════════════════════════
import os as _os

LANGUAGES = {
    "Français 🇫🇷": "fr",
    "English 🇬🇧":  "en",
    "Deutsch 🇩🇪":  "de",
    "Español 🇪🇸":  "es",
    "한국어 🇰🇷":   "ko",
    "中文 🇨🇳":     "zh",
    "日本語 🇯🇵":   "ja",
}

@st.cache_data
def load_lang(code: str) -> dict:
    """Charge le fichier lang/{code}.json (mis en cache par Streamlit)."""
    try:
        base = _os.path.dirname(_os.path.abspath(__file__))
    except NameError:
        base = _os.getcwd()
    path = _os.path.join(base, "lang", f"{code}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_waste() -> dict:
    """Charge lang/waste.json (mis en cache)."""
    try:
        base = _os.path.dirname(_os.path.abspath(__file__))
    except NameError:
        base = _os.getcwd()
    path = _os.path.join(base, "lang", "waste.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def get_waste_label(key):
    lc = get_lang_code()
    waste = load_waste()
    return waste.get(key, {}).get(lc, waste.get(key, {}).get("en", key))

COUNTRY_GUIDES = {
    "France 🇫🇷": {"rows": [
        ("plastic_cans",    "🟡 Jaune"),
        ("cardboard_paper", "🟡 Jaune"),
        ("glass",           "🟢 Verte"),
        ("food_waste",      "🟤 Marron"),
        ("general_waste",   "⚫ Noire"),
        ("hazardous",       "🔴 Déchetterie"),
        ("electronics",     "🔴 DEEE"),
    ]},
    "Belgique 🇧🇪": {"rows": [
        ("pmc_be",          "🔵 Sac bleu"),
        ("cardboard_paper", "🟡 Sac jaune"),
        ("glass",           "🟢 Bulles verre"),
        ("food_waste",      "🟤 GFT / Compost"),
        ("general_waste",   "⚫ Sac blanc"),
        ("hazardous",       "🔴 Recypark"),
    ]},
    "Suisse 🇨🇭": {"rows": [
        ("plastic_cans",    "🔵 Points PET/alu"),
        ("glass",           "🟢 Conteneur verre"),
        ("cardboard_paper", "🟡 Collecte papier"),
        ("food_waste",      "🟤 Compost"),
        ("general_waste",   "⚫ Sac taxé"),
        ("textiles",        "👕 Points collecte"),
        ("hazardous",       "🔴 Déchetterie"),
    ]},
    "Deutschland 🇩🇪": {"rows": [
        ("plastic_cans",    "🟡 Gelbe Tonne"),
        ("cardboard_paper", "🔵 Blaue Tonne"),
        ("glass",           "🟢 Glascontainer"),
        ("food_waste",      "🟤 Braune Tonne"),
        ("general_waste",   "⚫ Schwarze Tonne"),
        ("hazardous",       "🔴 Wertstoffhof"),
        ("electronics",     "🔴 Wertstoffhof"),
    ]},
    "United Kingdom 🇬🇧": {"rows": [
        ("plastic_cans",    "🔵 Blue bin"),
        ("glass",           "🟢 Bottle bank"),
        ("food_waste",      "🟤 Food caddy"),
        ("general_waste",   "⚫ Black bin"),
        ("garden_waste",    "🟢 Green bin"),
        ("hazardous",       "🔴 HWRC"),
        ("electronics",     "🔴 WEEE"),
    ]},
    "United States 🇺🇸": {"rows": [
        ("plastic_cans",    "🔵 Blue bin"),
        ("glass",           "🟢 Glass bin"),
        ("food_waste",      "🟤 Compost"),
        ("garden_waste",    "🟢 Green bin"),
        ("general_waste",   "⚫ Black bin"),
        ("hazardous",       "🔴 HHW facility"),
        ("electronics",     "🔴 E-waste drop-off"),
    ]},
    "日本 🇯🇵": {"rows": [
        ("combustible_jp",    "🔴 可燃ごみ袋"),
        ("noncombustible_jp", "⚫ 不燃ごみ袋"),
        ("plastic_wrap_jp",   "🟡 プラ袋"),
        ("pet_jp",            "🔵 PET回収"),
        ("glass",             "🟢 びん回収"),
        ("cardboard_paper",   "📦 集団回収"),
        ("bulky_jp",          "📞 事前申込"),
    ]},
    "대한민국 🇰🇷": {"rows": [
        ("food_waste",      "🟤 음식물봉투"),
        ("cardboard_paper", "📦 종이류"),
        ("recyclables_kr",  "🔵 재활용함"),
        ("general_kr",      "⚫ 종량제봉투"),
        ("bulky_jp",        "📞 구청신고"),
        ("fluorescent_kr",  "🔴 전용수거함"),
        ("electronics",     "🔴 무상방문수거"),
    ]},
    "中国 🇨🇳": {"rows": [
        ("food_waste",      "🟤 厨余垃圾桶"),
        ("recyclable_cn",   "🔵 可回收物桶"),
        ("hazardous_cn",    "🔴 有害垃圾桶"),
        ("other_cn",        "⚫ 其他垃圾桶"),
    ]},
    "España 🇪🇸": {"rows": [
        ("plastic_cans",    "🟡 Amarillo"),
        ("cardboard_paper", "🔵 Azul"),
        ("glass",           "🟢 Verde (iglú)"),
        ("food_waste",      "🟤 Marrón"),
        ("general_waste",   "⚫ Gris/Negro"),
        ("hazardous",       "🔴 Punto Limpio"),
        ("electronics",     "🔴 Punto Limpio"),
    ]},
}

# ══════════════════════════════════════════════
# CONSTANTES MODÈLES
# ══════════════════════════════════════════════
GEMINI_FREE_MODELS = {
    "gemini-2.5-flash-lite":         "⚡ 2.5 Flash Lite  (~1 000 req/day) ✅",
    "gemini-2.5-flash":              "🚀 2.5 Flash       (~250 req/day)",
    "gemini-3-flash-preview":        "🔥 3 Flash Preview (~200 req/day)",
    "gemini-3.1-flash-lite-preview": "🧪 3.1 Flash Lite  (~200 req/day)",
}
OPENROUTER_FREE_MODELS = {
    "openrouter/free":                               "🎲 Auto-free router",
    "qwen/qwen2.5-vl-72b-instruct:free":             "🧠 Qwen 2.5 VL 72B",
    "meta-llama/llama-3.2-11b-vision-instruct:free": "🦙 Llama 3.2 11B Vision",
    "google/gemma-3-27b-it:free":                    "💎 Gemma 3 27B",
    "mistralai/mistral-small-3.1-24b-instruct:free": "🌬️ Mistral Small 3.1",
}
DEFAULT_GEMINI     = "gemini-2.5-flash-lite"
DEFAULT_OPENROUTER = "openrouter/free"

DEFAULT_BINS = [
    {"name":"🟡 Poubelle Jaune",      "couleur":"#f5c518","description":"Recyclables : plastiques, métaux, cartons, briques"},
    {"name":"🟢 Poubelle Verte",      "couleur":"#00b34a","description":"Verre uniquement : bouteilles, bocaux, pots"},
    {"name":"⚫ Poubelle Noire/Grise","couleur":"#888888","description":"Ordures ménagères résiduelles non recyclables"},
    {"name":"🟤 Poubelle Marron",     "couleur":"#8B4513","description":"Bio-déchets et compostables"},
]

# ══════════════════════════════════════════════
# RÔLES
# ══════════════════════════════════════════════
def is_admin(): return st.session_state.get("role") == "admin"
def is_guest(): return st.session_state.get("role") == "guest"
def is_logged(): return st.session_state.get("role") in ("admin","guest")

# ══════════════════════════════════════════════
# USAGE TRACKING
# ══════════════════════════════════════════════
if "usage_log" not in st.session_state:
    st.session_state.usage_log = []

def log_analysis(success, provider, model, objet="", role="guest"):
    st.session_state.usage_log.append({
        "ts": datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "role": role, "provider": provider, "model": model,
        "objet": objet, "success": success,
    })

# ══════════════════════════════════════════════
# HELPERS LANGUE
# ══════════════════════════════════════════════

# Minimal inline fallback so the UI never crashes if lang/*.json are missing
_FALLBACK_STRINGS = {
    "login_title": "Login", "login_subtitle": "AI Waste Sorting",
    "username": "Username", "password": "Password",
    "login_btn": "Log in", "login_error": "Invalid credentials",
    "guest_btn": "Continue without account",
    "guest_hint": "Guests can analyse waste but cannot access the dashboard.",
    "logout": "Log out", "config": "Settings", "dashboard": "Dashboard",
    "lang_label": "Language", "country_label": "Country",
    "provider": "Provider", "model_label": "Model",
    "tab_camera": "📷 Camera", "tab_upload": "🖼️ Upload",
    "analyze_btn": "🔍 Analyse", "ready": "Image ready.",
    "result_title": "### 🎯 Result", "material": "Material",
    "confidence": "Confidence", "recyclable": "✅ Recyclable",
    "not_recyclable": "❌ Not recyclable", "dangerous": "⚠️ Hazardous",
    "not_dangerous": "✅ Not hazardous", "gestures": "**Tips:**",
    "alternatives": "**Alternatives:**", "debug_title": "Debug / JSON",
    "guide_title": "Sorting guide", "guide_tip": "Check your local rules.",
    "key_missing_main": "Add your API key in the sidebar ←",
    "no_bin_active": "Enable at least one bin in the sidebar.",
    "json_err": "JSON parse error", "quota_err": "Quota exceeded (429). Try another model.",
    "err_prefix": "Error", "scan_title": "Scan bins",
    "scan_hint": "Photograph your bins to configure them automatically.",
    "scan_btn": "Identify bins", "scan_success": "bins detected",
    "scan_added": "added", "scan_updated": "updated",
    "scan_err_json": "Could not parse bin data.", "scan_key_missing": "API key missing.",
    "scan_err_quota": "Quota exceeded.",
    "bins_title": "Active bins", "add_title": "Add a bin",
    "bin_name_ph": "Bin name", "bin_content": "Accepted content",
    "add_btn": "Add", "reset_btn": "Reset to defaults",
    "key_loaded_gemini": "✅ Gemini key loaded",
    "key_miss_gemini": "⚠️ Gemini key missing",
    "key_loaded_or": "✅ OpenRouter key loaded",
    "key_miss_or": "⚠️ OpenRouter key missing",
    "model_hint_gemini": "Choose a Gemini model:",
    "model_hint_or": "Choose an OpenRouter model:",
    "step1": "Photo", "step2": "Analyse", "step3": "Sort",
    "dash_total": "Total", "dash_ok": "Success", "dash_err": "Errors",
    "dash_guest": "Guest", "dash_log": "**Log:**",
    "dash_stats": "**Stats:**", "dash_by_provider": "By provider",
    "dash_by_role": "By role", "dash_top": "**Top objects:**",
    "dash_clear": "Clear log", "dash_empty": "No analyses yet.",
    "ai_lang": "English",
}

def get_lang_code():
    label = st.session_state.get("ui_lang", "Français 🇫🇷")
    return LANGUAGES.get(label, "fr")

def t(key: str) -> str:
    """Return UI string for current language, with robust fallback chain."""
    lc = get_lang_code()
    try:
        val = load_lang(lc).get(key)
        if val is not None:
            return val
        # fallback 1: English json
        val = load_lang("en").get(key)
        if val is not None:
            return val
    except Exception:
        pass
    # fallback 2: inline dict (works even if lang/ folder is missing)
    return _FALLBACK_STRINGS.get(key, key)

def get_ai_lang():
    try:
        return load_lang(get_lang_code()).get("ai_lang", "English")
    except Exception:
        return "English"

# ══════════════════════════════════════════════
# LOGIN SCREEN
# ══════════════════════════════════════════════
def check_admin(username, password):
    try:
        ok_u = hmac.compare_digest(username, st.secrets["Identifiers"]["APP_USERNAME"])
        ok_p = hmac.compare_digest(password,  st.secrets["Identifiers"]["APP_PASSWORD"])
        return ok_u and ok_p
    except Exception:
        return False

def login_screen():
    # Language picker on login screen (before login)
    lang_keys = list(LANGUAGES.keys())
    cur_lang  = st.session_state.get("ui_lang", "Français 🇫🇷")
    cur_idx   = lang_keys.index(cur_lang) if cur_lang in lang_keys else 0
    col_l, col_r = st.columns([3,1])
    with col_r:
        chosen_lang = st.selectbox("", lang_keys, index=cur_idx, label_visibility="collapsed", key="lang_login")
        if chosen_lang != cur_lang:
            st.session_state["ui_lang"] = chosen_lang
            st.rerun()

    # background-clip needs both vendor prefix and standard for full Safari support
    st.markdown(f"""
    <div style="max-width:400px;margin:2rem auto 0;text-align:center">
        <div style="font-size:3rem;line-height:1">♻️</div>
        <div style="font-size:1.8rem;font-weight:700;
            background:linear-gradient(135deg,#00d084,#00a8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;
            background-clip:text;color:transparent;
            margin:.4rem 0">TriSmart</div>
        <div style="color:#888;margin:.3rem 0 1.5rem;font-size:.95rem">{t('login_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([0.5, 3, 0.5])
    with col2:
        with st.form("login_form"):
            st.markdown(f"#### {t('login_title')}")
            # autocomplete hints help iOS Keychain / password managers
            username = st.text_input(t("username"), placeholder="username",
                                     autocomplete="username")
            password = st.text_input(t("password"), type="password",
                                     placeholder="••••••••",
                                     autocomplete="current-password")
            if st.form_submit_button(t("login_btn"), use_container_width=True, type="primary"):
                if check_admin(username, password):
                    st.session_state["role"] = "admin"
                    st.rerun()
                else:
                    st.error(t("login_error"))

        st.markdown("<div style='text-align:center;color:#666;margin:.5rem 0'>— or —</div>", unsafe_allow_html=True)

        if st.button(t("guest_btn"), use_container_width=True, type="secondary"):
            st.session_state["role"] = "guest"
            st.rerun()

        st.markdown(f"""<div style='text-align:center;font-size:.75rem;color:#555;margin-top:.8rem'>
        {t('guest_hint')}</div>""", unsafe_allow_html=True)

if not is_logged():
    login_screen()
    st.stop()

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
if "bins" not in st.session_state:
    st.session_state.bins = {
        b["name"]:{"description":b["description"],"couleur":b["couleur"],"active":True}
        for b in DEFAULT_BINS}

def get_color(name):
    return st.session_state.bins.get(name,{}).get("couleur","#888888")

def get_provider():
    return st.session_state.get("provider","Gemini")

def get_gemini_model():
    m = st.session_state.get("gemini_model", DEFAULT_GEMINI)
    return m if m in GEMINI_FREE_MODELS else DEFAULT_GEMINI

def get_openrouter_model():
    m = st.session_state.get("openrouter_model", DEFAULT_OPENROUTER)
    return m if m in OPENROUTER_FREE_MODELS else DEFAULT_OPENROUTER

# ══════════════════════════════════════════════
# HELPERS IMAGE
# ══════════════════════════════════════════════
def prepare_image(uploaded):
    """
    Load, normalise and resize an image from any upload source.
    Handles: HEIC/HEIF (iPhone), wrong EXIF orientation, large files, RGBA→RGB.
    Returns: (PIL.Image, bytes, mime_type, base64_str)
    """
    raw_bytes = uploaded.read() if hasattr(uploaded, "read") else uploaded.getvalue()

    # HEIC / HEIF support — register opener if pillow-heif is installed
    fname = getattr(uploaded, "name", "").lower()
    if fname.endswith((".heic", ".heif")):
        try:
            import pillow_heif
            pillow_heif.register_heif_opener()
        except ImportError:
            pass  # best-effort; PIL may still open it on some builds

    img = Image.open(io.BytesIO(raw_bytes))

    # Normalise format
    fmt = (img.format or "JPEG").upper()
    if fmt not in ("JPEG", "PNG", "WEBP"):
        fmt = "JPEG"

    # Convert colour modes
    if fmt == "JPEG" and img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    elif fmt == "PNG" and img.mode == "P":
        img = img.convert("RGBA")

    # Fix EXIF orientation (iPhone photos often arrive rotated)
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass

    # Resize if too large (saves bandwidth & avoids API payload limits)
    MAX_SIDE = 1600
    if max(img.size) > MAX_SIDE:
        img.thumbnail((MAX_SIDE, MAX_SIDE), Image.LANCZOS)

    buf = io.BytesIO()
    save_kw = {"format": fmt}
    if fmt == "JPEG":
        save_kw["quality"]   = 85
        save_kw["optimize"]  = True
    img.save(buf, **save_kw)
    result_bytes = buf.getvalue()
    mime = f"image/{fmt.lower()}"
    return img, result_bytes, mime, base64.b64encode(result_bytes).decode()

# ══════════════════════════════════════════════
# HELPERS IA
# ══════════════════════════════════════════════
def clean_raw(raw):
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"): raw = raw[4:]
    return raw.strip()

def call_gemini(api_key, prompt, image_bytes, mime_type, retries=3):
    client = genai.Client(api_key=api_key)
    contents = [types.Content(role="user", parts=[
        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
        types.Part.from_text(text=prompt),
    ])]
    for attempt in range(retries):
        try:
            r = client.models.generate_content(model=get_gemini_model(), contents=contents)
            return clean_raw(r.text.strip())
        except Exception as e:
            err = str(e)
            if "429" in err and attempt < retries-1:
                wait = 20
                m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err)
                if m: wait = int(m.group(1))+2
                st.warning(f"⏳ Quota Gemini, retry {attempt+1}/{retries} dans {wait}s…")
                time.sleep(wait); continue
            raise

def call_openrouter(api_key, prompt, b64, mime_type, retries=3):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)
    msgs = [{"role":"user","content":[
        {"type":"text","text":prompt},
        {"type":"image_url","image_url":{"url":f"data:{mime_type};base64,{b64}"}},
    ]}]
    for attempt in range(retries):
        try:
            r = client.chat.completions.create(model=get_openrouter_model(), messages=msgs)
            return clean_raw(r.choices[0].message.content.strip())
        except Exception as e:
            if "429" in str(e) and attempt < retries-1:
                st.warning(f"⏳ Quota OpenRouter, retry {attempt+1}/{retries} dans 15s…")
                time.sleep(15); continue
            raise

def call_ai(gemini_key, openrouter_key, prompt, image_bytes, mime_type, b64):
    if get_provider()=="Gemini":
        if not gemini_key: raise ValueError("Clé Gemini manquante.")
        return call_gemini(gemini_key, prompt, image_bytes, mime_type)
    else:
        if not openrouter_key: raise ValueError("Clé OpenRouter manquante.")
        return call_openrouter(openrouter_key, prompt, b64, mime_type)

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    role_label = "🛡️ Admin" if is_admin() else "👤 " + ("Invité" if get_lang_code()=="fr" else "Guest")
    role_class = "role-badge-admin" if is_admin() else "role-badge-guest"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
        <span style="font-weight:700;font-size:1.1rem">{t('config')}</span>
        <span class="{role_class}">{role_label}</span>
    </div>""", unsafe_allow_html=True)

    if st.button(t("logout"), use_container_width=True):
        st.session_state["role"] = None
        st.rerun()

    if is_admin():
        if st.button(t("dashboard"), use_container_width=True):
            st.session_state["show_dashboard"] = not st.session_state.get("show_dashboard", False)

    st.markdown("---")

    # ── Langue UI ──
    lang_keys = list(LANGUAGES.keys())
    cur_lang  = st.session_state.get("ui_lang","Français 🇫🇷")
    cur_idx   = lang_keys.index(cur_lang) if cur_lang in lang_keys else 0
    chosen_lang = st.selectbox(t("lang_label"), lang_keys, index=cur_idx)
    if chosen_lang != cur_lang:
        st.session_state["ui_lang"] = chosen_lang
        st.rerun()

    # ── Pays ──
    country_keys = list(COUNTRY_GUIDES.keys())
    cur_country  = st.session_state.get("country", list(COUNTRY_GUIDES.keys())[0])
    if cur_country not in country_keys: cur_country = country_keys[0]
    chosen_country = st.selectbox(t("country_label"), country_keys,
                                   index=country_keys.index(cur_country))
    st.session_state["country"] = chosen_country

    st.markdown("---")

    # ── Provider ──
    st.markdown(f"### {t('provider')}")
    provider_choice = st.radio("Provider", ["Gemini (Google)","OpenRouter"],
        index=0 if get_provider()=="Gemini" else 1,
        label_visibility="collapsed", horizontal=True)
    st.session_state["provider"] = "Gemini" if "Gemini" in provider_choice else "OpenRouter"
    st.markdown("---")

    # ── Clés API ──
    gemini_key = openrouter_key = ""
    try:
        gemini_key = st.secrets["API_Key"]["GEMINI_API_KEY"]
        if get_provider()=="Gemini": st.success(t("key_loaded_gemini"))
    except Exception:
        if get_provider()=="Gemini": st.warning(t("key_miss_gemini"))

    try:
        openrouter_key = st.secrets["API_Key"]["OPEN_ROUTER_API_KEY"]
        if get_provider()=="OpenRouter": st.success(t("key_loaded_or"))
    except Exception:
        if get_provider()=="OpenRouter": st.warning(t("key_miss_or"))

    st.markdown("---")

    # ── Modèle ──
    st.markdown(f"### {t('model_label')}")
    if get_provider()=="Gemini":
        st.caption(t("model_hint_gemini"))
        gk = list(GEMINI_FREE_MODELS.keys())
        gl = list(GEMINI_FREE_MODELS.values())
        cur = get_gemini_model()
        chosen = st.radio("mg", gl, index=gk.index(cur), label_visibility="collapsed")
        st.session_state["gemini_model"] = gk[gl.index(chosen)]
        st.caption(f"`{st.session_state['gemini_model']}`")
    else:
        st.caption(t("model_hint_or"))
        ok = list(OPENROUTER_FREE_MODELS.keys())
        ol = list(OPENROUTER_FREE_MODELS.values())
        cur = get_openrouter_model()
        chosen = st.radio("mor", ol, index=ok.index(cur), label_visibility="collapsed")
        st.session_state["openrouter_model"] = ok[ol.index(chosen)]
        st.caption(f"`{st.session_state['openrouter_model']}`")

    # ── Scanner poubelles ──
    active_key = gemini_key if get_provider()=="Gemini" else openrouter_key
    st.markdown("---")
    st.markdown(f"### {t('scan_title')}")
    st.caption(t("scan_hint"))
    scan_tab1, scan_tab2 = st.tabs(["📷","🖼️"])
    scan_image = None
    with scan_tab1:
        # Gate camera_input to avoid iOS Safari freeze on sidebar open
        if "scan_cam_active" not in st.session_state:
            st.session_state["scan_cam_active"] = False
        if not st.session_state["scan_cam_active"]:
            if st.button("📷 " + ("Activer" if get_lang_code()=="fr" else "Activate"),
                         use_container_width=True, type="secondary", key="btn_scan_cam"):
                st.session_state["scan_cam_active"] = True
                st.rerun()
        else:
            sc = st.camera_input("", label_visibility="collapsed", key="cam_scan")
            if sc: scan_image = sc
    with scan_tab2:
        su = st.file_uploader("", type=["jpg","jpeg","png","webp","heic","heif"],
                               label_visibility="collapsed", key="up_scan")
        if su:
            scan_image = su
            st.session_state["scan_cam_active"] = False  # reset if user switched to upload

    if scan_image and active_key:
        if st.button(t("scan_btn"), use_container_width=True, type="primary"):
            with st.spinner("..."):
                try:
                    _, ib, mime, b64 = prepare_image(scan_image)
                    prompt_scan = """Analyse this photo of waste bins/containers.
Identify each visible bin (color, label, type).
Reply ONLY with valid JSON, no backticks:
[{"name":"🟡 Yellow Bin","couleur":"#f5c518","description":"accepted content"}]
Use a matching color emoji in the name. Be precise about accepted content."""
                    raw = call_ai(gemini_key, openrouter_key, prompt_scan, ib, mime, b64)
                    detected = json.loads(raw)
                    new_bins = {
                        b["name"]:{"description":b["description"],"couleur":b.get("couleur","#888"),"active":True}
                        for b in detected}
                    added   = [n for n in new_bins if n not in st.session_state.bins]
                    updated = [n for n in new_bins if n in st.session_state.bins]
                    st.session_state.bins.update(new_bins)
                    msg = f"✅ {len(detected)} {t('scan_success')}"
                    if added:   msg += f" · {len(added)} {t('scan_added')}"
                    if updated: msg += f" · {len(updated)} {t('scan_updated')}"
                    st.success(msg)
                    st.rerun()
                except json.JSONDecodeError:
                    st.error(t("scan_err_json"))
                except Exception as e:
                    st.error(f"❌ {t('scan_err_quota') if '429' in str(e) else str(e)}")
    elif scan_image and not active_key:
        st.warning(t("scan_key_missing"))

    # ── Gestion poubelles ──
    st.markdown("---")
    st.markdown(f"### {t('bins_title')}")
    to_delete = []
    for bname, bdata in list(st.session_state.bins.items()):
        ca, cb = st.columns([5,1])
        with ca:
            active = st.checkbox(bname, value=bdata["active"], key=f"cb_{bname}")
            st.session_state.bins[bname]["active"] = active
        with cb:
            if st.button("✕", key=f"del_{bname}"): to_delete.append(bname)
        if active:
            nd = st.text_area("", value=bdata["description"], key=f"desc_{bname}",
                               height=60, label_visibility="collapsed")
            st.session_state.bins[bname]["description"] = nd
    for b in to_delete:
        del st.session_state.bins[b]; st.rerun()

    st.markdown("---")
    st.markdown(f"### {t('add_title')}")
    with st.form("add_bin", clear_on_submit=True):
        nn  = st.text_input(t("bin_name_ph"), placeholder=t("bin_name_ph"))
        nd2 = st.text_area(t("bin_content"), height=55)
        nc  = st.color_picker("🎨", "#4488ff")
        if st.form_submit_button(t("add_btn"), use_container_width=True) and nn:
            st.session_state.bins[nn] = {"description":nd2,"couleur":nc,"active":True}
            st.rerun()

    if st.button(t("reset_btn"), use_container_width=True):
        st.session_state.bins = {b["name"]:{"description":b["description"],"couleur":b["couleur"],"active":True} for b in DEFAULT_BINS}
        st.rerun()

    st.markdown(f"""<div style='font-size:.7rem;color:#555;text-align:center;margin-top:.8rem'>
    TriSmart v11.0 · {get_provider()} · Free</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════
if is_admin() and st.session_state.get("show_dashboard", False):
    st.markdown(f"## {t('dashboard')}")
    logs  = st.session_state.usage_log
    total = len(logs)
    # 4 metrics in 2×2 grid — safe on all screen widths
    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    r1c1.metric(t("dash_total"), total)
    r1c2.metric(t("dash_ok"),    sum(1 for l in logs if l["success"]))
    r2c1.metric(t("dash_err"),   sum(1 for l in logs if not l["success"]))
    r2c2.metric(t("dash_guest"), sum(1 for l in logs if l["role"]=="guest"))

    if logs:
        st.markdown(t("dash_log"))
        st.dataframe(logs, use_container_width=True, hide_index=True)

        st.markdown(t("dash_stats"))
        cc1, cc2 = st.columns(2)
        with cc1:
            st.markdown(t("dash_by_provider"))
            prov = {}
            for l in logs: prov[l["provider"]] = prov.get(l["provider"],0)+1
            for p,n in prov.items(): st.progress(n/total, text=f"{p}: {n}")
        with cc2:
            st.markdown(t("dash_by_role"))
            roles = {}
            for l in logs: roles[l["role"]] = roles.get(l["role"],0)+1
            for r,n in roles.items(): st.progress(n/total, text=f"{r}: {n}")

        st.markdown(t("dash_top"))
        objets = {}
        for l in logs:
            if l["objet"]: objets[l["objet"]] = objets.get(l["objet"],0)+1
        for obj,cnt in sorted(objets.items(), key=lambda x:-x[1])[:10]:
            st.markdown(f"- **{obj}** × {cnt}")

        if st.button(t("dash_clear"), type="secondary"):
            st.session_state.usage_log = []
            st.rerun()
    else:
        st.info(t("dash_empty"))
    st.markdown("---")

# ══════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════
st.markdown('<div class="hero-title">♻️ TriSmart</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-sub">AI Waste Sorting · {get_provider()} · Free</div>', unsafe_allow_html=True)

# Step badges — pure HTML row, never overflows on any screen width
st.markdown(f"""
<div style="display:flex;justify-content:center;gap:clamp(.5rem,3vw,2rem);
    flex-wrap:wrap;margin-bottom:.8rem;font-size:clamp(.8rem,3vw,.95rem);color:#ccc">
  <span><span class="step-badge">1</span>{t('step1')}</span>
  <span><span class="step-badge">2</span>{t('step2')}</span>
  <span><span class="step-badge">3</span>{t('step3')}</span>
</div>
""", unsafe_allow_html=True)
st.markdown("---")

bins_config = {k:v for k,v in st.session_state.bins.items() if v.get("active")}
active_key  = gemini_key if get_provider()=="Gemini" else openrouter_key

if not active_key:
    st.info(f"👈 {t('key_missing_main')}")

if bins_config:
    # CSS grid: 4 cols on desktop, 2 on mobile — avoids st.columns overflow
    cards_html = "".join(
        f'<div style="background:{v["couleur"]}22;border:1px solid {v["couleur"]};'
        f'border-radius:8px;padding:8px 4px;text-align:center;font-size:.78rem;'
        f'color:#ddd;line-height:1.3;word-break:break-word">{k}</div>'
        for k, v in bins_config.items()
    )
    st.markdown(
        f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));'
        f'gap:6px;margin-bottom:.5rem">{cards_html}</div>',
        unsafe_allow_html=True,
    )
    st.markdown("")

# ══════════════════════════════════════════════
# CAPTURE — PC · iOS · iPadOS · Android
# ══════════════════════════════════════════════
#
# Platform strategy:
#   Desktop Chrome / Firefox  →  st.camera_input  (live webcam stream)
#   Android Chrome            →  st.camera_input  (works natively)
#   iOS Safari / iPadOS       →  file_uploader with accept="image/*"
#                                triggers the native iOS camera sheet
#                                (Camera / Photo Library / Files) — most
#                                reliable approach on WebKit.
#   All platforms             →  Gallery/upload tab always available.
#
# NOTE: _stc.html() with postMessage intentionally NOT used — injected iframes
# block the Streamlit WebSocket handshake on iOS Safari, causing the
# skeleton loading screen to freeze permanently.
# ──────────────────────────────────────────────

_IOS_HINT = {
    "fr": "iOS / Safari : utilisez ce bouton",
    "en": "iOS / Safari: use this button",
    "de": "iOS / Safari: diese Schaltflaeche nutzen",
    "es": "iOS / Safari: use este boton",
    "ko": "iOS / Safari: 이 버튼 사용",
    "zh": "iOS / Safari: 使用此按钮",
    "ja": "iOS / Safari: このボタンを使用",
}
_IOS_BTN = {
    "fr": "Prendre une photo (iOS / Safari)",
    "en": "Take a photo (iOS / Safari)",
    "de": "Foto aufnehmen (iOS / Safari)",
    "es": "Tomar una foto (iOS / Safari)",
    "ko": "사진 찍기 (iOS / Safari)",
    "zh": "拍照 (iOS / Safari)",
    "ja": "写真を撮る (iOS / Safari)",
}
_ACTIVATE_CAM = {
    "fr": "Activer la camera", "en": "Activate camera",
    "de": "Kamera aktivieren", "es": "Activar camara",
    "ko": "카메라 활성화",       "zh": "启用摄像头",      "ja": "カメラを起動",
}
_CAPTURE_BTN = {
    "fr": "Prendre la photo", "en": "Take photo",
    "de": "Aufnehmen",        "es": "Tomar foto",
    "ko": "촬영",              "zh": "拍照",            "ja": "撮影",
}
_RETAKE_BTN = {
    "fr": "Reprendre", "en": "Retake",
    "de": "Wiederholen","es": "Repetir",
    "ko": "다시 찍기",   "zh": "重拍",              "ja": "撮り直す",
}

_lc = get_lang_code()

# Initialise camera state
if "cam_active"  not in st.session_state: st.session_state["cam_active"]  = False
if "cam_facing"  not in st.session_state: st.session_state["cam_facing"]  = "environment"
if "cam_b64"     not in st.session_state: st.session_state["cam_b64"]     = ""

tab1, tab2 = st.tabs([t("tab_camera"), t("tab_upload")])
captured_image = None
source_label   = ""

with tab1:

    if not st.session_state["cam_active"]:
        # ── Activate button — camera permission not requested until tapped ──
        if st.button(
            "📷  " + _ACTIVATE_CAM.get(_lc, "Activate camera"),
            use_container_width=True, type="primary", key="btn_activate_cam"
        ):
            st.session_state["cam_active"] = True
            st.session_state["cam_b64"]    = ""
            st.rerun()

    else:
        facing = st.session_state["cam_facing"]

        # ── Single swap button ──
        swap_icon  = "⬅️ Avant" if facing == "environment" else "Arriere ➡️"
        if _lc != "fr":
            swap_icon = "⬅️ Front" if facing == "environment" else "Rear ➡️"
        swap_col, _ = st.columns([1, 4])
        with swap_col:
            if st.button(swap_icon, use_container_width=True,
                         type="secondary", key="btn_swap_cam"):
                st.session_state["cam_facing"] = (
                    "user" if facing == "environment" else "environment"
                )
                st.session_state["cam_b64"] = ""
                st.rerun()

        cap_lbl = _CAPTURE_BTN.get(_lc, "Take photo")
        ret_lbl = _RETAKE_BTN.get(_lc, "Retake")

        # ── Custom JS camera — proper facingMode, capture→base64→session_state ──
        # We inject a tiny <textarea id="st-cam-out"> that Streamlit's st.text_area
        # widget reads via its key. The JS writes the base64 JPEG there and
        # dispatches an 'input' event so Streamlit picks it up.
        cam_html = f"""
<style>
#cam-wrap{{width:100%;max-width:540px;margin:0 auto;font-family:inherit}}
#cam-video{{width:100%;border-radius:12px;display:block;background:#111;
            min-height:220px}}
#cam-preview{{display:none;width:100%;border-radius:12px}}
#cam-err{{color:#f88;font-size:.85rem;text-align:center;padding:.4rem 0;
           display:none}}
.cam-btn{{width:100%;min-height:52px;border:none;border-radius:10px;
          font-size:1rem;font-weight:700;cursor:pointer;
          -webkit-appearance:none;margin-top:8px;transition:.15s}}
#btn-capture{{background:#00d084;color:#000}}
#btn-capture:active{{opacity:.8}}
#btn-retake{{background:#333;color:#eee;display:none}}
</style>
<div id="cam-wrap">
  <video id="cam-video" autoplay playsinline muted></video>
  <canvas id="cam-canvas" style="display:none"></canvas>
  <img   id="cam-preview" alt="captured"/>
  <div   id="cam-err"></div>
  <button id="btn-capture" class="cam-btn">📸 {cap_lbl}</button>
  <button id="btn-retake"  class="cam-btn">🔄 {ret_lbl}</button>
</div>
<script>
(function(){{
  var facing  = "{facing}";
  var video   = document.getElementById("cam-video");
  var canvas  = document.getElementById("cam-canvas");
  var preview = document.getElementById("cam-preview");
  var errDiv  = document.getElementById("cam-err");
  var btnCap  = document.getElementById("btn-capture");
  var btnRet  = document.getElementById("btn-retake");
  var stream  = null;

  function showErr(msg){{
    errDiv.textContent = "⚠️ " + msg;
    errDiv.style.display = "block";
    btnCap.disabled = true;
  }}

  function startCam(){{
    var constraints = {{
      video: {{ facingMode: {{ ideal: facing }}, width: {{ideal:1280}}, height: {{ideal:720}} }},
      audio: false
    }};
    navigator.mediaDevices.getUserMedia(constraints)
      .then(function(s){{
        stream = s;
        video.srcObject = s;
        errDiv.style.display = "none";
        btnCap.disabled = false;
      }})
      .catch(function(e){{ showErr(e.message || e.name); }});
  }}

  btnCap.addEventListener("click", function(){{
    if (!stream) return;
    canvas.width  = video.videoWidth  || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0);
    var dataUrl = canvas.toDataURL("image/jpeg", 0.88);
    // show preview
    preview.src = dataUrl;
    video.style.display   = "none";
    preview.style.display = "block";
    btnCap.style.display  = "none";
    btnRet.style.display  = "block";
    // stop stream (free camera LED)
    stream.getTracks().forEach(function(t){{ t.stop(); }});
    stream = null;
    // send to bridge listener
    window.parent.postMessage({{ type: "cam_photo", value: dataUrl }}, "*");
  }});

  btnRet.addEventListener("click", function(){{
    preview.style.display = "none";
    video.style.display   = "block";
    btnRet.style.display  = "none";
    btnCap.style.display  = "block";
    btnCap.disabled = true;
    startCam();
  }});

  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia){{
    startCam();
  }} else {{
    showErr("Camera API not available in this browser.");
  }}
}})();
</script>
"""
        # ── Render camera widget ──
        _stc.html(cam_html, height=380)

        # ── Receive captured photo ──
        # The JS cannot directly write to st.session_state.
        # We place a hidden st.text_area whose DOM textarea the JS fills,
        # then triggers an 'input' event. On next rerun Streamlit reads it.
        # We hide it with CSS so the user never sees it.
        st.markdown(
            "<style>#cam-b64-area{opacity:0;height:1px;padding:0;margin:0;"
            "pointer-events:none;position:absolute}</style>",
            unsafe_allow_html=True,
        )
        cam_b64_raw = st.text_area(
            "", key="cam_b64_input",
            value=st.session_state.get("cam_b64", ""),
            label_visibility="collapsed",
            height=1,
        )
        # JS target: the textarea rendered for key "cam_b64_input"
        # We inject a small bridge script to wire JS → textarea
        bridge = """
<script>
(function waitForTextarea() {
  var ta = window.parent.document.querySelector(
    'textarea[data-testid="stTextArea"]');
  if (!ta) { setTimeout(waitForTextarea, 200); return; }
  ta.id = "cam-b64-area";
  window.addEventListener("message", function(ev) {
    if (ev.data && ev.data.type === "cam_photo") {
      ta.value = ev.data.value;
      ta.dispatchEvent(new Event("input", {bubbles:true}));
      ta.dispatchEvent(new Event("change", {bubbles:true}));
    }
  });
})();
</script>"""
        _stc.html(bridge, height=0)

        if cam_b64_raw and cam_b64_raw.startswith("data:image"):
            try:
                header, b64data = cam_b64_raw.split(",", 1)
                img_bytes_js = base64.b64decode(b64data)
                captured_image = io.BytesIO(img_bytes_js)
                captured_image.name = "camera.jpg"
                source_label = t("tab_camera")
                st.session_state["cam_b64"] = cam_b64_raw
            except Exception:
                pass

        # Fallback: standard camera_input for Android Chrome
        with st.expander("📷 " + ("Autre option" if _lc=="fr" else "Alternative"), expanded=False):
            std_cam = st.camera_input("", label_visibility="collapsed",
                                      key=f"stdcam_{facing}")
            if std_cam:
                captured_image = std_cam
                source_label   = t("tab_camera")

    # ── iOS / Safari native fallback — file input with capture attribute ──
    # This triggers the native iOS camera/photo picker — most reliable on WebKit.
    st.markdown(
        f"<div style='text-align:center;color:#666;font-size:.78rem;margin:.5rem 0'>"
        f"📱 {_IOS_HINT.get(_lc, _IOS_HINT['en'])}</div>",
        unsafe_allow_html=True,
    )
    ios_file = st.file_uploader(
        "📸  " + _IOS_BTN.get(_lc, _IOS_BTN["en"]),
        type=["jpg", "jpeg", "png", "webp", "heic", "heif"],
        label_visibility="visible",
        key="ios_cam",
    )
    if ios_file:
        captured_image = ios_file
        source_label   = "photo"

with tab2:
    if st.session_state.get("cam_active"):
        st.session_state["cam_active"] = False
    upl = st.file_uploader(
        "", type=["jpg","jpeg","png","webp","heic","heif"],
        label_visibility="collapsed", key="up_dechet",
    )
    if upl:
        captured_image = upl
        source_label   = upl.name

# ══════════════════════════════════════════════
# ANALYSE
# ══════════════════════════════════════════════
if captured_image and active_key and bins_config:
    img, img_bytes, mime_type, b64_img = prepare_image(captured_image)

    # Preview + analyse — two columns (CSS stacks them on mobile automatically)
    ci, co = st.columns([1, 1])
    with ci:
        st.image(img, caption=f"📷 {source_label}", use_container_width=True)
    with co:
        model_active = get_gemini_model() if get_provider()=="Gemini" else get_openrouter_model()
        st.markdown(t("ready"))
        st.caption(f"{img.size[0]}×{img.size[1]}px · `{model_active}`")
        analyze = st.button(t("analyze_btn"), use_container_width=True, type="primary")

    if analyze:
        bins_text = "\n".join([f"- **{n}** : {d['description']}" for n,d in bins_config.items()])
        ai_lang   = get_ai_lang()
        prompt    = f"""You are an expert in waste management and recycling. Analyze this photo of a waste item.

AVAILABLE BINS:
{bins_text}

Reply ONLY with valid JSON, no backticks:
{{
  "objet_detecte": "precise name of the object",
  "materiau": "main material",
  "poubelle_recommandee": "EXACT NAME of one of the bins listed above",
  "confiance": 85,
  "raison": "short explanation in {ai_lang}",
  "gestes_importants": ["tip 1 in {ai_lang}", "tip 2 in {ai_lang}"],
  "poubelles_alternatives": [],
  "recyclable": true,
  "dangereux": false,
  "emoji": "🥤"
}}"""

        with st.spinner(f"🤖 {get_provider()}..."):
            raw = ""
            try:
                raw    = call_ai(gemini_key, openrouter_key, prompt, img_bytes, mime_type, b64_img)
                result = json.loads(raw)
                log_analysis(True, get_provider(), model_active,
                             result.get("objet_detecte",""), st.session_state.get("role","guest"))

                st.markdown(t("result_title"))
                bin_name  = result.get("poubelle_recommandee","?")
                bin_color = get_color(bin_name)
                conf      = result.get("confiance",0)

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d1f0d,#0d1520);
                    border:2px solid {bin_color};border-radius:20px;
                    padding:clamp(.8rem,4vw,1.5rem) clamp(.8rem,4vw,2rem);
                    margin:1rem 0;word-break:break-word">
                    <div style="font-size:clamp(2rem,8vw,3rem);text-align:center">{result.get('emoji','♻️')}</div>
                    <div style="text-align:center;font-size:clamp(1.1rem,4vw,1.5rem);font-weight:700;color:white;margin:.5rem 0">
                        {result.get('objet_detecte','?')}</div>
                    <div style="text-align:center;color:#aaa;font-size:clamp(.8rem,3vw,.9rem)">
                        {t('material')} : <strong style="color:#ddd">{result.get('materiau','?')}</strong></div>
                    <div style="margin:1rem 0;text-align:center">
                        <span style="background:{bin_color}22;border:2px solid {bin_color};color:white;
                            padding:.5rem clamp(.8rem,3vw,1.5rem);border-radius:999px;
                            font-size:clamp(1rem,4vw,1.2rem);font-weight:700;
                            display:inline-block;max-width:100%;white-space:normal;word-break:break-word">
                            ➜ {bin_name}</span></div>
                    <div style="margin:.5rem 0">
                        <div style="display:flex;justify-content:space-between;color:#aaa;font-size:.8rem;margin-bottom:4px">
                            <span>{t('confidence')}</span><span>{conf}%</span></div>
                        <div style="background:#333;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,{bin_color},#00a8ff);
                                width:{conf}%;height:8px;border-radius:4px"></div></div></div>
                    <div style="color:#ccc;font-size:clamp(.85rem,3vw,.95rem);margin-top:1rem;line-height:1.6">
                        💡 {result.get('raison','')}</div>
                </div>""", unsafe_allow_html=True)

                gestes = result.get("gestes_importants",[])
                if gestes:
                    st.markdown(t("gestures"))
                    for g in gestes: st.markdown(f"✅ {g}")

                alts = result.get("poubelles_alternatives",[])
                if alts:
                    st.markdown(t("alternatives"))
                    for a in alts:
                        c = get_color(a)
                        st.markdown(f'<div style="border-left:3px solid {c};padding-left:8px;color:#ccc">⚠️ {a}</div>',
                                    unsafe_allow_html=True)

                r1,r2 = st.columns(2)
                with r1:
                    if result.get("recyclable"): st.success(t("recyclable"))
                    else: st.error(t("not_recyclable"))
                with r2:
                    if result.get("dangereux"): st.warning(t("dangerous"))
                    else: st.info(t("not_dangerous"))

                if is_admin():
                    with st.expander(t("debug_title")):
                        st.json(result)
                        st.markdown(f"**Provider:** `{get_provider()}` · **Model:** `{model_active}` · **Role:** `{st.session_state.get('role')}`")

            except json.JSONDecodeError as e:
                log_analysis(False, get_provider(), model_active, role=st.session_state.get("role","guest"))
                st.error(f"{t('json_err')}: {e}")
                if is_admin(): st.code(raw)
            except Exception as e:
                log_analysis(False, get_provider(), model_active, role=st.session_state.get("role","guest"))
                if "429" in str(e): st.error(t("quota_err"))
                else:
                    st.error(f"{t('err_prefix')}: {e}")
                    if is_admin(): st.exception(e)

elif captured_image and not active_key:
    st.warning(f"⚠️ {t('key_missing_main')}")
elif captured_image and not bins_config:
    st.warning(t("no_bin_active"))

# ══════════════════════════════════════════════
# GUIDE DE TRI
# ══════════════════════════════════════════════
st.markdown("---")
country_keys = list(COUNTRY_GUIDES.keys())
country = st.session_state.get("country", country_keys[0])
if country not in country_keys: country = country_keys[0]
guide = COUNTRY_GUIDES[country]

with st.expander(f"{t('guide_title')} — {country}"):
    header_waste = {"fr":"Déchet","en":"Waste","de":"Abfall","es":"Residuo",
                    "ko":"쓰레기","zh":"废弃物","ja":"ごみ"}
    header_bin   = {"fr":"Conteneur","en":"Bin","de":"Tonne","es":"Contenedor",
                    "ko":"분리수거함","zh":"垃圾桶","ja":"ごみ箱"}
    lc = get_lang_code()
    hw = header_waste.get(lc, "Waste")
    hb = header_bin.get(lc, "Bin")

    table = f"| {hw} | {hb} |\n|---|---|\n"
    for waste_key, bin_label in guide["rows"]:
        waste_label = get_waste_label(waste_key)
        table += f"| {waste_label} | {bin_label} |\n"
    st.markdown(table)
    st.markdown(f"> {t('guide_tip')}")

st.markdown("""
<div style='text-align:center;color:#444;font-size:.8rem;margin-top:2rem'>
TriSmart v8.3 · Gemini + OpenRouter · Streamlit · Free
</div>""", unsafe_allow_html=True)