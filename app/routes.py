import os
import logging

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session
from .database import delete_user, get_all_users, get_db, get_original_plan, get_user, save_plan, save_user, update_plan
from .gemini_client import GeminiGenerationError, get_model_status
from .gemini_generator import generate_workout_gemini
from .gemini_flash_generator import generate_nutrition_tip_with_flash
from .updated_plan import update_workout_plan
from .schemas import UserInput, FeedbackRequest

router = APIRouter()
logger = logging.getLogger(__name__)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "app", "templates"))

@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.post("/generate-workout")
async def generate_workout(request: Request, username: str = Form(...), user_id: str = Form(...), age: int = Form(...), weight: float = Form(...), goal: str = Form(...), intensity: str = Form(...), db: Session = Depends(get_db)):
    try:
        data = UserInput(username=username, user_id=user_id, age=age, weight=weight, goal=goal, intensity=intensity)
        plan = generate_workout_gemini(data.username, data.age, data.weight, data.goal, data.intensity)
        tip = generate_nutrition_tip_with_flash(data.goal)
        save_user(db, data.user_id, data.username, data.age, str(data.weight), data.goal, data.intensity)
        save_plan(db, data.user_id, plan, tip)
        return templates.TemplateResponse(request=request, name="result.html", context={"username": data.username, "user_id": data.user_id, "age": data.age, "weight": data.weight, "goal": data.goal, "intensity": data.intensity, "workout_plan": plan, "updated_plan": None, "nutrition_tip": tip, "message": None})
    except ValidationError as exc:
        return templates.TemplateResponse(request=request, name="error.html", context={"error": f"Please check your input: {exc}"}, status_code=422)
    except GeminiGenerationError as exc:
        logger.exception("Workout generation failed for all Gemini candidates")
        status_code = 503 if exc.quota_exhausted else 502
        return templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)}, status_code=status_code)
    except Exception as exc:
        logger.exception("Workout generation failed")
        return templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)}, status_code=500)

@router.post("/submit-feedback")
async def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...), db: Session = Depends(get_db)):
    try:
        req = FeedbackRequest(user_id=user_id, feedback=feedback)
        user = get_user(db, req.user_id)
        if not user:
            return templates.TemplateResponse(request=request, name="error.html", context={"error": "User ID not found."}, status_code=404)
        original = get_original_plan(db, req.user_id)
        if not original:
            return templates.TemplateResponse(request=request, name="error.html", context={"error": "No original workout plan found."}, status_code=404)
        revised = update_workout_plan(original, req.feedback, user.username, user.age, float(user.weight), user.goal, user.intensity)
        update_plan(db, req.user_id, revised)
        return templates.TemplateResponse(request=request, name="result.html", context={"username": user.username, "user_id": user.user_id, "age": user.age, "weight": user.weight, "goal": user.goal, "intensity": user.intensity, "workout_plan": original, "updated_plan": revised, "nutrition_tip": user.nutrition_tip, "message": "Your workout plan has been updated successfully."})
    except ValidationError as exc:
        return templates.TemplateResponse(request=request, name="error.html", context={"error": f"Please check your feedback: {exc}"}, status_code=422)
    except GeminiGenerationError as exc:
        logger.exception("Feedback update failed for all Gemini candidates")
        status_code = 503 if exc.quota_exhausted else 502
        return templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)}, status_code=status_code)
    except Exception as exc:
        logger.exception("Feedback update failed")
        return templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)}, status_code=500)

@router.get("/view-all-users")
async def view_all_users(request: Request, db: Session = Depends(get_db)):
    return templates.TemplateResponse(request=request, name="all_users.html", context={"users": get_all_users(db)})

@router.post("/delete-user/{user_id}")
async def remove_user(user_id: str, db: Session = Depends(get_db)):
    delete_user(db, user_id)
    return RedirectResponse("/view-all-users", status_code=303)

@router.get("/model-status")
async def model_status():
    return get_model_status()

@router.get("/health")
async def health():
    return {"status": "healthy", "application": "FitBuddy"}
