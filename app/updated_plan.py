from .gemini_client import generate_text

UPDATE_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
]

def update_workout_plan(original_plan: str, feedback: str, username: str, age: int, weight: float, goal: str, intensity: str) -> str:
    prompt = f"""You are FitBuddy.

Original plan:
{original_plan}

User: {username}, Age: {age}, Weight: {weight} kg, Goal: {goal}, Intensity: {intensity}

Feedback:
{feedback}

Create an updated 7-day plan. Preserve useful parts, apply the feedback, and include Focus, Warm-up, Main Workout with sets/reps or duration and rest, and Cooldown/Recovery for every day. Include appropriate recovery. No tables, medical diagnosis, or dangerous/extreme recommendations. End with UPDATE SUMMARY describing the changes."""
    return generate_text(prompt, UPDATE_MODELS)
