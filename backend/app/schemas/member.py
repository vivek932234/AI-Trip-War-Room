
from pydantic import BaseModel, EmailStr
from typing import Literal


class AddMember(BaseModel):
    email: EmailStr
    role: Literal["viewer", "planner"] = "viewer"


class CreateInvite(BaseModel):
    role: Literal["viewer", "planner"] = "viewer"


class JoinTrip(BaseModel):
    invite_code: str
