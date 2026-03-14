import streamlit as st
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
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════
# CSS
# ══════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
html,body,[class*="css"]{font-family:'Inter',sans-serif}
.hero-title{font-size:2.4rem;font-weight:700;background:linear-gradient(135deg,#00d084,#00a8ff);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;text-align:center;margin-bottom:.2rem}
.hero-sub{text-align:center;color:#888;font-size:1rem;margin-bottom:2rem}
.step-badge{background:#1e3a2a;color:#00d084;border-radius:50%;width:28px;height:28px;
    display:inline-flex;align-items:center;justify-content:center;font-weight:700;font-size:.85rem;margin-right:8px}
.role-badge-admin{background:#1a2a4a;border:1px solid #4488ff;border-radius:999px;
    padding:2px 10px;font-size:.75rem;color:#88aaff}
.role-badge-guest{background:#2a2a1a;border:1px solid #aaa;border-radius:999px;
    padding:2px 10px;font-size:.75rem;color:#aaa}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# CONSTANTES MODÈLES
# ══════════════════════════════════════════════
GEMINI_FREE_MODELS = {
    "gemini-2.5-flash-lite":         "⚡ 2.5 Flash Lite  (~1 000 req/jour) ✅",
    "gemini-2.5-flash":              "🚀 2.5 Flash       (~250 req/jour)",
    "gemini-3-flash-preview":        "🔥 3 Flash Preview (~200 req/jour, preview)",
    "gemini-3.1-flash-lite-preview": "🧪 3.1 Flash Lite  (~200 req/jour, preview)",
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
# role: "admin" | "guest" | None (not logged in)

def is_admin():
    return st.session_state.get("role") == "admin"

def is_guest():
    return st.session_state.get("role") == "guest"

def is_logged():
    return st.session_state.get("role") in ("admin", "guest")

# ══════════════════════════════════════════════
# USAGE TRACKING (in-memory, session only)
# ══════════════════════════════════════════════
if "usage_log" not in st.session_state:
    st.session_state.usage_log = []  # list of dicts

def log_analysis(success: bool, provider: str, model: str, objet: str = "", role: str = "guest"):
    st.session_state.usage_log.append({
        "ts":       datetime.now(timezone.utc).strftime("%H:%M:%S"),
        "role":     role,
        "provider": provider,
        "model":    model,
        "objet":    objet,
        "success":  success,
    })

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
    st.markdown("""
    <div style="max-width:400px;margin:3rem auto 0;text-align:center">
        <div style="font-size:3rem">♻️</div>
        <div style="font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#00d084,#00a8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent">TriSmart</div>
        <div style="color:#666;margin:.5rem 0 1.5rem">Tri intelligent des déchets par IA</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("#### 🔐 Connexion")
            username = st.text_input("Nom d'utilisateur", placeholder="username")
            password = st.text_input("Mot de passe", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Se connecter", use_container_width=True, type="primary")
            if submitted:
                if check_admin(username, password):
                    st.session_state["role"] = "admin"
                    st.rerun()
                else:
                    st.error("❌ Identifiants incorrects")

        st.markdown("<div style='text-align:center;color:#666;margin:.5rem 0'>— ou —</div>", unsafe_allow_html=True)

        if st.button("👤 Continuer sans compte  *(accès limité)*",
                     use_container_width=True, type="secondary"):
            st.session_state["role"] = "guest"
            st.rerun()

        st.markdown("""
        <div style='text-align:center;font-size:.75rem;color:#555;margin-top:.8rem'>
        Accès invité : modèles gratuits uniquement · pas de détails techniques
        </div>""", unsafe_allow_html=True)

if not is_logged():
    login_screen()
    st.stop()

# ══════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════
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
    m = st.session_state.get("gemini_model", DEFAULT_GEMINI)
    return m if m in GEMINI_FREE_MODELS else DEFAULT_GEMINI

def get_openrouter_model():
    m = st.session_state.get("openrouter_model", DEFAULT_OPENROUTER)
    return m if m in OPENROUTER_FREE_MODELS else DEFAULT_OPENROUTER

# ══════════════════════════════════════════════
# HELPERS IMAGE
# ══════════════════════════════════════════════
def prepare_image(uploaded):
    img = Image.open(uploaded)
    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() not in ["JPEG","PNG","WEBP"]: fmt = "JPEG"
    (img.convert("RGB") if fmt == "JPEG" else img).save(buf, format=fmt)
    raw = buf.getvalue()
    mime = f"image/{fmt.lower()}"
    return img, raw, mime, base64.b64encode(raw).decode()

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
            if "429" in err and attempt < retries - 1:
                wait = 20
                m = re.search(r"retry_delay\s*\{\s*seconds:\s*(\d+)", err)
                if m: wait = int(m.group(1)) + 2
                st.warning(f"⏳ Quota Gemini, retry dans {wait}s… ({attempt+1}/{retries})")
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
            err = str(e)
            if "429" in err and attempt < retries - 1:
                st.warning(f"⏳ Quota OpenRouter, retry dans 15s… ({attempt+1}/{retries})")
                time.sleep(15); continue
            raise

def call_ai(gemini_key, openrouter_key, prompt, image_bytes, mime_type, b64):
    if get_provider() == "Gemini":
        if not gemini_key: raise ValueError("Clé Gemini manquante.")
        return call_gemini(gemini_key, prompt, image_bytes, mime_type)
    else:
        if not openrouter_key: raise ValueError("Clé OpenRouter manquante.")
        return call_openrouter(openrouter_key, prompt, b64, mime_type)

# ══════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════
with st.sidebar:
    # Rôle badge + déconnexion
    role_label = "🛡️ Admin" if is_admin() else "👤 Invité"
    role_class = "role-badge-admin" if is_admin() else "role-badge-guest"
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.5rem">
        <span style="font-weight:700;font-size:1.1rem">⚙️ Config</span>
        <span class="{role_class}">{role_label}</span>
    </div>""", unsafe_allow_html=True)

    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["role"] = None
        st.rerun()

    # Dashboard (admin seulement)
    if is_admin():
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["show_dashboard"] = not st.session_state.get("show_dashboard", False)

    st.markdown("---")

    # Provider
    st.markdown("### 🔌 Provider IA")
    provider_choice = st.radio("Provider", ["Gemini (Google)", "OpenRouter"],
        index=0 if get_provider()=="Gemini" else 1,
        label_visibility="collapsed", horizontal=True)
    st.session_state["provider"] = "Gemini" if "Gemini" in provider_choice else "OpenRouter"
    st.markdown("---")

    # Clés API (toujours depuis secrets, jamais saisie manuelle pour ne pas risquer de fuite)
    gemini_key = ""
    openrouter_key = ""
    try:
        gemini_key = st.secrets["API_Key"]["GEMINI_API_KEY"]
        if get_provider() == "Gemini":
            st.success("🔑 Clé Gemini chargée")
    except Exception:
        if get_provider() == "Gemini":
            st.warning("⚠️ Clé Gemini introuvable dans les secrets")

    try:
        openrouter_key = st.secrets["API_Key"]["OPEN_ROUTER_API_KEY"]
        if get_provider() == "OpenRouter":
            st.success("🔑 Clé OpenRouter chargée")
    except Exception:
        if get_provider() == "OpenRouter":
            st.warning("⚠️ Clé OpenRouter introuvable dans les secrets")

    st.markdown("---")
    lang = st.selectbox("🌐 Langue", ["Français","English","Español","Deutsch"])

    # Sélecteur de modèle
    st.markdown("---")
    st.markdown("### 🤖 Modèle IA")
    if get_provider() == "Gemini":
        st.caption("Changer si quota 429 atteint")
        gk = list(GEMINI_FREE_MODELS.keys())
        gl = list(GEMINI_FREE_MODELS.values())
        cur = get_gemini_model()
        chosen = st.radio("mg", gl, index=gk.index(cur), label_visibility="collapsed")
        st.session_state["gemini_model"] = gk[gl.index(chosen)]
        st.caption(f"`{st.session_state['gemini_model']}`")
    else:
        st.caption("Tous gratuits avec vision")
        ok = list(OPENROUTER_FREE_MODELS.keys())
        ol = list(OPENROUTER_FREE_MODELS.values())
        cur = get_openrouter_model()
        chosen = st.radio("mor", ol, index=ok.index(cur), label_visibility="collapsed")
        st.session_state["openrouter_model"] = ok[ol.index(chosen)]
        st.caption(f"`{st.session_state['openrouter_model']}`")

    # Scanner ses poubelles
    active_key = gemini_key if get_provider()=="Gemini" else openrouter_key
    st.markdown("---")
    st.markdown("### 📷 Scanner mes poubelles")
    st.caption("Photo de vos poubelles → configuration automatique")
    scan_tab1, scan_tab2 = st.tabs(["Caméra","Importer"])
    scan_image = None
    with scan_tab1:
        sc = st.camera_input("", label_visibility="collapsed", key="cam_scan")
        if sc: scan_image = sc
    with scan_tab2:
        su = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="up_scan")
        if su: scan_image = su

    if scan_image and active_key:
        if st.button("🤖 Détecter mes poubelles", use_container_width=True, type="primary"):
            with st.spinner("Analyse..."):
                try:
                    _, ib, mime, b64 = prepare_image(scan_image)
                    prompt_scan = """Analyse cette photo de poubelles/conteneurs de tri.
Réponds UNIQUEMENT en JSON valide sans backticks :
[{"name":"🟡 Poubelle Jaune","couleur":"#f5c518","description":"contenu accepté"}]
Emoji de couleur dans le nom. Précis sur le contenu."""
                    raw = call_ai(gemini_key, openrouter_key, prompt_scan, ib, mime, b64)
                    detected = json.loads(raw)
                    st.session_state.bins = {
                        b["name"]:{"description":b["description"],"couleur":b.get("couleur","#888"),"active":True}
                        for b in detected}
                    st.success(f"✅ {len(detected)} poubelle(s) détectée(s) !")
                    st.rerun()
                except json.JSONDecodeError:
                    st.error("❌ JSON invalide, réessayez.")
                except Exception as e:
                    st.error(f"❌ {'Quota atteint — changez de modèle' if '429' in str(e) else str(e)}")
    elif scan_image and not active_key:
        st.warning("Clé API manquante")

    # Gestion poubelles
    st.markdown("---")
    st.markdown("### 🗑️ Mes poubelles")
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
    st.markdown("### ➕ Ajouter")
    with st.form("add_bin", clear_on_submit=True):
        nn = st.text_input("Nom", placeholder="🔵 Poubelle Bleue")
        nd2 = st.text_area("Contenu", height=55)
        nc = st.color_picker("Couleur", "#4488ff")
        if st.form_submit_button("Ajouter", use_container_width=True) and nn:
            st.session_state.bins[nn] = {"description":nd2,"couleur":nc,"active":True}
            st.rerun()

    if st.button("↺ Réinitialiser", use_container_width=True):
        st.session_state.bins = {b["name"]:{"description":b["description"],"couleur":b["couleur"],"active":True} for b in DEFAULT_BINS}
        st.rerun()

    st.markdown(f"""<div style='font-size:.7rem;color:#555;text-align:center;margin-top:.8rem'>
    TriSmart v6.0 · {get_provider()} · Gratuit</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DASHBOARD (admin only)
# ══════════════════════════════════════════════
if is_admin() and st.session_state.get("show_dashboard", False):
    st.markdown("## 📊 Dashboard")
    logs = st.session_state.usage_log

    col1, col2, col3, col4 = st.columns(4)
    total    = len(logs)
    success  = sum(1 for l in logs if l["success"])
    errors   = total - success
    guests   = sum(1 for l in logs if l["role"] == "guest")

    col1.metric("🔍 Analyses totales", total)
    col2.metric("✅ Succès", success)
    col3.metric("❌ Erreurs", errors)
    col4.metric("👤 par Invités", guests)

    if logs:
        st.markdown("### 📋 Journal des analyses")
        st.dataframe(
            data=logs,
            use_container_width=True,
            column_config={
                "ts":       st.column_config.TextColumn("Heure"),
                "role":     st.column_config.TextColumn("Rôle"),
                "provider": st.column_config.TextColumn("Provider"),
                "model":    st.column_config.TextColumn("Modèle"),
                "objet":    st.column_config.TextColumn("Objet détecté"),
                "success":  st.column_config.CheckboxColumn("Succès"),
            },
            hide_index=True,
        )

        # Stats par provider
        st.markdown("### 📈 Répartition")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Par provider**")
            providers = {}
            for l in logs:
                providers[l["provider"]] = providers.get(l["provider"], 0) + 1
            for p, n in providers.items():
                st.progress(n / total, text=f"{p} : {n}")
        with c2:
            st.markdown("**Par rôle**")
            roles = {}
            for l in logs:
                roles[l["role"]] = roles.get(l["role"], 0) + 1
            for r, n in roles.items():
                st.progress(n / total, text=f"{r} : {n}")

        st.markdown("### 🗑️ Objets les plus analysés")
        objets = {}
        for l in logs:
            if l["objet"]:
                objets[l["objet"]] = objets.get(l["objet"], 0) + 1
        for obj, count in sorted(objets.items(), key=lambda x: -x[1])[:10]:
            st.markdown(f"- **{obj}** × {count}")

        if st.button("🗑️ Effacer le journal", type="secondary"):
            st.session_state.usage_log = []
            st.rerun()
    else:
        st.info("Aucune analyse enregistrée pour cette session.")

    st.markdown("---")

# ══════════════════════════════════════════════
# HEADER PRINCIPAL
# ══════════════════════════════════════════════
st.markdown('<div class="hero-title">♻️ TriSmart</div>', unsafe_allow_html=True)
st.markdown(f'<div class="hero-sub">Tri intelligent · {get_provider()} · Gratuit</div>', unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: st.markdown('<span class="step-badge">1</span> **Scannez** vos poubelles', unsafe_allow_html=True)
with c2: st.markdown('<span class="step-badge">2</span> **Photographiez** le déchet', unsafe_allow_html=True)
with c3: st.markdown('<span class="step-badge">3</span> **Obtenez** le bon tri', unsafe_allow_html=True)
st.markdown("---")

bins_config = {k: v for k, v in st.session_state.bins.items() if v.get("active")}
active_key  = gemini_key if get_provider()=="Gemini" else openrouter_key

if not active_key:
    st.info(f"👈 Clé {'Gemini' if get_provider()=='Gemini' else 'OpenRouter'} manquante dans les secrets Streamlit.")

if bins_config:
    cols = st.columns(min(len(bins_config), 4))
    for i, (bname, bdata) in enumerate(bins_config.items()):
        with cols[i % 4]:
            st.markdown(f"""<div style="background:{bdata['couleur']}22;border:1px solid {bdata['couleur']};
                border-radius:8px;padding:6px;text-align:center;font-size:.75rem;color:#ddd;margin-bottom:4px">
                {bname}</div>""", unsafe_allow_html=True)
    st.markdown("")

# ══════════════════════════════════════════════
# ZONE CAPTURE
# ══════════════════════════════════════════════
tab1, tab2 = st.tabs(["📸 Prendre une photo","🖼️ Importer une image"])
captured_image = None
source_label = ""

with tab1:
    cam = st.camera_input("", label_visibility="collapsed", key="cam_dechet")
    if cam: captured_image = cam; source_label = "photo caméra"

with tab2:
    upl = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                            label_visibility="collapsed", key="up_dechet")
    if upl: captured_image = upl; source_label = f"image ({upl.name})"

# ══════════════════════════════════════════════
# ANALYSE
# ══════════════════════════════════════════════
if captured_image and active_key and bins_config:
    img, img_bytes, mime_type, b64_img = prepare_image(captured_image)

    ci, co = st.columns([1,1])
    with ci:
        st.image(img, caption=f"📷 {source_label}", use_container_width=True)
    with co:
        model_active = get_gemini_model() if get_provider()=="Gemini" else get_openrouter_model()
        st.markdown("### 🔍 Prêt")
        st.caption(f"{img.size[0]}×{img.size[1]}px · `{model_active}`")
        analyze = st.button("🤖 Analyser", use_container_width=True, type="primary")

    if analyze:
        bins_text = "\n".join([f"- **{n}** : {d['description']}" for n,d in bins_config.items()])
        prompt = f"""Tu es un expert en gestion des déchets. Analyse cette photo.

POUBELLES DISPONIBLES :
{bins_text}

Réponds UNIQUEMENT en JSON valide, sans backticks :
{{
  "objet_detecte": "nom précis",
  "materiau": "matériau principal",
  "poubelle_recommandee": "NOM EXACT d'une des poubelles listées",
  "confiance": 85,
  "raison": "explication courte en {lang}",
  "gestes_importants": ["conseil 1 en {lang}", "conseil 2 en {lang}"],
  "poubelles_alternatives": [],
  "recyclable": true,
  "dangereux": false,
  "emoji": "🥤"
}}"""

        with st.spinner(f"🤖 Analyse via {get_provider()}..."):
            raw = ""
            try:
                raw = call_ai(gemini_key, openrouter_key, prompt, img_bytes, mime_type, b64_img)
                result = json.loads(raw)

                log_analysis(
                    success=True,
                    provider=get_provider(),
                    model=model_active,
                    objet=result.get("objet_detecte",""),
                    role=st.session_state.get("role","guest"),
                )

                st.markdown("---")
                st.markdown("## 🎯 Résultat")

                bin_name  = result.get("poubelle_recommandee","Inconnue")
                bin_color = get_color(bin_name)
                conf      = result.get("confiance", 0)

                st.markdown(f"""
                <div style="background:linear-gradient(135deg,#0d1f0d,#0d1520);
                    border:2px solid {bin_color};border-radius:20px;padding:1.5rem 2rem;margin:1rem 0">
                    <div style="font-size:3rem;text-align:center">{result.get('emoji','♻️')}</div>
                    <div style="text-align:center;font-size:1.5rem;font-weight:700;color:white;margin:.5rem 0">
                        {result.get('objet_detecte','Objet non identifié')}</div>
                    <div style="text-align:center;color:#aaa;font-size:.9rem">
                        Matériau : <strong style="color:#ddd">{result.get('materiau','Inconnu')}</strong></div>
                    <div style="margin:1rem 0;text-align:center">
                        <span style="background:{bin_color}22;border:2px solid {bin_color};color:white;
                            padding:.5rem 1.5rem;border-radius:999px;font-size:1.2rem;font-weight:700">
                            ➜ {bin_name}</span></div>
                    <div style="margin:.5rem 0">
                        <div style="display:flex;justify-content:space-between;color:#aaa;font-size:.8rem;margin-bottom:4px">
                            <span>Confiance IA</span><span>{conf}%</span></div>
                        <div style="background:#333;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,{bin_color},#00a8ff);
                                width:{conf}%;height:8px;border-radius:4px"></div></div></div>
                    <div style="color:#ccc;font-size:.95rem;margin-top:1rem;line-height:1.5">
                        💡 {result.get('raison','')}</div>
                </div>""", unsafe_allow_html=True)

                gestes = result.get("gestes_importants",[])
                if gestes:
                    st.markdown("### 📋 Gestes importants")
                    for g in gestes: st.markdown(f"✅ {g}")

                alts = result.get("poubelles_alternatives",[])
                if alts:
                    st.markdown("### 🔄 Alternatives")
                    for a in alts:
                        c = get_color(a)
                        st.markdown(f'<div style="border-left:3px solid {c};padding-left:8px;color:#ccc">⚠️ {a}</div>',
                                    unsafe_allow_html=True)

                r1, r2 = st.columns(2)
                with r1:
                    if result.get("recyclable"):
                        st.success("♻️ Recyclable")
                    else:
                        st.error("🚫 Non recyclable")
                with r2:
                    if result.get("dangereux"):
                        st.warning("⚠️ Dangereux")
                    else:
                        st.info("✅ Non dangereux")

                # JSON brut — admin seulement
                if is_admin():
                    with st.expander("🔧 Debug — JSON brut + infos techniques"):
                        st.json(result)
                        st.markdown(f"""
                        **Provider :** `{get_provider()}`  
                        **Modèle :** `{model_active}`  
                        **Rôle :** `{st.session_state.get('role')}`  
                        **Analyses cette session :** `{len(st.session_state.usage_log)}`
                        """)

            except json.JSONDecodeError as e:
                log_analysis(False, get_provider(), model_active, role=st.session_state.get("role","guest"))
                st.error(f"❌ Erreur JSON : {e}")
                if is_admin(): st.code(raw)

            except Exception as e:
                log_analysis(False, get_provider(), model_active, role=st.session_state.get("role","guest"))
                err = str(e)
                if "429" in err:
                    st.error("❌ **Quota atteint.**\n\n👉 Changez de modèle ou de provider dans la sidebar.")
                else:
                    st.error(f"❌ Erreur : {e}")
                    if is_admin(): st.exception(e)

elif captured_image and not active_key:
    st.warning("⚠️ Clé API manquante dans les secrets.")
elif captured_image and not bins_config:
    st.warning("⚠️ Aucune poubelle active.")

# ══════════════════════════════════════════════
# GUIDE
# ══════════════════════════════════════════════
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

st.markdown("""
<div style='text-align:center;color:#444;font-size:.8rem;margin-top:2rem'>
TriSmart v6.0 · Gemini + OpenRouter · Streamlit · 100% Gratuit
</div>""", unsafe_allow_html=True)
