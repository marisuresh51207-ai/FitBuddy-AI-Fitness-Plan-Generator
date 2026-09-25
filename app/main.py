import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import create_tables
from .routes import router

app = FastAPI(title="FitBuddy - AI Fitness Plan Generator", description="Personalized workout and nutrition planning with Gemini AI.", version="1.0.0")
create_tables()
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "app", "static")), name="static")
app.include_router(router)
