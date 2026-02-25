from pydantic import BaseModel
from typing import Any, Dict, List
from datetime import datetime

class EmailOut(BaseModel):
    id: int
    from_email: str
    subject: str
    received_at: datetime
    status: str
    extracted: Dict[str, Any]
    missing_fields: List[str]
    last_error: str
    body_text: str

    class Config:
        from_attributes = True

class ReviewUpdateIn(BaseModel):
    proposed_fields: Dict[str, Any]
    reviewer: str = "human"

class OrderOut(BaseModel):
    id: int
    job_id: str
    customer_name: str
    weight_kg: int
    pickup_location: str
    drop_location: str
    pickup_time_window: str
    created_at: datetime

    class Config:
        from_attributes = True