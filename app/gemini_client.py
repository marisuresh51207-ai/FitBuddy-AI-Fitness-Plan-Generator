import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))
API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
client = None
MAX_TEMPORARY_RETRIES = 1
TEXT_GENERATION_MODELS = {
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
}


class GeminiGenerationError(RuntimeError):
    def __init__(self, attempted_models: list[str], quota_exhausted: bool = False):
        self.attempted_models = attempted_models
        self.quota_exhausted = quota_exhausted
        models = ", ".join(attempted_models) or "none"
        if quota_exhausted:
            message = (
                "Gemini generation quota is unavailable for every attempted model "
                f"({models}). Check the project's AI Studio rate limits or billing."
            )
        else:
            message = f"Gemini generation failed for the attempted models: {models}."
        super().__init__(message)


def get_client():
    global client
    if client is None:
        if not API_KEY:
            raise RuntimeError("Gemini API key not found. Create .env and set GEMINI_API_KEY.")
        client = genai.Client(api_key=API_KEY)
    return client


def normalize_model_name(name: str) -> str:
    return name.replace("models/", "").strip()


def _list_available_generate_models() -> tuple[list[str], str | None]:
    available = []
    try:
        for model in get_client().models.list():
            name = normalize_model_name(getattr(model, "name", ""))
            actions = getattr(model, "supported_actions", []) or []
            if name in TEXT_GENERATION_MODELS and (not actions or "generateContent" in actions):
                available.append(name)
        return available, None
    except Exception as exc:
        return available, type(exc).__name__


def get_available_generate_models() -> list[str]:
    available, _ = _list_available_generate_models()
    return available


def choose_model(candidates: list[str]) -> str | None:
    available = set(get_available_generate_models())
    for candidate in candidates:
        if candidate in available:
            return candidate
    return candidates[0] if candidates else None


def _is_quota_error(exc: Exception) -> bool:
    details = " ".join(
        str(getattr(exc, field, ""))
        for field in ("status", "message", "details")
    ).lower()
    return (
        "limit: 0" in details
        or "limit 0" in details
        or ("quota" in details and "zero" in details)
        or ("free_tier" in details and "0" in details)
    )


def _is_rate_limit_error(exc: Exception) -> bool:
    return getattr(exc, "code", None) == 429 or getattr(exc, "status", "") == "RESOURCE_EXHAUSTED"


def _candidate_order(candidates: list[str]) -> list[str]:
    available = set(get_available_generate_models())
    if not available:
        return list(dict.fromkeys(candidates))
    return [candidate for candidate in dict.fromkeys(candidates) if candidate in available]


def generate_text(prompt: str, candidates: list[str]) -> str:
    ordered_candidates = _candidate_order(candidates)
    attempted_models = []
    quota_failures = 0

    for model in ordered_candidates:
        attempted_models.append(model)
        temporary_retries = 0
        while True:
            try:
                response = get_client().models.generate_content(model=model, contents=prompt)
                text = getattr(response, "text", None)
                if not text:
                    break
                return text.strip()
            except APIError as exc:
                if _is_quota_error(exc):
                    quota_failures += 1
                    break
                if _is_rate_limit_error(exc) and temporary_retries < MAX_TEMPORARY_RETRIES:
                    time.sleep(2**temporary_retries)
                    temporary_retries += 1
                    continue
                break
            except Exception:
                break

    raise GeminiGenerationError(
        attempted_models,
        quota_exhausted=bool(attempted_models) and quota_failures == len(attempted_models),
    )


def get_model_status() -> dict:
    workout = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-3.1-pro-preview",
        "gemini-2.5-pro",
    ]
    nutrition = [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
    ]
    available, discovery_error = _list_available_generate_models()
    available_set = set(available)
    return {
        "api_key_detected": bool(API_KEY),
        "available_models": available,
        "selected_workout_model": next((model for model in workout if model in available_set), None),
        "selected_nutrition_model": next((model for model in nutrition if model in available_set), None),
        "model_discovery_error": discovery_error,
    }
