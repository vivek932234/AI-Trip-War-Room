
from pydantic import BaseModel, Field
from datetime import date, time
from typing import Optional


class ItineraryCreate(BaseModel):
    day: int = Field(gt=0)
    activity: str = Field(min_length=3, max_length=200)
    location: str
    activity_date: date
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    estimated_cost: float = Field(default=0, ge=0)
    notes: Optional[str] = None


class ItineraryUpdate(BaseModel):
    day: Optional[int] = Field(default=None, gt=0)
    activity: Optional[str] = Field(
        default=None, min_length=3, max_length=200
    )
    location: Optional[str] = None
    activity_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    estimated_cost: Optional[float] = Field(
        default=None, ge=0
    )
    notes: Optional[str] = None
