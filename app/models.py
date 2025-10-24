# app/models.py (Versão FINAL - Reorganizada para evitar Referência)

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship 
from .database import Base

# ====================================================================
# Classes SEM FKs de saída (definidas primeiro)
# ====================================================================

# 1. API KEY MODEL
class ApiKey(Base):
    __tablename__ = "api_keys"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, index=True)
    key_value = Column(String(255), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True) 
    purpose = Column(String(100), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# 2. RPA BOT MODEL
class RpaBot(Base):
    __tablename__ = "rpa_bots"
    __table_args__ = {'schema': 'public'} 

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=False) 
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    system_target = Column(String(100), nullable=True)
    status = Column(String(20), default="Deployed", nullable=False)
    last_successful_run_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# ====================================================================
# Classes com FKs de entrada (definidas por último)
# ====================================================================

# 3. CLIENT MODEL
class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {'schema': 'public'} 

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    contact_user_id = Column(Integer, unique=True, nullable=True) 
    status = Column(String(20), default="Active", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)


# 4. USER MODEL
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False) 
    role = Column(String(50), default="client_admin", nullable=False)
    
    # FK para clients
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="RESTRICT"), nullable=True) 
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
# OBS: O erro de FK (NoReferencedTableError) sumirá porque 'clients' é definida antes de 'users'.
