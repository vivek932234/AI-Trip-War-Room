
import json
import time

from google import genai
from google.genai import errors
from app.services.security import settings

client = genai.Client(
    api_key=settings.GEMINI_API_KEY
)


def generate_ai_response(prompt: str):
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt
            )

            return response.text

        except errors.ServerError as e:
            if e.code == 503 and attempt < 2:
                print(f"Gemini busy. Retrying ({attempt + 1}/3)...")
                time.sleep(8 * (attempt + 1))
                continue

            raise Exception(
                "Gemini is temporarily unavailable."
            ) from e

        except Exception as e:
            print("Gemini API Error:", str(e))
            raise Exception(
                "AI service is temporarily unavailable."
            ) from e


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
