from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import hashlib
import os
from datetime import datetime

from ...database import get_db
from ...models import Rental
from ...schemas import RentalCreateRequest, RentalResponse

router = APIRouter(prefix="/rentals", tags=["rentals"])

@router.post("", response_model=RentalResponse)
def create_rental(request: RentalCreateRequest, db: Session = Depends(get_db)):
    token = f"mp@{hashlib.sha256(os.urandom(32)).hexdigest()[:12]}"
    new_rental = Rental(
        token=token, 
        seller_user_id=request.seller_user_id,
        usage_limit=request.usage_limit
    )
    db.add(new_rental)
    db.commit()
    db.refresh(new_rental)
    return {
        "success": True, 
        "token": token, 
        "seller_user_id": new_rental.seller_user_id,
        "usage_limit": new_rental.usage_limit,
        "usage_current": new_rental.usage_current
    }
