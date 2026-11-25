
from pydantic import BaseModel, Field
from typing import Literal


class ExpenseCreate(BaseModel):
    title: str = Field(min_length=3, max_length=150)

    amount: float = Field(gt=0)

    category: Literal[
        "hotel",
        "food",
        "transport",
        "shopping",
        "activities",
        "other"
    ]

    paid_by: str

    split_between: list[str] = Field(min_length=1)

    notes: str | None = None
