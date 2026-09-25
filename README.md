# FitBuddy - AI Fitness Plan Generator using Gemini Models

This project is built from the supplied FitBuddy project plan. It includes FastAPI, Jinja2, SQLite/SQLAlchemy, Gemini workout generation, nutrition/recovery tips, feedback-based updates, and a user/admin view.

## Run in VS Code (Windows)

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set:

```env
GEMINI_API_KEY=your_real_api_key
```

Start:

```powershell
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000

Other pages:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/view-all-users
- http://127.0.0.1:8000/model-status
- http://127.0.0.1:8000/health

Gemini model selection checks the models exposed by the configured API key and prefers Flash models for normal generation. If every candidate returns a quota error, FitBuddy shows the attempted models and a rate-limit/billing message instead of fabricating a plan. Check `/model-status` for key detection and current model visibility. Rate limits are project-specific; a model appearing in the API list does not guarantee usable quota.
