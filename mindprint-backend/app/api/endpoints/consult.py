from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ...database import get_db
from ...models import MemoryData, Rental
from ...schemas import ConsultRequest, ConsultResponse
from ...core.config import settings
from ...services.skills import SkillDiscoveryService
from ...services.memory import MemoryService
import json
import os

# Set Groq API Key for LiteLLM if provided
if settings.GROQ_API_KEY:
    os.environ["GROQ_API_KEY"] = settings.GROQ_API_KEY

router = APIRouter(prefix="/consult", tags=["consult"])

# Initialize Services
memory_service = MemoryService()

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
    
    # 2. Dynamic Skill Discovery & Tracking
    skill_service = SkillDiscoveryService(db)
    detected_skill_slug = await skill_service.detect_intent(request.query)
    
    skill_instructions = ""
    if detected_skill_slug:
        # Fetch instructions (cached or from web)
        skill_instructions = skill_service.get_skill_instructions(detected_skill_slug)
        # Track usage for this user
        skill_service.track_usage(rental.id, detected_skill_slug)
        
    # 3. Long-Term Semantic Memory (Mem0)
    # Use the rental token as a unique user identifier for memory
    past_facts = memory_service.get_relevant_memories(user_id=request.token, query=request.query)

    # 4. Retrieve Seller's Cognition Architecture (All 10 files)
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
        
    # 5. Construct the LLM Prompt with rich context
    architecture_context = ""
    for cf in sorted(cognition_files, key=lambda x: x.file_path):
        filename = os.path.basename(cf.file_path)
        architecture_context += f"\n### {filename}\n{cf.content}\n"

    system_prompt = f"""You are acting as a digital twin (Cognitive Persona) of a specialized professional. 
Your behavior, decision-making, values, and execution style are defined by the following distilled cognitive architecture:

--- FULL COGNITIVE ARCHITECTURE ---
{architecture_context}
--- END ARCHITECTURE ---

--- PROCEDURAL KNOWLEDGE (SKILL-BASED EXPERTISE) ---
{skill_instructions if skill_instructions else "No specialized external tools currently required for this query."}
--- END SKILLS ---

--- LONG-TERM CONTEXT (PAST FACTS & PREFERENCES) ---
{past_facts if past_facts else "No relevant past context for this user."}
--- END MEMORY ---

Answer the user's question as if you are this person. 
Strictly follow the 'Execution Operating System' and 'Decision Tree System' defined in the architecture.
Ensure your tone matches the 'Communication Layer' (File 10).
If procedural knowledge is provided above, use it to provide specific, technical guidance as an expert in that domain.
Redact any PII if it inadvertently appears.
"""

    try:
        # 6. Call LiteLLM
        import litellm
        response = litellm.completion(
            model=settings.CONSULT_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.query}
            ]
        )
        
        answer = response.choices[0].message.content
        
        # 7. Update Long-Term Memory (Mem0)
        # Extract new facts from this turn so they can be retrieved later.
        memory_service.add_interaction(user_id=request.token, query=request.query, answer=answer)
        
        # 8. Increment Usage
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
