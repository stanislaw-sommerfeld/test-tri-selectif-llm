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
    try:
        # Check against Streamlit secrets if deployed
        valid_user = hmac.compare_digest(username, st.secrets["Identifiers"]["APP_USERNAME"])
        valid_pass = hmac.compare_digest(password, st.secrets["Identifiers"]["APP_PASSWORD"])
        return valid_user and valid_pass
    except FileNotFoundError:
        # Fallback to True if you are testing locally without a secrets.toml file
        return True 
    except KeyError:
        return True

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
    
    with st.form("login_form"):
        username = st.text_input("Nom d'utilisateur")
        password = st.text_input("Mot de passe", type="password")
        submit = st.form_submit_button("Se connecter", use_container_width=True)
        
        if submit:
            if check_credentials(username, password):
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Identifiants incorrects")

# Initialize authentication state
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# Enforce login screen if not authenticated
# (Comment the next 3 lines out if you want to bypass the login screen completely)
if not st.session_state["authenticated"]:
    login_screen()
    st.stop()

# ─────────────────────────────────────────────
# MAIN APP
# ─────────────────────────────────────────────
st.title("♻️ TriSmart Analyzer")

# Configuration in the Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Clé API Gemini", 
        type="password", 
        help="Insérez votre clé gratuite générée depuis Google AI Studio"
    )
    st.markdown("[Obtenir une clé API gratuite](https://aistudio.google.com/)")
    
    bins_config = st.multiselect(
        "Poubelles actives", 
        ["🟡 Jaune", "🟢 Verte", "🟤 Marron", "⚫ Noire", "🔴 Déchetterie"], 
        default=["🟡 Jaune", "🟢 Verte", "⚫ Noire"]
    )

captured_image = st.camera_input("📸 Prenez une photo du déchet à trier")

if captured_image and api_key and bins_config:
    try:
        # Initialize the API with your free-tier key
        genai.configure(api_key=api_key)
        
        # 🟢 CRUCIAL: Use a model that supports the Free Tier!
        # Gemini 2.5 Flash is highly capable for vision tasks and operates on the free tier.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        image = Image.open(captured_image)
        
        with st.spinner("Analyse en cours par Gemini..."):
            prompt = f"""
            Analyse cette image de déchet. 
            Les poubelles disponibles sont: {', '.join(bins_config)}.
            Réponds UNIQUEMENT avec un objet JSON valide. N'inclus pas de balises markdown comme ```json.
            Utilise exactement ces clés :
            - "poubelle": (la couleur de la poubelle recommandée)
            - "explication": (une courte justification de ton choix)
            - "recyclable": (boolean, true ou false)
            - "dangereux": (boolean, true ou false)
            """
            
            # Send the text prompt and the image to the model
            response = model.generate_content([prompt, image])
            raw = response.text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(raw)
            
            st.success(f"### Poubelle recommandée : {result.get('poubelle', 'Non identifiée')}")
            st.info(f"**Pourquoi ?** {result.get('explication', '')}")
            
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
        # If the API key is invalid or rate limits are hit, it will show here.
        st.error(f"❌ Erreur de l'API : {e}")

elif captured_image and not api_key:
    st.warning("⚠️ Clé API manquante. Veuillez entrer votre clé dans la barre latérale.")
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