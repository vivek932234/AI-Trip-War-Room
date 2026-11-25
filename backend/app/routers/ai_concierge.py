from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.services.auth_service import get_current_user
from app.services.gemini_service import generate_ai_response, generate_structured_itinerary

from bson import ObjectId
from bson.errors import InvalidId
from app.database import db

from datetime import datetime, timezone, date, timedelta


router = APIRouter(
    prefix="/ai",
    tags=["AI Travel Concierge"]
)
trips_collection = db["trips"]
members_collection = db["trip_members"]
itineraries_collection = db["ai_itineraries"]
ai_chat_collection = db["ai_chat_messages"]

def check_trip_access(trip_id: str, current_user: dict):
    try:
        trip_object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    trip = trips_collection.find_one({
        "_id": trip_object_id
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    is_creator = trip.get("created_by") == current_user["id"]

    membership = members_collection.find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not is_creator and not membership:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this trip"
        )

    return trip



class TravelRequest(BaseModel):
    destination: str = Field(min_length=2, max_length=100)
    days: int = Field(gt=0, le=30)
    budget: float = Field(gt=0)
    travelers: int = Field(gt=0, le=50)
    preferences: str = Field(default="General sightseeing", max_length=500)

class AIChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=2000)


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
    # Validate trip access
    trip = check_trip_access(trip_id, current_user)

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

        # Get the latest itinerary version for this trip
        latest_itinerary = itineraries_collection.find_one(
            {"trip_id": trip_id},
            sort=[("version", -1)]
        )

        version = (
            latest_itinerary["version"] + 1
            if latest_itinerary
            else 1
        )

        # Save the new itinerary in MongoDB
        itinerary_document = {
            "trip_id": trip_id,
            "trip_title": trip.get("title"),
            "destination": trip.get("destination"),
            "version": version,
            "travel_plan": ai_response,
            "generated_by": current_user["id"],
            "created_at": datetime.now(timezone.utc)
        }

        save_result = itineraries_collection.insert_one(
            itinerary_document
        )


        return {
    "message": "Trip-based travel plan generated and saved successfully",
    "trip_id": trip_id,
    "trip_title": trip.get("title"),
    "destination": trip.get("destination"),
    "itinerary_id": str(save_result.inserted_id),
    "version": version,
    "travel_plan": ai_response
}

    except Exception as e:
        print("AI Travel Plan Error:", str(e))
        raise HTTPException(
            status_code=503,
            detail="AI Travel Concierge is temporarily unavailable"
        )


@router.get("/trips/{trip_id}/itineraries")
def get_trip_itineraries(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Verify trip access
    check_trip_access(trip_id, current_user)

    # Fetch all saved itinerary versions
    itineraries = list(
        itineraries_collection.find(
            {"trip_id": trip_id}
        ).sort("version", -1)
    )

    # Convert MongoDB documents into API responses
    result = []

    for itinerary in itineraries:
        result.append({
            "itinerary_id": str(itinerary["_id"]),
            "trip_id": itinerary["trip_id"],
            "version": itinerary["version"],
            "destination": itinerary["destination"],
            "generated_by": itinerary["generated_by"],
            "created_at": itinerary["created_at"].isoformat(),
            "travel_plan": itinerary["travel_plan"]
        })

    return {
        "message": "Itinerary history retrieved successfully",
        "total_versions": len(result),
        "itineraries": result
    }

@router.get("/trips/{trip_id}/itineraries/{version}")
def get_specific_itinerary(
    trip_id: str,
    version: int,
    current_user: dict = Depends(get_current_user)
):
    # Verify trip access
    check_trip_access(trip_id, current_user)

    # Validate version
    if version < 1:
        raise HTTPException(
            status_code=400,
            detail="Version must be greater than zero"
        )

    # Find the requested itinerary version
    itinerary = itineraries_collection.find_one({
        "trip_id": trip_id,
        "version": version
    })

    if not itinerary:
        raise HTTPException(
            status_code=404,
            detail="Itinerary version not found"
        )

    return {
        "message": "Itinerary retrieved successfully",
        "itinerary_id": str(itinerary["_id"]),
        "trip_id": trip_id,
        "version": itinerary["version"],
        "destination": itinerary["destination"],
        "generated_by": itinerary["generated_by"],
        "created_at": itinerary["created_at"].isoformat(),
        "travel_plan": itinerary["travel_plan"]
    }


@router.post("/trips/{trip_id}/chat")
def chat_with_ai(
    trip_id: str,
    request: AIChatRequest,
    current_user: dict = Depends(get_current_user)
):
    # Step 1: Verify trip access
    trip = check_trip_access(trip_id, current_user)

    # Step 2: Fetch the latest 10 conversation messages
    previous_messages = list(
        ai_chat_collection.find({
            "trip_id": trip_id,
            "user_id": current_user["id"]
        }).sort("created_at", -1).limit(10)
    )

    previous_messages.reverse()

    # Step 3: Prepare conversation history
    conversation_history = ""

    for item in previous_messages:
        conversation_history += (
            f'{item["role"]}: {item["message"]}\n'
        )

    # Step 4: Build the Gemini prompt
    prompt = f"""
    You are an AI Travel Concierge for a collaborative travel platform.

    Help the user with practical travel-related questions.

    Actual trip details:
    Trip title: {trip.get("title")}
    Destination: {trip.get("destination")}
    Start date: {trip.get("start_date")}
    End date: {trip.get("end_date")}
    Total budget: INR {trip.get("budget")}
    Description: {trip.get("description", "No description")}

    Previous conversation:
    {conversation_history}

    Current user question:
    {request.message}

    Instructions:
    - Answer according to the actual trip details.
    - Give practical and budget-conscious suggestions.
    - Use INR when discussing costs.
    - Clearly identify estimated prices.
    - Do not claim to have verified live prices or availability.
    - If information is unavailable, say so.
    - Keep your response clear and helpful.
    """

    # Step 5: Generate the AI response
    try:
        ai_response = generate_ai_response(prompt)

        if not isinstance(ai_response, str) or not ai_response.strip():
            raise ValueError("Empty AI response")

    except Exception as e:
        print("AI Chat Error:", str(e))
        raise HTTPException(
            status_code=503,
            detail="AI Travel Concierge is temporarily unavailable."
        )

    # Step 6: Save both messages in MongoDB
    now = datetime.now(timezone.utc)

    ai_chat_collection.insert_many([
        {
            "trip_id": trip_id,
            "user_id": current_user["id"],
            "role": "user",
            "message": request.message,
            "created_at": now
        },
        {
            "trip_id": trip_id,
            "user_id": current_user["id"],
            "role": "assistant",
            "message": ai_response,
            "created_at": now
        }
    ])

    # Step 7: Return the response
    return {
        "message": "AI response generated successfully",
        "trip_id": trip_id,
        "question": request.message,
        "answer": ai_response
    }


@router.get("/trips/{trip_id}/chat/history")
def get_ai_chat_history(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    # Verify that the user has access to this trip
    check_trip_access(trip_id, current_user)

    # Retrieve this user's previous AI chat messages
    messages = list(
        ai_chat_collection.find(
            {
                "trip_id": trip_id,
                "user_id": current_user["id"]
            }
        ).sort([
            ("created_at", 1),
            ("_id", 1)
        ])
    )

    # Convert MongoDB documents into API response format
    chat_history = []

    for msg in messages:
        chat_history.append({
            "id": str(msg["_id"]),
            "role": msg["role"],
            "message": msg["message"],
            "created_at": msg["created_at"]
        })

    return {
        "message": "AI chat history retrieved successfully",
        "trip_id": trip_id,
        "total_messages": len(chat_history),
        "history": chat_history
    }
