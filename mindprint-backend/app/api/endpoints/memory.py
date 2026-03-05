from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Optional
import json
from datetime import datetime

from ...database import get_db
from ...models import MemoryData
from ...schemas import MemoryUploadRequest, MemoryResponse

router = APIRouter(prefix="/memory", tags=["memory"])

@router.post("")
def store_memory(request: MemoryUploadRequest, db: Session = Depends(get_db)):
    stored_count = 0
    updated_count = 0
    
    for item in request.memory_data:
        existing = db.query(MemoryData).filter_by(
            file_path=item.file_path,
            file_hash=item.file_hash
        ).first()
        
        metadata_str = json.dumps(item.metadata)
        
        if existing:
            existing.content = item.content
            existing.scanned_at = datetime.utcnow()
            existing.extra_metadata = metadata_str
            updated_count += 1
        else:
            new_mem = MemoryData(
                file_path=item.file_path,
                content=item.content,
                file_hash=item.file_hash,
                user_id=item.user_id,
                extra_metadata=metadata_str
            )
            db.add(new_mem)
            stored_count += 1
            
    db.commit()
    return {"success": True, "stored": stored_count, "updated": updated_count}

@router.get("", response_model=dict)
def get_memories(
    user_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(MemoryData)
    if user_id:
        query = query.filter(MemoryData.user_id == user_id)
    
    memories = query.order_by(MemoryData.scanned_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "success": True,
        "count": len(memories),
        "memories": [
            {
                "id": m.id,
                "file_path": m.file_path,
                "content": m.content,
                "scanned_at": m.scanned_at,
                "user_id": m.user_id,
                "metadata": json.loads(m.extra_metadata) if m.extra_metadata else {}
            }
            for m in memories
        ]
    }

@router.get("/stats")
def get_memory_stats(db: Session = Depends(get_db)):
    total = db.query(func.count(MemoryData.id)).scalar()
    unique_files = db.query(func.count(func.distinct(MemoryData.file_path))).scalar()
    last_scan = db.query(func.max(MemoryData.scanned_at)).scalar()
    
    return {
        "success": True,
        "stats": {
            "total_memories": total,
            "unique_files": unique_files,
            "last_scan": last_scan.isoformat() if last_scan else None
        }
    }
