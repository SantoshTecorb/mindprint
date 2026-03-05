from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
import requests
import json

from ...database import get_db
from ...models import RentalIntegration, Rental, MemoryData
from ...schemas import WhatsAppWebhook, WhatsAppLinkResponse, ConsultResponse
from ...core.config import settings

router = APIRouter(prefix="/whatsapp", tags=["whatsapp"])

# In a real prod environment, this would be an environment variable
BRIDGE_API_URL = "http://localhost:3001" 

@router.get("/link/{rental_id}", response_model=WhatsAppLinkResponse)
def get_whatsapp_qr(rental_id: int, db: Session = Depends(get_db)):
    """Request a QR code from the bridge to link a buyer's account."""
    # 1. Verify Rental
    rental = db.query(Rental).filter(Rental.id == rental_id).first()
    if not rental:
        raise HTTPException(status_code=404, detail="Rental not found")

    try:
        # 2. Call Bridge to get QR
        # This assumes the bridge has an endpoint to generate a new session
        response = requests.get(f"{BRIDGE_API_URL}/session/qr?id={rental_id}")
        data = response.json()
        
        return {
            "success": True,
            "qr_code": data.get("qr"),
            "status": "waiting_for_scan"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "bridge_unreachable",
            "error": str(e)
        }

@router.post("/webhook")
async def whatsapp_webhook(payload: WhatsAppWebhook, db: Session = Depends(get_db)):
    """Receive messages from the WhatsApp bridge and route to AI."""
    # 1. Find Rental by Sender Phone Number
    # We look for an integration where platform_user_id matches the sender
    integration = db.query(RentalIntegration).filter(
        RentalIntegration.platform_user_id == payload.sender,
        RentalIntegration.channel_type == "whatsapp",
        RentalIntegration.is_enabled == 1
    ).first()

    if not integration:
        # Log this: Message from unknown WhatsApp number
        return {"status": "ignored", "reason": "unlinked_sender"}

    rental = db.query(Rental).filter(Rental.id == integration.rental_id).first()
    if not rental or (rental.usage_current >= rental.usage_limit):
        return {"status": "error", "reason": "auth_or_usage_failed"}

    # 2. Trigger Consultation Logic (Re-using core logic)
    # Note: In a real app, refactor consult_persona into a service function
    # For now, let's keep it simple
    from .consult import consult_persona
    from ...schemas import ConsultRequest
    
    try:
        # We simulate a consult request using the rental token
        ai_response = await consult_persona(
            ConsultRequest(token=rental.token, query=payload.content),
            db=db
        )
        
        # 3. Send Response back to WhatsApp Bridge
        requests.post(f"{BRIDGE_API_URL}/send", json={
            "to": payload.sender,
            "message": ai_response["answer"],
            "session_id": rental.id
        })
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
