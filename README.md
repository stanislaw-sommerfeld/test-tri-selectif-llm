# ♻️ TriSmart – AI-Powered Waste Sorting

A Streamlit app that uses AI vision (Gemini or OpenRouter) to identify waste from a photo and tell you which bin to use — based on *your* available bins.

**100% free · Login protected · Admin dashboard · Mobile-ready**

---

## ✨ Features

- **📸 Camera capture** directly from the browser (desktop & mobile)
- **🖼️ Image upload** from your gallery
- **🤖 AI vision analysis** — identifies the object, material, and correct bin
- **🗑️ Configurable bins** — add, remove, edit, or auto-detect from a photo
- **📷 Bin scanner** — photograph your bins to configure them automatically
- **🔐 Role-based access** — Admin and Guest modes
- **📊 Admin dashboard** — usage stats for the current session
- **🔌 Dual AI provider** — switch between Gemini (Google) and OpenRouter
- **🌐 Multilingual** — French, English, Spanish, German

---

## 🔐 Access Roles

| Feature | Admin | Guest |
|---------|-------|-------|
| Waste analysis | ✅ | ✅ |
| Model selection | ✅ All models | ✅ Free only |
| Raw JSON + debug info | ✅ | ❌ |
| Error stack traces | ✅ | ❌ |
| Dashboard | ✅ | ❌ |

- **Admin** → log in with your credentials stored in Streamlit Secrets
- **Guest** → click *"Continue without account"* on the login screen (no registration needed)

---

## 🚀 Deployment on Streamlit Cloud (recommended)

### 1. Get your free API keys

**Gemini (Google):**
- Go to [aistudio.google.com](https://aistudio.google.com) → **Get API Key**
- Free tier: ~1 000 requests/day with `gemini-2.5-flash-lite`

**OpenRouter:**
- Go to [openrouter.ai](https://openrouter.ai) → create a free account → **Keys**
- Free tier: multiple free vision models available (Qwen, Llama, Gemma, Mistral...)

### 2. Push files to GitHub

Create a GitHub repository (public or private) and upload only:
- `app.py`
- `requirements.txt`

> ⚠️ Never upload `secrets.toml` to GitHub.

### 3. Deploy on Streamlit Cloud

- Go to [share.streamlit.io](https://share.streamlit.io)
- Connect your GitHub account
- Click **New app** → select your repo → `app.py`
- Click **Advanced settings** → choose **Python 3.11**
- In the **Secrets** field, paste the following (replace with your real values):

```toml
[Identifiers]
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"

[API_Key]
GEMINI_API_KEY = "AIza..."
OPEN_ROUTER_API_KEY = "sk-or-..."
```

- Click **Save** then **Deploy**

Your app will be live at `https://your-app.streamlit.app` in ~2 minutes.

---

## 💻 Running locally (optional)

```bash
pip install -r requirements.txt
streamlit run app.py
```

For local secrets, create `.streamlit/secrets.toml`:

```toml
[Identifiers]
APP_USERNAME = "your_username"
APP_PASSWORD = "your_password"

[API_Key]
GEMINI_API_KEY = "AIza..."
OPEN_ROUTER_API_KEY = "sk-or-..."
```

> ⚠️ Add `.streamlit/secrets.toml` to your `.gitignore` — never push it to GitHub.

---

## 🤖 AI Providers & Models

### Gemini (Google) — via `google-genai`

| Model | Free quota | Notes |
|-------|-----------|-------|
| `gemini-2.5-flash-lite` | ~1 000 req/day | **Recommended default** |
| `gemini-2.5-flash` | ~250 req/day | Higher quality |
| `gemini-3-flash-preview` | ~200 req/day | Preview |
| `gemini-3.1-flash-lite-preview` | ~200 req/day | Preview |

### OpenRouter — via OpenAI-compatible API

| Model | Notes |
|-------|-------|
| `openrouter/free` | **Auto-router** — picks the best available free model |
| `qwen/qwen2.5-vl-72b-instruct:free` | Excellent vision quality |
| `meta-llama/llama-3.2-11b-vision-instruct:free` | Fast and reliable |
| `google/gemma-3-27b-it:free` | Good generalist |
| `mistralai/mistral-small-3.1-24b-instruct:free` | Great multilingual |

> 💡 If you hit a 429 quota error on one model, switch to another in the sidebar — or switch provider entirely.

---

## 📊 Dashboard (Admin only)

Click the **📊 Dashboard** button at the top of the sidebar to see:
- Total analyses, successes, errors, and guest usage for the current session
- Full analysis log (time, role, provider, model, detected object)
- Breakdown by provider and role
- Top 10 most analysed objects
- Button to clear the log

> ⚠️ The log is **in-memory only** — it resets when the app restarts. No external database needed, keeping everything free.

---

## 💰 Cost

| Service | Price |
|---------|-------|
| Streamlit Cloud | Free |
| GitHub | Free |
| Gemini API (free tier) | Free (~1 000 analyses/day) |
| OpenRouter (free models) | Free |
| **Total** | **$0** |

---

## 📦 Tech Stack

- **Frontend:** Streamlit
- **AI — Gemini:** `google-genai` (official Google SDK)
- **AI — OpenRouter:** `openai` (OpenAI-compatible client)
- **Image processing:** Pillow
- **Python:** 3.11
