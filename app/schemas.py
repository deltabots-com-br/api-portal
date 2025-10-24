# app/schemas.py (Simplificado)

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
# REMOVIDO: from fastapi.security import OAuth2PasswordBearer
# REMOVIDO: from fastapi.security import OAuth2PasswordBearer

# ... (outros schemas permanecem os mesmos) ...

class UserBase(BaseModel):
    email: EmailStr
# ...

# REMOVIDO: Token e TokenData

# NOVO: Esquema de segurança para API Key (para uso no main.py)
from fastapi.security import APIKeyHeader
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)
