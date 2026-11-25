from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone, timedelta

from app.database import db
from app.schemas.member import AddMember, CreateInvite, JoinTrip
from app.services.auth_service import get_current_user
from app.services.permissions import require_roles

import secrets
import string

import os
from dotenv import load_dotenv
load_dotenv()

from app.schemas.member import AddMember, CreateInvite


from bson import ObjectId
from bson.errors import InvalidId

router = APIRouter(prefix="/trips", tags=["Trip Members"])

trips_collection = db["trips"]
users_collection = db["users"]
invites_collection = db["trip_invites"]

@router.post("/{trip_id}/members")
def add_member(
    trip_id: str,
    member: AddMember,
    current_user: dict = Depends(get_current_user)
):

    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    trip = trips_collection.find_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found or you are not the creator"
        )

    new_user = users_collection.find_one({
        "email": member.email
    })

    if not new_user:
        raise HTTPException(
            status_code=404,
            detail="User is not registered"
        )

    if member.role not in ["viewer", "planner"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid member role"
        )

    if new_user["role"] == "admin":
        raise HTTPException(
            status_code=400,
            detail="Admin cannot be added as a trip member"
        )

    if new_user["_id"] == current_user.get("_id"):
        raise HTTPException(
            status_code=400,
            detail="You are already the trip creator"
        )

    existing_member = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": str(new_user["_id"])
    })

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="User is already a trip member"
        )

    db["trip_members"].insert_one({
        "trip_id": trip_id,
        "user_id": str(new_user["_id"]),
        "email": new_user["email"],
        "role": member.role,
        "added_by": current_user["id"],
        "added_at": datetime.now(timezone.utc)
    })

    return {
        "message": "Member added successfully",
        "trip_id": trip_id,
        "member_email": new_user["email"],
        "role": member.role
    }

@router.post("/{trip_id}/invite")
def create_trip_invite(
    trip_id: str,
    invite: CreateInvite,
    current_user: dict = Depends(get_current_user)
):
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    # Only the trip creator can generate invitations
    trip = trips_collection.find_one({
        "_id": object_id,
        "created_by": current_user["id"]
    })

    if not trip:
        raise HTTPException(
            status_code=403,
            detail="Only the trip creator can generate invitations"
        )

    # Generate a unique 8-character invitation code
    characters = string.ascii_uppercase + string.digits

    while True:
        invite_code = "".join(
            secrets.choice(characters) for _ in range(8)
        )

        existing_invite = invites_collection.find_one({
            "invite_code": invite_code
        })

        if not existing_invite:
            break

    # Set invitation creation and expiry timestamps
    created_at = datetime.now(timezone.utc)
    expires_at = created_at + timedelta(days=7)

    # Save invitation details
    invites_collection.insert_one({
        "invite_code": invite_code,
        "trip_id": trip_id,
        "role": invite.role,
        "created_by": current_user["id"],
        "created_at": created_at,
        "expires_at": expires_at,
        "is_active": True
    })


    return {
        "message": "Invitation created successfully",
        "trip_id": trip_id,
        "invite_code": invite_code,
        "role": invite.role,
       "invite_link": f"{os.getenv('FRONTEND_URL', 'http://localhost:5173').rstrip('/')}/join/{invite_code}",
        "expires_at": expires_at.isoformat()
    }


@router.post("/join")
def join_trip(
    join_data: JoinTrip,
    current_user: dict = Depends(get_current_user)
):
    # Find the invitation
    invitation = invites_collection.find_one({
        "invite_code": join_data.invite_code.upper(),
        "is_active": True
    })

    if not invitation:
     raise HTTPException(
        status_code=404,
        detail="Invalid or inactive invitation code"
    )

    # Check invitation expiry
    expires_at = invitation.get("expires_at")

    # Support older invitations created before expiry was implemented
    if expires_at is None:
        created_at = invitation.get("created_at")

        if created_at is None:
            raise HTTPException(
                status_code=410,
                detail="Invitation has expired"
            )

        expires_at = created_at + timedelta(days=7)

    # MongoDB may return naive UTC datetimes
    current_time = datetime.now(timezone.utc).replace(tzinfo=None)
    expiry_time = expires_at.replace(tzinfo=None)

    if current_time >= expiry_time:
        raise HTTPException(
            status_code=410,
            detail="Invitation has expired"
        )

    trip_id = invitation["trip_id"]

    # Check whether the trip still exists
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID in invitation"
        )

    trip = trips_collection.find_one({
        "_id": object_id
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip no longer exists"
        )

    # Prevent the trip creator from joining again
    if trip["created_by"] == current_user["id"]:
        raise HTTPException(
            status_code=400,
            detail="You are already the trip creator"
        )

    # Prevent duplicate membership
    existing_member = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if existing_member:
        raise HTTPException(
            status_code=409,
            detail="You are already a member of this trip"
        )

    # Add user to trip_members
    db["trip_members"].insert_one({
        "trip_id": trip_id,
        "user_id": current_user["id"],
        "email": current_user.get("email"),
        "role": invitation["role"],
        "added_by": invitation["created_by"],
        "added_at": datetime.now(timezone.utc)
    })

    return {
        "message": "Successfully joined the trip",
        "trip_id": trip_id,
        "trip_title": trip["title"],
        "role": invitation["role"]
    }


# GET ALL MEMBERS OF A TRIP
@router.get("/{trip_id}/members")
def get_trip_members(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        object_id = ObjectId(trip_id)
    except InvalidId:
        raise HTTPException(
            status_code=400,
            detail="Invalid trip ID"
        )

    trip = trips_collection.find_one({
        "_id": object_id
    })

    if not trip:
        raise HTTPException(
            status_code=404,
            detail="Trip not found"
        )

    # Verify trip access
    is_creator = trip["created_by"] == current_user["id"]

    membership = db["trip_members"].find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not is_creator and not membership:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this trip"
        )

    # Include trip creator
    member_ids = {trip["created_by"]}

    members = db["trip_members"].find({
        "trip_id": trip_id
    })

    for member in members:
        member_ids.add(member["user_id"])

    result = []

    for member_id in member_ids:
        user = users_collection.find_one({
            "_id": ObjectId(member_id)
        })

        if user:
            result.append({
                "user_id": member_id,
                "full_name": user.get("full_name") or user.get("name") or user.get("email"),
                "email": user.get("email")
            })

    return {
        "message": "Trip members retrieved successfully",
        "total_members": len(result),
        "members": result
    }
