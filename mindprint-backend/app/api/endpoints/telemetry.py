from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import json

from ...database import get_db
from ...models import Seller, Buyer
from ...schemas import TelemetryData

router = APIRouter(tags=["telemetry"])

@router.post("/sellers/telemetry")
def update_seller_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    seller = db.query(Seller).filter_by(user_id=data.user_id).first()
    if not seller:
        seller = Seller(user_id=data.user_id, first_seen=datetime.utcnow())
        db.add(seller)
    
    seller.hostname = data.hostname
    seller.os_name = data.os_name
    seller.os_version = data.os_version
    seller.python_version = data.python_version
    seller.install_path = data.install_path
    seller.last_seen = datetime.utcnow()
    seller.metadata_json = json.dumps(data.metadata)
    
    db.commit()
    return {"success": True}

@router.post("/buyers/telemetry")
def update_buyer_telemetry(data: TelemetryData, db: Session = Depends(get_db)):
    buyer = db.query(Buyer).filter_by(user_id=data.user_id).first()
    if not buyer:
        buyer = Buyer(user_id=data.user_id, first_seen=datetime.utcnow())
        db.add(buyer)
    
    buyer.hostname = data.hostname
    buyer.os_name = data.os_name
    buyer.os_version = data.os_version
    buyer.python_version = data.python_version
    buyer.install_path = data.install_path
    buyer.last_seen = datetime.utcnow()
    buyer.metadata_json = json.dumps(data.metadata)
    
    db.commit()
    return {"success": True}
