# ♻️ TriSmart – Tri Intelligent des Déchets

Application Streamlit de détection et tri des déchets par IA (Gemini 1.5 Flash).  
100% gratuit · Protégé par login · Déployable en 5 minutes.

---

## 🔐 Authentification

L'app est protégée par un login username/password.  
Les identifiants sont stockés uniquement dans les Secrets Streamlit, jamais dans le code.  
Un bouton **"Se déconnecter"** est disponible dans la barre latérale.

---

## 💻 Lancement en local (optionnel)

```bash
pip install -r requirements.txt
streamlit run app.py
```

En local, entre ta clé Gemini directement dans la barre latérale.  
Pour le login en local, crée un fichier `.streamlit/secrets.toml` :

```toml
GEMINI_API_KEY = "AIza..."
APP_USERNAME = "tonnom"
APP_PASSWORD = "tonmotdepasse"
```

> ⚠️ Ajoute `.streamlit/secrets.toml` à ton `.gitignore` pour ne jamais le pousser sur GitHub.

---

## 📱 Fonctionnalités

- **📸 Capture caméra** directement depuis le navigateur (desktop & mobile)
- **🖼️ Import d'image** depuis la galerie
- **🤖 Analyse IA** avec Gemini 1.5 Flash (Google)
- **🗑️ Poubelles configurables** selon ta commune / situation
- **➕ Ajout de poubelles** personnalisées
- **🌐 Multilingue** : FR / EN / ES / DE
- **📋 Conseils de tri** personnalisés
- **🔐 Login** protégé par username/password

---

## 🗑️ Configuration des poubelles

Dans la barre latérale :
1. Coche les poubelles présentes chez toi
2. Modifie leur description si ta commune a des règles spécifiques
3. Ajoute des poubelles personnalisées si besoin

---

## 💰 Coût

| Service | Prix |
|---------|------|
| Streamlit Cloud | Gratuit |
| GitHub | Gratuit |
| Gemini 1.5 Flash | Gratuit (1 500 analyses/jour) |
| **Total** | **0 €** |

---

## 📦 Stack technique

- **Frontend** : Streamlit
- **IA** : Gemini 1.5 Flash (Google AI)
- **Python** : 3.11
- **Librairies** : google-generativeai, Pillow
