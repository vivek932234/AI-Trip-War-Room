
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.auth_service import get_current_user
from app.services.gemini_service import generate_ai_response, generate_structured_itinerary

from bson import ObjectId
from bson.errors import InvalidId
from app.database import db


router = APIRouter(
    prefix="/ai",
    tags=["AI Travel Concierge"]
)
trips_collection = db["trips"]
members_collection = db["trip_members"]


class TravelRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    days: int = Field(gt=0, le=30)
    budget: float = Field(gt=0)
    travelers: int = Field(gt=0, le=50)
    preferences: str = Field(default="General sightseeing", max_length=500)


@router.post("/travel-plan")
def generate_travel_plan(
    request: TravelRequest,
    current_user: dict = Depends(get_current_user)
):
    prompt = f"""
    You are an expert AI Travel Concierge.

    Create a practical travel plan using these details:

    Destination: {request.destination}
    Duration: {request.days} days
    Total Budget: {request.budget}
    Number of Travelers: {request.travelers}
    Preferences: {request.preferences}

    Provide:
    1. A day-wise itinerary.
    2. Recommended activities and attractions.
    3. Suggested food options.
    4. Estimated expenses.
    5. Useful travel tips.

    Keep the suggestions within the given budget.
    Clearly mention when costs are estimates.
    """

    try:
        ai_response = generate_ai_response(prompt)

        return {
            "message": "Travel plan generated successfully",
            "user": current_user["full_name"],
            "destination": request.destination,
            "travel_plan": ai_response
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="AI Travel Concierge is temporarily unavailable. Please try again."
        )


@router.post("/trips/{trip_id}/travel-plan")
def generate_trip_travel_plan(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Validate trip ID
    try:
        trip_object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    # Fetch trip from MongoDB
    trip = trips_collection.find_one({
        "_id": trip_object_id
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    # Check whether user created or joined this trip
    is_creator = trip.get("created_by") == current_user["id"]

    # Build prompt using actual MongoDB trip details
    prompt = f"""
    You are an expert AI Travel Concierge.

    Create a personalized travel itinerary using these
    actual trip details from our database:

    Trip Title: {trip.get("title")}
    Destination: {trip.get("destination")}
    Start Date: {trip.get("start_date")}
    End Date: {trip.get("end_date")}
    Total Budget: {trip.get("budget")} INR
    Description: {trip.get("description", "No description")}

    Provide:
    1. Day-wise travel itinerary.
    2. Recommended attractions and activities.
    3. Suggested local food.
    4. Estimated budget breakdown.
    5. Useful travel tips.

    Keep suggestions within the available budget.
    All costs must be numeric INR values.
    Treat the budget as the total trip budget, not per person.
    Do not claim to have verified live prices or availability.
    """

    try:
        ai_response = generate_structured_itinerary(prompt)

        # Validate itinerary structure
        if not isinstance(ai_response, dict):
            raise ValueError("Invalid itinerary format")

        if not isinstance(ai_response.get("days"), list):
            raise ValueError("Itinerary days must be a list")

        if not ai_response["days"]:
            raise ValueError("Itinerary must contain at least one day")

        # Validate trip dates
        from datetime import date, timedelta

        trip_start = date.fromisoformat(trip["start_date"])
        trip_end = date.fromisoformat(trip["end_date"])

        expected_days = (trip_end - trip_start).days + 1

        if len(ai_response["days"]) != expected_days:
            raise ValueError("AI generated an incorrect number of trip days")

        
        for index, day in enumerate(ai_response["days"]):

            if not isinstance(day, dict):
                raise ValueError("Invalid day format")

            # Validate day number
            if day.get("day") != index + 1:
                raise ValueError("Invalid itinerary day number")

            # Validate date
            expected_date = trip_start + timedelta(days=index)

            if day.get("date") != expected_date.isoformat():
                raise ValueError("Activity date is outside the expected trip schedule")

            # Validate activities list BEFORE iterating
            activities = day.get("activities")

            if not isinstance(activities, list) or not activities:
                raise ValueError("Each day must contain at least one activity")

            # Validate individual activities
            for activity in activities:

                if not isinstance(activity, dict):
                    raise ValueError("Invalid activity format")

                if not isinstance(activity.get("name"), str) or not activity["name"].strip():
                    raise ValueError("Activity name is required")

                if not isinstance(activity.get("location"), str) or not activity["location"].strip():
                    raise ValueError("Activity location is required")

                cost = activity.get("estimated_cost")

                if (
                    not isinstance(cost, (int, float))
                    or isinstance(cost, bool)
                    or cost < 0
                ):
                    raise ValueError("Invalid activity cost")


        # Calculate total activity cost using Python
        total_cost = 0

        for day in ai_response["days"]:
            for activity in day["activities"]:
                cost = activity["estimated_cost"]

                if (
                    not isinstance(cost, (int, float))
                    or isinstance(cost, bool)
                    or cost < 0
                ):
                    raise ValueError("Invalid activity cost returned by AI")

                total_cost += cost

        # Calculate budget using actual MongoDB trip budget
        trip_budget = float(trip.get("budget", 0))
        remaining_budget = trip_budget - total_cost

        ai_response["budget"] = trip_budget
        ai_response["total_estimated_cost"] = total_cost
        ai_response["remaining_budget"] = remaining_budget
        ai_response["over_budget"] = remaining_budget < 0

        return {
            "message": "Trip-based travel plan generated successfully",
            "trip_id": trip_id,
            "trip_title": trip.get("title"),
            "destination": trip.get("destination"),
            "travel_plan": ai_response
        }

    except Exception as e:
        print("AI Travel Plan Error:", str(e))
        raise HTTPException(
            status_code=503,
            detail="AI Travel Concierge is temporarily unavailable"
        )
