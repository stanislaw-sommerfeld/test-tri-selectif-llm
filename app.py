import streamlit as st
from google import genai
from google.genai import types
from openai import OpenAI
import base64
import json
from PIL import Image
import io
import hmac
import time
import re

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="♻️ TriSmart – Tri Intelligent des Déchets",
    page_icon="♻️",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# LOGIN
# ─────────────────────────────────────────────
def check_credentials(username, password):
    try:
        valid_user = hmac.compare_digest(username, st.secrets["Identifiers"]["APP_USERNAME"])
        valid_pass = hmac.compare_digest(password, st.secrets["Identifiers"]["APP_PASSWORD"])
        return valid_user and valid_pass
    except Exception:
        return False

def login_screen():
    st.markdown("""
    <div style="max-width:380px;margin:4rem auto 0 auto;text-align:center">
        <div style="font-size:3rem">♻️</div>
        <div style="font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#00d084,#00a8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:0.3rem">
            TriSmart
        </div>
        <div style="color:#888;margin-bottom:2rem">Connectez-vous pour continuer</div>
    </div>
    """, unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("👤 Nom d'utilisateur", placeholder="username")
            password = st.text_input("🔒 Mot de passe", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            if submitted:
                if check_credentials(username, password):
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")

if not st.session_state.get("logged_in", False):
    login_screen()
    st.stop()

# ─────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .hero-title {
        font-size: 2.4rem; font-weight: 700;
        background: linear-gradient(135deg, #00d084 0%, #00a8ff 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        text-align: center; margin-bottom: 0.2rem;
    }
    .hero-sub { text-align: center; color: #888; font-size: 1rem; margin-bottom: 2rem; }
    .step-badge {
        background: #1e3a2a; color: #00d084; border-radius: 50%;
        width: 28px; height: 28px; display: inline-flex;
        align-items: center; justify-content: center;
        font-weight: 700; font-size: 0.85rem; margin-right: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# CONSTANTES — MODÈLES
# ─────────────────────────────────────────────

# Gemini free tier (via google-genai)
GEMINI_MODELS = {
    "gemini-2.5-flash-lite":          "⚡ 2.5 Flash Lite  (~1 000 req/jour)  ✅ recommandé",
    "gemini-2.5-flash":               "🚀 2.5 Flash       (~250 req/jour)",
    "gemini-3-flash-preview":         "🔥 3 Flash Preview (~200 req/jour, preview)",
    "gemini-3.1-flash-lite-preview":  "🧪 3.1 Flash Lite  (~200 req/jour, preview)",
}
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

# OpenRouter free vision models (via openai-compatible API)
OPENROUTER_MODELS = {
    "openrouter/free":                          "🎲 Auto-free router  (choisit le meilleur dispo)",
    "qwen/qwen2.5-vl-72b-instruct:free":        "🧠 Qwen 2.5 VL 72B  (très bon en vision)",
    "meta-llama/llama-3.2-11b-vision-instruct:free": "🦙 Llama 3.2 11B Vision",
    "google/gemma-3-27b-it:free":               "💎 Gemma 3 27B",
    "mistralai/mistral-small-3.1-24b-instruct:free": "🌬️ Mistral Small 3.1 24B",
}
DEFAULT_OPENROUTER_MODEL = "openrouter/free"

DEFAULT_BINS = [
    {"name": "🟡 Poubelle Jaune",       "couleur": "#f5c518", "description": "Recyclables : plastiques, métaux, cartons, briques alimentaires"},
    {"name": "🟢 Poubelle Verte",       "couleur": "#00b34a", "description": "Verre uniquement : bouteilles, bocaux, pots"},
    {"name": "⚫ Poubelle Noire/Grise", "couleur": "#888888", "description": "Ordures ménagères résiduelles non recyclables"},
    {"name": "🟤 Poubelle Marron",      "couleur": "#8B4513", "description": "Bio-déchets et compostables"},
]

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
if "bins" not in st.session_state:
    st.session_state.bins = {
        b["name"]: {"description": b["description"], "couleur": b["couleur"], "active": True}
        for b in DEFAULT_BINS
    }

def get_color(name):
    return st.session_state.bins.get(name, {}).get("couleur", "#888888")

def get_provider():
    return st.session_state.get("provider", "Gemini")

def get_gemini_model():
    m = st.session_state.get("gemini_model", DEFAULT_GEMINI_MODEL)
    return m if m in GEMINI_MODELS else DEFAULT_GEMINI_MODEL

def get_openrouter_model():
    m = st.session_state.get("openrouter_model", DEFAULT_OPENROUTER_MODEL)
    return m if m in OPENROUTER_MODELS else DEFAULT_OPENROUTER_MODEL

# ─────────────────────────────────────────────
# HELPERS — IMAGE
# ─────────────────────────────────────────────
def prepare_image(uploaded):
    img = Image.open(uploaded)
    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() not in ["JPEG", "PNG", "WEBP"]:
        fmt = "JPEG"
    img_out = img.convert("RGB") if fmt == "JPEG" else img
    img_out.save(buf, format=fmt)
    raw_bytes = buf.getvalue()
    mime = f"image/{fmt.lower()}"
    b64 = base64.b64encode(raw_bytes).decode("utf-8")
    return img, raw_bytes, mime, b64

# ─────────────────────────────────────────────
# HELPERS — APPELS IA
# ─────────────────────────────────────────────
def clean_raw(raw):
    """Nettoie les balises markdown du JSON retourné."""
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()

def call_gemini(api_key, prompt, image_bytes, mime_type, retries=3):
    """Appel Gemini via google-genai avec retry sur 429."""
    client = genai.Client(api_key=api_key)
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    text_part  = types.Part.from_text(text=prompt)
    contents   = [types.Content(role="user", parts=[image_part, text_part])]

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=get_gemini_model(),
                contents=contents,
            )
            return clean_raw(response.text.strip())
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < retries - 1:
                wait = 20
                match = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err_str)
                if match:
                    wait = int(match.group(1)) + 2
                st.warning(f"⏳ Quota Gemini momentané, nouvelle tentative dans {wait}s… ({attempt+1}/{retries})")
                time.sleep(wait)
                continue
            raise

def call_openrouter(api_key, prompt, b64_image, mime_type, retries=3):
    """Appel OpenRouter via API compatible OpenAI avec retry sur 429."""
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    messages = [{
        "role": "user",
        "content": [
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_image}"}},
        ]
    }]

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=get_openrouter_model(),
                messages=messages,
            )
            return clean_raw(response.choices[0].message.content.strip())
        except Exception as e:
            err_str = str(e)
            if "429" in err_str and attempt < retries - 1:
                st.warning(f"⏳ Quota OpenRouter momentané, nouvelle tentative dans 15s… ({attempt+1}/{retries})")
                time.sleep(15)
                continue
            raise

def call_ai(gemini_key, openrouter_key, prompt, image_bytes, mime_type, b64_image):
    """Dispatcher : appelle le bon provider selon le choix de l'utilisateur."""
    provider = get_provider()
    if provider == "Gemini":
        if not gemini_key:
            raise ValueError("Clé API Gemini manquante.")
        return call_gemini(gemini_key, prompt, image_bytes, mime_type)
    else:
        if not openrouter_key:
            raise ValueError("Clé API OpenRouter manquante.")
        return call_openrouter(openrouter_key, prompt, b64_image, mime_type)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
    st.markdown("---")

    # ── Choix du provider ──
    st.markdown("### 🔌 Provider IA")
    provider_choice = st.radio(
        "Provider",
        ["Gemini (Google)", "OpenRouter"],
        index=0 if get_provider() == "Gemini" else 1,
        label_visibility="collapsed",
        horizontal=True,
    )
    st.session_state["provider"] = "Gemini" if provider_choice == "Gemini (Google)" else "OpenRouter"

    st.markdown("---")

    # ── Clés API ──
    gemini_key = ""
    openrouter_key = ""

    if get_provider() == "Gemini":
        try:
            gemini_key = st.secrets["API_Key"]["GEMINI_API_KEY"]
            st.success("🔑 Clé Gemini chargée depuis les secrets")
        except Exception:
            gemini_key = st.text_input("🔑 Clé API Gemini", type="password",
                                        placeholder="AIza...",
                                        help="Gratuit sur https://aistudio.google.com")
    else:
        try:
            openrouter_key = st.secrets["API_Key"]["OPEN_ROUTER_API_KEY"]
            st.success("🔑 Clé OpenRouter chargée depuis les secrets")
        except Exception:
            openrouter_key = st.text_input("🔑 Clé API OpenRouter", type="password",
                                            placeholder="sk-or-...",
                                            help="Gratuit sur https://openrouter.ai")

    st.markdown("---")
    lang = st.selectbox("🌐 Langue", ["Français", "English", "Español", "Deutsch"])

    # ── Sélecteur de modèle ──
    st.markdown("---")
    st.markdown("### 🤖 Modèle IA")

    if get_provider() == "Gemini":
        st.caption("Si quota atteint, bascule sur un autre modèle")
        g_keys   = list(GEMINI_MODELS.keys())
        g_labels = list(GEMINI_MODELS.values())
        g_cur    = get_gemini_model()
        g_idx    = g_keys.index(g_cur)
        g_chosen = st.radio("Modèle Gemini", g_labels, index=g_idx, label_visibility="collapsed")
        st.session_state["gemini_model"] = g_keys[g_labels.index(g_chosen)]
        st.caption(f"Actif : `{st.session_state['gemini_model']}`")
    else:
        st.caption("Tous ces modèles supportent la vision et sont gratuits")
        or_keys   = list(OPENROUTER_MODELS.keys())
        or_labels = list(OPENROUTER_MODELS.values())
        or_cur    = get_openrouter_model()
        or_idx    = or_keys.index(or_cur)
        or_chosen = st.radio("Modèle OpenRouter", or_labels, index=or_idx, label_visibility="collapsed")
        st.session_state["openrouter_model"] = or_keys[or_labels.index(or_chosen)]
        st.caption(f"Actif : `{st.session_state['openrouter_model']}`")

    # ── Scanner ses poubelles par photo ──
    active_key = gemini_key if get_provider() == "Gemini" else openrouter_key
    st.markdown("---")
    st.markdown("### 📷 Scanner mes poubelles")
    st.caption("Photographiez vos poubelles pour les configurer automatiquement via l'IA")

    scan_tab1, scan_tab2 = st.tabs(["Caméra", "Importer"])
    scan_image = None
    with scan_tab1:
        sc = st.camera_input("Photo poubelles", label_visibility="collapsed", key="cam_scan")
        if sc: scan_image = sc
    with scan_tab2:
        su = st.file_uploader("Image poubelles", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="up_scan")
        if su: scan_image = su

    if scan_image and active_key:
        if st.button("🤖 Détecter mes poubelles", use_container_width=True, type="primary"):
            with st.spinner("Analyse des poubelles en cours..."):
                try:
                    _, img_bytes, mime, b64 = prepare_image(scan_image)
                    prompt_scan = """Analyse cette photo de poubelles/conteneurs de tri.
Identifie chaque poubelle visible (couleur, étiquette, type).
Réponds UNIQUEMENT en JSON valide, sans texte ni backticks :
[
  {
    "name": "🟡 Poubelle Jaune",
    "couleur": "#f5c518",
    "description": "ce qu'elle accepte selon ce que tu vois sur la photo"
  }
]
Utilise un emoji de couleur correspondante dans le nom. Sois précis sur le contenu accepté."""
                    raw = call_ai(gemini_key, openrouter_key, prompt_scan, img_bytes, mime, b64)
                    detected = json.loads(raw)
                    st.session_state.bins = {
                        b["name"]: {"description": b["description"], "couleur": b.get("couleur","#888"), "active": True}
                        for b in detected
                    }
                    st.success(f"✅ {len(detected)} poubelle(s) détectée(s) !")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("❌ Réponse JSON invalide, réessayez.")
                except Exception as e:
                    err = str(e)
                    if "429" in err:
                        st.error("❌ Quota atteint. Changez de modèle ou de provider ci-dessus.")
                    else:
                        st.error(f"❌ Erreur : {e}")
    elif scan_image and not active_key:
        st.warning("Clé API requise pour scanner.")

    # ── Gestion manuelle des poubelles ──
    st.markdown("---")
    st.markdown("### 🗑️ Mes poubelles")

    to_delete = []
    for bname, bdata in list(st.session_state.bins.items()):
        col_a, col_b = st.columns([5, 1])
        with col_a:
            active = st.checkbox(bname, value=bdata["active"], key=f"cb_{bname}")
            st.session_state.bins[bname]["active"] = active
        with col_b:
            if st.button("✕", key=f"del_{bname}", help="Supprimer"):
                to_delete.append(bname)
        if active:
            new_desc = st.text_area("", value=bdata["description"],
                                     key=f"desc_{bname}", height=60, label_visibility="collapsed")
            st.session_state.bins[bname]["description"] = new_desc

    for b in to_delete:
        del st.session_state.bins[b]
        st.rerun()

    st.markdown("---")
    st.markdown("### ➕ Ajouter une poubelle")
    with st.form("add_bin_form", clear_on_submit=True):
        new_name = st.text_input("Nom", placeholder="🔵 Poubelle Bleue")
        new_desc_add = st.text_area("Contenu accepté", height=60)
        new_color = st.color_picker("Couleur", "#4488ff")
        if st.form_submit_button("Ajouter", use_container_width=True) and new_name:
            st.session_state.bins[new_name] = {"description": new_desc_add, "couleur": new_color, "active": True}
            st.success(f"✅ {new_name} ajoutée !")
            st.rerun()

    if st.button("↺ Réinitialiser par défaut", use_container_width=True):
        st.session_state.bins = {
            b["name"]: {"description": b["description"], "couleur": b["couleur"], "active": True}
            for b in DEFAULT_BINS
        }
        st.rerun()

    provider_label = get_provider()
    model_label = get_gemini_model() if get_provider() == "Gemini" else get_openrouter_model()
    st.markdown(f"""
    <div style='font-size:0.75rem;color:#666;text-align:center;margin-top:1rem'>
    TriSmart v5.0 · {provider_label} · Streamlit · 100% Gratuit
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">♻️ TriSmart</div>', unsafe_allow_html=True)
provider_display = "Gemini (Google)" if get_provider() == "Gemini" else "OpenRouter"
st.markdown(f'<div class="hero-sub">Détection intelligente des déchets · {provider_display} · Gratuit</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<span class="step-badge">1</span> **Scannez** vos poubelles', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="step-badge">2</span> **Photographiez** le déchet', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="step-badge">3</span> **Obtenez** le bon tri', unsafe_allow_html=True)

st.markdown("---")

bins_config = {k: v for k, v in st.session_state.bins.items() if v.get("active")}
active_key  = gemini_key if get_provider() == "Gemini" else openrouter_key

if not active_key:
    if get_provider() == "Gemini":
        st.info("👈 Clé API Gemini requise — gratuite sur [aistudio.google.com](https://aistudio.google.com)")
    else:
        st.info("👈 Clé API OpenRouter requise — gratuite sur [openrouter.ai](https://openrouter.ai)")

# Résumé visuel des poubelles actives
if bins_config:
    cols = st.columns(min(len(bins_config), 4))
    for i, (bname, bdata) in enumerate(bins_config.items()):
        with cols[i % 4]:
            st.markdown(f"""<div style="background:{bdata['couleur']}22;border:1px solid {bdata['couleur']};
                border-radius:8px;padding:6px;text-align:center;font-size:0.75rem;color:#ddd;margin-bottom:4px">
                {bname}</div>""", unsafe_allow_html=True)
    st.markdown("")

# ─────────────────────────────────────────────
# ZONE CAPTURE DÉCHET
# ─────────────────────────────────────────────
tab1, tab2 = st.tabs(["📸 Prendre une photo", "🖼️ Importer une image"])
captured_image = None
source_label = ""

with tab1:
    cam = st.camera_input("Photo du déchet", label_visibility="collapsed", key="cam_dechet")
    if cam:
        captured_image = cam
        source_label = "photo caméra"

with tab2:
    upl = st.file_uploader("Image du déchet", type=["jpg","jpeg","png","webp"],
                            label_visibility="collapsed", key="up_dechet")
    if upl:
        captured_image = upl
        source_label = f"image importée ({upl.name})"

# ─────────────────────────────────────────────
# ANALYSE DÉCHET
# ─────────────────────────────────────────────
if captured_image and active_key and bins_config:
    img, img_bytes, mime_type, b64_img = prepare_image(captured_image)

    col_img, col_info = st.columns([1, 1])
    with col_img:
        st.image(img, caption=f"📷 {source_label}", use_container_width=True)
    with col_info:
        st.markdown("### 🔍 Prêt à analyser")
        model_active = get_gemini_model() if get_provider() == "Gemini" else get_openrouter_model()
        st.caption(f"{img.size[0]}×{img.size[1]}px · {model_active}")
        analyze = st.button("🤖 Analyser avec l'IA", use_container_width=True, type="primary")

    if analyze:
        bins_text = "\n".join([f"- **{name}** : {data['description']}" for name, data in bins_config.items()])
        prompt = f"""Tu es un expert en gestion des déchets et recyclage. Analyse cette photo d'un déchet.

POUBELLES DISPONIBLES :
{bins_text}

Réponds UNIQUEMENT en JSON valide, sans texte ni backticks :
{{
  "objet_detecte": "nom précis de l'objet",
  "materiau": "matériau principal",
  "poubelle_recommandee": "NOM EXACT d'une des poubelles listées ci-dessus",
  "confiance": 85,
  "raison": "explication courte en {lang}",
  "gestes_importants": ["conseil 1 en {lang}", "conseil 2 en {lang}"],
  "poubelles_alternatives": [],
  "recyclable": true,
  "dangereux": false,
  "emoji": "🥤"
}}"""

        with st.spinner(f"🤖 Analyse via {get_provider()}..."):
            try:
                raw = call_ai(gemini_key, openrouter_key, prompt, img_bytes, mime_type, b64_img)
                result = json.loads(raw)

                st.markdown("---")
                st.markdown("## 🎯 Résultat")

                bin_name   = result.get("poubelle_recommandee", "Inconnue")
                bin_color  = get_color(bin_name)
                confidence = result.get("confiance", 0)

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d1f0d,#0d1520);
                    border:2px solid {bin_color};border-radius:20px;padding:1.5rem 2rem;margin:1rem 0">
                    <div style="font-size:3rem;text-align:center">{result.get('emoji','♻️')}</div>
                    <div style="text-align:center;font-size:1.5rem;font-weight:700;color:white;margin:0.5rem 0">
                        {result.get('objet_detecte','Objet non identifié')}
                    </div>
                    <div style="text-align:center;color:#aaa;font-size:0.9rem">
                        Matériau : <strong style="color:#ddd">{result.get('materiau','Inconnu')}</strong>
                    </div>
                    <div style="margin:1rem 0;text-align:center">
                        <span style="background:{bin_color}22;border:2px solid {bin_color};
                            color:white;padding:0.5rem 1.5rem;border-radius:999px;
                            font-size:1.2rem;font-weight:700">➜ {bin_name}</span>
                    </div>
                    <div style="margin:0.5rem 0">
                        <div style="display:flex;justify-content:space-between;color:#aaa;font-size:0.8rem;margin-bottom:4px">
                            <span>Confiance IA</span><span>{confidence}%</span>
                        </div>
                        <div style="background:#333;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,{bin_color},#00a8ff);
                                width:{confidence}%;height:8px;border-radius:4px"></div>
                        </div>
                    </div>
                    <div style="color:#ccc;font-size:0.95rem;margin-top:1rem;line-height:1.5">
                        💡 {result.get('raison','')}
                    </div>
                </div>""", unsafe_allow_html=True)

                gestes = result.get("gestes_importants", [])
                if gestes:
                    st.markdown("### 📋 Gestes importants")
                    for g in gestes:
                        st.markdown(f"✅ {g}")

                alts = result.get("poubelles_alternatives", [])
                if alts:
                    st.markdown("### 🔄 Alternatives")
                    for a in alts:
                        c = get_color(a)
                        st.markdown(f'<div style="border-left:3px solid {c};padding-left:8px;color:#ccc">⚠️ {a}</div>', unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    if result.get("recyclable"):
                        st.success("♻️ Recyclable")
                    else:
                        st.error("🚫 Non recyclable")
                with c2:
                    if result.get("dangereux"):
                        st.warning("⚠️ Dangereux")
                    else:
                        st.info("✅ Non dangereux")

                with st.expander("🔧 JSON brut"):
                    st.json(result)

            except json.JSONDecodeError as e:
                st.error(f"❌ Erreur JSON : {e}")
                st.code(raw)
            except Exception as e:
                err = str(e)
                if "429" in err:
                    st.error(
                        "❌ **Quota atteint.**\n\n"
                        "👉 Changez de modèle dans la sidebar\n"
                        "👉 Ou basculez sur l'autre provider (Gemini ↔ OpenRouter)"
                    )
                else:
                    st.error(f"❌ Erreur : {e}")
                    st.exception(e)

elif captured_image and not active_key:
    st.warning("⚠️ Clé API manquante dans la sidebar.")
elif captured_image and not bins_config:
    st.warning("⚠️ Aucune poubelle active.")

# ─────────────────────────────────────────────
# GUIDE
# ─────────────────────────────────────────────
st.markdown("---")
with st.expander("📖 Guide de tri rapide (France)"):
    st.markdown("""
| Déchet | Poubelle |
|--------|----------|
| Bouteilles plastique, canettes | 🟡 Jaune |
| Cartons, journaux | 🟡 Jaune |
| Bouteilles en verre, bocaux | 🟢 Verte |
| Épluchures, restes alimentaires | 🟤 Marron |
| Sacs sales, mouchoirs | ⚫ Noire |
| Piles, médicaments | 🔴 Déchetterie |
> 💡 Vider et rincer les emballages avant recyclage !
    """)

st.markdown(f"""
<div style='text-align:center;color:#444;font-size:0.8rem;margin-top:2rem'>
    TriSmart v5.0 · Gemini + OpenRouter · Streamlit · 100% Gratuit
</div>""", unsafe_allow_html=True)
