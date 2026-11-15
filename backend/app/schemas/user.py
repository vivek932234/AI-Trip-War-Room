
from pydantic import BaseModel, EmailStr, Field
from typing import Literal


class UserRegister(BaseModel):
    full_name: str = Field(min_length=2, max_length=100)

    email: EmailStr

    password: str = Field(min_length=8)

    role: Literal["viewer"] = "viewer"


class UserLogin(BaseModel):
    email: EmailStr

    password: str
