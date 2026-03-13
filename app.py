import streamlit as st
import google.generativeai as genai
import json
from PIL import Image
import io

# ─────────────────────────────────────────────
# CONFIG PAGE
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="♻️ TriSmart – Tri Intelligent des Déchets",
    page_icon="♻️",
    layout="centered",
    initial_sidebar_state="expanded",
)

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
# POUBELLES PAR DÉFAUT
# ─────────────────────────────────────────────
DEFAULT_BINS = {
    "🟡 Poubelle Jaune": {
        "couleur": "#f5c518",
        "description": "Recyclables : plastiques, métaux, cartons, briques alimentaires",
    },
    "🟢 Poubelle Verte": {
        "couleur": "#00b34a",
        "description": "Verre uniquement : bouteilles, bocaux, pots",
    },
    "⚫ Poubelle Noire / Grise": {
        "couleur": "#888888",
        "description": "Ordures ménagères résiduelles non recyclables",
    },
    "🟤 Poubelle Marron": {
        "couleur": "#8B4513",
        "description": "Bio-déchets et compostables",
    },
}

BIN_COLORS = {
    "🟡 Poubelle Jaune": "#f5c518",
    "🟢 Poubelle Verte": "#00b34a",
    "⚫ Poubelle Noire / Grise": "#666666",
    "🟤 Poubelle Marron": "#8B4513",
    "🔴 Déchetterie / Dangereux": "#e74c3c",
}

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Clé API — d'abord depuis les secrets Streamlit, sinon champ manuel
    api_key = st.secrets.get("GEMINI_API_KEY", "") if hasattr(st, "secrets") else ""
    if not api_key:
        api_key = st.text_input(
            "🔑 Clé API Google Gemini",
            type="password",
            help="Gratuit sur https://aistudio.google.com — 1 500 requêtes/jour",
            placeholder="AIza...",
        )
    else:
        st.success("🔑 Clé API chargée depuis les secrets")

    st.markdown("---")
    st.markdown("### 🗑️ Mes poubelles disponibles")
    st.caption("Cochez les poubelles présentes et décrivez leur contenu accepté")

    bins_config = {}
    for bin_name, bin_data in DEFAULT_BINS.items():
        active = st.checkbox(bin_name, value=True, key=f"cb_{bin_name}")
        if active:
            desc = st.text_area(
                "Contenu accepté",
                value=bin_data["description"],
                key=f"desc_{bin_name}",
                height=68,
            )
            bins_config[bin_name] = {"description": desc, "couleur": bin_data["couleur"]}

    st.markdown("---")
    st.markdown("### ➕ Ajouter une poubelle")
    new_bin_name = st.text_input("Nom (ex: 🔵 Poubelle Bleue)", key="new_bin_name")
    new_bin_desc = st.text_area("Ce qu'elle accepte", key="new_bin_desc", height=68)
    if st.button("Ajouter", use_container_width=True) and new_bin_name:
        bins_config[new_bin_name] = {"description": new_bin_desc, "couleur": "#4488ff"}
        st.success(f"✅ {new_bin_name} ajoutée !")

    st.markdown("---")
    lang = st.selectbox("🌐 Langue de réponse", ["Français", "English", "Español", "Deutsch"])

    st.markdown("---")
    st.markdown("""
    <div style='font-size:0.75rem; color:#666; text-align:center'>
    TriSmart v2.0 · Gemini 1.5 Flash<br>
    Google AI · Streamlit · 100% Gratuit
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────
st.markdown('<div class="hero-title">♻️ TriSmart</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Détection intelligente des déchets · Propulsé par Gemini Flash · Gratuit</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown('<span class="step-badge">1</span> **Configurez** vos poubelles', unsafe_allow_html=True)
with col2:
    st.markdown('<span class="step-badge">2</span> **Photographiez** votre déchet', unsafe_allow_html=True)
with col3:
    st.markdown('<span class="step-badge">3</span> **Obtenez** le bon tri', unsafe_allow_html=True)

st.markdown("---")

# ─────────────────────────────────────────────
# ZONE DE CAPTURE
# ─────────────────────────────────────────────
if not api_key:
    st.info("👈 **Entrez votre clé API Google Gemini** dans la barre latérale.\n\n🆓 Gratuite sur [aistudio.google.com](https://aistudio.google.com) — 1 500 analyses/jour !")

tab1, tab2 = st.tabs(["📸 Prendre une photo", "🖼️ Importer une image"])

captured_image = None
source_label = ""

with tab1:
    st.markdown("#### Utilisez votre appareil photo")
    camera_photo = st.camera_input(
        "Pointez la caméra sur votre déchet",
        label_visibility="collapsed",
    )
    if camera_photo:
        captured_image = camera_photo
        source_label = "photo caméra"

with tab2:
    st.markdown("#### Importez depuis votre galerie")
    uploaded_file = st.file_uploader(
        "Glissez une image ou cliquez pour parcourir",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )
    if uploaded_file:
        captured_image = uploaded_file
        source_label = f"image importée ({uploaded_file.name})"

# ─────────────────────────────────────────────
# ANALYSE
# ─────────────────────────────────────────────
if captured_image and api_key and bins_config:

    img = Image.open(captured_image)
    col_img, col_info = st.columns([1, 1])
    with col_img:
        st.image(img, caption=f"📷 {source_label}", use_container_width=True)
    with col_info:
        st.markdown("### 🔍 Prêt à analyser")
        st.caption(f"{img.size[0]}×{img.size[1]}px · Gemini 1.5 Flash")
        analyze = st.button("🤖 Analyser avec l'IA", use_container_width=True, type="primary")
        st.markdown("**Poubelles configurées :**")
        for bname in bins_config:
            color = BIN_COLORS.get(bname, "#888")
            st.markdown(
                f'<div style="border-left:3px solid {color};padding-left:8px;margin:2px 0;font-size:0.85rem">{bname}</div>',
                unsafe_allow_html=True,
            )

    if analyze:
        bins_text = "\n".join(
            [f"- **{name}** : {data['description']}" for name, data in bins_config.items()]
        )

        prompt = f"""Tu es un expert en gestion des déchets et recyclage. Analyse cette photo d'un déchet ou d'un objet à jeter.

POUBELLES DISPONIBLES POUR CE TRI :
{bins_text}

Réponds UNIQUEMENT en JSON valide avec cette structure exacte :
{{
  "objet_detecte": "nom précis de l'objet/déchet identifié",
  "materiau": "matériau principal (ex: plastique PET, verre, papier, métal aluminium, etc.)",
  "poubelle_recommandee": "NOM EXACT d'une des poubelles listées ci-dessus",
  "confiance": 85,
  "raison": "explication courte en {lang} pourquoi ce déchet va dans cette poubelle",
  "gestes_importants": ["conseil 1 en {lang}", "conseil 2 en {lang}"],
  "poubelles_alternatives": [],
  "recyclable": true,
  "dangereux": false,
  "emoji": "🥤"
}}

La confiance est un entier entre 0 et 100.
Réponds UNIQUEMENT avec le JSON, sans texte avant ou après, sans backticks."""

        with st.spinner("🤖 Analyse en cours avec Gemini Flash..."):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")

                # Convertir image pour Gemini
                img_bytes = io.BytesIO()
                fmt = img.format or "JPEG"
                if fmt.upper() not in ["JPEG", "PNG", "WEBP"]:
                    fmt = "JPEG"
                img_rgb = img.convert("RGB") if fmt == "JPEG" else img
                img_rgb.save(img_bytes, format=fmt)
                img_bytes.seek(0)

                from PIL import Image as PILImage
                pil_img = PILImage.open(img_bytes)

                response = model.generate_content([prompt, pil_img])
                raw = response.text.strip()

                # Nettoyer si markdown
                if "```" in raw:
                    raw = raw.split("```")[1]
                    if raw.startswith("json"):
                        raw = raw[4:]
                raw = raw.strip()

                result = json.loads(raw)

                # ── RÉSULTAT ──
                st.markdown("---")
                st.markdown("## 🎯 Résultat de l'analyse")

                bin_name = result.get("poubelle_recommandee", "Inconnue")
                bin_color = BIN_COLORS.get(bin_name, "#00d084")
                confidence = result.get("confiance", 0)

                st.markdown(f"""
                <div style="
                    background: linear-gradient(135deg, #0d1f0d 0%, #0d1520 100%);
                    border: 2px solid {bin_color};
                    border-radius: 20px;
                    padding: 1.5rem 2rem;
                    margin: 1rem 0;
                ">
                    <div style="font-size:3rem;text-align:center">{result.get('emoji','♻️')}</div>
                    <div style="text-align:center;font-size:1.5rem;font-weight:700;color:white;margin:0.5rem 0">
                        {result.get('objet_detecte','Objet non identifié')}
                    </div>
                    <div style="text-align:center;color:#aaa;font-size:0.9rem">
                        Matériau : <strong style="color:#ddd">{result.get('materiau','Inconnu')}</strong>
                    </div>
                    <div style="margin:1rem 0;text-align:center">
                        <span style="
                            background:{bin_color}22;border:2px solid {bin_color};
                            color:white;padding:0.5rem 1.5rem;border-radius:999px;
                            font-size:1.2rem;font-weight:700;
                        ">➜ {bin_name}</span>
                    </div>
                    <div style="margin:0.5rem 0">
                        <div style="display:flex;justify-content:space-between;color:#aaa;font-size:0.8rem;margin-bottom:4px">
                            <span>Confiance IA</span><span>{confidence}%</span>
                        </div>
                        <div style="background:#333;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,{bin_color},#00a8ff);width:{confidence}%;height:8px;border-radius:4px"></div>
                        </div>
                    </div>
                    <div style="color:#ccc;font-size:0.95rem;margin-top:1rem;line-height:1.5">
                        💡 {result.get('raison','')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                gestes = result.get("gestes_importants", [])
                if gestes:
                    st.markdown("### 📋 Gestes importants")
                    for g in gestes:
                        st.markdown(f"✅ {g}")

                alts = result.get("poubelles_alternatives", [])
                if alts:
                    st.markdown("### 🔄 Alternatives possibles")
                    for a in alts:
                        c = BIN_COLORS.get(a, "#888")
                        st.markdown(
                            f'<div style="border-left:3px solid {c};padding-left:8px;color:#ccc">⚠️ {a}</div>',
                            unsafe_allow_html=True,
                        )

                col_b1, col_b2 = st.columns(2)
                with col_b1:
                    if result.get("recyclable"):
                        st.success("♻️ Recyclable")
                    else:
                        st.error("🚫 Non recyclable")
                with col_b2:
                    if result.get("dangereux"):
                        st.warning("⚠️ Déchet dangereux")
                    else:
                        st.info("✅ Non dangereux")

                with st.expander("🔧 Détails techniques (JSON brut)"):
                    st.json(result)

            except json.JSONDecodeError as e:
                st.error(f"❌ Erreur de parsing JSON : {e}")
                st.code(raw)
            except Exception as e:
                st.error(f"❌ Erreur : {e}")
                st.exception(e)

elif captured_image and not api_key:
    st.warning("⚠️ Entrez votre clé API Google Gemini dans la barre latérale.")
elif captured_image and not bins_config:
    st.warning("⚠️ Activez au moins une poubelle dans la barre latérale.")

# ─────────────────────────────────────────────
# GUIDE
# ─────────────────────────────────────────────
st.markdown("---")
with st.expander("📖 Guide de tri rapide (France métropolitaine)"):
    st.markdown("""
| Déchet | Poubelle |
|--------|----------|
| Bouteilles plastique, canettes, boîtes | 🟡 Jaune |
| Cartons, journaux, magazines | 🟡 Jaune |
| Bouteilles en verre, bocaux | 🟢 Verte |
| Épluchures, restes alimentaires | 🟤 Marron |
| Sacs plastiques sales, mouchoirs | ⚫ Noire |
| Piles, médicaments, huiles | 🔴 Déchetterie |
| Appareils électroniques | 🔴 DEEE |

> 💡 Toujours vider et rincer les emballages avant recyclage !
    """)

st.markdown("""
<div style='text-align:center;color:#444;font-size:0.8rem;margin-top:2rem'>
    TriSmart v2.0 · Gemini 1.5 Flash (Google AI) · Streamlit · 100% Gratuit
</div>
""", unsafe_allow_html=True)
