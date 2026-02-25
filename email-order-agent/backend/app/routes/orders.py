from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Order
from ..schemas import OrderOut
from ..auth import get_current_user

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("", response_model=list[OrderOut])
def list_orders(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    return db.query(Order).order_by(Order.created_at.desc()).limit(200).all()