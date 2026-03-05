from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import json

from ...database import get_db
from ...models import RentalIntegration, Rental
from ...schemas import IntegrationCreate, IntegrationResponse

router = APIRouter(prefix="/integrations", tags=["integrations"])

@router.get("/{rental_id}", response_model=List[IntegrationResponse])
def get_integrations(rental_id: int, db: Session = Depends(get_db)):
    """List all integrations for a specific rental."""
    integrations = db.query(RentalIntegration).filter(RentalIntegration.rental_id == rental_id).all()
    
    # Parse config_json back to dict for the response
    result = []
    for item in integrations:
        res = {
            "id": item.id,
            "rental_id": item.rental_id,
            "channel_type": item.channel_type,
            "is_enabled": bool(item.is_enabled),
            "platform_user_id": item.platform_user_id,
            "config": json.loads(item.config_json) if item.config_json else {},
            "last_active_at": item.last_active_at
        }
        result.append(res)
    return result

@router.post("", response_model=IntegrationResponse)
def upsert_integration(request: IntegrationCreate, db: Session = Depends(get_db)):
    """Create or update a channel integration for a rental."""
    # 1. Verify rental exists
    rental = db.query(Rental).filter(Rental.id == request.rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental session not found")

    # 2. Check for existing integration of this type
    integration = db.query(RentalIntegration).filter(
        RentalIntegration.rental_id == request.rental_id,
        RentalIntegration.channel_type == request.channel_type
    ).first()

    config_str = json.dumps(request.config)

    if integration:
        # Update existing
        integration.is_enabled = 1 if request.is_enabled else 0
        integration.config_json = config_str
        integration.platform_user_id = request.platform_user_id
        integration.last_active_at = datetime.utcnow()
    else:
        # Create new
        integration = RentalIntegration(
            rental_id=request.rental_id,
            channel_type=request.channel_type,
            is_enabled=1 if request.is_enabled else 0,
            config_json=config_str,
            platform_user_id=request.platform_user_id
        )
        db.add(integration)

    db.commit()
    db.refresh(integration)

    return {
        "id": integration.id,
        "rental_id": integration.rental_id,
        "channel_type": integration.channel_type,
        "is_enabled": bool(integration.is_enabled),
        "platform_user_id": integration.platform_user_id,
        "config": json.loads(integration.config_json),
        "last_active_at": integration.last_active_at
    }

@router.delete("/{rental_id}/{channel_type}")
def delete_integration(rental_id: int, channel_type: str, db: Session = Depends(get_db)):
    """Remove an integration."""
    integration = db.query(RentalIntegration).filter(
        RentalIntegration.rental_id == rental_id,
        RentalIntegration.channel_type == channel_type
    ).first()
    
    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    
    db.delete(integration)
    db.commit()
    return {"success": True}
