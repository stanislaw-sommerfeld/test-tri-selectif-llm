# ♻️ TriSmart – Tri Intelligent des Déchets

Application Streamlit de détection et tri des déchets par IA (Gemini 1.5 Flash).  
100% gratuit · Protégé par login · Déployable en 5 minutes.

---

## 🚀 Déploiement sur Streamlit Cloud (recommandé)

### 1. Clé API Gemini (gratuite)
- Va sur [aistudio.google.com](https://aistudio.google.com)
- Clique **"Get API Key"** → copie la clé (`AIza...`)

### 2. Mettre les fichiers sur GitHub
Crée un dépôt GitHub (public ou privé) et dépose uniquement :
- `app.py`
- `requirements.txt`

> ⚠️ Ne jamais mettre `secrets.toml` sur GitHub !

### 3. Déployer sur Streamlit Cloud
- Va sur [share.streamlit.io](https://share.streamlit.io)
- Connecte ton compte GitHub
- Clique **"New app"** → sélectionne ton dépôt → `app.py`
- Clique **"Advanced settings"** et choisis **Python 3.11**
- Dans la zone **Secrets**, colle ceci en remplaçant par tes vraies valeurs :

```toml
GEMINI_API_KEY = "AIza..."
APP_USERNAME = "tonnom"
APP_PASSWORD = "tonmotdepasse"
```

- Clique **Save** puis **Deploy**

En 2 minutes tu obtiens une URL publique `https://[ton-app].streamlit.app` 🎉

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
