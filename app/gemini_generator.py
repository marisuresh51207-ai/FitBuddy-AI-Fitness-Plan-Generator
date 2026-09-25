from .gemini_client import generate_text

WORKOUT_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-2.5-pro",
]

def generate_workout_gemini(username: str, age: int, weight: float, goal: str, intensity: str) -> str:
    prompt = f"""You are FitBuddy, an AI fitness plan generator.

Create a personalized 7-day workout plan.

Name: {username}
Age: {age}
Weight: {weight} kg
Fitness goal: {goal}
Workout intensity: {intensity}

Requirements:
- Exactly 7 days, Day 1 to Day 7.
- Goal- and intensity-appropriate training.
- Every day has a clear focus.
- Warm-up 5-10 minutes.
- Main workout with exercises, sets, reps/duration, and rest.
- Cooldown/recovery guidance.
- Include sensible recovery/rest days.
- No tables, no medical diagnosis, no dangerous/extreme recommendations.

Format each day with: Focus, Warm-up, Main Workout, Cooldown/Recovery.
End with a short SAFETY NOTE."""
    return generate_text(prompt, WORKOUT_MODELS)
