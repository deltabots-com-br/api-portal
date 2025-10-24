from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship
from .database import Base

# ====================================================================
# 1. CLIENT MODEL
# ====================================================================
class Client(Base):
    __tablename__ = "clients"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(150), unique=True, nullable=False)
    # Contact user ID ainda não é uma FK no ORM, apenas no DB
    contact_user_id = Column(Integer, unique=True, nullable=True) 
    status = Column(String(20), default="Active", nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", back_populates="client", foreign_keys="[User.client_id]") # <--- EXPLICITA FK
    bots = relationship("RpaBot", back_populates="client")
    api_keys = relationship("ApiKey", back_populates="client")


# ====================================================================
# 2. USER MODEL
# ====================================================================
class User(Base):
    __tablename__ = "users"
    __table_args__ = {'schema': 'public'}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False) 
    role = Column(String(50), default="client_admin", nullable=False)
    
    # A ÚLTIMA CORREÇÃO: Usar 'public.clients' minúsculo
    client_id = Column(Integer, ForeignKey("public.clients.id", ondelete="RESTRICT"), nullable=True) 
    
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Força a associação de volta (para evitar ambiguidade na configuração)
    client = relationship("Client", back_populates="users", foreign_keys="[User.client_id]") 


# ... (O restante dos modelos RpaBot e ApiKey deve usar o 'public.clients.id' no ForeignKey) ...
