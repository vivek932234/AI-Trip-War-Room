from pydantic import BaseModel, Field
from datetime import date
from typing import Optional


class TripCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    destination: str
    start_date: date
    end_date: date
    budget: float = Field(gt=0)
    description: Optional[str] = None