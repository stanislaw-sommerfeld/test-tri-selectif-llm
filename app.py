import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io
import hmac

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
    valid_user = hmac.compare_digest(username, st.secrets["Identifiers"]["APP_USERNAME"])
    valid_pass = hmac.compare_digest(password, st.secrets["Identifiers"]["APP_PASSWORD"])
    return valid_user and valid_pass

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
# CONSTANTES
# ─────────────────────────────────────────────
DEFAULT_BINS = [
    {"name": "🟡 Poubelle Jaune",       "couleur": "#f5c518", "description": "Recyclables : plastiques, métaux, cartons, briques alimentaires"},
    {"name": "🟢 Poubelle Verte",       "couleur": "#00b34a", "description": "Verre uniquement : bouteilles, bocaux, pots"},
    {"name": "⚫ Poubelle Noire/Grise", "couleur": "#888888", "description": "Ordures ménagères résiduelles non recyclables"},
    {"name": "🟤 Poubelle Marron",      "couleur": "#8B4513", "description": "Bio-déchets et compostables"},
]

# ─────────────────────────────────────────────
# SESSION STATE — poubelles persistantes
# ─────────────────────────────────────────────
if "bins" not in st.session_state:
    st.session_state.bins = {
        b["name"]: {"description": b["description"], "couleur": b["couleur"], "active": True}
        for b in DEFAULT_BINS
    }

def get_color(name):
    return st.session_state.bins.get(name, {}).get("couleur", "#888888")

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def prepare_image(uploaded):
    img = Image.open(uploaded)
    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() not in ["JPEG", "PNG", "WEBP"]:
        fmt = "JPEG"
    img_out = img.convert("RGB") if fmt == "JPEG" else img
    img_out.save(buf, format=fmt)
    buf.seek(0)
    return img, Image.open(buf)

def call_gemini(api_key, prompt, pil_img):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content([prompt, pil_img])
    raw = response.text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    if st.button("🚪 Se déconnecter", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()
    st.markdown("---")

    # Clé API
    api_key = st.secrets["API_Key"]["GEMINI_API_KEY"] if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input("🔑 Clé API Google Gemini", type="password",
                                 help="Gratuit sur https://aistudio.google.com",
                                 placeholder="AIza...")
    else:
        st.success("🔑 Clé API chargée")

    st.markdown("---")
    lang = st.selectbox("🌐 Langue", ["Français", "English", "Español", "Deutsch"])

    # ── Scanner ses poubelles par photo ──
    st.markdown("---")
    st.markdown("### 📷 Scanner mes poubelles")
    st.caption("Photographiez vos poubelles pour les configurer automatiquement via l'IA")

    scan_tab1, scan_tab2 = st.tabs(["Caméra", "Importer"])
    scan_image = None
    with scan_tab1:
        sc = st.camera_input("Photo poubelles", label_visibility="collapsed", key="cam_scan")
        if sc:
            scan_image = sc
    with scan_tab2:
        su = st.file_uploader("Image poubelles", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="up_scan")
        if su:
            scan_image = su

    if scan_image and api_key:
        if st.button("🤖 Détecter mes poubelles", use_container_width=True, type="primary"):
            with st.spinner("Analyse des poubelles en cours..."):
                try:
                    _, pil_scan = prepare_image(scan_image)
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
                    raw = call_gemini(api_key, prompt_scan, pil_scan)
                    detected = json.loads(raw)
                    st.session_state.bins = {
                        b["name"]: {
                            "description": b["description"],
                            "couleur": b.get("couleur", "#888"),
                            "active": True
                        }
                        for b in detected
                    }
                    st.success(f"✅ {len(detected)} poubelle(s) détectée(s) !")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur : {e}")
    elif scan_image and not api_key:
        st.warning("Clé API requise pour scanner")

    # ── Gestion manuelle ──
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
                                     key=f"desc_{bname}", height=60,
                                     label_visibility="collapsed")
            st.session_state.bins[bname]["description"] = new_desc

    for b in to_delete:
        del st.session_state.bins[b]
        st.rerun()

    # ── Ajouter une poubelle ──
    st.markdown("---")
    st.markdown("### ➕ Ajouter une poubelle")
    with st.form("add_bin_form", clear_on_submit=True):
        new_name = st.text_input("Nom", placeholder="🔵 Poubelle Bleue")
        new_desc_add = st.text_area("Contenu accepté", height=60)
        new_color = st.color_picker("Couleur", "#4488ff")
        if st.form_submit_button("Ajouter", use_container_width=True) and new_name:
            st.session_state.bins[new_name] = {
                "description": new_desc_add,
                "couleur": new_color,
                "active": True
            }
            st.success(f"✅ {new_name} ajoutée !")
            st.rerun()

    if st.button("↺ Réinitialiser par défaut", use_container_width=True):
        st.session_state.bins = {
            b["name"]: {"description": b["description"], "couleur": b["couleur"], "active": True}
            for b in DEFAULT_BINS
        }
        st.rerun()

    st.markdown("""
    <div style='font-size:0.75rem;color:#666;text-align:center;margin-top:1rem'>
    TriSmart v3.0 · Gemini 2.0 Flash · Gratuit
    </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">♻️ TriSmart</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Détection intelligente des déchets · Gemini 2.0 Flash · Gratuit</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<span class="step-badge">1</span> **Scannez** vos poubelles', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="step-badge">2</span> **Photographiez** le déchet', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="step-badge">3</span> **Obtenez** le bon tri', unsafe_allow_html=True)

st.markdown("---")

# Poubelles actives
bins_config = {k: v for k, v in st.session_state.bins.items() if v.get("active")}

if not api_key:
    st.info("👈 **Entrez votre clé API Google Gemini** dans la barre latérale.\n\n🆓 Gratuite sur [aistudio.google.com](https://aistudio.google.com)")

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
if captured_image and api_key and bins_config:
    img, pil_img = prepare_image(captured_image)

    col_img, col_info = st.columns([1, 1])
    with col_img:
        st.image(img, caption=f"📷 {source_label}", use_container_width=True)
    with col_info:
        st.markdown("### 🔍 Prêt à analyser")
        st.caption(f"{img.size[0]}×{img.size[1]}px · Gemini 2.0 Flash")
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

        with st.spinner("🤖 Analyse en cours..."):
            try:
                raw = call_gemini(api_key, prompt, pil_img)
                result = json.loads(raw)

                st.markdown("---")
                st.markdown("## 🎯 Résultat")

                bin_name = result.get("poubelle_recommandee", "Inconnue")
                bin_color = get_color(bin_name)
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
                    st.success("♻️ Recyclable") if result.get("recyclable") else st.error("🚫 Non recyclable")
                with c2:
                    st.warning("⚠️ Dangereux") if result.get("dangereux") else st.info("✅ Non dangereux")

                with st.expander("🔧 JSON brut"):
                    st.json(result)

            except json.JSONDecodeError as e:
                st.error(f"❌ Erreur JSON : {e}")
                st.code(raw)
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
                st.exception(e)

elif captured_image and not api_key:
    st.warning("⚠️ Clé API manquante.")
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

st.markdown("""
<div style='text-align:center;color:#444;font-size:0.8rem;margin-top:2rem'>
    TriSmart v3.0 · Gemini 2.0 Flash · Streamlit · 100% Gratuit
</div>""", unsafe_allow_html=True)