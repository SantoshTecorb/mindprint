from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import litellm
import os

from ...database import get_db
from ...models import MemoryData, Rental
from ...schemas import ConsultRequest, ConsultResponse
from ...core.config import settings

router = APIRouter(prefix="/consult", tags=["consult"])

@router.post("", response_model=ConsultResponse)
async def consult_persona(request: ConsultRequest, db: Session = Depends(get_db)):
    """The Consulting AI endpoint for buyers."""
    # 1. Validate Token and Usage
    rental = db.query(Rental).filter_by(token=request.token).first()
    if not rental:
        raise HTTPException(status_code=403, detail="Invalid or expired token")
    
    if rental.usage_current >= rental.usage_limit:
        raise HTTPException(status_code=403, detail="Usage limit exceeded for this token")
        
    seller_id = rental.seller_user_id
    
    # 2. Retrieve Seller's Cognition Profile
    cognition = db.query(MemoryData).filter(
        MemoryData.user_id == seller_id,
        MemoryData.file_path.like("%cognition.md")
    ).order_by(MemoryData.scanned_at.desc()).first()
    
    if not cognition:
        raise HTTPException(status_code=404, detail="Cognitive profile not found for this persona")
        
    # 3. Construct the LLM Prompt
    system_prompt = f"""You are acting as a digital twin (Cognitive Persona) of a specialized professional. 
Your behavior and decision-making patterns are defined by the following distilled cognitive profile:

--- COGNITIVE PROFILE ---
{cognition.content}
--- END PROFILE ---

Answer the user's question as if you are this person. If the profile contains specific constraints or styles, follow them strictly.
Redact any PII if it inadvertently appears.
"""

    try:
        # 4. Call LiteLLM
        response = litellm.completion(
            model=settings.CONSULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ]
        )
        
        answer = response.choices[0].message.content
        
        # 5. Increment Usage
        rental.usage_current += 1
        db.commit()

        return {
            "success": True,
            "answer": answer,
            "persona_id": seller_id,
            "scanned_at": cognition.scanned_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
