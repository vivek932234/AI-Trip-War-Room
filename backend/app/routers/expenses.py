
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timezone
from bson import ObjectId
from bson.errors import InvalidId

from app.database import db
from app.schemas.expense import ExpenseCreate
from app.services.auth_service import get_current_user


router = APIRouter(prefix="/trips", tags=["Expenses"])

trips_collection = db["trips"]
members_collection = db["trip_members"]
expenses_collection = db["expenses"]
users_collection = db["users"]
settlement_payments_collection = db["settlement_payments"]

# CHECK TRIP ACCESS
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

    is_creator = trip["created_by"] == current_user["id"]

    member = members_collection.find_one({
        "trip_id": trip_id,
        "user_id": current_user["id"]
    })

    if not is_creator and not member:
        raise HTTPException(
            status_code=403,
            detail="You do not have access to this trip"
        )

    return trip


# GET VALID TRIP MEMBER IDS
def get_trip_member_ids(trip_id: str, trip: dict):

    member_ids = {trip["created_by"]}

    members = members_collection.find({
        "trip_id": trip_id
    })

    for member in members:
        member_ids.add(member["user_id"])

    return member_ids


# GET MEMBER NAME
def get_member_name(member_id: str):

    try:
        user = users_collection.find_one({
            "_id": ObjectId(member_id)
        })

        if user:
            return user.get("full_name") or user.get("name") or user.get("email") or "Unknown Member"

    except Exception:
        pass

    return "Unknown Member"



# ADD GROUP EXPENSE
@router.post("/{trip_id}/expenses", status_code=201)
def add_expense(
    trip_id: str,
    expense: ExpenseCreate,
    current_user: dict = Depends(get_current_user)
):

    trip = check_trip_access(trip_id, current_user)

    valid_member_ids = get_trip_member_ids(trip_id, trip)

    # Check who paid
    if expense.paid_by not in valid_member_ids:
        raise HTTPException(
            status_code=400,
            detail="Payer is not a member of this trip"
        )

    # Check who shares the expense
    if not set(expense.split_between).issubset(valid_member_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more split members are not part of this trip"
        )

    # Remove duplicate member IDs
    split_members = list(dict.fromkeys(expense.split_between))

    expense_data = expense.model_dump()

    expense_data["split_between"] = split_members
    expense_data["trip_id"] = trip_id
    expense_data["created_by"] = current_user["id"]
    expense_data["created_at"] = datetime.now(timezone.utc)

    result = expenses_collection.insert_one(expense_data)

    return {
        "message": "Expense added successfully",
        "expense_id": str(result.inserted_id)
    }

# GET ALL GROUP EXPENSES
@router.get("/{trip_id}/expenses")
def get_expenses(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    check_trip_access(trip_id, current_user)

    expenses = list(
        expenses_collection.find({
            "trip_id": trip_id
        }).sort("created_at", -1)
    )

    for expense in expenses:
        expense["id"] = str(expense.pop("_id"))

        # Convert payer ID into member name
        expense["paid_by_name"] = get_member_name(
            expense["paid_by"]
        )

    return {
        "message": "Expenses retrieved successfully",
        "total_expenses": len(expenses),
        "expenses": expenses
    }

# GET GROUP EXPENSE SETTLEMENT
@router.get("/{trip_id}/expenses/settlement")
def get_expense_settlement(
    trip_id: str,
    current_user: dict = Depends(get_current_user)
):
    trip = check_trip_access(trip_id, current_user)
    valid_member_ids = get_trip_member_ids(trip_id, trip)

    expenses = list(expenses_collection.find({
        "trip_id": trip_id
    }))

    # Initialize balances in paise
    balances = {
        member_id: 0
        for member_id in sorted(valid_member_ids)
    }

    # Calculate balances for ALL expenses
    for expense in expenses:
        amount_paise = round(float(expense["amount"]) * 100)
        payer = expense["paid_by"]

        split_members = sorted(
            set(expense["split_between"])
        )

        if not split_members:
            continue

        # Credit the payer
        balances[payer] += amount_paise

        # Divide expense equally, distributing leftover paise
        base_share = amount_paise // len(split_members)
        remainder = amount_paise % len(split_members)

        for index, member_id in enumerate(split_members):
            share = base_share + (1 if index < remainder else 0)
            balances[member_id] -= share

    # Separate creditors and debtors
    creditors = []
    debtors = []

    for member_id, balance in balances.items():
        if balance > 0:
            creditors.append({
                "member_id": member_id,
                "amount": balance
            })

        elif balance < 0:
            debtors.append({
                "member_id": member_id,
                "amount": abs(balance)
            })

    # Calculate settlements entirely in paise
    settlements = []

    i = 0
    j = 0

    while i < len(debtors) and j < len(creditors):

        amount_paise = min(
            debtors[i]["amount"],
            creditors[j]["amount"]
        )

        settlements.append({
            "from": debtors[i]["member_id"],
            "to": creditors[j]["member_id"],
            "amount": amount_paise / 100
        })

        debtors[i]["amount"] -= amount_paise
        creditors[j]["amount"] -= amount_paise

        if debtors[i]["amount"] == 0:
            i += 1

        if creditors[j]["amount"] == 0:
            j += 1

    # Convert balances into member names and rupees
    named_balances = {}

    for member_id, balance in balances.items():
        member_name = get_member_name(member_id)
        named_balances[member_name] = balance / 100

    # Fetch confirmed payments
    received_payments = list(
        settlement_payments_collection.find({
            "trip_id": trip_id,
            "status": "received"
        })
    )

    # Match current settlements with confirmed payments
    named_settlements = []

    for settlement in settlements:
        from_id = settlement["from"]
        to_id = settlement["to"]
        amount = settlement["amount"]

        status = "pending"

        for payment in received_payments:
            if (
                payment["from"] == from_id
                and payment["to"] == to_id
                and round(float(payment["amount"]) * 100)
                    == round(amount * 100)
            ):
                status = "received"
                break

        named_settlements.append({
            "from": get_member_name(from_id),
            "to": get_member_name(to_id),
            "from_id": from_id,
            "to_id": to_id,
            "amount": amount,
            "status": status
        })


    # Calculate outstanding balances from pending settlements
    outstanding_balances = {
        member_id: 0
        for member_id in valid_member_ids
    }

    for settlement in named_settlements:
        if settlement["status"] == "pending":
            from_id = settlement["from_id"]
            to_id = settlement["to_id"]
            amount_paise = round(settlement["amount"] * 100)

            outstanding_balances[from_id] -= amount_paise
            outstanding_balances[to_id] += amount_paise

    # Convert outstanding balances into member names and rupees
    named_outstanding_balances = {}

    for member_id, balance in outstanding_balances.items():
        member_name = get_member_name(member_id)
        named_outstanding_balances[member_name] = balance / 100

    return {
        "message": "Expense settlement calculated successfully",
        "balances": named_balances,
        "outstanding_balances": named_outstanding_balances,
        "settlements": named_settlements
    }


#
# MARK SETTLEMENT PAYMENT AS RECEIVED
@router.post("/{trip_id}/expenses/settlement/received")
def mark_payment_received(
    trip_id: str,
    payment: dict,
    current_user: dict = Depends(get_current_user)
):
    trip = check_trip_access(trip_id, current_user)

    from_member = payment.get("from")
    to_member = payment.get("to")
    amount = payment.get("amount")

    if not from_member or not to_member or amount is None:
        raise HTTPException(
            status_code=400,
            detail="from, to and amount are required"
        )

    try:
        amount = round(float(amount), 2)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid payment amount"
        )

    if amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment amount must be greater than zero"
        )

    valid_member_ids = get_trip_member_ids(trip_id, trip)

    if from_member not in valid_member_ids or to_member not in valid_member_ids:
        raise HTTPException(
            status_code=400,
            detail="Both members must belong to this trip"
        )

    if from_member == to_member:
        raise HTTPException(
            status_code=400,
            detail="Payer and receiver cannot be the same"
        )

    # Only the person receiving the money can confirm it
    if current_user["id"] != to_member:
        raise HTTPException(
            status_code=403,
            detail="Only the receiver can confirm this payment"
        )

    existing_payment = settlement_payments_collection.find_one({
        "trip_id": trip_id,
        "from": from_member,
        "to": to_member,
        "amount": amount,
        "status": "received"
    })

    if existing_payment:
        raise HTTPException(
            status_code=409,
            detail="This payment is already marked as received"
        )

    settlement_payments_collection.insert_one({
        "trip_id": trip_id,
        "from": from_member,
        "to": to_member,
        "amount": amount,
        "status": "received",
        "confirmed_by": current_user["id"],
        "confirmed_at": datetime.now(timezone.utc)
    })

    return {
        "message": "Payment marked as received successfully",
        "status": "received"
    }
