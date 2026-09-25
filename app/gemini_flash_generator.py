from .gemini_client import generate_text

NUTRITION_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
]

def generate_nutrition_tip_with_flash(goal: str) -> str:
    prompt = f"""You are FitBuddy's nutrition and recovery assistant.
Fitness goal: {goal}
Generate one concise 3-6 sentence practical tip related to the goal. Focus on healthy food, hydration, protein, sleep, or recovery. Avoid extreme dieting and medical treatment. Return only the tip."""
    return generate_text(prompt, NUTRITION_MODELS)
