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
# LANGUES UI
# ══════════════════════════════════════════════
LANGUAGES = {
    "🇫🇷 Français":  "fr",
    "🇬🇧 English":   "en",
    "🇩🇪 Deutsch":   "de",
    "🇪🇸 Español":   "es",
    "🇰🇷 한국어":     "ko",
    "🇨🇳 中文":      "zh",
    "🇯🇵 日本語":     "ja",
}

UI = {
    "fr": {
        "login_subtitle":    "Tri intelligent des déchets par IA",
        "login_title":       "🔐 Connexion",
        "username":          "Nom d'utilisateur",
        "password":          "Mot de passe",
        "login_btn":         "Se connecter",
        "login_error":       "❌ Identifiants incorrects",
        "guest_btn":         "👤 Continuer sans compte *(accès limité)*",
        "guest_hint":        "Accès invité : modèles gratuits uniquement · pas de détails techniques",
        "config":            "⚙️ Config",
        "logout":            "🚪 Se déconnecter",
        "dashboard":         "📊 Dashboard",
        "provider":          "🔌 Provider IA",
        "key_loaded_gemini": "🔑 Clé Gemini chargée",
        "key_miss_gemini":   "⚠️ Clé Gemini introuvable",
        "key_loaded_or":     "🔑 Clé OpenRouter chargée",
        "key_miss_or":       "⚠️ Clé OpenRouter introuvable",
        "lang_label":        "🌐 Langue",
        "country_label":     "🌍 Pays (guide de tri)",
        "model_label":       "🤖 Modèle IA",
        "model_hint_gemini": "Changer si quota 429 atteint",
        "model_hint_or":     "Tous gratuits avec vision",
        "scan_title":        "📷 Scanner mes poubelles",
        "scan_hint":         "Photo de vos poubelles → configuration automatique",
        "scan_btn":          "🤖 Détecter mes poubelles",
        "scan_success":      "poubelle(s) détectée(s)",
        "scan_added":        "ajoutée(s)",
        "scan_updated":      "mise(s) à jour",
        "scan_err_json":     "❌ JSON invalide, réessayez.",
        "scan_err_quota":    "Quota atteint — changez de modèle",
        "scan_key_missing":  "Clé API manquante",
        "bins_title":        "🗑️ Mes poubelles",
        "add_title":         "➕ Ajouter",
        "bin_name_ph":       "🔵 Poubelle Bleue",
        "bin_content":       "Contenu",
        "add_btn":           "Ajouter",
        "reset_btn":         "↺ Réinitialiser",
        "step1":             "**Scannez** vos poubelles",
        "step2":             "**Photographiez** le déchet",
        "step3":             "**Obtenez** le bon tri",
        "tab_camera":        "📸 Prendre une photo",
        "tab_upload":        "🖼️ Importer une image",
        "ready":             "### 🔍 Prêt",
        "analyze_btn":       "🤖 Analyser",
        "result_title":      "## 🎯 Résultat",
        "material":          "Matériau",
        "confidence":        "Confiance IA",
        "gestures":          "### 📋 Gestes importants",
        "alternatives":      "### 🔄 Alternatives",
        "recyclable":        "♻️ Recyclable",
        "not_recyclable":    "🚫 Non recyclable",
        "dangerous":         "⚠️ Dangereux",
        "not_dangerous":     "✅ Non dangereux",
        "debug_title":       "🔧 Debug — JSON brut + infos techniques",
        "key_missing_main":  "Clé API manquante dans les secrets.",
        "no_bin_active":     "⚠️ Aucune poubelle active.",
        "guide_title":       "📖 Guide de tri rapide",
        "guide_tip":         "💡 Vider et rincer les emballages avant recyclage !",
        "dash_total":        "🔍 Analyses totales",
        "dash_ok":           "✅ Succès",
        "dash_err":          "❌ Erreurs",
        "dash_guest":        "👤 par Invités",
        "dash_log":          "### 📋 Journal",
        "dash_stats":        "### 📈 Répartition",
        "dash_by_provider":  "**Par provider**",
        "dash_by_role":      "**Par rôle**",
        "dash_top":          "### 🗑️ Objets les plus analysés",
        "dash_clear":        "🗑️ Effacer le journal",
        "dash_empty":        "Aucune analyse enregistrée pour cette session.",
        "quota_err":         "❌ **Quota atteint.**\n\n👉 Changez de modèle ou de provider dans la sidebar.",
        "json_err":          "❌ Erreur JSON",
        "err_prefix":        "❌ Erreur",
        "ai_lang":           "French",
    },
    "en": {
        "login_subtitle":    "AI-powered intelligent waste sorting",
        "login_title":       "🔐 Login",
        "username":          "Username",
        "password":          "Password",
        "login_btn":         "Log in",
        "login_error":       "❌ Incorrect credentials",
        "guest_btn":         "👤 Continue without account *(limited access)*",
        "guest_hint":        "Guest access: free models only · no technical details",
        "config":            "⚙️ Config",
        "logout":            "🚪 Log out",
        "dashboard":         "📊 Dashboard",
        "provider":          "🔌 AI Provider",
        "key_loaded_gemini": "🔑 Gemini key loaded",
        "key_miss_gemini":   "⚠️ Gemini key not found",
        "key_loaded_or":     "🔑 OpenRouter key loaded",
        "key_miss_or":       "⚠️ OpenRouter key not found",
        "lang_label":        "🌐 Language",
        "country_label":     "🌍 Country (sorting guide)",
        "model_label":       "🤖 AI Model",
        "model_hint_gemini": "Switch if 429 quota hit",
        "model_hint_or":     "All free with vision",
        "scan_title":        "📷 Scan my bins",
        "scan_hint":         "Photo of your bins → auto-configuration",
        "scan_btn":          "🤖 Detect my bins",
        "scan_success":      "bin(s) detected",
        "scan_added":        "added",
        "scan_updated":      "updated",
        "scan_err_json":     "❌ Invalid JSON, please retry.",
        "scan_err_quota":    "Quota reached — switch model",
        "scan_key_missing":  "API key missing",
        "bins_title":        "🗑️ My bins",
        "add_title":         "➕ Add",
        "bin_name_ph":       "🔵 Blue Bin",
        "bin_content":       "Content",
        "add_btn":           "Add",
        "reset_btn":         "↺ Reset",
        "step1":             "**Scan** your bins",
        "step2":             "**Photograph** the waste",
        "step3":             "**Get** the right bin",
        "tab_camera":        "📸 Take a photo",
        "tab_upload":        "🖼️ Upload an image",
        "ready":             "### 🔍 Ready",
        "analyze_btn":       "🤖 Analyze",
        "result_title":      "## 🎯 Result",
        "material":          "Material",
        "confidence":        "AI confidence",
        "gestures":          "### 📋 Important tips",
        "alternatives":      "### 🔄 Alternatives",
        "recyclable":        "♻️ Recyclable",
        "not_recyclable":    "🚫 Not recyclable",
        "dangerous":         "⚠️ Hazardous",
        "not_dangerous":     "✅ Not hazardous",
        "debug_title":       "🔧 Debug — Raw JSON + technical info",
        "key_missing_main":  "API key missing in secrets.",
        "no_bin_active":     "⚠️ No active bin.",
        "guide_title":       "📖 Quick sorting guide",
        "guide_tip":         "💡 Always empty and rinse packaging before recycling!",
        "dash_total":        "🔍 Total analyses",
        "dash_ok":           "✅ Success",
        "dash_err":          "❌ Errors",
        "dash_guest":        "👤 by Guests",
        "dash_log":          "### 📋 Log",
        "dash_stats":        "### 📈 Breakdown",
        "dash_by_provider":  "**By provider**",
        "dash_by_role":      "**By role**",
        "dash_top":          "### 🗑️ Most analysed objects",
        "dash_clear":        "🗑️ Clear log",
        "dash_empty":        "No analyses recorded for this session.",
        "quota_err":         "❌ **Quota reached.**\n\n👉 Switch model or provider in the sidebar.",
        "json_err":          "❌ JSON error",
        "err_prefix":        "❌ Error",
        "ai_lang":           "English",
    },
    "de": {
        "login_subtitle":    "KI-gestützte intelligente Mülltrennung",
        "login_title":       "🔐 Anmelden",
        "username":          "Benutzername",
        "password":          "Passwort",
        "login_btn":         "Anmelden",
        "login_error":       "❌ Falsche Anmeldedaten",
        "guest_btn":         "👤 Ohne Konto fortfahren *(eingeschränkter Zugang)*",
        "guest_hint":        "Gastzugang: nur kostenlose Modelle · keine technischen Details",
        "config":            "⚙️ Einstellungen",
        "logout":            "🚪 Abmelden",
        "dashboard":         "📊 Dashboard",
        "provider":          "🔌 KI-Anbieter",
        "key_loaded_gemini": "🔑 Gemini-Schlüssel geladen",
        "key_miss_gemini":   "⚠️ Gemini-Schlüssel nicht gefunden",
        "key_loaded_or":     "🔑 OpenRouter-Schlüssel geladen",
        "key_miss_or":       "⚠️ OpenRouter-Schlüssel nicht gefunden",
        "lang_label":        "🌐 Sprache",
        "country_label":     "🌍 Land (Trennungsführer)",
        "model_label":       "🤖 KI-Modell",
        "model_hint_gemini": "Wechseln bei 429-Fehler",
        "model_hint_or":     "Alle kostenlos mit Vision",
        "scan_title":        "📷 Meine Tonnen scannen",
        "scan_hint":         "Foto der Tonnen → automatische Konfiguration",
        "scan_btn":          "🤖 Tonnen erkennen",
        "scan_success":      "Tonne(n) erkannt",
        "scan_added":        "hinzugefügt",
        "scan_updated":      "aktualisiert",
        "scan_err_json":     "❌ Ungültiges JSON, bitte erneut versuchen.",
        "scan_err_quota":    "Kontingent erreicht — Modell wechseln",
        "scan_key_missing":  "API-Schlüssel fehlt",
        "bins_title":        "🗑️ Meine Tonnen",
        "add_title":         "➕ Hinzufügen",
        "bin_name_ph":       "🔵 Blaue Tonne",
        "bin_content":       "Inhalt",
        "add_btn":           "Hinzufügen",
        "reset_btn":         "↺ Zurücksetzen",
        "step1":             "**Scannen** Sie Ihre Tonnen",
        "step2":             "**Fotografieren** Sie den Abfall",
        "step3":             "**Erhalten** Sie den richtigen Behälter",
        "tab_camera":        "📸 Foto aufnehmen",
        "tab_upload":        "🖼️ Bild hochladen",
        "ready":             "### 🔍 Bereit",
        "analyze_btn":       "🤖 Analysieren",
        "result_title":      "## 🎯 Ergebnis",
        "material":          "Material",
        "confidence":        "KI-Konfidenz",
        "gestures":          "### 📋 Wichtige Hinweise",
        "alternatives":      "### 🔄 Alternativen",
        "recyclable":        "♻️ Recyclebar",
        "not_recyclable":    "🚫 Nicht recyclebar",
        "dangerous":         "⚠️ Gefährlich",
        "not_dangerous":     "✅ Nicht gefährlich",
        "debug_title":       "🔧 Debug — Roh-JSON + technische Infos",
        "key_missing_main":  "API-Schlüssel in Secrets fehlt.",
        "no_bin_active":     "⚠️ Keine aktive Tonne.",
        "guide_title":       "📖 Schneller Trennführer",
        "guide_tip":         "💡 Verpackungen vor dem Recyceln leeren und ausspülen!",
        "dash_total":        "🔍 Analysen gesamt",
        "dash_ok":           "✅ Erfolgreich",
        "dash_err":          "❌ Fehler",
        "dash_guest":        "👤 von Gästen",
        "dash_log":          "### 📋 Protokoll",
        "dash_stats":        "### 📈 Aufschlüsselung",
        "dash_by_provider":  "**Nach Anbieter**",
        "dash_by_role":      "**Nach Rolle**",
        "dash_top":          "### 🗑️ Am häufigsten analysierte Objekte",
        "dash_clear":        "🗑️ Protokoll löschen",
        "dash_empty":        "Keine Analysen für diese Sitzung aufgezeichnet.",
        "quota_err":         "❌ **Kontingent erreicht.**\n\n👉 Modell oder Anbieter in der Seitenleiste wechseln.",
        "json_err":          "❌ JSON-Fehler",
        "err_prefix":        "❌ Fehler",
        "ai_lang":           "German",
    },
    "es": {
        "login_subtitle":    "Clasificación inteligente de residuos con IA",
        "login_title":       "🔐 Iniciar sesión",
        "username":          "Nombre de usuario",
        "password":          "Contraseña",
        "login_btn":         "Iniciar sesión",
        "login_error":       "❌ Credenciales incorrectas",
        "guest_btn":         "👤 Continuar sin cuenta *(acceso limitado)*",
        "guest_hint":        "Acceso de invitado: solo modelos gratuitos · sin detalles técnicos",
        "config":            "⚙️ Configuración",
        "logout":            "🚪 Cerrar sesión",
        "dashboard":         "📊 Panel",
        "provider":          "🔌 Proveedor IA",
        "key_loaded_gemini": "🔑 Clave Gemini cargada",
        "key_miss_gemini":   "⚠️ Clave Gemini no encontrada",
        "key_loaded_or":     "🔑 Clave OpenRouter cargada",
        "key_miss_or":       "⚠️ Clave OpenRouter no encontrada",
        "lang_label":        "🌐 Idioma",
        "country_label":     "🌍 País (guía de reciclaje)",
        "model_label":       "🤖 Modelo IA",
        "model_hint_gemini": "Cambiar si cuota 429",
        "model_hint_or":     "Todos gratuitos con visión",
        "scan_title":        "📷 Escanear mis contenedores",
        "scan_hint":         "Foto de tus contenedores → configuración automática",
        "scan_btn":          "🤖 Detectar contenedores",
        "scan_success":      "contenedor(es) detectado(s)",
        "scan_added":        "añadido(s)",
        "scan_updated":      "actualizado(s)",
        "scan_err_json":     "❌ JSON inválido, vuelve a intentarlo.",
        "scan_err_quota":    "Cuota alcanzada — cambiar modelo",
        "scan_key_missing":  "Falta la clave API",
        "bins_title":        "🗑️ Mis contenedores",
        "add_title":         "➕ Añadir",
        "bin_name_ph":       "🔵 Contenedor Azul",
        "bin_content":       "Contenido",
        "add_btn":           "Añadir",
        "reset_btn":         "↺ Restablecer",
        "step1":             "**Escanea** tus contenedores",
        "step2":             "**Fotografía** el residuo",
        "step3":             "**Obtén** el contenedor correcto",
        "tab_camera":        "📸 Tomar una foto",
        "tab_upload":        "🖼️ Subir una imagen",
        "ready":             "### 🔍 Listo",
        "analyze_btn":       "🤖 Analizar",
        "result_title":      "## 🎯 Resultado",
        "material":          "Material",
        "confidence":        "Confianza IA",
        "gestures":          "### 📋 Consejos importantes",
        "alternatives":      "### 🔄 Alternativas",
        "recyclable":        "♻️ Reciclable",
        "not_recyclable":    "🚫 No reciclable",
        "dangerous":         "⚠️ Peligroso",
        "not_dangerous":     "✅ No peligroso",
        "debug_title":       "🔧 Debug — JSON bruto + info técnica",
        "key_missing_main":  "Clave API faltante en secrets.",
        "no_bin_active":     "⚠️ Ningún contenedor activo.",
        "guide_title":       "📖 Guía rápida de reciclaje",
        "guide_tip":         "💡 ¡Vaciar y enjuagar los envases antes de reciclar!",
        "dash_total":        "🔍 Análisis totales",
        "dash_ok":           "✅ Éxito",
        "dash_err":          "❌ Errores",
        "dash_guest":        "👤 por Invitados",
        "dash_log":          "### 📋 Registro",
        "dash_stats":        "### 📈 Desglose",
        "dash_by_provider":  "**Por proveedor**",
        "dash_by_role":      "**Por rol**",
        "dash_top":          "### 🗑️ Objetos más analizados",
        "dash_clear":        "🗑️ Borrar registro",
        "dash_empty":        "No se registraron análisis para esta sesión.",
        "quota_err":         "❌ **Cuota alcanzada.**\n\n👉 Cambia modelo o proveedor en la barra lateral.",
        "json_err":          "❌ Error JSON",
        "err_prefix":        "❌ Error",
        "ai_lang":           "Spanish",
    },
    "ko": {
        "login_subtitle":    "AI 기반 지능형 쓰레기 분리수거",
        "login_title":       "🔐 로그인",
        "username":          "사용자 이름",
        "password":          "비밀번호",
        "login_btn":         "로그인",
        "login_error":       "❌ 잘못된 자격증명",
        "guest_btn":         "👤 계정 없이 계속하기 *(제한된 접근)*",
        "guest_hint":        "게스트 접근: 무료 모델만 · 기술 세부사항 없음",
        "config":            "⚙️ 설정",
        "logout":            "🚪 로그아웃",
        "dashboard":         "📊 대시보드",
        "provider":          "🔌 AI 제공자",
        "key_loaded_gemini": "🔑 Gemini 키 로드됨",
        "key_miss_gemini":   "⚠️ Gemini 키를 찾을 수 없음",
        "key_loaded_or":     "🔑 OpenRouter 키 로드됨",
        "key_miss_or":       "⚠️ OpenRouter 키를 찾을 수 없음",
        "lang_label":        "🌐 언어",
        "country_label":     "🌍 국가 (분리수거 가이드)",
        "model_label":       "🤖 AI 모델",
        "model_hint_gemini": "429 오류 시 변경",
        "model_hint_or":     "모두 무료 비전 지원",
        "scan_title":        "📷 분리수거함 스캔",
        "scan_hint":         "분리수거함 사진 → 자동 설정",
        "scan_btn":          "🤖 분리수거함 감지",
        "scan_success":      "개 분리수거함 감지됨",
        "scan_added":        "추가됨",
        "scan_updated":      "업데이트됨",
        "scan_err_json":     "❌ 유효하지 않은 JSON, 다시 시도하세요.",
        "scan_err_quota":    "할당량 초과 — 모델 변경",
        "scan_key_missing":  "API 키 없음",
        "bins_title":        "🗑️ 내 분리수거함",
        "add_title":         "➕ 추가",
        "bin_name_ph":       "🔵 파란 통",
        "bin_content":       "내용물",
        "add_btn":           "추가",
        "reset_btn":         "↺ 초기화",
        "step1":             "분리수거함 **스캔**",
        "step2":             "쓰레기 **촬영**",
        "step3":             "올바른 통 **확인**",
        "tab_camera":        "📸 사진 찍기",
        "tab_upload":        "🖼️ 이미지 업로드",
        "ready":             "### 🔍 준비됨",
        "analyze_btn":       "🤖 분석",
        "result_title":      "## 🎯 결과",
        "material":          "재료",
        "confidence":        "AI 신뢰도",
        "gestures":          "### 📋 중요한 팁",
        "alternatives":      "### 🔄 대안",
        "recyclable":        "♻️ 재활용 가능",
        "not_recyclable":    "🚫 재활용 불가",
        "dangerous":         "⚠️ 위험물",
        "not_dangerous":     "✅ 위험하지 않음",
        "debug_title":       "🔧 디버그 — 원시 JSON + 기술 정보",
        "key_missing_main":  "시크릿에 API 키가 없습니다.",
        "no_bin_active":     "⚠️ 활성화된 분리수거함 없음.",
        "guide_title":       "📖 빠른 분리수거 가이드",
        "guide_tip":         "💡 재활용 전에 포장재를 비우고 헹구세요!",
        "dash_total":        "🔍 총 분석",
        "dash_ok":           "✅ 성공",
        "dash_err":          "❌ 오류",
        "dash_guest":        "👤 게스트",
        "dash_log":          "### 📋 로그",
        "dash_stats":        "### 📈 분포",
        "dash_by_provider":  "**제공자별**",
        "dash_by_role":      "**역할별**",
        "dash_top":          "### 🗑️ 가장 많이 분석된 물건",
        "dash_clear":        "🗑️ 로그 지우기",
        "dash_empty":        "이 세션에 기록된 분석 없음.",
        "quota_err":         "❌ **할당량 초과.**\n\n👉 사이드바에서 모델 또는 제공자를 변경하세요.",
        "json_err":          "❌ JSON 오류",
        "err_prefix":        "❌ 오류",
        "ai_lang":           "Korean",
    },
    "zh": {
        "login_subtitle":    "AI 智能垃圾分类",
        "login_title":       "🔐 登录",
        "username":          "用户名",
        "password":          "密码",
        "login_btn":         "登录",
        "login_error":       "❌ 凭据错误",
        "guest_btn":         "👤 无账号继续 *(受限访问)*",
        "guest_hint":        "访客访问：仅免费模型 · 无技术详情",
        "config":            "⚙️ 设置",
        "logout":            "🚪 退出登录",
        "dashboard":         "📊 仪表板",
        "provider":          "🔌 AI 提供商",
        "key_loaded_gemini": "🔑 Gemini 密钥已加载",
        "key_miss_gemini":   "⚠️ 未找到 Gemini 密钥",
        "key_loaded_or":     "🔑 OpenRouter 密钥已加载",
        "key_miss_or":       "⚠️ 未找到 OpenRouter 密钥",
        "lang_label":        "🌐 语言",
        "country_label":     "🌍 国家（垃圾分类指南）",
        "model_label":       "🤖 AI 模型",
        "model_hint_gemini": "遇到 429 错误时切换",
        "model_hint_or":     "全部免费支持视觉",
        "scan_title":        "📷 扫描我的垃圾桶",
        "scan_hint":         "拍摄垃圾桶照片 → 自动配置",
        "scan_btn":          "🤖 检测垃圾桶",
        "scan_success":      "个垃圾桶已检测",
        "scan_added":        "已添加",
        "scan_updated":      "已更新",
        "scan_err_json":     "❌ JSON 无效，请重试。",
        "scan_err_quota":    "配额已达 — 请切换模型",
        "scan_key_missing":  "缺少 API 密钥",
        "bins_title":        "🗑️ 我的垃圾桶",
        "add_title":         "➕ 添加",
        "bin_name_ph":       "🔵 蓝色垃圾桶",
        "bin_content":       "内容",
        "add_btn":           "添加",
        "reset_btn":         "↺ 重置",
        "step1":             "**扫描**垃圾桶",
        "step2":             "**拍摄**废弃物",
        "step3":             "**获取**正确分类",
        "tab_camera":        "📸 拍照",
        "tab_upload":        "🖼️ 上传图片",
        "ready":             "### 🔍 准备就绪",
        "analyze_btn":       "🤖 分析",
        "result_title":      "## 🎯 结果",
        "material":          "材料",
        "confidence":        "AI 置信度",
        "gestures":          "### 📋 重要提示",
        "alternatives":      "### 🔄 备选方案",
        "recyclable":        "♻️ 可回收",
        "not_recyclable":    "🚫 不可回收",
        "dangerous":         "⚠️ 危险品",
        "not_dangerous":     "✅ 无危险",
        "debug_title":       "🔧 调试 — 原始 JSON + 技术信息",
        "key_missing_main":  "Secrets 中缺少 API 密钥。",
        "no_bin_active":     "⚠️ 没有激活的垃圾桶。",
        "guide_title":       "📖 快速分类指南",
        "guide_tip":         "💡 回收前请清空并冲洗包装！",
        "dash_total":        "🔍 总分析次数",
        "dash_ok":           "✅ 成功",
        "dash_err":          "❌ 错误",
        "dash_guest":        "👤 访客",
        "dash_log":          "### 📋 日志",
        "dash_stats":        "### 📈 分布",
        "dash_by_provider":  "**按提供商**",
        "dash_by_role":      "**按角色**",
        "dash_top":          "### 🗑️ 最常分析的物品",
        "dash_clear":        "🗑️ 清除日志",
        "dash_empty":        "本次会话没有记录任何分析。",
        "quota_err":         "❌ **配额已达。**\n\n👉 在侧边栏切换模型或提供商。",
        "json_err":          "❌ JSON 错误",
        "err_prefix":        "❌ 错误",
        "ai_lang":           "Chinese",
    },
    "ja": {
        "login_subtitle":    "AI搭載のインテリジェントなごみ分別",
        "login_title":       "🔐 ログイン",
        "username":          "ユーザー名",
        "password":          "パスワード",
        "login_btn":         "ログイン",
        "login_error":       "❌ 認証情報が正しくありません",
        "guest_btn":         "👤 アカウントなしで続ける *(制限付きアクセス)*",
        "guest_hint":        "ゲストアクセス：無料モデルのみ · 技術詳細なし",
        "config":            "⚙️ 設定",
        "logout":            "🚪 ログアウト",
        "dashboard":         "📊 ダッシュボード",
        "provider":          "🔌 AIプロバイダー",
        "key_loaded_gemini": "🔑 Geminiキー読み込み済み",
        "key_miss_gemini":   "⚠️ Geminiキーが見つかりません",
        "key_loaded_or":     "🔑 OpenRouterキー読み込み済み",
        "key_miss_or":       "⚠️ OpenRouterキーが見つかりません",
        "lang_label":        "🌐 言語",
        "country_label":     "🌍 国（分別ガイド）",
        "model_label":       "🤖 AIモデル",
        "model_hint_gemini": "429エラー時に切り替え",
        "model_hint_or":     "すべて無料でビジョン対応",
        "scan_title":        "📷 ごみ箱をスキャン",
        "scan_hint":         "ごみ箱の写真 → 自動設定",
        "scan_btn":          "🤖 ごみ箱を検出",
        "scan_success":      "個のごみ箱を検出",
        "scan_added":        "追加",
        "scan_updated":      "更新",
        "scan_err_json":     "❌ 無効なJSON、再試行してください。",
        "scan_err_quota":    "クォータ超過 — モデルを切り替え",
        "scan_key_missing":  "APIキーがありません",
        "bins_title":        "🗑️ 私のごみ箱",
        "add_title":         "➕ 追加",
        "bin_name_ph":       "🔵 青いごみ箱",
        "bin_content":       "内容",
        "add_btn":           "追加",
        "reset_btn":         "↺ リセット",
        "step1":             "ごみ箱を**スキャン**",
        "step2":             "ごみを**撮影**",
        "step3":             "正しい分別を**確認**",
        "tab_camera":        "📸 写真を撮る",
        "tab_upload":        "🖼️ 画像をアップロード",
        "ready":             "### 🔍 準備完了",
        "analyze_btn":       "🤖 分析",
        "result_title":      "## 🎯 結果",
        "material":          "素材",
        "confidence":        "AI信頼度",
        "gestures":          "### 📋 重要なヒント",
        "alternatives":      "### 🔄 代替案",
        "recyclable":        "♻️ リサイクル可能",
        "not_recyclable":    "🚫 リサイクル不可",
        "dangerous":         "⚠️ 危険物",
        "not_dangerous":     "✅ 危険なし",
        "debug_title":       "🔧 デバッグ — 生JSON + 技術情報",
        "key_missing_main":  "SecretsにAPIキーがありません。",
        "no_bin_active":     "⚠️ アクティブなごみ箱がありません。",
        "guide_title":       "📖 クイック分別ガイド",
        "guide_tip":         "💡 リサイクル前に容器を空にしてすすいでください！",
        "dash_total":        "🔍 総分析数",
        "dash_ok":           "✅ 成功",
        "dash_err":          "❌ エラー",
        "dash_guest":        "👤 ゲスト",
        "dash_log":          "### 📋 ログ",
        "dash_stats":        "### 📈 内訳",
        "dash_by_provider":  "**プロバイダー別**",
        "dash_by_role":      "**ロール別**",
        "dash_top":          "### 🗑️ 最も分析されたオブジェクト",
        "dash_clear":        "🗑️ ログをクリア",
        "dash_empty":        "このセッションに記録された分析はありません。",
        "quota_err":         "❌ **クォータ超過。**\n\n👉 サイドバーでモデルまたはプロバイダーを切り替えてください。",
        "json_err":          "❌ JSONエラー",
        "err_prefix":        "❌ エラー",
        "ai_lang":           "Japanese",
    },
}

# ══════════════════════════════════════════════
# GUIDES DE TRI PAR PAYS
# ══════════════════════════════════════════════
COUNTRY_GUIDES = {
    "🇫🇷 France": {
        "rows": [
            ("Bouteilles plastique, canettes", "🟡 Jaune"),
            ("Cartons, journaux, magazines",   "🟡 Jaune"),
            ("Bouteilles en verre, bocaux",    "🟢 Verte (colonne verre)"),
            ("Épluchures, restes alimentaires","🟤 Marron / Compost"),
            ("Sacs sales, mouchoirs, couches", "⚫ Noire"),
            ("Piles, médicaments, huiles",     "🔴 Déchetterie"),
            ("Appareils électroniques",        "🔴 DEEE / Déchetterie"),
        ],
    },
    "🇧🇪 Belgique": {
        "rows": [
            ("PMC : plastiques, métaux, cartons à boissons", "🔵 Sac bleu"),
            ("Papier, carton",                               "🟡 Sac jaune / Conteneur"),
            ("Verre",                                        "🟢 Bulles à verre"),
            ("Déchets organiques",                           "🟤 Compost / GFT"),
            ("Ordures ménagères",                            "⚫ Sac blanc / Noire"),
            ("Déchets dangereux",                            "🔴 Recypark"),
        ],
    },
    "🇨🇭 Suisse": {
        "rows": [
            ("PET, aluminium",          "🔵 Points de collecte PET/alu"),
            ("Verre",                   "🟢 Conteneur verre"),
            ("Papier, carton",          "🟡 Collecte papier"),
            ("Déchets verts, bio",      "🟤 Compost communal"),
            ("Ordures ménagères",       "⚫ Sac taxé officiel"),
            ("Textiles, vêtements",     "👕 Points collecte"),
            ("Déchets spéciaux",        "🔴 Déchetterie"),
        ],
    },
    "🇩🇪 Deutschland": {
        "rows": [
            ("Plastik, Metall, Verbundverpackungen", "🟡 Gelbe Tonne / Gelber Sack"),
            ("Papier, Pappe, Karton",                "🔵 Blaue Tonne"),
            ("Glas",                                 "🟢 Glascontainer"),
            ("Bioabfälle",                           "🟤 Braune Tonne"),
            ("Restmüll",                             "⚫ Schwarze/Graue Tonne"),
            ("Sondermüll",                           "🔴 Wertstoffhof"),
            ("Elektroschrott",                       "🔴 Wertstoffhof / Händler"),
        ],
    },
    "🇬🇧 United Kingdom": {
        "rows": [
            ("Plastics, cans, paper, cardboard", "🔵 Blue bin / Recycling"),
            ("Glass bottles, jars",              "🟢 Green bin or bottle bank"),
            ("Food waste",                       "🟤 Brown / Food caddy"),
            ("General waste",                    "⚫ Black / Grey bin"),
            ("Garden waste",                     "🟢 Green bin (varies by council)"),
            ("Hazardous waste",                  "🔴 Household Waste Recycling Centre"),
            ("Electronics",                      "🔴 WEEE — retailer or HWRC"),
        ],
    },
    "🇺🇸 United States": {
        "rows": [
            ("Paper, cardboard, plastics, cans", "🔵 Blue bin (single-stream recycling)"),
            ("Glass",                             "🟢 Glass bin (varies by city)"),
            ("Food waste",                        "🟤 Compost (where available)"),
            ("Yard waste",                        "🟢 Green bin"),
            ("General trash",                     "⚫ Black bin"),
            ("Hazardous waste",                   "🔴 HHW facility"),
            ("Electronics",                       "🔴 E-waste drop-off / retailer"),
        ],
    },
    "🇯🇵 日本": {
        "rows": [
            ("可燃ごみ（生ごみ、紙など）",  "🔴 赤/指定袋"),
            ("不燃ごみ（ガラス、金属）",    "⚫ 黒/指定袋"),
            ("プラスチック容器・包装",      "🟡 黄色袋"),
            ("ペットボトル",               "🔵 青色袋"),
            ("缶・ビン",                   "🟢 緑袋 / 回収拠点"),
            ("段ボール・古紙",             "📦 集団回収"),
            ("粗大ごみ",                   "📞 事前申込制"),
        ],
    },
    "🇰🇷 대한민국": {
        "rows": [
            ("음식물 쓰레기",                "🟤 음식물 전용봉투/용기"),
            ("종이, 골판지",                 "📦 종이류 분리배출"),
            ("플라스틱, 캔, 유리",           "🔵 재활용 분리배출함"),
            ("일반 쓰레기",                  "⚫ 종량제 봉투"),
            ("대형 폐기물",                  "📞 구청 신고 후 배출"),
            ("형광등, 전지",                 "🔴 전용 수거함"),
            ("전자제품",                     "🔴 무상방문수거 / 판매점"),
        ],
    },
    "🇨🇳 中国": {
        "rows": [
            ("厨余垃圾（食物残渣）", "🟤 厨余垃圾桶"),
            ("可回收物（纸、塑料、金属）", "🔵 可回收物桶"),
            ("有害垃圾（电池、药品）", "🔴 有害垃圾桶"),
            ("其他垃圾",             "⚫ 其他垃圾桶"),
        ],
    },
    "🇪🇸 España": {
        "rows": [
            ("Envases plásticos, latas, bricks", "🟡 Amarillo"),
            ("Papel y cartón",                   "🔵 Azul"),
            ("Vidrio",                           "🟢 Verde (iglú)"),
            ("Residuos orgánicos",               "🟤 Marrón"),
            ("Resto",                            "⚫ Gris/Negro"),
            ("Residuos peligrosos",              "🔴 Punto Limpio"),
            ("Electrónica",                      "🔴 Punto Limpio / tienda"),
        ],
    },
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
def get_lang_code():
    label = st.session_state.get("ui_lang", "🇫🇷 Français")
    return LANGUAGES.get(label, "fr")

def t(key):
    return UI[get_lang_code()].get(key, UI["en"].get(key, key))

def get_ai_lang():
    return UI[get_lang_code()]["ai_lang"]

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
    cur_lang  = st.session_state.get("ui_lang", "🇫🇷 Français")
    cur_idx   = lang_keys.index(cur_lang) if cur_lang in lang_keys else 0
    col_l, col_r = st.columns([3,1])
    with col_r:
        chosen_lang = st.selectbox("", lang_keys, index=cur_idx, label_visibility="collapsed", key="lang_login")
        if chosen_lang != cur_lang:
            st.session_state["ui_lang"] = chosen_lang
            st.rerun()

    st.markdown(f"""
    <div style="max-width:400px;margin:2rem auto 0;text-align:center">
        <div style="font-size:3rem">♻️</div>
        <div style="font-size:1.8rem;font-weight:700;background:linear-gradient(135deg,#00d084,#00a8ff);
            -webkit-background-clip:text;-webkit-text-fill-color:transparent">TriSmart</div>
        <div style="color:#666;margin:.5rem 0 1.5rem">{t('login_subtitle')}</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        with st.form("login_form"):
            st.markdown(f"#### {t('login_title')}")
            username = st.text_input(t("username"), placeholder="username")
            password = st.text_input(t("password"), type="password", placeholder="••••••••")
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
    img = Image.open(uploaded)
    buf = io.BytesIO()
    fmt = img.format or "JPEG"
    if fmt.upper() not in ["JPEG","PNG","WEBP"]: fmt = "JPEG"
    (img.convert("RGB") if fmt=="JPEG" else img).save(buf, format=fmt)
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
    cur_lang  = st.session_state.get("ui_lang","🇫🇷 Français")
    cur_idx   = lang_keys.index(cur_lang) if cur_lang in lang_keys else 0
    chosen_lang = st.selectbox(t("lang_label"), lang_keys, index=cur_idx)
    if chosen_lang != cur_lang:
        st.session_state["ui_lang"] = chosen_lang
        st.rerun()

    # ── Pays ──
    country_keys = list(COUNTRY_GUIDES.keys())
    cur_country  = st.session_state.get("country", "🇫🇷 France")
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
        sc = st.camera_input("", label_visibility="collapsed", key="cam_scan")
        if sc: scan_image = sc
    with scan_tab2:
        su = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                               label_visibility="collapsed", key="up_scan")
        if su: scan_image = su

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
    TriSmart v7.0 · {get_provider()} · Free</div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════
if is_admin() and st.session_state.get("show_dashboard", False):
    st.markdown(f"## {t('dashboard')}")
    logs  = st.session_state.usage_log
    total = len(logs)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric(t("dash_total"), total)
    c2.metric(t("dash_ok"),    sum(1 for l in logs if l["success"]))
    c3.metric(t("dash_err"),   sum(1 for l in logs if not l["success"]))
    c4.metric(t("dash_guest"), sum(1 for l in logs if l["role"]=="guest"))

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

c1,c2,c3 = st.columns(3)
with c1: st.markdown(f'<span class="step-badge">1</span> {t("step1")}', unsafe_allow_html=True)
with c2: st.markdown(f'<span class="step-badge">2</span> {t("step2")}', unsafe_allow_html=True)
with c3: st.markdown(f'<span class="step-badge">3</span> {t("step3")}', unsafe_allow_html=True)
st.markdown("---")

bins_config = {k:v for k,v in st.session_state.bins.items() if v.get("active")}
active_key  = gemini_key if get_provider()=="Gemini" else openrouter_key

if not active_key:
    st.info(f"👈 {t('key_missing_main')}")

if bins_config:
    cols = st.columns(min(len(bins_config),4))
    for i,(bname,bdata) in enumerate(bins_config.items()):
        with cols[i%4]:
            st.markdown(f"""<div style="background:{bdata['couleur']}22;border:1px solid {bdata['couleur']};
                border-radius:8px;padding:6px;text-align:center;font-size:.75rem;color:#ddd;margin-bottom:4px">
                {bname}</div>""", unsafe_allow_html=True)
    st.markdown("")

# ══════════════════════════════════════════════
# CAPTURE
# ══════════════════════════════════════════════
tab1, tab2 = st.tabs([t("tab_camera"), t("tab_upload")])
captured_image = None
source_label   = ""

with tab1:
    cam = st.camera_input("", label_visibility="collapsed", key="cam_dechet")
    if cam: captured_image = cam; source_label = t("tab_camera")

with tab2:
    upl = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                            label_visibility="collapsed", key="up_dechet")
    if upl: captured_image = upl; source_label = upl.name

# ══════════════════════════════════════════════
# ANALYSE
# ══════════════════════════════════════════════
if captured_image and active_key and bins_config:
    img, img_bytes, mime_type, b64_img = prepare_image(captured_image)
    ci,co = st.columns([1,1])
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
                    border:2px solid {bin_color};border-radius:20px;padding:1.5rem 2rem;margin:1rem 0">
                    <div style="font-size:3rem;text-align:center">{result.get('emoji','♻️')}</div>
                    <div style="text-align:center;font-size:1.5rem;font-weight:700;color:white;margin:.5rem 0">
                        {result.get('objet_detecte','?')}</div>
                    <div style="text-align:center;color:#aaa;font-size:.9rem">
                        {t('material')} : <strong style="color:#ddd">{result.get('materiau','?')}</strong></div>
                    <div style="margin:1rem 0;text-align:center">
                        <span style="background:{bin_color}22;border:2px solid {bin_color};color:white;
                            padding:.5rem 1.5rem;border-radius:999px;font-size:1.2rem;font-weight:700">
                            ➜ {bin_name}</span></div>
                    <div style="margin:.5rem 0">
                        <div style="display:flex;justify-content:space-between;color:#aaa;font-size:.8rem;margin-bottom:4px">
                            <span>{t('confidence')}</span><span>{conf}%</span></div>
                        <div style="background:#333;border-radius:4px;height:8px">
                            <div style="background:linear-gradient(90deg,{bin_color},#00a8ff);
                                width:{conf}%;height:8px;border-radius:4px"></div></div></div>
                    <div style="color:#ccc;font-size:.95rem;margin-top:1rem;line-height:1.5">
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
country = st.session_state.get("country","🇫🇷 France")
guide   = COUNTRY_GUIDES.get(country, COUNTRY_GUIDES["🇫🇷 France"])

with st.expander(f"{t('guide_title')} — {country}"):
    header_waste = {"fr":"Déchet","en":"Waste","de":"Abfall","es":"Residuo",
                    "ko":"쓰레기","zh":"废弃物","ja":"ごみ"}
    header_bin   = {"fr":"Poubelle","en":"Bin","de":"Tonne","es":"Contenedor",
                    "ko":"분리수거함","zh":"垃圾桶","ja":"ごみ箱"}
    lc = get_lang_code()
    hw = header_waste.get(lc,"Waste")
    hb = header_bin.get(lc,"Bin")

    table = f"| {hw} | {hb} |\n|---|---|\n"
    for waste, bin_name in guide["rows"]:
        table += f"| {waste} | {bin_name} |\n"
    st.markdown(table)
    st.markdown(f"> {t('guide_tip')}")

st.markdown("""
<div style='text-align:center;color:#444;font-size:.8rem;margin-top:2rem'>
TriSmart v7.0 · Gemini + OpenRouter · Streamlit · Free
</div>""", unsafe_allow_html=True)
