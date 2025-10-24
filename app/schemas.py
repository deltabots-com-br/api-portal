# app/schemas.py

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# ====================================================================
# SCHEMAS BASE (Dados que podem ser lidos)
# Usados para formatar a resposta da API (Response Model)
# ====================================================================

class ApiKeyBase(BaseModel):
    key_value: str = Field(..., max_length=255)
    purpose: str = Field(..., max_length=100)
    expires_at: Optional[datetime] = None
    is_active: bool = True
    
    class Config:
        from_attributes = True # Permite mapeamento de objetos ORM

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
# SCHEMAS DE CRIAÇÃO (Dados de entrada para POST/PUT)
# ====================================================================

# Schemas de Criação de Usuário
class UserCreate(UserBase):
    password: str = Field(..., min_length=6)
    client_id: Optional[int] = None

# Schemas de Criação de Cliente
class ClientCreate(ClientBase):
    pass

# Schemas de Criação de Robô
class RpaBotCreate(RpaBotBase):
    client_id: int

# Schemas de Criação de ApiKey
class ApiKeyCreate(ApiKeyBase):
    client_id: Optional[int] = None


# ====================================================================
# SCHEMAS COMPLETOS (Incluindo IDs e Relacionamentos)
# Usados para representar o objeto completo na saída
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
    bots: List[RpaBot] = [] # Opcional, se quisermos carregar todos os robôs do cliente

class Client(ClientBase):
    id: int
    contact_user_id: Optional[int] = None
    
    # Relações aninhadas (para leitura)
    users: List[User] = []
    bots: List[RpaBot] = []
