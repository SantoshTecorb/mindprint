import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
import sqlite3
from contextlib import asynccontextmanager

# Config
DATA_DIR = "data"
DB_FILE = "mindprint.db"
os.makedirs(DATA_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personas (
            id TEXT PRIMARY KEY,
            auth_key TEXT,
            filepath TEXT,
            created_at DATETIME
        )
    ''')
    conn.commit()
    conn.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="MindPrint Persona API", lifespan=lifespan)

class UploadRequest(BaseModel):
    auth_key: str
    twin_content: str

@app.post("/personas/upload")
async def upload_persona(req: UploadRequest):
    # In a real app, validate auth_key against a user database
    if not req.auth_key:
        raise HTTPException(status_code=400, detail="Missing auth key")
    if not req.twin_content:
        raise HTTPException(status_code=400, detail="Twin content is empty")
        
    # Generate short UUID (e.g. 'A7xF21')
    persona_id = uuid.uuid4().hex[:6]
    filepath = os.path.join(DATA_DIR, f"{persona_id}.md")
    
    # Save the markdown file
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(req.twin_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
        
    # Save metadata to DB
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO personas (id, auth_key, filepath, created_at) VALUES (?, ?, ?, ?)",
            (persona_id, req.auth_key, filepath, datetime.utcnow())
        )
        conn.commit()
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update database: {e}")
        
    return {
        "status": "success",
        "persona_id": persona_id,
        "message": "Persona saved successfully"
    }

@app.get("/personas/{persona_id}")
async def get_persona(persona_id: str):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM personas WHERE id = ?", (persona_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Persona not found")
        
    filepath = row[0]
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Persona file missing on disk")
        
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    return Response(content=content, media_type="text/markdown")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
