# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from fastapi.security import OAuth2PasswordBearer

# ====================================================================
# SCHEMAS BASE (Para leitura e saída)
# ====================================================================

class ApiKeyBase(BaseModel):
    key_value: str = Field(..., max_length=255)
    purpose: str = Field(..., max_length=100)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True 

class RpaBotBase(BaseModel):
    code: str = Field(..., max_length=50)
    description: Optional[str] = None
    system_target: Optional[str] = Field(None, max_length=100)
    status: str = "Deployed"
    last_successful_run_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ClientBase(BaseModel):
    name: str = Field(..., max_length=150)
    status: str = "Active"

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: EmailStr
    name: str = Field(..., max_length=100)
    role: str = "client_admin"
    is_active: bool = True

    class Config:
        from_attributes = True

# ====================================================================
# SCHEMAS DE CRIAÇÃO (Entrada)
# ====================================================================

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    client_id: Optional[int] = None

class ClientCreate(ClientBase):
    pass

class RpaBotCreate(RpaBotBase):
    client_id: int

class ApiKeyCreate(ApiKeyBase):
    client_id: Optional[int] = None

# ====================================================================
# SCHEMAS COMPLETOS (Saída e Relações)
# ====================================================================

class ApiKey(ApiKeyBase):
    id: int
    client_id: Optional[int] = None

class RpaBot(RpaBotBase):
    id: int
    client_id: int

class User(UserBase):
    id: int
    client_id: Optional[int] = None

class Client(ClientBase):
    id: int
    contact_user_id: Optional[int] = None
    
# Os relacionamentos aninhados nos Schemas foram removidos na fase de depuração para estabilidade.


# ====================================================================
# SCHEMAS DE AUTENTICAÇÃO JWT
# ====================================================================
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ====================================================================
# NOVOS: SCHEMAS DE LOGS EXTERNOS
# ====================================================================

class RpaLogResponse(BaseModel):
    status: str
    total_resultados: int
    # Usamos 'dict' aqui porque a estrutura do log externo é variável (JSON)
    logs: List[dict]
