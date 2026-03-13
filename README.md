# ♻️ TriSmart – Tri Intelligent des Déchets

Application Streamlit de détection et tri des déchets par IA (Claude Vision).

## 🚀 Lancement rapide

### 1. Installer les dépendances
```bash
pip install -r requirements.txt
```

### 2. Lancer l'application
```bash
streamlit run app.py
```

### 3. Sur mobile (accès depuis téléphone)
Lancez sur votre PC/Mac, puis depuis votre téléphone sur le même réseau WiFi :
```
http://[IP_de_votre_machine]:8501
```

Ou utilisez **ngrok** pour un accès distant :
```bash
pip install pyngrok
ngrok http 8501
```

## 📱 Fonctionnalités

- **📸 Capture caméra** directement depuis le navigateur (desktop & mobile)
- **🖼️ Import d'image** depuis la galerie
- **🤖 Analyse IA** avec Claude Vision (Anthropic)
- **🗑️ Poubelles configurables** selon votre commune / situation
- **🌐 Multilingue** : FR / EN / ES / DE
- **📋 Conseils de tri** personnalisés

## 🔑 Clé API

Obtenez votre clé sur : https://console.anthropic.com

## 🗑️ Configuration des poubelles

Dans la barre latérale :
1. Cochez les poubelles présentes chez vous
2. Modifiez leur description si votre commune a des règles spécifiques
3. Ajoutez des poubelles personnalisées

## 📦 Stack technique

- **Frontend** : Streamlit
- **IA** : Claude claude-opus-4-5 Vision (Anthropic)
- **Python** : 3.9+
- **Librairies** : anthropic, Pillow
