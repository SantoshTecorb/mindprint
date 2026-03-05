from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class MemoryItem(BaseModel):
    file_path: str
    content: str
    file_hash: str
    user_id: Optional[str] = "default"
    metadata: Optional[Dict[str, Any]] = {}

class MemoryUploadRequest(BaseModel):
    memory_data: List[MemoryItem]

class MemoryResponse(BaseModel):
    id: int
    file_path: str
    content: str
    scanned_at: datetime
    user_id: Optional[str]
    metadata: Dict[str, Any]

class ConsultRequest(BaseModel):
    token: str
    query: str

class ConsultResponse(BaseModel):
    success: bool
    answer: str
    persona_id: str
    scanned_at: datetime

class TelemetryData(BaseModel):
    user_id: str
    hostname: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    python_version: Optional[str] = None
    install_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class RentalCreateRequest(BaseModel):
    seller_user_id: str
    usage_limit: Optional[int] = 10

class RentalResponse(BaseModel):
    success: bool
    token: str
    seller_user_id: str
    usage_limit: int
    usage_current: int

class PersonaProfile(BaseModel):
    user_id: str
    metadata: Dict[str, Any]
    last_seen: datetime
    expertise_preview: Optional[str] = None
    asset_count: int

class PersonaDiscoveryResponse(BaseModel):
    success: bool
    personas: List[PersonaProfile]

class IntegrationBase(BaseModel):
    channel_type: str
    is_enabled: Optional[bool] = True
    config: Dict[str, Any]
    platform_user_id: Optional[str] = None

class IntegrationCreate(IntegrationBase):
    rental_id: int

class IntegrationResponse(BaseModel):
    id: int
    rental_id: int
    channel_type: str
    is_enabled: bool
    config: Dict[str, Any]
    platform_user_id: Optional[str]
    last_active_at: datetime

class WhatsAppWebhook(BaseModel):
    sender: str  # The buyer's phone number
    content: str # The incoming message text
    bridge_token: Optional[str] = None # Optional auth token

class WhatsAppLinkResponse(BaseModel):
    success: bool
    qr_code: Optional[str] = None
    status: str
