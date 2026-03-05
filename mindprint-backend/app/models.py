from sqlalchemy import Column, Integer, String, Text, DateTime, UniqueConstraint
from datetime import datetime
from .database import Base

class MemoryData(Base):
    __tablename__ = 'memory_data'
    id = Column(Integer, primary_key=True)
    file_path = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    file_hash = Column(String(32), nullable=False)
    scanned_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(String(100))
    extra_metadata = Column(Text)
    __table_args__ = (UniqueConstraint('file_path', 'file_hash', name='uix_file_path_hash'),)

class Rental(Base):
    __tablename__ = 'rentals'
    id = Column(Integer, primary_key=True)
    token = Column(String(100), unique=True, nullable=False)
    seller_user_id = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    usage_limit = Column(Integer, default=10) # Max messages allowed
    usage_current = Column(Integer, default=0) # Count of messages used

class Seller(Base):
    __tablename__ = 'sellers'
    user_id = Column(String(100), primary_key=True)
    hostname = Column(Text)
    os_name = Column(Text)
    os_version = Column(Text)
    python_version = Column(Text)
    install_path = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text)

class Buyer(Base):
    __tablename__ = 'buyers'
    user_id = Column(String(100), primary_key=True)
    hostname = Column(Text)
    os_name = Column(Text)
    os_version = Column(Text)
    python_version = Column(Text)
    install_path = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    metadata_json = Column(Text)

class RentalIntegration(Base):
    __tablename__ = 'rental_integrations'
    id = Column(Integer, primary_key=True)
    rental_id = Column(Integer, nullable=False) # Linked to rentals.id
    channel_type = Column(String(50), nullable=False) # 'whatsapp', 'telegram', 'slack'
    platform_user_id = Column(String(100)) # The buyer's ID on that platform (e.g. phone number or telegram ID)
    is_enabled = Column(Integer, default=1)
    config_json = Column(Text) # JSON string of credentials/webhook info
    last_active_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (UniqueConstraint('rental_id', 'channel_type', name='uix_rental_channel'),)
