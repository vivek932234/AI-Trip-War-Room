
import json
import time

import random
from google import genai
from google.genai import errors
from app.services.security import settings

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def generate_ai_response(prompt: str):
    primary_model = settings.GEMINI_MODEL

    fallback_models = [
        model.strip()
        for model in settings.GEMINI_FALLBACK_MODELS.split(",")
        if model.strip()
    ]

    models_to_try = list(dict.fromkeys(
        [primary_model] + fallback_models
    ))

    for model in models_to_try:
        print(f"Trying Gemini model: {model}")

        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if not response.text:
                    raise ValueError("Gemini returned an empty response.")

                print(f"SUCCESS: Generated response using {model}")
                return response.text

            except errors.ServerError as e:
                print(f"Gemini Server Error ({model}): {e}")

                if e.code == 503 and attempt == 0:
                    wait_time = 5 + random.uniform(0, 2)
                    print(f"Retrying {model} in {wait_time:.1f} seconds...")
                    time.sleep(wait_time)
                    continue

                if e.code == 503:
                    print(f"Switching from {model} to next model.")
                    break

                raise

            except Exception as e:
                print(f"Gemini API Error ({model}): {e}")
                raise

    raise Exception(
        "All Gemini models are temporarily unavailable. Please try again later."
    )


def generate_structured_itinerary(prompt: str):
    structured_prompt = f"""
    {prompt}

    IMPORTANT:
    Return ONLY valid JSON.
    Do not use Markdown code fences.

    Follow this exact structure:

    {{
        "destination": "Destination name",
        "budget": 15000,
        "days": [
            {{
                "day": 1,
                "date": "YYYY-MM-DD",
                "activities": [
                    {{
                        "name": "Activity name",
                        "location": "Location",
                        "estimated_cost": 500,
                        "description": "Activity details"
                    }}
                ]
            }}
        ],
        "total_estimated_cost": 0,
        "remaining_budget": 0,
        "travel_tips": ["Travel tip"]
    }}

    Rules:
    - All costs must be numeric INR values.
    - Budget means the TOTAL trip budget, not per person.
    - Include all activities within the trip dates.
    - Do not calculate or estimate total_estimated_cost
      or remaining_budget. Python will calculate them.
    - Do not use negative activity costs.
    """

    response_text = generate_ai_response(structured_prompt)

    try:
        return json.loads(response_text)

    except json.JSONDecodeError as e:
        raise Exception(
            "Gemini returned invalid JSON. Please retry."
        ) from e
