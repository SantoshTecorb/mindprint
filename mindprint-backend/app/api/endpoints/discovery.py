from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
import json
from typing import List

from ...database import get_db
from ...models import Seller, MemoryData
from ...schemas import PersonaDiscoveryResponse, PersonaProfile

router = APIRouter(prefix="/discovery", tags=["discovery"])

@router.get("", response_model=PersonaDiscoveryResponse)
def list_available_personas(db: Session = Depends(get_db)):
    """List all sellers who have uploaded cognitive assets."""
    # 1. Find sellers with at least one memory entry
    # We join Seller with MemoryData to ensure they actually have "cognition" to sell
    sellers_with_assets = db.query(
        Seller, 
        func.count(MemoryData.id).label("asset_count")
    ).join(MemoryData, Seller.user_id == MemoryData.user_id).group_by(Seller.user_id).all()
    
    personas = []
    for seller, count in sellers_with_assets:
        # Try to get a preview from their latest cognition.md
        latest_cognition = db.query(MemoryData).filter(
            MemoryData.user_id == seller.user_id,
            MemoryData.file_path.like("%cognition.md")
        ).order_by(MemoryData.scanned_at.desc()).first()
        
        preview = None
        if latest_cognition:
            # Take the first 200 characters as a preview
            preview = latest_cognition.content[:200] + "..." if len(latest_cognition.content) > 200 else latest_cognition.content

        personas.append(PersonaProfile(
            user_id=seller.user_id,
            metadata=json.loads(seller.metadata_json) if seller.metadata_json else {},
            last_seen=seller.last_seen,
            expertise_preview=preview,
            asset_count=count
        ))
        
    return {
        "success": True,
        "personas": personas
    }
