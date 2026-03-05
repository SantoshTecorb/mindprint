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
    
    # 2. Retrieve Seller's Cognition Architecture (All 10 files)
    cognition_files = db.query(MemoryData).filter(
        MemoryData.user_id == seller_id,
        (MemoryData.file_path.like("%01_%") | 
         MemoryData.file_path.like("%02_%") |
         MemoryData.file_path.like("%03_%") |
         MemoryData.file_path.like("%04_%") |
         MemoryData.file_path.like("%05_%") |
         MemoryData.file_path.like("%06_%") |
         MemoryData.file_path.like("%07_%") |
         MemoryData.file_path.like("%08_%") |
         MemoryData.file_path.like("%09_%") |
         MemoryData.file_path.like("%10_%"))
    ).all()
    
    # Store the primary cognition file for scanned_at in return, or the first of the 10 files
    primary_cognition_file = None

    if not cognition_files:
        # Fallback to general profile if architecture isn't found
        fallback_cognition_files = db.query(MemoryData).filter(
            MemoryData.user_id == seller_id,
            MemoryData.file_path.like("%cognition.md")
        ).all()
        if fallback_cognition_files:
            cognition_files = fallback_cognition_files
            primary_cognition_file = fallback_cognition_files[0]

    if not cognition_files:
        raise HTTPException(status_code=404, detail="Cognitive profile not found for this persona")
    
    if not primary_cognition_file and cognition_files:
        primary_cognition_file = cognition_files[0] # Use the first file if no specific primary was set
        
    # 3. Construct the LLM Prompt with rich context
    architecture_context = ""
    for cf in sorted(cognition_files, key=lambda x: x.file_path):
        filename = os.path.basename(cf.file_path)
        architecture_context += f"\n### {filename}\n{cf.content}\n"

    system_prompt = f"""You are acting as a digital twin (Cognitive Persona) of a specialized professional. 
Your behavior, decision-making, values, and execution style are defined by the following distilled cognitive architecture:

--- FULL COGNITIVE ARCHITECTURE ---
{architecture_context}
--- END ARCHITECTURE ---

Answer the user's question as if you are this person. 
Strictly follow the 'Execution Operating System' and 'Decision Tree System' defined in the context.
Ensure your tone matches the 'Communication Layer' (File 10).
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
            "scanned_at": primary_cognition_file.scanned_at
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Error: {str(e)}")
