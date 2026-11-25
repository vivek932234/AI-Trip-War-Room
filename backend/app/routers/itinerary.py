
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from app.database import db
from app.schemas.itinerary import ItineraryCreate, ItineraryUpdate
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/trips", tags=["Itinerary"])

trips_collection = db["trips"]
members_collection = db["trip_members"]
itinerary_collection = db["itineraries"]


# Check whether the user has access to the trip
def check_trip_access(trip_id: str, current_user: dict):

    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    trip = trips_collection.find_one({"_id": object_id})

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    is_creator = trip["created_by"] == current_user["id"]

    is_member = members_collection.find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not is_creator and not is_member:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this trip"
        )

    return trip


# Check whether the user can modify the itinerary
def check_trip_edit_access(trip_id: str, current_user: dict):

    trip = check_trip_access(trip_id, current_user)

    # Trip creator can edit
    if trip["created_by"] == current_user["id"]:
        return trip

    # Global admin can edit
    if current_user.get("role") == "admin":
        return trip

    # Check the user's role in this particular trip
    member = members_collection.find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not member or member.get("role") not in ["planner", "leader"]:
        raise HTTPException(
            status_code=403,
            detail="Only trip planners can modify the itinerary"
        )

    return trip


# ADD ITINERARY ACTIVITY
@router.post("/{trip_id}/itinerary")
def add_itinerary(
    trip_id: str,
    activity: ItineraryCreate,
    current_user: dict = Depends(get_current_user)
):

    trip = check_trip_edit_access(trip_id, current_user)

    trip_start_date = datetime.strptime(
        trip["start_date"], "%Y-%m-%d"
    ).date()

    trip_end_date = datetime.strptime(
        trip["end_date"], "%Y-%m-%d"
    ).date()

    if (
        activity.activity_date < trip_start_date
        or activity.activity_date > trip_end_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Activity date must be within the trip dates"
        )

    activity_data = activity.model_dump()

    activity_data["activity_date"] = (
        activity_data["activity_date"].isoformat()
    )

    activity_data["start_time"] = (
        activity_data["start_time"].isoformat()
        if activity_data["start_time"] else None
    )

    activity_data["end_time"] = (
        activity_data["end_time"].isoformat()
        if activity_data["end_time"] else None
    )

    activity_data.update({
        "trip_id": trip_id,
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc)
    })

    result = itinerary_collection.insert_one(activity_data)

    return {
        "message": "Itinerary activity added successfully",
        "activity_id": str(result.inserted_id)
    }


# GET ITINERARY ACTIVITIES
@router.get("/{trip_id}/itinerary")
def get_itinerary(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):

    check_trip_access(trip_id, current_user)

    activities = list(
        itinerary_collection.find(
            {"trip_id": trip_id}
        ).sort(
            [("activity_date", 1), ("start_time", 1)]
        )
    )

    for activity in activities:
        activity["id"] = str(activity.pop("_id"))

    return {
        "message": "Itinerary retrieved successfully",
        "total_activities": len(activities),
        "itinerary": activities
    }


# UPDATE ITINERARY ACTIVITY
@router.patch("/{trip_id}/itinerary/{activity_id}")
def update_itinerary(
    trip_id: str,
    activity_id: str,
    activity: ItineraryUpdate,
    current_user: dict = Depends(get_current_user)
):

    trip = check_trip_edit_access(trip_id, current_user)

    try:
        activity_object_id = ObjectId(activity_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid activity ID"
        )

    existing_activity = itinerary_collection.find_one({
        "_id": activity_object_id,
        "trip_id": trip_id
    })

    if not existing_activity:
        raise HTTPException(
            status_code=404,
            detail="Itinerary activity not found"
        )

    update_data = activity.model_dump(exclude_unset=True)

    if "activity_date" in update_data:

        new_date = update_data["activity_date"]

        trip_start = datetime.strptime(
            trip["start_date"], "%Y-%m-%d"
        ).date()

        trip_end = datetime.strptime(
            trip["end_date"], "%Y-%m-%d"
        ).date()

        if new_date < trip_start or new_date > trip_end:
            raise HTTPException(
                status_code=400,
                detail="Activity date must be within trip dates"
            )

        update_data["activity_date"] = new_date.isoformat()

    for field in ["start_time", "end_time"]:

        if field in update_data:
            update_data[field] = (
                update_data[field].isoformat()
                if update_data[field] else None
            )

    if update_data:
        itinerary_collection.update_one(
            {
                "_id": activity_object_id,
                "trip_id": trip_id
            },
            {"$set": update_data}
        )

    return {
        "message": "Itinerary activity updated successfully"
    }


# DELETE ITINERARY ACTIVITY
@router.delete("/{trip_id}/itinerary/{activity_id}")
def delete_itinerary(
    trip_id: str,
    activity_id: str,
    current_user: dict = Depends(get_current_user)
):

    check_trip_edit_access(trip_id, current_user)

    try:
        activity_object_id = ObjectId(activity_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid activity ID"
        )

    result = itinerary_collection.delete_one({
        "_id": activity_object_id,
        "trip_id": trip_id
    })

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Itinerary activity not found"
        )

    return {
        "message": "Itinerary activity deleted successfully"
    }
